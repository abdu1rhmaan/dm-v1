from typing import List
from .hls_analyzer import HlsAnalyzer
from .hls_result import HlsResult, HlsVariant, StreamType
from application.grabber.grabber_result import GrabberResult, GrabberItem, UrlType
from application.grabber.item_type import ItemType


class HlsEngine:
    """Main HLS engine that integrates with the grabber system."""
    
    def __init__(self):
        self.analyzer = HlsAnalyzer()
    
    def analyze_stream(self, m3u8_url: str) -> HlsResult:
        """
        Analyze an HLS stream and return available variants.
        
        Args:
            m3u8_url: URL to the m3u8 playlist
            
        Returns:
            HlsResult with available variants
        """
        return self.analyzer.analyze(m3u8_url)
    
    def convert_to_grabber_result(self, hls_result: HlsResult) -> GrabberResult:
        """
        Convert HLS result to grabber result for integration with the grabber system.
        
        Args:
            hls_result: The HLS analysis result
            
        Returns:
            GrabberResult that can be used by the grabber system
        """
        items = []
        
        for variant in hls_result.variants:
            # Create a grabber item for each variant
            item = GrabberItem(
                url=variant.uri,
                item_type=ItemType.STREAM,  # HLS variants are streams
                file_size=variant.estimated_size,
                title=f"{variant.quality_label or 'HLS Variant'} - {hls_result.stream_type.value.upper()}",
                filename=self._get_variant_filename(variant, hls_result.stream_type),
                mime_type="application/vnd.apple.mpegurl"  # HLS MIME type
            )
            items.append(item)
        
        return GrabberResult(
            items=items,
            source_url=hls_result.master_url,
            url_type=UrlType.STREAM_HINT,
            page_title=hls_result.title,
            total_found=len(hls_result.variants),
            total_filtered=len(hls_result.variants)
        )
    
    def _get_variant_filename(self, variant: HlsVariant, stream_type: StreamType) -> str:
        """Generate a filename for the variant."""
        quality = variant.quality_label or "quality"
        stream_type_str = stream_type.value.upper()
        
        # Determine file extension based on codecs or stream type
        if variant.codecs and ('mp4a' in variant.codecs.lower() or 'aac' in variant.codecs.lower()):
            if 'avc' not in variant.codecs.lower() and 'h264' not in variant.codecs.lower():
                # Audio-only stream
                return f"audio_{quality}_{stream_type_str.lower()}.m4a"
        
        # Default to MP4 for video streams
        return f"video_{quality}_{stream_type_str.lower()}.mp4"
    
    def get_selected_variant_info(self, selected_item: GrabberItem) -> dict:
        """
        Get information about a selected HLS variant for download.
        
        Args:
            selected_item: The selected grabber item
            
        Returns:
            Dictionary with variant information
        """
        return {
            'uri': selected_item.url,
            'file_size': selected_item.file_size,
            'filename': selected_item.filename,
            'is_live': 'LIVE' in (selected_item.title or '').upper(),
            'quality_info': selected_item.title
        }