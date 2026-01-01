from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from application.discovery.discovery_result import DiscoveredLink
from .item_type import ItemType


class UrlType(Enum):
    DIRECT_FILE = "direct_file"
    HTML_PAGE = "html_page"
    STREAM_HINT = "stream_hint"
    UNKNOWN = "unknown"


@dataclass
class GrabberItem:
    """Represents a single item that can be grabbed/downloaded."""
    url: str
    item_type: ItemType
    file_size: Optional[int] = None  # in bytes
    title: Optional[str] = None
    mime_type: Optional[str] = None
    filename: Optional[str] = None


@dataclass
class GrabberResult:
    """Result from the grabber engine."""
    items: List[GrabberItem]
    source_url: str
    url_type: UrlType
    page_title: Optional[str] = None
    total_found: int = 0
    total_filtered: int = 0