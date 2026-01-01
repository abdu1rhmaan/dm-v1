from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class StreamType(Enum):
    VOD = "vod"
    LIVE = "live"
    EVENT = "event"


class QualityType(Enum):
    VIDEO = "video"
    AUDIO = "audio"
    SUBTITLE = "subtitle"


@dataclass
class HlsVariant:
    """Represents a single HLS stream variant."""
    uri: str  # The URL to the media playlist
    bandwidth: Optional[int] = None  # Bandwidth in bits per second
    resolution: Optional[str] = None  # Resolution like "1920x1080"
    codecs: Optional[str] = None  # Video/audio codecs
    audio_group: Optional[str] = None  # Audio group ID if present
    subtitle_group: Optional[str] = None  # Subtitle group ID if present
    quality_label: Optional[str] = None  # Human-readable quality label (e.g., "1080p")
    estimated_size: Optional[int] = None  # Estimated total size in bytes


@dataclass
class HlsResult:
    """Result from HLS analysis."""
    variants: List[HlsVariant]
    stream_type: StreamType
    master_url: str
    estimated_duration: Optional[float] = None  # Duration in seconds if available
    has_audio: bool = False
    has_video: bool = False
    has_subtitles: bool = False
    title: Optional[str] = None