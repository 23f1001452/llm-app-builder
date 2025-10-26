from github import Github, GithubException
import os
import time
import requests
from typing import Dict

class GitHubManager:
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        
        self.g = Github(token)
        self.user = self.g.get_user()
        print(f"GitHub authenticated as: {self.user.login}")
    
    def create_and_deploy_repo(self, task_id: str, files: Dict[str, str]) -> Dict[str, str]:
        """Create repository, push files, enable GitHub Pages"""
        
        # Create a clean repo name
        repo_name = f"app-{task_id}".replace("_", "-").lower()
        
        try:
            print(f"Creating repository: {repo_name}")
            
            # Create repository
            repo = self.user.create_repo(
                name=repo_name,
                description=f"Auto-generated app for task {task_id}",
                private=False,
                auto_init=True,
                license_template="mit"  # GitHub will create MIT LICENSE automatically
            )
            
            print(f"Repository created: {repo.html_url}")
            
            # Wait for repo initialization
            time.sleep(2)
            
            # Push all files
            for filename, content in files.items():
                print(f"Adding file: {filename}")
                try:
                    # For files that might already exist (like README.md from auto_init)
                    # use update_or_create instead
                    self._update_or_create_file(repo, filename, content)
                except GithubException as e:
                    print(f"Warning: Could not create {filename}: {e}")
            
            # Enable GitHub Pages - use multiple methods for reliability
            print("Enabling GitHub Pages...")
            self._enable_github_pages(repo)
            
            # Trigger GitHub Pages build by making a small commit
            print("Triggering Pages deployment...")
            self._trigger_pages_build(repo)
            
            # Get latest commit SHA
            commits = list(repo.get_commits())
            commit_sha = commits[0].sha if commits else "main"
            
            pages_url = f"https://{self.user.login}.github.io/{repo_name}/"
            
            print(f"✓ Setup complete!")
            print(f"✓ Pages should be live in 1-2 minutes at: {pages_url}")
            
            return {
                "repo_url": repo.html_url,
                "commit_sha": commit_sha,
                "pages_url": pages_url
            }
            
        except GithubException as e:
            print(f"GitHub API error: {e}")
            # If repo already exists, try to use it
            if e.status == 422:
                print(f"Repository {repo_name} already exists, attempting to use it...")
                repo = self.g.get_repo(f"{self.user.login}/{repo_name}")
                
                # Update files
                for filename, content in files.items():
                    self._update_or_create_file(repo, filename, content)
                
                commits = list(repo.get_commits())
                commit_sha = commits[0].sha if commits else "main"
                
                return {
                    "repo_url": repo.html_url,
                    "commit_sha": commit_sha,
                    "pages_url": f"https://{self.user.login}.github.io/{repo_name}/"
                }
            raise
    
    def _enable_github_pages(self, repo):
        """Enable GitHub Pages for the repository using REST API"""
        
        # Method 1: Use REST API directly (most reliable)
        try:
            token = os.getenv("GITHUB_TOKEN")
            url = f"https://api.github.com/repos/{repo.full_name}/pages"
            
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "source": {
                    "branch": "main",
                    "path": "/"
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 201:
                print("✓ GitHub Pages enabled via REST API")
                return True
            elif response.status_code == 409:
                print("✓ GitHub Pages already enabled")
                return True
            else:
                print(f"REST API response: {response.status_code}")
                
        except Exception as e:
            print(f"REST API method: {e}")
        
        # Method 2: Create gh-pages branch (triggers auto-enable)
        try:
            main_branch = repo.get_branch("main")
            
            try:
                repo.create_git_ref(
                    ref="refs/heads/gh-pages",
                    sha=main_branch.commit.sha
                )
                print("✓ Created gh-pages branch")
            except:
                pass
                
        except Exception as e:
            print(f"Branch method: {e}")
        
        # Method 3: Set pages flag via PATCH
        try:
            token = os.getenv("GITHUB_TOKEN")
            url = f"https://api.github.com/repos/{repo.full_name}"
            
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {"has_pages": True}
            
            response = requests.patch(url, json=data, headers=headers)
            if response.status_code == 200:
                print("✓ GitHub Pages flag set")
                return True
                
        except Exception as e:
            print(f"PATCH method: {e}")
        
        print("✓ GitHub Pages setup completed")
        return True
    
    def update_repo(self, repo_url: str, files: Dict[str, str]) -> str:
        """Update existing repository with new files"""
        
        # Extract repo name from URL
        repo_name = repo_url.rstrip('/').split('/')[-1]
        repo_full_name = f"{self.user.login}/{repo_name}"
        
        print(f"Updating repository: {repo_full_name}")
        
        try:
            repo = self.g.get_repo(repo_full_name)
        except GithubException:
            print(f"Could not find repo {repo_full_name}")
            raise
        
        # Update each file
        for filename, content in files.items():
            self._update_or_create_file(repo, filename, content)
        
        # Get latest commit SHA
        commits = list(repo.get_commits())
        commit_sha = commits[0].sha if commits else "main"
        
        return commit_sha
    
    def _update_or_create_file(self, repo, filename: str, content: str):
        """Update file if it exists, create if it doesn't"""
        try:
            # Try to get existing file
            file_content = repo.get_contents(filename, ref="main")
            
            # Update existing file
            repo.update_file(
                path=filename,
                message=f"Update {filename}",
                content=content,
                sha=file_content.sha,
                branch="main"
            )
            print(f"Updated: {filename}")
            
        except GithubException as e:
            if e.status == 404:
                # File doesn't exist, create it
                repo.create_file(
                    path=filename,
                    message=f"Add {filename}",
                    content=content,
                    branch="main"
                )
                print(f"Created: {filename}")
            else:
                print(f"Error with {filename}: {e}")
                raise
    
    def _trigger_pages_build(self, repo):
        """Trigger a GitHub Pages build by creating an empty commit"""
        try:
            # Get the latest commit
            commits = list(repo.get_commits())
            if not commits:
                return
            
            # Create a dummy file to trigger rebuild (then delete it)
            try:
                repo.create_file(
                    path=".pages-trigger",
                    message="Trigger Pages build",
                    content="",
                    branch="main"
                )
                time.sleep(1)
                
                # Delete the dummy file
                file = repo.get_contents(".pages-trigger", ref="main")
                repo.delete_file(
                    path=".pages-trigger",
                    message="Remove trigger file",
                    sha=file.sha,
                    branch="main"
                )
                print("✓ Pages build triggered")
            except:
                pass
                
        except Exception as e:
            print(f"Trigger note: {e}")