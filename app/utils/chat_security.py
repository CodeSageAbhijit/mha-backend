# app/utils/chat_security.py
import os
import hashlib
import mimetypes
from typing import Optional, Tuple
from fastapi import HTTPException
import aiofiles

class ChatSecurityManager:
    """Handle chat security including file validation, encryption, etc."""
    
    ALLOWED_FILE_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'text/plain', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'audio/mpeg', 'audio/wav', 'video/mp4'
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_MESSAGE_LENGTH = 5000
    
    @staticmethod
    def validate_message_content(content: str) -> bool:
        """Validate message content for safety"""
        if not content or len(content) > ChatSecurityManager.MAX_MESSAGE_LENGTH:
            return False
        
        # Check for potentially harmful content
        suspicious_patterns = [
            '<script', 'javascript:', 'data:text/html',
            'vbscript:', 'onload=', 'onerror='
        ]
        
        content_lower = content.lower()
        for pattern in suspicious_patterns:
            if pattern in content_lower:
                return False
        
        return True
    
    @staticmethod
    def validate_file(file_content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate uploaded file for safety"""
        # Check file size
        if len(file_content) > ChatSecurityManager.MAX_FILE_SIZE:
            return False, "File size exceeds 10MB limit"
        
        # Check file type by content
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type not in ChatSecurityManager.ALLOWED_FILE_TYPES:
            return False, f"File type {mime_type} not allowed"
        
        # Check for malicious file signatures
        if ChatSecurityManager._is_malicious_file(file_content):
            return False, "File contains potentially harmful content"
        
        return True, None
    
    @staticmethod
    def _is_malicious_file(content: bytes) -> bool:
        """Check for malicious file signatures"""
        malicious_signatures = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'data:text/html'
        ]
        
        content_lower = content.lower()
        for signature in malicious_signatures:
            if signature in content_lower:
                return True
        
        return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        dangerous_chars = ['..', '/', '\\', '|', ':', '*', '?', '"', '<', '>']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        return filename
    
    @staticmethod
    def generate_secure_filename(original_filename: str) -> str:
        """Generate a secure filename with hash"""
        ext = os.path.splitext(original_filename)[1]
        hash_obj = hashlib.sha256(original_filename.encode())
        secure_name = hash_obj.hexdigest()[:16]
        return f"{secure_name}{ext}"
    
    @staticmethod
    def validate_user_permissions(user_id: str, target_user_id: str, user_role: str) -> bool:
        """Validate if user has permission to chat with target user"""
        # Business logic for chat permissions
        # For example: patients can only chat with their assigned doctors/counselors
        
        if user_role == "user":  # Patient
            # Implement logic to check if target is assigned doctor/counselor
            return True  # Simplified for now
        elif user_role in ["psychiatrist", "counselor"]:
            # Healthcare providers can chat with their patients
            return True  # Simplified for now
        elif user_role == "admin":
            # Admins can chat with anyone
            return True
        
        return False
    
    @staticmethod
    async def scan_message_for_threats(content: str) -> Tuple[bool, Optional[str]]:
        """Scan message content for security threats"""
        # Implement content scanning logic
        # This could include:
        # - Profanity filtering
        # - Spam detection
        # - Personal information detection (SSN, credit cards, etc.)
        
        # Basic implementation
        if len(content) > ChatSecurityManager.MAX_MESSAGE_LENGTH:
            return False, "Message too long"
        
        # Check for potential PII
        import re
        
        # SSN pattern
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        if re.search(ssn_pattern, content):
            return False, "Message may contain sensitive personal information"
        
        # Credit card pattern (simplified)
        cc_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        if re.search(cc_pattern, content):
            return False, "Message may contain credit card information"
        
        return True, None
    
    @staticmethod
    def encrypt_message(content: str, key: str) -> str:
        """Encrypt message content (if required)"""
        # Implement encryption if needed for sensitive communications
        # For now, return as-is
        return content
    
    @staticmethod
    def decrypt_message(encrypted_content: str, key: str) -> str:
        """Decrypt message content"""
        # Implement decryption if needed
        return encrypted_content