from enum import Enum


class ItemType(Enum):
    """Enum for different types of downloadable items."""
    FILE = "file"
    MEDIA = "media"
    STREAM = "stream"