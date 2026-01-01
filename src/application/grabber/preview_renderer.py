from typing import List, Tuple
from .grabber_result import GrabberResult, GrabberItem, UrlType
from .item_type import ItemType


class PreviewRenderer:
    """Renders preview of grabber results and handles user approval."""
    
    def render_and_get_approval(self, result: GrabberResult) -> List[GrabberItem]:
        """
        Render the grabber result and get user approval.
        
        Args:
            result: The grabber result to render
            
        Returns:
            List of approved GrabberItem objects
        """
        if not result.items:
            if result.url_type == UrlType.STREAM_HINT:
                print(f"Stream detected but no downloadable variants.")
            elif result.url_type == UrlType.HTML_PAGE:
                print(f"No downloadable files found on page.")
            else:
                print(f"No downloadable items found.")
            return []
        
        print(f"Found {result.total_filtered} item(s):")
        
        for i, item in enumerate(result.items, 1):
            # Format file size
            size_str = "? MB"
            if item.file_size:
                size_mb = item.file_size / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB"
            
            # Get a display name
            display_name = item.filename or item.url.split('/')[-1][-30:]  # Limit length
            if len(display_name) > 30:
                display_name = display_name[:27] + "..."
            
            # Determine type string
            type_str = self._get_type_string(item.item_type)
            
            print(f"[{i}] {display_name} ({size_str}) [{type_str}]")
        
        print("\nActions:")
        print("  [A] Add all")
        print("  [S] Select manually") 
        print("  [R] Reject")
        
        choice = input("Choose an action: ").strip().upper()
        
        if choice == "A":
            # Add all items
            return result.items
        elif choice == "S":
            # Select manually
            selected_indices = input("Enter space-separated numbers to add (e.g., '1 3 5'): ").strip()
            if selected_indices:
                try:
                    indices = [int(x) for x in selected_indices.split()]
                    selected_items = []
                    for idx in indices:
                        if 1 <= idx <= len(result.items):
                            selected_items.append(result.items[idx - 1])
                    return selected_items
                except ValueError:
                    print("Invalid input. No items selected.")
                    return []
            else:
                return []
        elif choice == "R":
            print("Rejected all items.")
            return []
        else:
            print("Invalid choice. No items added.")
            return []
    
    def _get_type_string(self, item_type: ItemType) -> str:
        """Get a human-readable string for the item type."""
        type_mapping = {
            ItemType.FILE: "FILE",
            ItemType.MEDIA: "MEDIA",
            ItemType.STREAM: "STREAM"
        }
        return type_mapping.get(item_type, "UNKNOWN")