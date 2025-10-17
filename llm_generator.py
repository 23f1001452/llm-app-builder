import openai
import os
import re
from typing import List, Dict

class LLMGenerator:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
    
    def generate_app_code(self, brief: str, checks: List[str], attachments: List[Dict], processed_attachments: Dict[str, str]) -> Dict[str, str]:
        """Generate HTML/CSS/JS code based on brief and requirements"""
        
        print("Building prompt for LLM...")
        prompt = self._build_prompt(brief, checks, attachments, processed_attachments)
        
        print("Calling LLM API...")
        message = self.client.chat.completions.create(
            model="groq/compound-mini",
            max_tokens=8000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        print("Parsing LLM response...")
        response = message.choices[0].message.content
        
        # Parse the response to extract code
        html_code = self._parse_response(response)
        
        # Generate README
        readme = self._generate_readme(brief, checks)
        
        return {
            "index.html": html_code,
            "README.md": readme
        }
    
    def _build_prompt(self, brief: str, checks: List[str], attachments: List[Dict], processed_attachments: Dict[str, str]) -> str:
        """Build the prompt for code generation"""
        
        # Format attachment information
        attachment_details = ""
        if attachments:
            attachment_details = "\n**Attachments provided:**\n"
            for att in attachments:
                name = att['name']
                attachment_details += f"- {name}"
                if name in processed_attachments and len(processed_attachments[name]) < 500:
                    attachment_details += f"\n  Content preview: {processed_attachments[name][:200]}...\n"
                else:
                    attachment_details += f" (data URI provided)\n"
        
        # Format checks and extract specific IDs/requirements
        checks_formatted = "\n".join(f"{i+1}. {check}" for i, check in enumerate(checks))
        
        # Extract any specific element IDs mentioned in checks
        element_ids = set()
        for check in checks:
            # Find #id-name patterns
            ids = re.findall(r'#([\w-]+)', check)
            element_ids.update(ids)
        
        id_requirements = ""
        if element_ids:
            id_requirements = f"\n**CRITICAL - Required Element IDs (MUST be present):**\n"
            for elem_id in sorted(element_ids):
                id_requirements += f"- Element with id=\"{elem_id}\" MUST exist\n"
        
        prompt = f"""You are an expert web developer. Create a complete, production-ready, single-page web application.

**PROJECT BRIEF:**
{brief}

**REQUIREMENTS TO PASS (Critical - the app will be tested against these):**
{checks_formatted}

{id_requirements}

{attachment_details}

**TECHNICAL REQUIREMENTS:**
1. Create a COMPLETE, SELF-CONTAINED HTML file with embedded CSS and JavaScript
2. Use CDN links for any external libraries (Bootstrap, marked.js, highlight.js, etc.)
3. If attachments are provided as data URIs, embed them directly in the code or fetch them
4. Make the app fully functional - all features must work immediately when opened
5. Include proper error handling
6. Use modern, clean code following best practices
7. Ensure responsive design
8. Add helpful comments in the code
9. **CRITICAL**: If checks mention specific element IDs (like #total-sales), you MUST create elements with those EXACT IDs
10. **CRITICAL**: Ensure all JavaScript functionality works without any external dependencies beyond CDN libraries

**IMPORTANT NOTES:**
- Pay close attention to specific element IDs mentioned in the checks
- If a check mentions querySelector("#some-id"), create an element with id="some-id"
- If checks mention data attributes, create them exactly as specified
- Test selectors and functionality mentally before outputting
- Do NOT include any API keys, tokens, or sensitive data in the code

**OUTPUT FORMAT:**
Return ONLY the complete HTML code. No explanations, no markdown code blocks, just pure HTML starting with <!DOCTYPE html>.

Begin generating the application now:"""
        
        return prompt
    
    def _parse_response(self, response: str) -> str:
        """Extract HTML code from LLM response"""
        
        # Remove markdown code blocks if present
        if "```html" in response:
            code = response.split("```html")[1].split("```")[0].strip()
        elif "```" in response:
            parts = response.split("```")
            # Find the part that starts with <!DOCTYPE or <html
            for part in parts:
                if "<!DOCTYPE" in part or part.strip().startswith("<html") or part.strip().startswith("<!doctype"):
                    code = part.strip()
                    break
            else:
                code = parts[1].strip() if len(parts) > 1 else response.strip()
        else:
            code = response.strip()
        
        # Ensure it starts with DOCTYPE
        if not code.strip().lower().startswith("<!doctype"):
            if code.strip().startswith("<html"):
                code = "<!DOCTYPE html>\n" + code
        
        return code
    
    def _generate_readme(self, brief: str, checks: List[str]) -> str:
        """Generate a professional README for the repository"""
        
        checks_formatted = "\n".join(f"- {check}" for check in checks)
        
        readme = f"""# Auto-Generated Application

## Summary
This application was automatically generated to meet specific project requirements using LLM-assisted development.

**Project Brief:** {brief}

## Features
This application includes:
{checks_formatted}

## Setup
No build process required! Simply:
1. Clone this repository
2. Open `index.html` in a modern web browser
3. The application will run immediately

## Usage
Open the `index.html` file in your browser. All functionality is self-contained within this single HTML file.

## Technical Details
- **Technology Stack:** HTML5, CSS3, JavaScript (ES6+)
- **External Dependencies:** Loaded via CDN (if any)
- **Browser Compatibility:** Modern browsers (Chrome, Firefox, Safari, Edge)

## Code Structure
The application is built as a single-page application with:
- Embedded CSS for styling
- Embedded JavaScript for functionality
- External libraries loaded from CDN when needed

## License
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

*This project was generated automatically as part of an educational exercise.*
"""
        return readme