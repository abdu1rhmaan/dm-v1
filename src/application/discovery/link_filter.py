from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from .discovery_result import DiscoveredLink, LinkType
import re


class LinkFilter:
    """Filters out noise, ads, and invalid links."""
    
    # Known ad/tracker domains
    AD_DOMAINS = {
        'doubleclick.net', 'googlesyndication.com', 'googleadservices.com',
        'facebook.com/tr', 'google-analytics.com', 'googletagmanager.com',
        'ads.', 'tracker.', 'metrics.', 'stat.'
    }
    
    # Common tracking parameters to remove
    TRACKING_PARAMS = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'ref', 'source', 'campaign', 'medium', 'term'
    }
    
    # Known ad-related class/id patterns
    AD_PATTERNS = [
        r'ad', r'promo', r'banner', r'sponsor', r'advertisement',
        r'popup', r'widget', r'lightbox', r'modal', r'overlay'
    ]
    
    # Minimum file size in bytes (5KB) to consider valid
    MIN_FILE_SIZE = 5 * 1024  # 5KB
    
    # Extensions that are typically not direct downloads
    NON_DOWNLOAD_EXTENSIONS = {'.html', '.htm', '.php', '.asp', '.jsp', '.cgi', '.aspx'}
    
    def __init__(self, allowed_extensions: set = None):
        """
        Initialize the filter.
        
        Args:
            allowed_extensions: Set of custom extensions to allow (optional)
        """
        self.allowed_extensions = allowed_extensions or set()
    
    def is_valid_link(self, link: DiscoveredLink, element_attrs: dict = None) -> bool:
        """
        Check if a link is valid for download.
        
        Args:
            link: The DiscoveredLink to validate
            element_attrs: HTML element attributes (for ad detection)
            
        Returns:
            True if the link should be kept, False if it should be filtered out
        """
        # Basic URL validation
        if not link.url or link.url.startswith(('javascript:', 'mailto:', '#', 'tel:')):
            return False
        
        # Check for ad domains
        parsed = urlparse(link.url)
        domain = parsed.netloc.lower()
        for ad_domain in self.AD_DOMAINS:
            if ad_domain in domain:
                return False
        
        # Check for ad-related classes/ids if available
        if element_attrs:
            for attr_name, attr_value in element_attrs.items():
                if attr_name in ['class', 'id']:
                    if isinstance(attr_value, list):
                        attr_value = ' '.join(attr_value)
                    attr_value_lower = attr_value.lower()
                    for pattern in self.AD_PATTERNS:
                        if re.search(pattern, attr_value_lower):
                            return False
        
        # Check file size if available (ignore if too small)
        if link.file_size is not None and link.file_size < self.MIN_FILE_SIZE:
            # But make exception for stream hints (m3u8 files are usually small)
            if link.link_type != LinkType.STREAM_HINT:
                return False
        
        # Check for non-download extensions (unless explicitly allowed)
        path = parsed.path.lower()
        for ext in self.NON_DOWNLOAD_EXTENSIONS:
            if path.endswith(ext) and ext not in self.allowed_extensions:
                return False
        
        return True
    
    def normalize_url(self, url: str, base_url: str) -> str:
        """
        Normalize a URL by converting relative to absolute and removing tracking params.
        
        Args:
            url: The URL to normalize
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Normalized URL
        """
        if not url:
            return url
        
        # Handle relative URLs
        if not url.startswith(('http://', 'https://', '//', 'mailto:', 'tel:', 'javascript:')):
            from urllib.parse import urljoin
            url = urljoin(base_url, url)
        
        # Remove URL fragments
        if '#' in url:
            url = url.split('#')[0]
        
        # Remove tracking parameters
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Filter out tracking parameters
        clean_params = {k: v for k, v in query_params.items() if k not in self.TRACKING_PARAMS}
        
        # Reconstruct URL without tracking params
        new_query = urlencode(clean_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    
    def filter_links(self, links: list, base_url: str) -> list:
        """
        Filter a list of links, normalizing URLs and removing invalid ones.
        
        Args:
            links: List of tuples (url, link_type, element_attrs)
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of valid DiscoveredLink objects
        """
        valid_links = []
        
        seen_urls = set()
        for item in links:
            if len(item) == 3:
                url, link_type, element_attrs = item
            else:
                url, link_type = item
                element_attrs = {}
            
            # Normalize URL
            normalized_url = self.normalize_url(url, base_url)
            
            # Skip if already seen
            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)
            
            # Create DiscoveredLink object
            link_obj = DiscoveredLink(
                url=normalized_url,
                link_type=link_type
            )
            
            # Validate the link
            if self.is_valid_link(link_obj, element_attrs):
                valid_links.append(link_obj)
        
        return valid_links