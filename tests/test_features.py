"""
Tests for URL feature extraction module.

Covers:
- Valid URLs (with/without schemes)
- Malformed and edge-case URLs
- IP address detection
- Feature vector consistency
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.features import extract_features, is_ip_address, get_feature_names


class TestIPAddressDetection:
    """Tests for IP address detection."""
    
    def test_ipv4_detection(self):
        """IPv4 addresses should be detected."""
        assert is_ip_address('192.168.1.1') == True
        assert is_ip_address('8.8.8.8') == True
        assert is_ip_address('127.0.0.1') == True
    
    def test_ipv6_detection(self):
        """IPv6 addresses should be detected."""
        assert is_ip_address('::1') == True
        assert is_ip_address('2001:db8::1') == True
    
    def test_hostname_not_ip(self):
        """Valid hostnames should not be detected as IP."""
        assert is_ip_address('google.com') == False
        assert is_ip_address('example.co.uk') == False
        assert is_ip_address('localhost') == False
    
    def test_invalid_ip(self):
        """Invalid IP strings should return False."""
        assert is_ip_address('256.256.256.256') == False
        assert is_ip_address('not-an-ip') == False
        assert is_ip_address('') == False


class TestFeatureExtraction:
    """Tests for feature extraction from valid URLs."""
    
    def test_basic_https_url(self):
        """Extract features from a simple HTTPS URL."""
        features = extract_features('https://www.google.com')
        assert len(features) == 12
        assert features[8] == 1  # has_https
        assert isinstance(features[0], (int, float))  # url_length is numeric
    
    def test_http_url(self):
        """Extract features from HTTP URL."""
        features = extract_features('http://example.com/path')
        assert len(features) == 12
        assert features[8] == 0  # has_https
    
    def test_url_without_scheme(self):
        """URLs without scheme should be handled (defaults to http)."""
        features = extract_features('example.com')
        assert len(features) == 12
        assert features[8] == 0  # defaults to http, not https
    
    def test_ip_address_url(self):
        """URL with IP address should be detected."""
        features = extract_features('http://192.168.1.1/admin')
        assert len(features) == 12
        assert features[7] == 1  # is_ip_address
    
    def test_url_with_at_sign(self):
        """URLs with @ signs (used in phishing) should be counted."""
        features = extract_features('http://real-site@phishing.com')
        assert features[6] > 0  # num_at_signs
    
    def test_url_with_special_characters(self):
        """URLs with special characters should count them."""
        features = extract_features('http://site.com/path?query=value&other=123')
        assert features[5] >= 2  # num_special_chars (at least ? and &)
    
    def test_url_with_query_parameters(self):
        """Query parameters should be counted."""
        features = extract_features('http://example.com?a=1&b=2&c=3')
        assert features[10] == 3  # num_query_params
    
    def test_url_with_unusual_port(self):
        """URLs with non-standard ports should be flagged."""
        features = extract_features('http://example.com:8080/path')
        assert features[11] == 1  # unusual_port
    
    def test_url_with_standard_ports(self):
        """Standard ports (80, 443) should not be flagged as unusual."""
        features_80 = extract_features('http://example.com:80/path')
        features_443 = extract_features('https://example.com:443/path')
        assert features_80[11] == 0  # not unusual
        assert features_443[11] == 0  # not unusual
    
    def test_feature_consistency(self):
        """Same URL should always produce same features."""
        url = 'https://www.github.com/user/repo?tab=readme'
        features1 = extract_features(url)
        features2 = extract_features(url)
        assert features1 == features2


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_url(self):
        """Empty URL should raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            extract_features('')
    
    def test_whitespace_only_url(self):
        """Whitespace-only URL should raise ValueError."""
        with pytest.raises(ValueError):
            extract_features('   ')
    
    def test_none_url(self):
        """None should raise ValueError."""
        with pytest.raises(ValueError):
            extract_features(None)
    
    def test_non_string_url(self):
        """Non-string input should raise ValueError."""
        with pytest.raises(ValueError):
            extract_features(123)
    
    def test_url_with_leading_trailing_whitespace(self):
        """Whitespace should be stripped."""
        features1 = extract_features('  https://example.com  ')
        features2 = extract_features('https://example.com')
        # Should handle gracefully
        assert len(features1) == 12
        assert len(features2) == 12


class TestFeatureNames:
    """Tests for feature name metadata."""
    
    def test_feature_names_exist(self):
        """Should return feature names."""
        names = get_feature_names()
        assert isinstance(names, list)
        assert len(names) == 12
    
    def test_feature_names_are_unique(self):
        """All feature names should be unique."""
        names = get_feature_names()
        assert len(names) == len(set(names))
    
    def test_feature_names_are_strings(self):
        """All feature names should be strings."""
        names = get_feature_names()
        assert all(isinstance(name, str) for name in names)


class TestPhishingIndicators:
    """Tests for common phishing URL patterns."""
    
    def test_long_url_detection(self):
        """Long URLs are more likely phishing."""
        short_url = extract_features('https://google.com')
        long_url = extract_features(
            'https://very-long-domain-name-designed-to-confuse.com/'
            '?id=123&session=abc&token=xyz'
        )
        assert long_url[0] > short_url[0]  # url_length
    
    def test_hyphenated_domain(self):
        """Hyphenated domains are sometimes phishing."""
        url = extract_features('https://bank-security-verify.com')
        assert url[3] > 0  # num_hyphens
    
    def test_numeric_ip_vs_domain(self):
        """IP-based URLs may be phishing."""
        ip_url = extract_features('http://192.168.1.1/banking')
        domain_url = extract_features('http://bank.com/banking')
        assert ip_url[7] == 1  # is_ip_address
        assert domain_url[7] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
