from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import os
import requests
import time
from dotenv import load_dotenv
import asyncio

from llm_generator import LLMGenerator
from github_manager import GitHubManager
from attachment_handler import AttachmentHandler
from secret_scanner import SecretScanner

load_dotenv()

app = FastAPI(title="LLM App Builder")

# Initialize services
llm_gen = LLMGenerator()
github_mgr = GitHubManager()
attachment_handler = AttachmentHandler()
secret_scanner = SecretScanner()

# Store for tracking repos by task
task_repos = {}

class Attachment(BaseModel):
    name: str
    url: str

class BuildRequest(BaseModel):
    email: str
    secret: str
    task: str
    round: int
    nonce: str
    brief: str
    checks: List[str]
    evaluation_url: str
    attachments: Optional[List[Attachment]] = []

class EvaluationPayload(BaseModel):
    email: str
    task: str
    round: int
    nonce: str
    repo_url: str
    commit_sha: str
    pages_url: str

def submit_to_evaluation(payload: EvaluationPayload, evaluation_url: str):
    """Submit results to evaluation API with exponential backoff retry"""
    delays = [1, 2, 4, 8]
    
    for attempt, delay in enumerate(delays, 1):
        try:
            print(f"Submitting to evaluation API (attempt {attempt})...")
            response = requests.post(
                evaluation_url,
                json=payload.dict(),
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"✓ Successfully submitted to evaluation API")
                return True
            else:
                print(f"✗ Evaluation API returned {response.status_code}")
                
        except Exception as e:
            print(f"✗ Error submitting to evaluation API: {e}")
        
        if attempt < len(delays):
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
    print("✗ Failed to submit to evaluation API after all retries")
    return False

def build_and_deploy(request: BuildRequest):
    """Background task to build and deploy the application"""
    import time
    start_time = time.time()
    MAX_TIME_SECONDS = 600  # 10 minutes as per requirements
    
    try:
        print(f"\n{'='*60}")
        print(f"Building app for task: {request.task} (Round {request.round})")
        print(f"{'='*60}")
        
        # Process attachments
        print("Processing attachments...")
        processed_attachments = attachment_handler.process_attachments(
            [a.dict() for a in request.attachments]
        )
        
        # Generate code using LLM
        print("Generating code with LLM...")
        files = llm_gen.generate_app_code(
            brief=request.brief,
            checks=request.checks,
            attachments=[a.dict() for a in request.attachments],
            processed_attachments=processed_attachments
        )
        
        # Deploy to GitHub
        if request.round == 1:
            print(f"Creating new GitHub repository...")
            result = github_mgr.create_and_deploy_repo(request.task, files)
            task_repos[request.task] = result["repo_url"]
            print(f"✓ Repository created: {result['repo_url']}")
        else:
            # Round 2+: Update existing repo
            print(f"Updating existing repository...")
            repo_url = task_repos.get(request.task)
            if not repo_url:
                print(f"✗ No existing repo found for task {request.task}")
                return
            
            commit_sha = github_mgr.update_repo(repo_url, files)
            
            # Extract username and repo name from URL
            parts = repo_url.rstrip('/').split('/')
            username = parts[-2]
            repo_name = parts[-1]
            
            result = {
                "repo_url": repo_url,
                "commit_sha": commit_sha,
                "pages_url": f"https://{username}.github.io/{repo_name}/"
            }
            print(f"✓ Repository updated with commit: {commit_sha[:7]}")
        
        print(f"✓ GitHub Pages URL: {result['pages_url']}")
        
        # Check if we're within the 10-minute time limit
        elapsed_time = time.time() - start_time
        if elapsed_time >= MAX_TIME_SECONDS:
            print(f"⚠️  WARNING: Exceeded 10 minute time limit ({elapsed_time:.1f}s)")
        else:
            print(f"✓ Completed in {elapsed_time:.1f} seconds (within 10 minute limit)")
        
        # Wait a moment for GitHub to process
        print("Waiting for GitHub to process deployment...")
        time.sleep(3)
        
        # Submit to evaluation API
        print("Submitting to evaluation API...")
        payload = EvaluationPayload(
            email=request.email,
            task=request.task,
            round=request.round,
            nonce=request.nonce,
            repo_url=result["repo_url"],
            commit_sha=result["commit_sha"],
            pages_url=result["pages_url"]
        )
        
        submit_to_evaluation(payload, request.evaluation_url)
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n✗ ERROR in build_and_deploy: {e}")
        import traceback
        traceback.print_exc()

@app.post("/build")
async def build_app(request: BuildRequest, background_tasks: BackgroundTasks):
    """Main endpoint to receive build requests"""
    
    # Verify secret
    expected_secret = os.getenv("SECRET_KEY")
    if not expected_secret:
        raise HTTPException(status_code=500, detail="Server configuration error")
    
    if request.secret != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    print(f"\n✓ Received valid build request for task: {request.task} (Round {request.round})")
    
    # Start background task
    background_tasks.add_task(build_and_deploy, request)
    
    # Return 200 immediately
    return {
        "status": "accepted",
        "message": f"Building app for task {request.task}, round {request.round}",
        "task": request.task,
        "round": request.round
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LLM App Builder",
        "status": "running",
        "endpoints": {
            "build": "/build",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "github_configured": bool(os.getenv("GITHUB_TOKEN")),
        "llm_configured": bool(os.getenv("LLM_API_KEY")),
        "secret_configured": bool(os.getenv("SECRET_KEY"))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)