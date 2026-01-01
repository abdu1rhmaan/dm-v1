from typing import List, Optional
from dataclasses import dataclass
from .hls_result import HlsVariant


@dataclass
class HlsVariantInfo:
    """Additional information about an HLS variant."""
    uri: str
    bandwidth: Optional[int] = None
    resolution: Optional[str] = None
    codecs: Optional[str] = None
    audio_group: Optional[str] = None
    subtitle_group: Optional[str] = None
    quality_label: Optional[str] = None
    estimated_size: Optional[int] = None
    duration: Optional[float] = None  # Duration in seconds if known
    media_type: str = "video"  # "video", "audio", or "subtitle"


class HlsVariantProcessor:
    """Processes HLS variants to extract additional information."""
    
    def __init__(self):
        pass
    
    def get_variant_display_info(self, variant: HlsVariant, base_url: str = "") -> dict:
        """Get display information for a variant."""
        info = {
            'label': self._get_display_label(variant),
            'size_estimate': self._get_size_estimate(variant),
            'type': self._get_media_type(variant),
            'details': self._get_details(variant)
        }
        return info
    
    def _get_display_label(self, variant: HlsVariant) -> str:
        """Get a user-friendly display label for the variant."""
        if variant.resolution:
            return f"{variant.quality_label or variant.resolution}"
        elif variant.bandwidth:
            # Convert bandwidth to human readable format
            if variant.bandwidth >= 1000000:  # Mbps
                mbps = variant.bandwidth // 1000000
                return f"~{mbps} Mbps"
            else:  # kbps
                kbps = variant.bandwidth // 1000
                return f"~{kbps} kbps"
        else:
            return "Unknown Quality"
    
    def _get_size_estimate(self, variant: HlsVariant) -> str:
        """Get a human-readable size estimate."""
        if variant.estimated_size:
            if variant.estimated_size >= 1024 * 1024 * 1024:  # GB
                gb = variant.estimated_size / (1024 * 1024 * 1024)
                return f"~{gb:.1f} GB"
            elif variant.estimated_size >= 1024 * 1024:  # MB
                mb = variant.estimated_size / (1024 * 1024)
                return f"~{mb:.1f} MB"
            elif variant.estimated_size >= 1024:  # KB
                kb = variant.estimated_size / 1024
                return f"~{kb:.1f} KB"
            else:
                return f"~{variant.estimated_size} B"
        else:
            return "~? MB"
    
    def _get_media_type(self, variant: HlsVariant) -> str:
        """Determine the media type of the variant."""
        if variant.codecs:
            if 'mp4a' in variant.codecs.lower() or 'aac' in variant.codecs.lower():
                if 'avc' not in variant.codecs.lower() and 'h264' not in variant.codecs.lower():
                    return "audio"
        
        # Default to video unless specified otherwise
        return "video"
    
    def _get_details(self, variant: HlsVariant) -> str:
        """Get detailed information about the variant."""
        details = []
        
        if variant.codecs:
            details.append(variant.codecs)
        
        if variant.resolution:
            details.append(variant.resolution)
        
        if variant.bandwidth:
            if variant.bandwidth >= 1000000:
                details.append(f"{variant.bandwidth // 1000000} Mbps")
            else:
                details.append(f"{variant.bandwidth // 1000} kbps")
        
        return ", ".join(details) if details else "Unknown"