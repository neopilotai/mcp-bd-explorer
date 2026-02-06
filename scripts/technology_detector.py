#!/usr/bin/env python3
"""
Technology Detection Module for MCP-BD Explorer
Detects CMS, frameworks, libraries, and server technologies
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class TechnologyDetector:
    """
    Detects technologies used by websites through multiple methods:
    - HTTP header analysis
    - HTML meta tag parsing
    - JavaScript patterns
    - Framework signatures
    """
    
    # CMS Signatures
    CMS_SIGNATURES = {
        'WordPress': {
            'headers': ['X-Powered-By', 'Server'],
            'patterns': [r'wp-content', r'wp-includes', r'wordpress', r'/wp-'],
            'meta': ['generator'],
            'files': ['/wp-admin/', '/wp-login.php']
        },
        'Drupal': {
            'patterns': [r'drupal', r'/sites/all/'],
            'meta': ['generator'],
            'files': ['/admin/']
        },
        'Joomla': {
            'patterns': [r'joomla', r'/components/com_'],
            'meta': ['generator'],
            'files': ['/administrator/']
        },
        'Shopify': {
            'patterns': [r'shopify', r'Shopify.shop'],
            'headers': ['X-Shopify'],
            'files': ['/cdn/']
        },
        'Magento': {
            'patterns': [r'magento', r'/media/catalog/', r'/skin/'],
            'meta': ['generator']
        },
    }
    
    # Framework Signatures
    FRAMEWORK_SIGNATURES = {
        'React': {
            'patterns': [r'react', r'_react', r'__REACT'],
            'scripts': ['react.js', 'react-dom.js']
        },
        'Vue.js': {
            'patterns': [r'vue', r'__vue', r'Vue\{'],
            'scripts': ['vue.js', 'vue.min.js']
        },
        'Angular': {
            'patterns': [r'angular', r'ng-app', r'ng-module'],
            'scripts': ['angular.js']
        },
        'Django': {
            'patterns': [r'django', r'csrf'],
            'headers': ['Server']
        },
        'Rails': {
            'patterns': [r'rails', r'_rails_'],
            'headers': ['X-Frame-Options']
        },
        'Laravel': {
            'patterns': [r'laravel', r'XSRF-TOKEN'],
            'headers': ['X-Laravel']
        },
        'Express': {
            'patterns': [r'express'],
            'headers': ['X-Powered-By']
        },
    }
    
    # Server Software
    SERVER_SIGNATURES = {
        'Nginx': ['nginx'],
        'Apache': ['apache'],
        'IIS': ['microsoft-iis'],
        'CloudFlare': ['cloudflare'],
        'LiteSpeed': ['litespeed'],
    }
    
    # Programming Languages
    LANGUAGE_SIGNATURES = {
        'PHP': {
            'patterns': [r'<?php', r'php'],
            'headers': ['X-Powered-By', 'Server'],
            'files': ['.php']
        },
        'Python': {
            'patterns': [r'python'],
            'headers': ['Server']
        },
        'Node.js': {
            'patterns': [r'nodejs', r'node.js'],
            'headers': ['X-Powered-By']
        },
        'Java': {
            'patterns': [r'java', r'tomcat'],
            'headers': ['Server']
        },
        'C#/.NET': {
            'patterns': [r'asp.net', r'\.net'],
            'headers': ['X-Powered-By', 'Server']
        },
        'Ruby': {
            'patterns': [r'ruby'],
            'headers': ['X-Runtime']
        },
    }
    
    # CDN Detection
    CDN_SIGNATURES = {
        'Cloudflare': {
            'headers': ['CF-Ray', 'CF-Cache-Status'],
            'patterns': [r'cloudflare']
        },
        'AWS CloudFront': {
            'headers': ['CloudFront-Id', 'X-Amz-Cf-Id'],
            'patterns': [r'cloudfront']
        },
        'Akamai': {
            'headers': ['Akamai-Origin-Hop', 'AkamaiGHost'],
            'patterns': [r'akamai']
        },
        'Fastly': {
            'headers': ['X-Served-By', 'X-Cache'],
            'patterns': [r'fastly']
        },
    }
    
    # Analytics Tools
    ANALYTICS_SIGNATURES = {
        'Google Analytics': {
            'patterns': [r'google-analytics', r'ga\(', r'gtag', r'_gaq'],
            'scripts': ['google-analytics.com', 'analytics.google.com']
        },
        'Facebook Pixel': {
            'patterns': [r'facebook.*pixel', r'fbq'],
            'scripts': ['facebook.com/en_US/fbevents.js']
        },
        'Mixpanel': {
            'patterns': [r'mixpanel'],
            'scripts': ['mixpanel.com']
        },
        'Hotjar': {
            'patterns': [r'hotjar'],
            'scripts': ['hotjar.com']
        },
        'Segment': {
            'patterns': [r'segment'],
            'scripts': ['segment.com']
        },
    }
    
    def __init__(self):
        self.detected_technologies = {}
        
    def detect_all(
        self,
        html_content: str,
        headers: Dict[str, str],
        url: str = ''
    ) -> Dict[str, any]:
        """
        Detect all technologies used by a website
        
        Args:
            html_content: HTML page content
            headers: HTTP response headers
            url: Page URL
            
        Returns:
            Dict with detected technologies
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        results = {
            'cms': self._detect_cms(html_content, headers, soup),
            'frameworks': self._detect_frameworks(html_content, headers, soup),
            'server_software': self._detect_server_software(headers),
            'programming_language': self._detect_language(html_content, headers),
            'cdn': self._detect_cdn(headers),
            'analytics': self._detect_analytics(html_content, soup),
            'libraries': self._detect_libraries(html_content, soup),
            'webservers': self._detect_webservers(headers),
            'technologies': []
        }
        
        # Aggregate all technologies
        results['technologies'] = self._aggregate_technologies(results)
        
        return results
        
    def _detect_cms(self, html: str, headers: Dict, soup: BeautifulSoup) -> Optional[str]:
        """Detect CMS"""
        for cms, signatures in self.CMS_SIGNATURES.items():
            # Check headers
            for header in signatures.get('headers', []):
                if header in headers:
                    header_val = headers.get(header, '').lower()
                    if cms.lower() in header_val:
                        logger.debug(f"Detected CMS: {cms} (header)")
                        return cms
                        
            # Check HTML patterns
            for pattern in signatures.get('patterns', []):
                if re.search(pattern, html, re.IGNORECASE):
                    logger.debug(f"Detected CMS: {cms} (pattern)")
                    return cms
                    
            # Check meta tags
            for meta_name in signatures.get('meta', []):
                meta = soup.find('meta', {'name': meta_name})
                if meta:
                    content = meta.get('content', '').lower()
                    if cms.lower() in content:
                        logger.debug(f"Detected CMS: {cms} (meta)")
                        return cms
                        
        return None
        
    def _detect_frameworks(self, html: str, headers: Dict, soup: BeautifulSoup) -> List[str]:
        """Detect front-end and back-end frameworks"""
        frameworks = []
        
        for framework, signatures in self.FRAMEWORK_SIGNATURES.items():
            # Check patterns
            for pattern in signatures.get('patterns', []):
                if re.search(pattern, html, re.IGNORECASE):
                    frameworks.append(framework)
                    logger.debug(f"Detected framework: {framework}")
                    break
                    
            # Check scripts
            if framework not in frameworks:
                script_sources = [s.get('src', '') for s in soup.find_all('script')]
                for script in signatures.get('scripts', []):
                    if any(script in src for src in script_sources):
                        frameworks.append(framework)
                        logger.debug(f"Detected framework: {framework} (script)")
                        break
                        
        return frameworks
        
    def _detect_server_software(self, headers: Dict) -> Optional[str]:
        """Detect server software from headers"""
        server_header = headers.get('Server', '').lower()
        
        for server, patterns in self.SERVER_SIGNATURES.items():
            for pattern in patterns:
                if pattern.lower() in server_header:
                    logger.debug(f"Detected server: {server}")
                    return server
                    
        return None if not server_header else 'Unknown'
        
    def _detect_language(self, html: str, headers: Dict) -> Optional[str]:
        """Detect programming language"""
        for language, signatures in self.LANGUAGE_SIGNATURES.items():
            # Check patterns
            for pattern in signatures.get('patterns', []):
                if re.search(pattern, html, re.IGNORECASE):
                    logger.debug(f"Detected language: {language}")
                    return language
                    
            # Check headers
            for header in signatures.get('headers', []):
                if header in headers:
                    header_val = headers.get(header, '').lower()
                    if language.lower() in header_val:
                        logger.debug(f"Detected language: {language}")
                        return language
                        
        return None
        
    def _detect_cdn(self, headers: Dict) -> Optional[str]:
        """Detect CDN"""
        for cdn, signatures in self.CDN_SIGNATURES.items():
            for header in signatures.get('headers', []):
                if header in headers:
                    logger.debug(f"Detected CDN: {cdn}")
                    return cdn
                    
        return None
        
    def _detect_analytics(self, html: str, soup: BeautifulSoup) -> List[str]:
        """Detect analytics tools"""
        analytics = []
        script_sources = [s.get('src', '') for s in soup.find_all('script')]
        script_content = ' '.join(script_sources)
        
        for tool, signatures in self.ANALYTICS_SIGNATURES.items():
            for pattern in signatures.get('patterns', []):
                if re.search(pattern, html + script_content, re.IGNORECASE):
                    analytics.append(tool)
                    logger.debug(f"Detected analytics: {tool}")
                    break
                    
        return analytics
        
    def _detect_libraries(self, html: str, soup: BeautifulSoup) -> List[str]:
        """Detect JavaScript libraries"""
        libraries = []
        script_sources = [s.get('src', '') for s in soup.find_all('script')]
        
        common_libs = {
            'jQuery': ['jquery'],
            'Bootstrap': ['bootstrap'],
            'Lodash': ['lodash'],
            'Moment.js': ['moment'],
            'D3.js': ['d3'],
        }
        
        for lib, patterns in common_libs.items():
            for script in script_sources:
                for pattern in patterns:
                    if pattern in script.lower():
                        libraries.append(lib)
                        logger.debug(f"Detected library: {lib}")
                        break
                        
        return libraries
        
    def _detect_webservers(self, headers: Dict) -> List[str]:
        """Detect web servers"""
        servers = []
        server_header = headers.get('Server', '').lower()
        
        if 'nginx' in server_header:
            servers.append('Nginx')
        if 'apache' in server_header:
            servers.append('Apache')
        if 'microsoft-iis' in server_header:
            servers.append('IIS')
            
        return servers
        
    def _aggregate_technologies(self, results: Dict) -> List[str]:
        """Aggregate all detected technologies"""
        technologies = []
        
        if results.get('cms'):
            technologies.append(results['cms'])
        if results.get('server_software'):
            technologies.append(results['server_software'])
        if results.get('programming_language'):
            technologies.append(results['programming_language'])
        if results.get('cdn'):
            technologies.append(results['cdn'])
            
        technologies.extend(results.get('frameworks', []))
        technologies.extend(results.get('libraries', []))
        technologies.extend(results.get('analytics', []))
        
        return list(set(technologies))  # Remove duplicates


def main():
    """Test technology detection"""
    detector = TechnologyDetector()
    
    # Sample HTML
    html = '''
    <html>
    <head>
        <meta name="generator" content="WordPress 6.0">
        <script src="https://cdn.jsdelivr.net/npm/react@18.0.0/umd/react.production.min.js"></script>
        <script src="https://www.googletagmanager.com/gtag/js?id=GA_ID"></script>
    </head>
    <body>
        <h1>Test Page</h1>
    </body>
    </html>
    '''
    
    headers = {
        'Server': 'nginx/1.20.0',
        'X-Powered-By': 'Express',
    }
    
    results = detector.detect_all(html, headers)
    print("Detected Technologies:")
    print(f"  CMS: {results['cms']}")
    print(f"  Frameworks: {results['frameworks']}")
    print(f"  Server: {results['server_software']}")
    print(f"  Analytics: {results['analytics']}")
    print(f"  All technologies: {results['technologies']}")


if __name__ == "__main__":
    main()
