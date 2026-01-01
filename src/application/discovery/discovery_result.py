from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


class LinkType(Enum):
    FILE = "file"
    MEDIA = "media"
    STREAM_HINT = "stream_hint"
    PAGE = "page"
    UNKNOWN = "unknown"


@dataclass
class DiscoveredLink:
    url: str
    link_type: LinkType
    file_size: Optional[int] = None  # in bytes
    title: Optional[str] = None
    mime_type: Optional[str] = None


@dataclass
class DiscoveryResult:
    links: List[DiscoveredLink]
    total_found: int
    total_filtered: int
    page_title: Optional[str] = None