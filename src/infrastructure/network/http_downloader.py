import requests
from typing import Callable, Optional, Any


class HttpDownloader:
    def check_range_support(self, url: str) -> bool:
        """Check if the server supports HTTP Range requests."""
        try:
            response = requests.head(url, allow_redirects=True)
            response.raise_for_status()
            return response.headers.get("Accept-Ranges", "").lower() == "bytes"
        except Exception:
            # If HEAD request fails, assume range is not supported
            return False
    
    def get_content_details(self, url: str) -> tuple[bool, bool, int | None]:
        """
        Get content details to determine if download is resumable.
        
        Returns:
            tuple: (is_resumable, has_content_length, content_length)
        """
        try:
            response = requests.head(url, allow_redirects=True)
            response.raise_for_status()
            
            # Check if server supports range requests
            accepts_ranges = response.headers.get("Accept-Ranges", "").lower() == "bytes"
            
            # Check if Transfer-Encoding is chunked (non-resumable)
            transfer_encoding = response.headers.get("Transfer-Encoding", "").lower()
            is_chunked = "chunked" in transfer_encoding
            
            # Check if Content-Length exists
            content_length = response.headers.get("Content-Length")
            has_content_length = content_length is not None
            content_length_int = int(content_length) if content_length else None
            
            # Resumable if: accepts ranges AND has content length AND not chunked
            is_resumable = accepts_ranges and has_content_length and not is_chunked
            
            return is_resumable, has_content_length, content_length_int
        except Exception:
            # If any error occurs, assume it's not resumable
            return False, False, None
    
    def get_content_length(self, url: str) -> Optional[int]:
        """Get the total content length of the URL."""
        try:
            response = requests.head(url, allow_redirects=True)
            response.raise_for_status()
            content_length = response.headers.get("Content-Length")
            return int(content_length) if content_length else None
        except Exception:
            return None
    
    def download(self, url: str, on_chunk: Callable, start_byte: int = 0, total_size: Optional[int] = None, pause_check: Callable[[], bool] | None = None):
        """
        Download content from URL starting at a specific byte offset.
        
        Args:
            url: URL to download from
            on_chunk: Callback function to handle downloaded chunks
            start_byte: Starting byte offset for Range request
            total_size: Total size of the content (for progress calculation)
            pause_check: Optional callback to check if download should pause
        """
        headers = {}
        if start_byte > 0:
            # Use Range header to download from specific byte offset
            headers["Range"] = f"bytes={start_byte}-"
        
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            
            # If total_size is not provided, try to get it from Content-Range or Content-Length
            if total_size is None:
                content_range = r.headers.get("Content-Range")
                if content_range:
                    # Content-Range format: "bytes start-end/total" or "bytes */total"
                    try:
                        total_size = int(content_range.split("/")[1])
                    except (IndexError, ValueError):
                        total_size = 0
                else:
                    content_length = r.headers.get("Content-Length")
                    if content_length:
                        total_size = int(content_length)
            
            downloaded = start_byte
            chunk_size = 8192
            
            for chunk in r.iter_content(chunk_size=chunk_size):
                if pause_check and pause_check():
                    # Stop downloading if pause was requested
                    break
                if chunk:
                    downloaded += len(chunk)
                    on_chunk(chunk, downloaded, total_size)
