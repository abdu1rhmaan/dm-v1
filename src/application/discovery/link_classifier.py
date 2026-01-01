from urllib.parse import urlparse
from .discovery_result import LinkType, DiscoveredLink
import re


class LinkClassifier:
    """Classifies links based on their extensions and content hints."""
    
    # Known file extensions by category
    FILE_EXTENSIONS = {
        'video': {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v', '.3gp', '.m3u8'},
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.tiff', '.ico'},
        'audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus'},
        'archive': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso', '.dmg', '.pkg'},
        'document': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf'},
    }
    
    # Flatten to a single set of extensions
    ALL_FILE_EXTENSIONS = set()
    for ext_set in FILE_EXTENSIONS.values():
        ALL_FILE_EXTENSIONS.update(ext_set)
    
    # Known media MIME types
    MEDIA_MIME_TYPES = {
        'video/mp4', 'video/mpeg', 'video/quicktime', 'video/webm', 'video/x-msvideo',
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
        'audio/mpeg', 'audio/wav', 'audio/flac', 'audio/aac', 'audio/ogg'
    }
    
    def classify_link(self, url: str, mime_type: str = None) -> LinkType:
        """
        Classify a link based on its URL and optional MIME type.
        
        Args:
            url: The URL to classify
            mime_type: Optional MIME type hint
            
        Returns:
            LinkType indicating the classification
        """
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Check MIME type first if provided
        if mime_type and mime_type in self.MEDIA_MIME_TYPES:
            return LinkType.MEDIA
        
        # Check for stream hints
        if path.endswith('.m3u8'):
            return LinkType.STREAM_HINT
        
        # Check for known file extensions
        for ext in self.ALL_FILE_EXTENSIONS:
            if path.endswith(ext):
                if ext in self.FILE_EXTENSIONS['video'] or ext in self.FILE_EXTENSIONS['audio']:
                    return LinkType.MEDIA
                else:
                    return LinkType.FILE
        
        # If no extension, likely a page
        if not path or path == '/':
            return LinkType.PAGE
        
        # Default to unknown
        return LinkType.UNKNOWN