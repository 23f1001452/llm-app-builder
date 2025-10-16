import openai
import os
from typing import List, Dict

class LLMGenerator:
    def __init__(self):
        self.client = openai.OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

    
    def generate_app_code(self, brief: str, checks: List[str], attachments: List[Dict]) -> Dict[str, str]:
        """Generate HTML/CSS/JS code based on brief"""
        
        prompt = self._build_prompt(brief, checks, attachments)
        
        message = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Parse the response to extract code
        return self._parse_response(message.content[0].text)
    
    def _build_prompt(self, brief: str, checks: List[str], attachments: List[Dict]) -> str:
        attachment_info = "\n".join([f"- {a['name']}: {a['url'][:100]}..." for a in attachments])
        
        return f"""You are a code generator. Create a complete, single-page web application.

**Brief:** {brief}

**Checks to pass:**
{chr(10).join(f"- {check}" for check in checks)}

**Attachments:**
{attachment_info}

**Requirements:**
- Generate complete HTML with embedded CSS and JavaScript
- Use CDN links for any libraries (Bootstrap, marked, highlight.js, etc.)
- Make it functional and production-ready
- Include all necessary error handling
- The app should work immediately when opened in a browser

Return ONLY valid HTML code, nothing else. Start with <!DOCTYPE html>"""
    
    def _parse_response(self, response: str) -> Dict[str, str]:
        """Extract code from LLM response"""
        # If response has code blocks, extract them
        if "```html" in response:
            code = response.split("```html")[1].split("```")[0].strip()
        elif "```" in response:
            code = response.split("```")[1].split("```")[0].strip()
        else:
            code = response.strip()
        
        return {
            "index.html": code,
            "README.md": self._generate_readme(code)
        }
    
    def _generate_readme(self, code: str) -> str:
        """Generate README based on the code"""
        # Use LLM to generate README or use a template
        return """# Generated Application

## Summary
This application was automatically generated based on project requirements.

## Setup
1. Clone this repository
2. Open `index.html` in a web browser

## Usage
Simply open the HTML file - no build process required.

## License
MIT License
"""