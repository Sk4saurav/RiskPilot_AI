import httpx
from typing import Optional, Dict, Any
import logging
from .base import NetworkIntelligenceProvider

logger = logging.getLogger("worker.intelligence")

class LiveIPProvider(NetworkIntelligenceProvider):
    """
    Real external intelligence adapter for IP data.
    Uses the free ip-api.com endpoint.
    """
    
    async def lookup_ip(self, ip_address: str) -> Optional[Dict[str, Any]]:
        # Skip local IPs
        if ip_address in ["127.0.0.1", "localhost", "::1"]:
            return None
            
        try:
            from apps.api.app.config import settings
            async with httpx.AsyncClient() as client:
                if settings.ipinfo_api_key:
                    url = f"https://ipinfo.io/{ip_address}?token={settings.ipinfo_api_key}"
                    resp = await client.get(url, timeout=3.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        privacy = data.get("privacy", {})
                        return {
                            "country": data.get("country"),
                            "city": data.get("city"),
                            "asn": data.get("org"),
                            "is_proxy": privacy.get("proxy", False) or privacy.get("hosting", False),
                            "source": "ipinfo.io"
                        }
                else:
                    # Need fields: country, city, proxy (hosting), isp/asn
                    # Using fields=17000447 for country, city, proxy, hosting, isp, as
                    url = f"http://ip-api.com/json/{ip_address}?fields=country,countryCode,city,isp,as,proxy,hosting"
                    resp = await client.get(url, timeout=3.0)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        return {
                            "country": data.get("countryCode"),
                            "city": data.get("city"),
                            "asn": data.get("as", "").split(" ")[0] if data.get("as") else data.get("isp"),
                            "is_proxy": data.get("proxy", False) or data.get("hosting", False),
                            "source": "ip-api.com"
                        }
        except Exception as e:
            logger.warning(f"Failed to fetch live IP intelligence for {ip_address}: {e}")
            return None
            
        return None


class RecordedIPProvider(NetworkIntelligenceProvider):
    """
    Deterministic provider for historical replay testing.
    Ensures that validation metrics never drift due to live API changes.
    """
    
    async def lookup_ip(self, ip_address: str) -> Optional[Dict[str, Any]]:
        # In a full system, this would query a frozen historical database or snapshot.
        # For this demo, we use a simple deterministic mapping.
        if "103.11.24" in ip_address: # The critical demo scenario IP
            return {
                "country": "RU",
                "city": "Moscow",
                "asn": "AS49505",
                "is_proxy": True,
                "source": "recorded_dataset"
            }
        elif "185.15.10" in ip_address: # The false positive demo scenario IP
            return {
                "country": "DE",
                "city": "Berlin",
                "asn": "AS3209",
                "is_proxy": True,
                "source": "recorded_dataset"
            }
        elif "142.250" in ip_address: # The suspicious demo scenario IP
            return {
                "country": "US",
                "city": "Mountain View",
                "asn": "AS15169",
                "is_proxy": False,
                "source": "recorded_dataset"
            }
            
        # Default benign fallback
        return {
            "country": "US",
            "city": "New York",
            "asn": "AS7922",
            "is_proxy": False,
            "source": "recorded_dataset"
        }
