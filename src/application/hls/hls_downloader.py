import requests
import os
import tempfile
from typing import Optional, Callable
from .hls_manifest import HlsManifest
from domain.entities.download_task import DownloadTask


class HlsDownloader:
    """Downloads HLS stream segments and merges them into a single file."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; dm_pro/1.0)'
        })
    
    def download_variant(
        self, 
        variant_uri: str, 
        output_path: str, 
        pause_check: Optional[Callable[[], bool]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Download an HLS variant to a file.
        
        Args:
            variant_uri: URI to the media playlist
            output_path: Path to save the final file
            pause_check: Callback to check if download should pause
            progress_callback: Callback for progress updates (downloaded, total)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Fetch the media playlist
            response = self.session.get(variant_uri, timeout=10)
            response.raise_for_status()
            
            # Parse the media playlist to get segments
            base_url = '/'.join(variant_uri.split('/')[:-1]) + '/'
            manifest = HlsManifest.parse(response.text, base_url)
            
            # Create a temporary directory for segments
            with tempfile.TemporaryDirectory() as temp_dir:
                # Download segments one by one
                total_segments = len(manifest.segments)
                downloaded_bytes = 0
                
                for i, segment in enumerate(manifest.segments):
                    # Check if pause was requested
                    if pause_check and pause_check():
                        print(f"Download paused after segment {i+1}/{total_segments}")
                        return False  # Indicate pause
                    
                    # Download the segment
                    segment_response = self.session.get(segment['uri'], timeout=30)
                    segment_response.raise_for_status()
                    
                    # Save segment to temp file
                    segment_path = os.path.join(temp_dir, f"segment_{i:05d}.ts")
                    with open(segment_path, 'wb') as f:
                        f.write(segment_response.content)
                    
                    downloaded_bytes += len(segment_response.content)
                    
                    # Report progress
                    if progress_callback:
                        progress_callback(downloaded_bytes, None)
                
                # Merge segments into final file
                self._merge_segments(temp_dir, output_path, total_segments)
                
                return True
                
        except requests.RequestException as e:
            print(f"HLS download failed: {e}")
            return False
        except Exception as e:
            print(f"HLS download error: {e}")
            return False
    
    def _merge_segments(self, temp_dir: str, output_path: str, total_segments: int):
        """Merge downloaded segments into a single file."""
        with open(output_path, 'wb') as output_file:
            for i in range(total_segments):
                segment_path = os.path.join(temp_dir, f"segment_{i:05d}.ts")
                if os.path.exists(segment_path):
                    with open(segment_path, 'rb') as segment_file:
                        output_file.write(segment_file.read())
    
    def get_stream_info(self, variant_uri: str) -> dict:
        """Get information about an HLS stream without downloading."""
        try:
            response = self.session.get(variant_uri, timeout=10)
            response.raise_for_status()
            
            manifest = HlsManifest.parse(response.text, variant_uri)
            
            return {
                'duration': manifest.duration,
                'target_duration': manifest.target_duration,
                'is_live': manifest.stream_type != 'vod',
                'segment_count': len(manifest.segments),
                'estimated_size': self._estimate_size(manifest)
            }
        except:
            return {
                'duration': 0,
                'target_duration': 0,
                'is_live': True,  # Default to live if we can't determine
                'segment_count': 0,
                'estimated_size': 0
            }
    
    def _estimate_size(self, manifest: HlsManifest) -> int:
        """Estimate total size based on segments."""
        # This is a rough estimate - in a real implementation, we'd need more info
        if manifest.duration and manifest.target_duration:
            # Estimate based on typical bitrate if available
            # For now, return 0 as the size will be estimated elsewhere
            pass
        return 0