"""
Threat Intelligence Integration Module

Integrates with AlienVault OTX API to check URLs against threat intelligence feeds.
Provides reputation scores and malware/phishing indicators.
"""

import requests
import os
import logging
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
import time

logger = logging.getLogger(__name__)


class OTXThreatIntel:
    """
    AlienVault OTX (Open Threat Exchange) integration for URL threat checking.
    
    Features:
    - URL reputation checking
    - Malware detection
    - Phishing indicators
    - Domain/IP analysis
    - Caching to reduce API calls
    """
    
    BASE_URL = "https://otx.alienvault.com/api/v1"
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 5):
        """
        Initialize OTX threat intelligence client.
        
        Args:
            api_key (str): AlienVault OTX API key. If None, loaded from OTX_API_KEY env var.
            timeout (int): Request timeout in seconds (default: 5).
            
        Raises:
            ValueError: If no API key is available.
        """
        self.api_key = api_key or os.getenv('OTX_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "OTX_API_KEY not found. Set environment variable or pass api_key parameter."
            )
        
        self.timeout = timeout
        self.headers = {
            'X-OTX-API-KEY': self.api_key,
            'User-Agent': 'Q-Sentinel/0.1.0'
        }
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour cache
        self._last_cache_clear = time.time()
    
    def _get_cached(self, key: str) -> Optional[Dict]:
        """Get value from cache if still valid."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: Dict):
        """Cache a value with timestamp."""
        self._cache[key] = (value, time.time())
    
    def check_url(self, url: str) -> Dict:
        """
        Check a URL against OTX threat intelligence.
        
        Args:
            url (str): URL to check.
            
        Returns:
            dict: {
                'is_malicious': bool,
                'reputation': int (-100 to 100),
                'threat_level': str ('critical', 'high', 'medium', 'low', 'clean'),
                'indicators': list of threat indicators,
                'data': full OTX response,
                'error': error message if any,
                'source': 'otx'
            }
        """
        try:
            # Parse URL to get hostname/domain
            parsed = urlparse(url)
            hostname = parsed.hostname or parsed.netloc.split(':')[0]
            
            if not hostname:
                return {
                    'is_malicious': False,
                    'reputation': 0,
                    'threat_level': 'unknown',
                    'indicators': [],
                    'data': None,
                    'error': 'Could not extract hostname from URL',
                    'source': 'otx'
                }
            
            # Check cache first
            cache_key = f"url:{hostname}"
            cached = self._get_cached(cache_key)
            if cached:
                cached['cached'] = True
                return cached
            
            # Query OTX for URL/domain reputation
            result = self._query_url(hostname)
            
            if result and 'data' in result:
                self._set_cache(cache_key, result)
            
            return result
        
        except Exception as e:
            logger.error(f"OTX threat check failed for {url}: {e}")
            return {
                'is_malicious': False,
                'reputation': 0,
                'threat_level': 'unknown',
                'indicators': [],
                'data': None,
                'error': str(e),
                'source': 'otx'
            }
    
    def _query_url(self, hostname: str) -> Dict:
        """
        Query OTX API for URL/domain reputation.
        
        Args:
            hostname (str): Hostname or domain to check.
            
        Returns:
            dict: Threat intelligence result.
        """
        try:
            # Query URL endpoint
            url = f"{self.BASE_URL}/urls/{hostname}"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 404:
                # URL not found in OTX (not malicious)
                return {
                    'is_malicious': False,
                    'reputation': 100,  # High reputation if clean
                    'threat_level': 'clean',
                    'indicators': [],
                    'data': {'status': 'not_found'},
                    'error': None,
                    'source': 'otx'
                }
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse response
                is_malicious = bool(data.get('malware_samples') or data.get('httpresponse'))
                reputation = self._calculate_reputation(data)
                threat_level = self._get_threat_level(reputation, data)
                indicators = self._extract_indicators(data)
                
                return {
                    'is_malicious': is_malicious,
                    'reputation': reputation,
                    'threat_level': threat_level,
                    'indicators': indicators,
                    'data': data,
                    'error': None,
                    'source': 'otx'
                }
            
            # Handle other status codes
            logger.warning(f"OTX returned status {response.status_code} for {hostname}")
            return {
                'is_malicious': False,
                'reputation': 0,
                'threat_level': 'unknown',
                'indicators': [],
                'data': None,
                'error': f"API returned status {response.status_code}",
                'source': 'otx'
            }
        
        except requests.exceptions.Timeout:
            logger.error(f"OTX API timeout for {hostname}")
            return {
                'is_malicious': False,
                'reputation': 0,
                'threat_level': 'unknown',
                'indicators': [],
                'data': None,
                'error': 'API request timeout',
                'source': 'otx'
            }
        
        except Exception as e:
            logger.error(f"OTX API error for {hostname}: {e}")
            return {
                'is_malicious': False,
                'reputation': 0,
                'threat_level': 'unknown',
                'indicators': [],
                'data': None,
                'error': str(e),
                'source': 'otx'
            }
    
    def _calculate_reputation(self, data: Dict) -> int:
        """
        Calculate reputation score from OTX data.
        
        Returns:
            int: -100 (most malicious) to +100 (most clean)
        """
        reputation = 100  # Start with clean
        
        # Deduct for indicators
        if data.get('malware_samples'):
            reputation -= 50
        
        if data.get('dga'):
            reputation -= 30
        
        if data.get('pulse_count', 0) > 0:
            reputation -= min(20, data['pulse_count'] * 2)
        
        if data.get('httpresponse'):
            reputation -= 40
        
        return max(-100, reputation)
    
    def _get_threat_level(self, reputation: int, data: Dict) -> str:
        """
        Determine threat level from reputation and data.
        
        Returns:
            str: 'critical', 'high', 'medium', 'low', or 'clean'
        """
        if reputation <= -80:
            return 'critical'
        elif reputation <= -40:
            return 'high'
        elif reputation <= 0:
            return 'medium'
        elif reputation < 80:
            return 'low'
        else:
            return 'clean'
    
    def _extract_indicators(self, data: Dict) -> list:
        """Extract list of threat indicators from OTX response."""
        indicators = []
        
        if data.get('malware_samples'):
            indicators.append(f"Malware detected: {len(data['malware_samples'])} samples")
        
        if data.get('dga'):
            indicators.append("DGA (Domain Generation Algorithm) detected")
        
        if data.get('pulse_count', 0) > 0:
            indicators.append(f"Found in {data['pulse_count']} threat pulses")
        
        if data.get('httpresponse'):
            indicators.append("Active in HTTP responses")
        
        if data.get('detections'):
            detections = data['detections']
            if detections.get('geo'):
                indicators.append(f"Geolocation anomalies detected")
        
        return indicators
    
    def check_ip(self, ip_address: str) -> Dict:
        """
        Check an IP address against OTX threat intelligence.
        
        Args:
            ip_address (str): IP address to check.
            
        Returns:
            dict: Threat intelligence result.
        """
        try:
            cache_key = f"ip:{ip_address}"
            cached = self._get_cached(cache_key)
            if cached:
                cached['cached'] = True
                return cached
            
            url = f"{self.BASE_URL}/ips/{ip_address}"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 404:
                result = {
                    'is_malicious': False,
                    'reputation': 100,
                    'threat_level': 'clean',
                    'indicators': [],
                    'data': {'status': 'not_found'},
                    'error': None,
                    'source': 'otx'
                }
            elif response.status_code == 200:
                data = response.json()
                is_malicious = bool(data.get('malware_samples') or data.get('reputation'))
                reputation = max(-100, min(100, 100 - data.get('reputation', 0)))
                
                result = {
                    'is_malicious': is_malicious,
                    'reputation': reputation,
                    'threat_level': self._get_threat_level(reputation, data),
                    'indicators': self._extract_indicators(data),
                    'data': data,
                    'error': None,
                    'source': 'otx'
                }
            else:
                result = {
                    'is_malicious': False,
                    'reputation': 0,
                    'threat_level': 'unknown',
                    'indicators': [],
                    'data': None,
                    'error': f"Status {response.status_code}",
                    'source': 'otx'
                }
            
            self._set_cache(cache_key, result)
            return result
        
        except Exception as e:
            logger.error(f"IP check failed for {ip_address}: {e}")
            return {
                'is_malicious': False,
                'reputation': 0,
                'threat_level': 'unknown',
                'indicators': [],
                'data': None,
                'error': str(e),
                'source': 'otx'
            }
    
    def get_api_status(self) -> Dict:
        """Check if OTX API is accessible."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/pulses/subscribed",
                headers=self.headers,
                timeout=self.timeout
            )
            return {
                'status': 'online' if response.status_code in [200, 404] else 'error',
                'code': response.status_code,
                'error': None
            }
        except Exception as e:
            return {
                'status': 'offline',
                'code': None,
                'error': str(e)
            }
