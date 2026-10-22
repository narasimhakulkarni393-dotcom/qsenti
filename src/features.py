"""
URL Feature Extraction Module

Extracts lexical features from URL strings for machine learning models.
Handles malformed URLs, missing schemes, and IP addresses safely.
"""

import re
from urllib.parse import urlparse, parse_qs
import ipaddress


def is_ip_address(hostname):
    """
    Check if a hostname is an IP address.
    
    Args:
        hostname (str): The hostname to check.
        
    Returns:
        bool: True if hostname is a valid IPv4 or IPv6 address, False otherwise.
    """
    if not hostname:
        return False
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def extract_features(url):
    """
    Extract lexical features from a URL string.
    
    Returns a consistent 12-element feature vector suitable for ML models.
    Handles malformed URLs, missing schemes, and edge cases gracefully.
    
    Args:
        url (str): The URL string to analyze.
        
    Returns:
        list: A 12-element list of numerical features:
              [url_length, hostname_length, num_dots, num_hyphens, num_digits,
               num_special_chars, num_at_signs, is_ip, has_https, 
               num_path_separators, num_query_params, unusual_port]
               
    Raises:
        ValueError: If url is None or not a string.
    """
    if url is None or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
    
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")
    
    # Attempt to parse the URL, adding a scheme if missing
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', url):
        # No scheme detected; assume http
        parsed_url = urlparse('http://' + url)
        original_scheme = None
    else:
        parsed_url = urlparse(url)
        original_scheme = parsed_url.scheme
    
    # Extract components safely
    hostname = parsed_url.hostname or parsed_url.netloc.split(':')[0]
    if not hostname:
        hostname = ''
    
    path = parsed_url.path or ''
    query = parsed_url.query or ''
    scheme = parsed_url.scheme or 'http'
    port = parsed_url.port
    
    # Feature 1: URL length
    url_length = len(url)
    
    # Feature 2: Hostname length
    hostname_length = len(hostname)
    
    # Feature 3: Number of dots in the entire URL
    num_dots = url.count('.')
    
    # Feature 4: Number of hyphens
    num_hyphens = url.count('-')
    
    # Feature 5: Number of digits
    num_digits = sum(1 for c in url if c.isdigit())
    
    # Feature 6: Number of special characters (excluding common URL chars)
    special_chars = set('!@#$%^&*()_+={}[]|:;"\'<>?,./~`')
    num_special_chars = sum(1 for c in url if c in special_chars)
    
    # Feature 7: Number of '@' signs (used in phishing URLs to hide real host)
    num_at_signs = url.count('@')
    
    # Feature 8: Is the hostname an IP address? (1 if yes, 0 if no)
    is_ip = 1 if is_ip_address(hostname) else 0
    
    # Feature 9: Does the URL use HTTPS? (1 if https, 0 otherwise)
    has_https = 1 if scheme.lower() == 'https' else 0
    
    # Feature 10: Number of path separators
    num_path_separators = path.count('/')
    
    # Feature 11: Number of query parameters
    try:
        parsed_params = parse_qs(query)
        num_query_params = len(parsed_params)
    except Exception:
        num_query_params = 0
    
    # Feature 12: Unusual port (1 if port is specified and not 80/443, 0 otherwise)
    unusual_port = 0
    if port is not None and port not in (80, 443):
        unusual_port = 1
    
    features = [
        url_length,
        hostname_length,
        num_dots,
        num_hyphens,
        num_digits,
        num_special_chars,
        num_at_signs,
        is_ip,
        has_https,
        num_path_separators,
        num_query_params,
        unusual_port
    ]
    
    return features


def get_feature_names():
    """
    Get human-readable names for the feature vector.
    
    Returns:
        list: List of 12 feature names in order.
    """
    return [
        'url_length',
        'hostname_length',
        'num_dots',
        'num_hyphens',
        'num_digits',
        'num_special_chars',
        'num_at_signs',
        'is_ip_address',
        'has_https',
        'num_path_separators',
        'num_query_params',
        'unusual_port'
    ]


def extract_features_batch(urls):
    """
    Extract features from multiple URLs.
    
    Args:
        urls (list): List of URL strings.
        
    Returns:
        list: List of feature vectors (each a list of 12 features).
        
    Raises:
        ValueError: If urls is not a list or contains non-strings.
    """
    if not isinstance(urls, list):
        raise ValueError("Input must be a list of URLs")
    
    features_list = []
    for url in urls:
        try:
            features = extract_features(url)
            features_list.append(features)
        except ValueError as e:
            # Skip invalid URLs with a warning
            print(f"Warning: Skipping invalid URL '{url}': {e}")
            continue
    
    return features_list
