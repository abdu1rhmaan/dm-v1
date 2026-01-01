import requests
from typing import List, Optional
from .hls_manifest import HlsManifest
from .hls_result import HlsResult, HlsVariant, StreamType
from .hls_variant import HlsVariantProcessor


class HlsAnalyzer:
    """Analyzes HLS streams to extract available qualities and metadata."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; dm_pro/1.0)'
        })
        self.variant_processor = HlsVariantProcessor()
    
    def analyze(self, m3u8_url: str) -> HlsResult:
        """
        Analyze an HLS stream to extract available variants and metadata.
        
        Args:
            m3u8_url: URL to the master playlist or media playlist
            
        Returns:
            HlsResult containing variants and metadata
        """
        try:
            # Fetch the master playlist
            response = self.session.get(m3u8_url, timeout=10)
            response.raise_for_status()
            
            # Parse the manifest
            manifest = HlsManifest.parse(response.text, m3u8_url)
            
            # If it's a master playlist, we have variants
            if manifest.is_master:
                # Process each variant to get additional info
                processed_variants = []
                for variant in manifest.variants:
                    # For VOD streams, try to get more info from the media playlist
                    if manifest.stream_type == StreamType.VOD:
                        variant.estimated_size = self._estimate_variant_size(variant.uri, variant.bandwidth)
                    
                    processed_variants.append(variant)
                
                return HlsResult(
                    variants=processed_variants,
                    stream_type=manifest.stream_type,
                    master_url=m3u8_url,
                    estimated_duration=manifest.duration,
                    has_audio=True,  # HLS streams typically have audio
                    has_video=True,  # Most HLS streams have video
                    title=f"HLS Stream: {m3u8_url.split('/')[-1]}"
                )
            else:
                # It's a media playlist, not a master playlist
                # Create a single variant representing this stream
                estimated_size = None
                if manifest.stream_type == StreamType.VOD:
                    estimated_size = self._estimate_variant_size(m3u8_url, None)
                
                variant = HlsVariant(
                    uri=m3u8_url,
                    bandwidth=None,  # Not available in media playlist
                    resolution=None,
                    codecs=None,
                    quality_label="Media Playlist",
                    estimated_size=estimated_size
                )
                
                return HlsResult(
                    variants=[variant],
                    stream_type=manifest.stream_type,
                    master_url=m3u8_url,
                    estimated_duration=manifest.duration,
                    has_audio=True,
                    has_video=True,
                    title=f"HLS Stream: {m3u8_url.split('/')[-1]}"
                )
                
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch HLS manifest: {e}")
        except Exception as e:
            raise Exception(f"Failed to analyze HLS stream: {e}")
    
    def _estimate_variant_size(self, media_playlist_url: str, bandwidth: Optional[int]) -> Optional[int]:
        """
        Estimate the total size of a variant based on bandwidth and duration.
        
        Args:
            media_playlist_url: URL to the media playlist
            bandwidth: Bandwidth in bits per second
            
        Returns:
            Estimated size in bytes, or None if not available
        """
        if not bandwidth:
            return None
        
        try:
            # Fetch the media playlist to get duration
            response = self.session.get(media_playlist_url, timeout=10)
            response.raise_for_status()
            
            # Parse to get duration
            manifest = HlsManifest.parse(response.text, media_playlist_url)
            
            if manifest.duration and bandwidth:
                # Size in bytes = (bandwidth in bits/s * duration in seconds) / 8
                estimated_bytes = (bandwidth * manifest.duration) / 8
                return int(estimated_bytes)
        
        except:
            # If we can't get the exact size, return None
            pass
        
        return None