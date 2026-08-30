from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class NetworkIntelligenceProvider(ABC):
    """
    Abstract adapter for fetching external network intelligence.
    Ensures that historical replay engines can use deterministic data 
    while the live worker uses real OSINT APIs.
    """
    
    @abstractmethod
    async def lookup_ip(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """
        Lookup intelligence for an IP address.
        Should return a dictionary containing keys like:
        - country
        - city
        - asn
        - is_proxy
        """
        pass
