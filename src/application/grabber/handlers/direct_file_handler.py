from typing import Optional
import requests
from .base import GrabberHandler
from application.grabber.grabber_result import GrabberResult, GrabberItem, UrlType
from application.grabber.item_type import ItemType


class DirectFileHandler(GrabberHandler):
    """Handler for direct file URLs."""
    
    def supports(self, url_type: UrlType) -> bool:
        return url_type == UrlType.DIRECT_FILE
    
    def handle(self, url: str) -> GrabberResult:
        """Handle a direct file URL."""
        # Try to get file size via HEAD request
        file_size = self._get_file_size(url)
        
        # Extract filename from URL
        filename = url.split('/')[-1]
        
        item = GrabberItem(
            url=url,
            item_type=ItemType.FILE,
            file_size=file_size,
            filename=filename
        )
        
        return GrabberResult(
            items=[item],
            source_url=url,
            url_type=UrlType.DIRECT_FILE,
            total_found=1,
            total_filtered=1
        )
    
    def _get_file_size(self, url: str) -> Optional[int]:
        """Get file size from URL via HEAD request."""
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            response.raise_for_status()
            content_length = response.headers.get('Content-Length')
            if content_length:
                return int(content_length)
        except:
            # If HEAD request fails, try GET with no content
            try:
                response = requests.get(url, stream=True, timeout=5)
                response.raise_for_status()
                content_length = response.headers.get('Content-Length')
                if content_length:
                    return int(content_length)
            except:
                pass
        return None