from typing import List
from .grabber_result import GrabberResult, UrlType
from .url_resolver import UrlResolver
from .handlers.direct_file_handler import DirectFileHandler
from .handlers.page_handler import PageHandler
from .handlers.hls_handler import HlsHandler


class GrabberEngine:
    """Main engine that handles URL grabbing based on URL type."""
    
    def __init__(self):
        self.url_resolver = UrlResolver()
        self.handlers = [
            DirectFileHandler(),
            PageHandler(),
            HlsHandler()
        ]
    
    def process(self, url: str) -> GrabberResult:
        """
        Process a URL and return appropriate grabber result.
        
        Args:
            url: The URL to process
            
        Returns:
            GrabberResult containing items to potentially download
        """
        # Resolve the URL to determine its type
        normalized_url, url_type = self.url_resolver.resolve(url)
        
        # Find and use the appropriate handler
        for handler in self.handlers:
            if handler.supports(url_type):
                try:
                    result = handler.handle(normalized_url)
                    # Ensure the result's url_type matches the resolved type
                    result.url_type = url_type
                    return result
                except Exception as e:
                    # For STREAM_HINT and HTML_PAGE, do NOT fallback
                    if url_type == UrlType.STREAM_HINT:
                        print(f"Warning: HLS handler failed for {url_type}: {e}")
                        # Return empty result with correct type
                        return GrabberResult(
                            items=[],
                            source_url=normalized_url,
                            url_type=url_type,
                            total_found=0,
                            total_filtered=0
                        )
                    elif url_type == UrlType.HTML_PAGE:
                        print(f"Warning: Page handler failed for {url_type}: {e}")
                        # Return empty result with correct type
                        return GrabberResult(
                            items=[],
                            source_url=normalized_url,
                            url_type=url_type,
                            total_found=0,
                            total_filtered=0
                        )
                    else:
                        # For DIRECT_FILE or other types, we can continue to next handler
                        print(f"Warning: Handler failed for {url_type}: {e}")
                        continue
        
        # If no handler supports this URL type, treat as direct file
        # But only for non-STREAM_HINT and non-HTML_PAGE types
        if url_type != UrlType.STREAM_HINT and url_type != UrlType.HTML_PAGE:
            direct_handler = DirectFileHandler()
            result = direct_handler.handle(normalized_url)
            result.url_type = url_type  # Maintain the resolved type
            return result
        else:
            # For STREAM_HINT and HTML_PAGE, return empty result if no handler worked
            return GrabberResult(
                items=[],
                source_url=normalized_url,
                url_type=url_type,
                total_found=0,
                total_filtered=0
            )
    
    def run_self_tests(self):
        """Run internal self-tests to verify the grabber system behavior."""
        print("=== Running Grabber Engine Self-Tests ===")
        
        # Test 1: Direct file
        print("\n1. Testing direct file:")
        result1 = self.process('https://httpbin.org/bytes/100')
        print(f"   URL: https://httpbin.org/bytes/100")
        print(f"   Type: {result1.url_type}")
        print(f"   Items: {len(result1.items)}")
        print(f"   Expected: DIRECT_FILE, items=1")
        print(f"   Status: {'PASS' if result1.url_type.value == 'direct_file' and len(result1.items) == 1 else 'FAIL'}")
        
        # Test 2: Page
        print("\n2. Testing page:")
        result2 = self.process('https://httpbin.org/links/2')
        print(f"   URL: https://httpbin.org/links/2")
        print(f"   Type: {result2.url_type}")
        print(f"   Items: {len(result2.items)}")
        print(f"   Expected: HTML_PAGE, items>=0")
        print(f"   Status: {'PASS' if result2.url_type.value == 'html_page' else 'FAIL'}")
        
        # Test 3: HLS (should not fallback)
        print("\n3. Testing HLS (no fallback):")
        result3 = self.process('https://example.com/test.m3u8')
        print(f"   URL: https://example.com/test.m3u8")
        print(f"   Type: {result3.url_type}")
        print(f"   Items: {len(result3.items)}")
        print(f"   Expected: STREAM_HINT, items=0, NO fallback")
        print(f"   Status: {'PASS' if result3.url_type.value == 'stream_hint' and len(result3.items) == 0 else 'FAIL'}")
        
        print("\n=== Self-Tests Complete ===")
    
