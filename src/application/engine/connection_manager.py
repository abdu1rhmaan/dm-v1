import threading
from typing import Dict, Optional
from urllib.parse import urlparse
import requests.adapters


class ConnectionManager:
    """Manages HTTP connections for multiple concurrent downloads."""
    
    def __init__(self, max_total_connections: int = 100, max_connections_per_host: int = 20):
        self.max_total_connections = max_total_connections
        self.max_connections_per_host = max_connections_per_host
        self._sessions: Dict[str, requests.Session] = {}
        self._lock = threading.Lock()
        self._setup_session_defaults()
    
    def _setup_session_defaults(self):
        """Setup default adapter settings for sessions."""
        # Create a default session with connection pooling settings
        default_session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=1,
            pool_maxsize=self.max_connections_per_host,
            max_retries=3
        )
        default_session.mount('http://', adapter)
        default_session.mount('https://', adapter)
        
        with self._lock:
            self._sessions['default'] = default_session
    
    def get_session_for_host(self, url: str) -> requests.Session:
        """Get an appropriate session for the given host."""
        host = urlparse(url).netloc
        
        with self._lock:
            if host not in self._sessions:
                # Create a new session for this host with connection pooling
                session = requests.Session()
                adapter = requests.adapters.HTTPAdapter(
                    pool_connections=1,
                    pool_maxsize=min(self.max_connections_per_host, self.max_total_connections),
                    max_retries=3
                )
                session.mount('http://', adapter)
                session.mount('https://', adapter)
                self._sessions[host] = session
            
            return self._sessions[host]
    
    def close_all_sessions(self):
        """Close all sessions and cleanup resources."""
        with self._lock:
            for session in self._sessions.values():
                session.close()
            self._sessions.clear()
    
    def get_stats(self):
        """Get connection statistics."""
        with self._lock:
            return {
                'active_sessions': len(self._sessions),
                'max_total_connections': self.max_total_connections,
                'max_per_host': self.max_connections_per_host
            }