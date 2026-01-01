import re
from typing import List, Dict, Optional
from .hls_result import HlsVariant, StreamType


class HlsManifest:
    """Parses and represents HLS manifest files (m3u8)."""
    
    def __init__(self):
        self.version = None
        self.is_master = False
        self.variants = []
        self.segments = []
        self.stream_type = StreamType.VOD
        self.duration = 0.0  # Total duration in seconds
        self.target_duration = 0  # Target segment duration in seconds
    
    @classmethod
    def parse(cls, content: str, base_url: str = ""):
        """Parse an m3u8 manifest and return an HlsManifest object."""
        manifest = cls()
        lines = content.strip().split('\n')
        
        # Check if it's a valid HLS playlist
        if not lines[0].startswith('#EXTM3U'):
            raise ValueError("Not a valid HLS playlist")
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            if line.startswith('#EXT-X-VERSION:'):
                manifest.version = int(line.split(':', 1)[1])
            elif line.startswith('#EXT-X-STREAM-INF:'):
                # This is a master playlist with variants
                manifest.is_master = True
                variant_info = cls._parse_stream_inf(line)
                
                # Get the URI for this variant (next non-comment line)
                i += 1
                while i < len(lines) and lines[i].strip().startswith('#'):
                    i += 1
                
                if i < len(lines):
                    uri = lines[i].strip()
                    if not uri.startswith(('http://', 'https://')):
                        # Make it absolute if it's relative
                        from urllib.parse import urljoin
                        uri = urljoin(base_url, uri)
                    
                    variant = HlsVariant(
                        uri=uri,
                        bandwidth=variant_info.get('bandwidth'),
                        resolution=variant_info.get('resolution'),
                        codecs=variant_info.get('codecs'),
                        audio_group=variant_info.get('audio'),
                        subtitle_group=variant_info.get('subtitles'),
                        quality_label=cls._get_quality_label(variant_info.get('resolution'), variant_info.get('bandwidth'))
                    )
                    manifest.variants.append(variant)
            elif line.startswith('#EXT-X-TARGETDURATION:'):
                manifest.target_duration = int(line.split(':', 1)[1])
            elif line.startswith('#EXT-X-ENDLIST'):
                # This is a VOD stream (not live)
                manifest.stream_type = StreamType.VOD
            elif line.startswith('#EXTINF:'):
                # This is a media playlist with segments
                duration_str = line.split(':', 1)[1].split(',')[0]
                duration = float(duration_str)
                manifest.duration += duration
                
                # Get the segment URI
                i += 1
                while i < len(lines) and lines[i].strip().startswith('#'):
                    i += 1
                
                if i < len(lines):
                    segment_uri = lines[i].strip()
                    if not segment_uri.startswith(('http://', 'https://')):
                        # Make it absolute if it's relative
                        from urllib.parse import urljoin
                        segment_uri = urljoin(base_url, segment_uri)
                    
                    manifest.segments.append({
                        'uri': segment_uri,
                        'duration': duration
                    })
            
            i += 1
        
        # If no #EXT-X-ENDLIST found, it's a live stream
        if manifest.stream_type != StreamType.VOD:
            manifest.stream_type = StreamType.LIVE
        
        return manifest
    
    @staticmethod
    def _parse_stream_inf(line: str) -> Dict:
        """Parse the attributes from an #EXT-X-STREAM-INF line."""
        attributes_str = line.split(':', 1)[1]
        attributes = {}
        
        # Parse attributes like BANDWIDTH, RESOLUTION, CODECS, etc.
        pairs = [pair.strip() for pair in attributes_str.split(',')]
        
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                key = key.strip().upper()
                value = value.strip().strip('"')  # Remove quotes
                
                if key == 'BANDWIDTH':
                    attributes['bandwidth'] = int(value)
                elif key == 'RESOLUTION':
                    attributes['resolution'] = value
                elif key == 'CODECS':
                    attributes['codecs'] = value
                elif key == 'AUDIO':
                    attributes['audio'] = value
                elif key == 'SUBTITLES':
                    attributes['subtitles'] = value
        
        return attributes
    
    @staticmethod
    def _get_quality_label(resolution: Optional[str], bandwidth: Optional[int]) -> str:
        """Generate a quality label based on resolution and bandwidth."""
        if resolution:
            # Extract height from resolution like "1920x1080"
            match = re.search(r'(\d+)x(\d+)', resolution)
            if match:
                height = int(match.group(2))
                if height >= 2160:
                    return "4K"
                elif height >= 1440:
                    return "1440p"
                elif height >= 1080:
                    return "1080p"
                elif height >= 720:
                    return "720p"
                elif height >= 480:
                    return "480p"
                else:
                    return "360p"
        
        # Fallback to bandwidth-based estimation
        if bandwidth:
            if bandwidth >= 8000000:  # 8 Mbps
                return "1080p+"
            elif bandwidth >= 5000000:  # 5 Mbps
                return "1080p"
            elif bandwidth >= 2500000:  # 2.5 Mbps
                return "720p"
            elif bandwidth >= 1000000:  # 1 Mbps
                return "480p"
            else:
                return "360p"
        
        return "Unknown"