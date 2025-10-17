import re

class SecretScanner:
    """Simple secret scanner to avoid committing sensitive data"""
    
    # Common secret patterns
    PATTERNS = [
        (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
        (r'(?i)github[_-]?token[_-]?[:\s=]+["\']?([a-zA-Z0-9_-]{40})["\']?', 'GitHub Token'),
        (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Personal Access Token'),
        (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
        (r'sk-ant-[a-zA-Z0-9-_]{95}', 'Anthropic API Key'),
        (r'AIza[0-9A-Za-z_-]{35}', 'Google API Key'),
        (r'(?i)api[_-]?key[_-]?[:\s=]+["\']?([a-zA-Z0-9_-]{20,})["\']?', 'Generic API Key'),
        (r'(?i)secret[_-]?key[_-]?[:\s=]+["\']?([a-zA-Z0-9_-]{20,})["\']?', 'Secret Key'),
        (r'(?i)password[_-]?[:\s=]+["\']?([a-zA-Z0-9_-]{8,})["\']?', 'Password'),
        (r'(?i)token[_-]?[:\s=]+["\']?([a-zA-Z0-9_-]{20,})["\']?', 'Generic Token'),
        (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'Email Address'),
    ]
    
    def scan_content(self, content: str, filename: str = "file") -> list:
        """
        Scan content for potential secrets
        Returns list of findings: [(pattern_name, matched_text, line_number)]
        """
        findings = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, name in self.PATTERNS:
                matches = re.finditer(pattern, line)
                for match in matches:
                    # Skip if it looks like a placeholder or example
                    matched_text = match.group(0)
                    if self._is_likely_placeholder(matched_text, line):
                        continue
                    
                    findings.append({
                        'type': name,
                        'match': matched_text,
                        'line': line_num,
                        'file': filename,
                        'context': line.strip()[:100]
                    })
        
        return findings
    
    def _is_likely_placeholder(self, text: str, context: str) -> bool:
        """Check if the matched text is likely a placeholder"""
        placeholder_indicators = [
            'example', 'placeholder', 'your', 'xxx', '***',
            'dummy', 'fake', 'test', 'sample', 'demo',
            'TODO', 'FIXME', 'CHANGE_ME', 'REPLACE',
            'sk-...', 'ghp_...', 'your_', 'my_'
        ]
        
        text_lower = text.lower()
        context_lower = context.lower()
        
        # Check if it's clearly a placeholder
        for indicator in placeholder_indicators:
            if indicator in text_lower or indicator in context_lower:
                return True
        
        # Check for repeated characters (e.g., xxxx, aaaa)
        if len(set(text.replace('-', '').replace('_', ''))) <= 3:
            return True
        
        return False
    
    def scan_files(self, files: dict) -> dict:
        """
        Scan multiple files for secrets
        Returns dict of {filename: [findings]}
        """
        all_findings = {}
        
        for filename, content in files.items():
            findings = self.scan_content(content, filename)
            if findings:
                all_findings[filename] = findings
        
        return all_findings
    
    def format_findings(self, findings: dict) -> str:
        """Format findings for display"""
        if not findings:
            return "✓ No secrets detected"
        
        output = ["⚠️  Potential secrets detected:"]
        for filename, file_findings in findings.items():
            output.append(f"\n  File: {filename}")
            for finding in file_findings:
                output.append(f"    Line {finding['line']}: {finding['type']}")
                output.append(f"      Match: {finding['match'][:50]}...")
                output.append(f"      Context: {finding['context']}")
        
        return "\n".join(output)
    
    def has_secrets(self, files: dict) -> bool:
        """Quick check if any secrets are present"""
        findings = self.scan_files(files)
        return len(findings) > 0