from github import Github, GithubException
import os
import base64
from typing import Dict

class GitHubManager:
    def __init__(self):
        self.g = Github(os.getenv("GITHUB_TOKEN"))
        self.user = self.g.get_user()
    
    def create_and_deploy_repo(self, task_id: str, files: Dict[str, str]) -> Dict[str, str]:
        """Create repo, push files, enable GitHub Pages"""
        
        repo_name = f"app-{task_id}"
        
        try:
            # Create repository
            repo = self.user.create_repo(
                name=repo_name,
                description=f"Auto-generated app for task {task_id}",
                private=False,
                auto_init=True
            )
            
            # Add MIT License
            self._add_license(repo)
            
            # Push files
            # Push files (create or update if they already exist)
            for filename, content in files.items():
                try:
                    repo.create_file(
                        path=filename,
                        message=f"Add {filename}",
                        content=content
                    )
                except GithubException as e:
                    # Handle case where file already exists (422 "sha wasn't supplied")
                    if e.status == 422 and "sha" in str(e.data):
                        try:
                            existing_file = repo.get_contents(filename)
                            repo.update_file(
                                path=filename,
                                message=f"Update {filename}",
                                content=content,
                                sha=existing_file.sha
                            )
                            print(f"✓ Updated existing file: {filename}")
                        except Exception as inner_e:
                            print(f"✗ Failed to update {filename}: {inner_e}")
                    else:
                        print(f"✗ Error creating {filename}: {e.data}")

            
            # Enable GitHub Pages
            self._enable_github_pages(repo)
            
            # Get latest commit SHA
            commit_sha = repo.get_commits()[0].sha
            
            return {
                "repo_url": repo.html_url,
                "commit_sha": commit_sha,
                "pages_url": f"https://{self.user.login}.github.io/{repo_name}/"
            }
            
        except GithubException as e:
            print(f"GitHub error: {e}")
            raise
    
    def _add_license(self, repo):
        """Add MIT License"""
        license_content = """MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy..."""
        
        repo.create_file(
            path="LICENSE",
            message="Add MIT License",
            content=license_content
        )
    
    def _enable_github_pages(self, repo):
        """Enable GitHub Pages for the repo"""
        try:
            repo.create_page(build_type="legacy", source={"branch": "main", "path": "/"})
        except:
            # Pages might already be enabled
            pass
    
    def update_repo(self, repo_url: str, files: Dict[str, str]) -> str:
        """Update existing repo with new files"""
        repo_name = repo_url.split("/")[-1]
        repo = self.g.get_repo(f"{self.user.login}/{repo_name}")
        
        for filename, content in files.items():
            try:
                # Get existing file
                file = repo.get_contents(filename)
                repo.update_file(
                    path=filename,
                    message=f"Update {filename}",
                    content=content,
                    sha=file.sha
                )
            except:
                # File doesn't exist, create it
                repo.create_file(
                    path=filename,
                    message=f"Add {filename}",
                    content=content
                )
        
        return repo.get_commits()[0].sha