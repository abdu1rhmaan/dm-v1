from .base import GrabberHandler
from application.grabber.grabber_result import GrabberResult, GrabberItem, UrlType
from application.hls.hls_engine import HlsEngine
from application.grabber.item_type import ItemType


class HlsHandler(GrabberHandler):
    """Handler for HLS stream URLs."""
    
    def __init__(self):
        self.hls_engine = HlsEngine()
    
    def supports(self, url_type: UrlType) -> bool:
        return url_type == UrlType.STREAM_HINT
    
    def handle(self, url: str) -> GrabberResult:
        """Handle an HLS stream URL using HLS engine."""
        try:
            # Analyze the HLS stream to get available variants
            hls_result = self.hls_engine.analyze_stream(url)
            
            # Convert HLS result to grabber result
            grabber_result = self.hls_engine.convert_to_grabber_result(hls_result)
            
            return grabber_result
        except Exception as e:
            # If HLS analysis fails, DO NOT throw, DO NOT fallback
            # Return empty result with STREAM_HINT type
            print(f"HLS stream detected but could not be analyzed.")
            return GrabberResult(
                items=[],
                source_url=url,
                url_type=UrlType.STREAM_HINT,
                total_found=0,
                total_filtered=0
            )