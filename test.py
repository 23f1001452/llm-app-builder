#!/usr/bin/env python3
"""
Test script to verify the LLM App Builder setup
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    print(f"✓ {text}")

def print_error(text):
    print(f"✗ {text}")

def print_warning(text):
    print(f"⚠ {text}")

def test_environment_variables():
    """Test if all required environment variables are set"""
    print_header("Testing Environment Variables")
    
    load_dotenv()
    
    required_vars = {
        'GITHUB_TOKEN': 'GitHub Personal Access Token',
        'LLM_API_KEY': 'OpenAI API Key',
        'SECRET_KEY': 'Your secret from Google Form'
    }
    
    all_set = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and len(value) > 10:
            print_success(f"{var} is set ({description})")
        else:
            print_error(f"{var} is NOT set or too short ({description})")
            all_set = False
    
    return all_set

def test_github_token():
    """Test if GitHub token is valid"""
    print_header("Testing GitHub Token")
    
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print_error("GitHub token not found")
        return False
    
    try:
        response = requests.get(
            'https://api.github.com/user',
            headers={'Authorization': f'token {token}'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"GitHub token is valid for user: {data['login']}")
            print_success(f"Remaining API calls: {response.headers.get('X-RateLimit-Remaining', 'Unknown')}")
            return True
        else:
            print_error(f"GitHub token is invalid: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error testing GitHub token: {e}")
        return False

def test_openai_key():
    """Test if OpenAI API key is valid"""
    print_header("Testing OpenAI API Key")
    
    key = os.getenv('LLM_API_KEY')
    if not key:
        print_error("OpenAI API key not found")
        return False
    
    try:
        import openai
        client = openai.OpenAI(api_key=key,base_url="https://api.groq.com/openai/v1")
        
        # Try a minimal API call
        message = client.chat.completions.create(
            model="groq/compound-mini",
            max_tokens=50,
            messages=[{"role": "user", "content": "Hi"}]
        )
        
        print_success("OpenAI API key is valid")
        print_success(f"Model accessed: groq/compound-mini")
        return True
        
    except Exception as e:
        print_error(f"OpenAI API key is invalid: {e}")
        return False

def test_dependencies():
    """Test if all required packages are installed"""
    print_header("Testing Python Dependencies")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'github',
        'openai',
        'requests',
        'dotenv',
        'pydantic'
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"{package} is installed")
        except ImportError:
            print_error(f"{package} is NOT installed")
            all_installed = False
    
    return all_installed

def test_api_server(base_url='http://localhost:8000'):
    """Test if the API server is running"""
    print_header(f"Testing API Server at {base_url}")
    
    try:
        # Test health endpoint
        response = requests.get(f'{base_url}/health', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"API server is running")
            print(f"   Status: {data.get('status')}")
            print(f"   GitHub configured: {data.get('github_configured')}")
            print(f"   LLM configured: {data.get('llm_configured')}")
            print(f"   Secret configured: {data.get('secret_configured')}")
            return True
        else:
            print_error(f"API server responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_warning("API server is not running")
        print("   Start it with: python main.py")
        return False
    except Exception as e:
        print_error(f"Error testing API server: {e}")
        return False

def test_build_endpoint(base_url='http://localhost:8000'):
    """Test the build endpoint with a sample request"""
    print_header(f"Testing Build Endpoint")
    
    secret = os.getenv('SECRET_KEY')
    if not secret:
        print_error("SECRET_KEY not set, skipping build test")
        return False
    
    test_payload = {
        "email": "test@example.com",
        "secret": secret,
        "task": "test-simple-page",
        "round": 1,
        "nonce": "test-nonce-12345",
        "brief": "Create a simple HTML page with an h1 that says 'Test Page'",
        "checks": ["Page has h1 tag"],
        "evaluation_url": "https://httpbin.org/post",
        "attachments": []
    }
    
    try:
        response = requests.post(
            f'{base_url}/build',
            json=test_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Build endpoint accepted the request")
            print(f"   Message: {data.get('message')}")
            print_warning("Check server logs to see build progress")
            return True
        else:
            print_error(f"Build endpoint returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error testing build endpoint: {e}")
        return False

def main():
    """Run all tests"""
    print_header("🧪 LLM App Builder - System Test")
    print("This script will verify your setup is correct\n")
    
    results = {
        'Environment Variables': test_environment_variables(),
        'Python Dependencies': test_dependencies(),
        'GitHub Token': test_github_token(),
        'OpenAI API Key': test_openai_key(),
        'API Server': test_api_server(),
    }
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("\n🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. If server is not running: python main.py")
        print("2. Deploy to a public URL (Railway, Render, etc.)")
        print("3. Submit your API URL to instructors")
        return 0
    else:
        print_error("\n❌ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Make sure .env file exists and has correct values")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Start the server: python main.py")
        return 1

if __name__ == '__main__':
    sys.exit(main())