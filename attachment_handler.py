import base64
from typing import Dict

class AttachmentHandler:
    @staticmethod
    def decode_data_uri(data_uri: str) -> bytes:
        """Decode base64 data URI"""
        if data_uri.startswith("data:"):
            # Extract base64 part
            base64_data = data_uri.split(",")[1]
            return base64.b64decode(base64_data)
        return b""
    
    @staticmethod
    def process_attachments(attachments: list) -> Dict[str, str]:
        """Process and save attachments"""
        processed = {}
        for att in attachments:
            content = AttachmentHandler.decode_data_uri(att["url"])
            processed[att["name"]] = content.decode('utf-8') if content else ""
        return processed