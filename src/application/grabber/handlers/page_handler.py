from .base import GrabberHandler
from application.grabber.grabber_result import GrabberResult, GrabberItem, UrlType
from application.discovery.page_discovery_service import PageDiscoveryService
from application.grabber.item_type import ItemType


class PageHandler(GrabberHandler):
    """Handler for HTML page URLs."""
    
    def __init__(self):
        self.page_discovery_service = PageDiscoveryService()
    
    def supports(self, url_type: UrlType) -> bool:
        return url_type == UrlType.HTML_PAGE
    
    def handle(self, url: str) -> GrabberResult:
        """Handle an HTML page URL using page discovery."""
        try:
            # Use the existing page discovery service
            discovery_result = self.page_discovery_service.discover_from_page(url)
            
            # Convert discovered links to grabber items
            items = []
            for link in discovery_result.links:
                item = self._create_grabber_item_from_discovered_link(link)
                items.append(item)
            
            return GrabberResult(
                items=items,
                source_url=url,
                url_type=UrlType.HTML_PAGE,
                page_title=discovery_result.page_title,
                total_found=discovery_result.total_found,
                total_filtered=discovery_result.total_filtered
            )
        except Exception as e:
            # If page discovery fails, do NOT fallback to direct file
            # Always return with HTML_PAGE type
            print(f"Could not discover links from page: {e}")
            return GrabberResult(
                items=[],
                source_url=url,
                url_type=UrlType.HTML_PAGE,
                total_found=0,
                total_filtered=0
            )
    
    def _create_grabber_item_from_discovered_link(self, link) -> GrabberItem:
        """Create a GrabberItem from a discovered link."""
        from application.discovery.discovery_result import LinkType
        
        item_type = self._map_link_type_to_item_type(link.link_type)
        
        return GrabberItem(
            url=link.url,
            item_type=item_type,
            file_size=link.file_size,
            title=link.title,
            mime_type=link.mime_type,
            filename=link.url.split('/')[-1]
        )
    
    def _map_link_type_to_item_type(self, link_type) -> ItemType:
        """Map discovery link type to grabber item type."""
        from application.discovery.discovery_result import LinkType
        
        if link_type == LinkType.STREAM_HINT:
            return ItemType.STREAM
        elif link_type == LinkType.MEDIA:
            return ItemType.MEDIA
        elif link_type == LinkType.FILE:
            return ItemType.FILE
        else:
            return ItemType.FILE  # Default to file for simplicity