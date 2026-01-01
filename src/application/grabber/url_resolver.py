import requests
from urllib.parse import urlparse
from .grabber_result import UrlType


class UrlResolver:
    """Resolves URLs to determine their type and normalize them."""
    
    def __init__(self):
        self.session = requests.Session()
        # Set a reasonable timeout and user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; dm_pro/1.0)'
        })
    
    def resolve(self, url: str) -> tuple[str, UrlType]:
        """
        Resolve a URL to determine its type and normalize it.
        
        Args:
            url: The URL to resolve
            
        Returns:
            Tuple of (normalized_url, UrlType)
        """
        # Normalize the URL first
        normalized_url = self._normalize_url(url)
        
        # Check for stream hints (m3u8 files)
        if self._is_stream_hint(normalized_url):
            return normalized_url, UrlType.STREAM_HINT
        
        # Try to determine type via HEAD request
        url_type = self._determine_url_type(normalized_url)
        
        return normalized_url, url_type
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by handling common issues."""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Parse and reconstruct to normalize
        parsed = urlparse(url)
        # Remove fragments
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        
        return normalized
    
    def _is_stream_hint(self, url: str) -> bool:
        """Check if URL is a stream hint (e.g., m3u8)."""
        parsed = urlparse(url)
        path = parsed.path.lower()
        return path.endswith('.m3u8')
    
    def _determine_url_type(self, url: str) -> UrlType:
        """Determine URL type using HEAD request and content analysis."""
        try:
            # Try HEAD request first to check headers
            response = self.session.head(url, timeout=10, allow_redirects=True)
            
            # Check Content-Type header
            content_type = response.headers.get('Content-Type', '').lower()
            
            # Check if it's likely an HTML page
            if any(ct in content_type for ct in ['text/html', 'application/xhtml+xml']):
                return UrlType.HTML_PAGE
            
            # Check if it's a direct file download
            content_disposition = response.headers.get('Content-Disposition', '').lower()
            if 'attachment' in content_disposition or 'filename=' in content_disposition:
                return UrlType.DIRECT_FILE
            
            # Check for file extensions in URL
            parsed = urlparse(url)
            path = parsed.path.lower()
            if self._has_file_extension(path):
                return UrlType.DIRECT_FILE
            
            # If Content-Type suggests it's a file-like resource
            if any(ct in content_type for ct in [
                'application/', 'image/', 'video/', 'audio/', 
                'text/plain', 'text/csv', 'text/javascript', 'text/css'
            ]):
                return UrlType.DIRECT_FILE
            
            # Default to HTML page if we can't determine
            return UrlType.HTML_PAGE
            
        except requests.RequestException:
            # If HEAD request fails, try GET with stream=True to check headers
            try:
                response = self.session.get(url, stream=True, timeout=10)
                content_type = response.headers.get('Content-Type', '').lower()
                
                if any(ct in content_type for ct in ['text/html', 'application/xhtml+xml']):
                    return UrlType.HTML_PAGE
                elif any(ct in content_type for ct in [
                    'application/', 'image/', 'video/', 'audio/', 
                    'text/plain', 'text/csv', 'text/javascript', 'text/css'
                ]):
                    return UrlType.DIRECT_FILE
                else:
                    return UrlType.HTML_PAGE  # Default to page
            except:
                # If all else fails, assume it's a page
                return UrlType.HTML_PAGE
    
    def _has_file_extension(self, path: str) -> bool:
        """Check if the path has a file extension."""
        import os
        _, ext = os.path.splitext(path)
        return bool(ext and len(ext) <= 10)  # Reasonable extension length