import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from .discovery_result import DiscoveryResult, DiscoveredLink, LinkType
from .link_classifier import LinkClassifier
from .link_filter import LinkFilter


class PageDiscoveryService:
    """Discovers downloadable links from HTML pages."""
    
    def __init__(self):
        self.classifier = LinkClassifier()
        self.filter = None  # Will be set when needed
    
    def discover_from_page(self, url: str, filters: List[str] = None, allowed_extensions: set = None) -> DiscoveryResult:
        """
        Discover downloadable links from a web page.
        
        Args:
            url: URL of the page to scan
            filters: List of filters to apply (e.g., ['video', 'image'])
            allowed_extensions: Set of custom extensions to allow
            
        Returns:
            DiscoveryResult with found links
        """
        # Set up the filter with allowed extensions
        self.filter = LinkFilter(allowed_extensions or set())
        
        try:
            # Fetch the page
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch page: {e}")
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract page title
        page_title = None
        title_tag = soup.find('title')
        if title_tag:
            page_title = title_tag.get_text().strip()
        
        # Find all potential links
        discovered_links = self._extract_links(soup, url)
        
        # Apply filters if specified
        if filters:
            discovered_links = self._apply_content_filters(discovered_links, filters)
        
        # Filter out noise and normalize URLs
        filtered_links = self.filter.filter_links(discovered_links, url)
        
        # Try to get file sizes for the links
        links_with_size = []
        for link in filtered_links:
            # Create a new DiscoveredLink with potentially updated file size
            size = self._get_file_size(link.url)
            updated_link = DiscoveredLink(
                url=link.url,
                link_type=link.link_type,
                file_size=size,
                title=link.title,
                mime_type=link.mime_type
            )
            links_with_size.append(updated_link)
        
        return DiscoveryResult(
            links=links_with_size,
            total_found=len(discovered_links),
            total_filtered=len(links_with_size),
            page_title=page_title
        )
    
    def _get_file_size(self, url: str) -> Optional[int]:
        """
        Attempt to get the file size of a URL by making a HEAD request.
        
        Args:
            url: URL to check
            
        Returns:
            File size in bytes, or None if unable to determine
        """
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            response.raise_for_status()
            content_length = response.headers.get('Content-Length')
            if content_length:
                return int(content_length)
        except:
            # If HEAD request fails, try GET with no content
            try:
                response = requests.get(url, stream=True, timeout=5)
                response.raise_for_status()
                content_length = response.headers.get('Content-Length')
                if content_length:
                    return int(content_length)
            except:
                pass
        return None
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[tuple]:
        """
        Extract potential download links from the HTML soup.
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for resolving relative links
            
        Returns:
            List of tuples (url, link_type, element_attrs)
        """
        links = []
        
        # Extract <a> tags
        for tag in soup.find_all('a', href=True):
            href = tag.get('href', '').strip()
            if href:
                abs_url = urljoin(base_url, href)
                link_type = self.classifier.classify_link(abs_url)
                attrs = dict(tag.attrs)
                links.append((abs_url, link_type, attrs))
        
        # Extract <img> tags
        for tag in soup.find_all('img', src=True):
            src = tag.get('src', '').strip()
            if src:
                abs_url = urljoin(base_url, src)
                link_type = self.classifier.classify_link(abs_url)
                attrs = dict(tag.attrs)
                links.append((abs_url, link_type, attrs))
        
        # Extract <video> tags with src
        for tag in soup.find_all('video', src=True):
            src = tag.get('src', '').strip()
            if src:
                abs_url = urljoin(base_url, src)
                link_type = self.classifier.classify_link(abs_url)
                attrs = dict(tag.attrs)
                links.append((abs_url, link_type, attrs))
        
        # Extract <source> tags inside video/audio
        for tag in soup.find_all('source', src=True):
            src = tag.get('src', '').strip()
            if src:
                abs_url = urljoin(base_url, src)
                link_type = self.classifier.classify_link(abs_url)
                attrs = dict(tag.attrs)
                links.append((abs_url, link_type, attrs))
        
        # Extract <link> tags with href (for potential downloads)
        for tag in soup.find_all('link', href=True):
            href = tag.get('href', '').strip()
            if href:
                abs_url = urljoin(base_url, href)
                link_type = self.classifier.classify_link(abs_url)
                attrs = dict(tag.attrs)
                links.append((abs_url, link_type, attrs))
        
        # Extract Open Graph tags for media hints
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        for tag in og_tags:
            prop = tag.get('property', '')
            content = tag.get('content', '')
            if content and prop in ['og:video', 'og:video:url', 'og:image', 'og:image:url']:
                abs_url = urljoin(base_url, content)
                link_type = LinkType.MEDIA  # Treat as media hint
                attrs = dict(tag.attrs)
                links.append((abs_url, link_type, attrs))
        
        return links
    
    def _apply_content_filters(self, links: List[tuple], filters: List[str]) -> List[tuple]:
        """
        Apply content filters to keep only specific types of links.
        
        Args:
            links: List of (url, link_type, attrs) tuples
            filters: List of filters to apply (e.g., ['video', 'image'])
            
        Returns:
            Filtered list of links
        """
        if not filters:
            return links
        
        # Map filter names to extensions
        filter_extensions = {
            'video': {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v', '.3gp', '.m3u8'},
            'image': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.tiff', '.ico'},
            'audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus'},
            'archive': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso', '.dmg', '.pkg'},
            'iso': {'.iso'}
        }
        
        # Add custom extensions if provided
        custom_extensions = set()
        for f in filters:
            if f not in filter_extensions:
                # Assume it's a custom extension
                ext = f if f.startswith('.') else f'.{f}'
                custom_extensions.add(ext.lower())
        
        valid_links = []
        for url, link_type, attrs in links:
            # Check if it matches any of the specified filters
            url_lower = url.lower()
            should_keep = False
            
            for filter_name in filters:
                if filter_name in filter_extensions:
                    for ext in filter_extensions[filter_name]:
                        if url_lower.endswith(ext):
                            should_keep = True
                            break
                elif filter_name in [ext.lstrip('.') for ext in custom_extensions]:
                    # Check for custom extensions
                    for ext in custom_extensions:
                        if url_lower.endswith(ext):
                            should_keep = True
                            break
            
            if should_keep:
                valid_links.append((url, link_type, attrs))
        
        return valid_links