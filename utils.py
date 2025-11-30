import re
import validators
from werkzeug.utils import secure_filename
from config import Config

def validate_email(email: str) -> bool:
    """Validate email format"""
    return validators.email(email) is True

def validate_password(password: str) -> bool:
    """Validate password strength (minimum 8 characters)"""
    return len(password) >= 8

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filename"""
    return secure_filename(filename)

def extract_keywords(text: str) -> list:
    """Extract keywords from text (simple NLP)"""
    # Remove common words
    stopwords = {'the', 'a', 'an', 'in', 'on', 'at', 'for', 'to', 'of', 'and', 'or', 
                 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
                 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might',
                 'can', 'this', 'that', 'these', 'those', 'with', 'from', 'as', 'by'}
    
    # Tokenize and filter
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if w not in stopwords and len(w) > 3]
    
    # Return unique keywords (up to 10)
    return list(set(keywords))[:10]

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
