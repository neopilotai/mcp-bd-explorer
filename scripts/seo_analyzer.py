#!/usr/bin/env python3
"""
SEO Data Analyzer for MCP-BD Explorer
Extracts and analyzes SEO-related metadata from web pages
"""

import logging
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from collections import Counter

logger = logging.getLogger(__name__)


class SEOAnalyzer:
    """
    Analyzes SEO data from web pages:
    - Title optimization
    - Meta description quality
    - Heading structure
    - Keywords & content
    - Structured data
    - Mobile friendliness signals
    - Technical SEO
    """
    
    def __init__(self):
        self.scores = {}
        
    def analyze(
        self,
        html_content: str,
        headers: Dict[str, str],
        url: str = ''
    ) -> Dict:
        """
        Perform comprehensive SEO analysis
        
        Args:
            html_content: HTML page content
            headers: HTTP response headers
            url: Page URL
            
        Returns:
            Dict with SEO analysis results
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        results = {
            'title': self._analyze_title(soup),
            'description': self._analyze_description(soup),
            'headings': self._analyze_headings(soup),
            'keywords': self._extract_keywords(soup),
            'structured_data': self._detect_structured_data(soup),
            'mobile_friendly': self._check_mobile_signals(soup, headers),
            'technical_seo': self._analyze_technical_seo(soup, headers),
            'links': self._analyze_links(soup, url),
            'content': self._analyze_content(soup),
            'seo_score': 0,  # Will be calculated
        }
        
        # Calculate overall SEO score
        results['seo_score'] = self._calculate_seo_score(results)
        
        return results
        
    def _analyze_title(self, soup: BeautifulSoup) -> Dict:
        """Analyze page title"""
        title_tag = soup.find('title')
        title_text = title_tag.text.strip() if title_tag else ''
        
        analysis = {
            'title': title_text,
            'length': len(title_text),
            'optimal_length': 30 <= len(title_text) <= 60,
            'present': bool(title_text),
            'score': 0
        }
        
        if analysis['present']:
            analysis['score'] += 10
        if analysis['optimal_length']:
            analysis['score'] += 15
            
        return analysis
        
    def _analyze_description(self, soup: BeautifulSoup) -> Dict:
        """Analyze meta description"""
        meta = soup.find('meta', {'name': 'description'})
        description = meta.get('content', '') if meta else ''
        
        analysis = {
            'description': description,
            'length': len(description),
            'optimal_length': 120 <= len(description) <= 160,
            'present': bool(description),
            'score': 0
        }
        
        if analysis['present']:
            analysis['score'] += 10
        if analysis['optimal_length']:
            analysis['score'] += 15
            
        return analysis
        
    def _analyze_headings(self, soup: BeautifulSoup) -> Dict:
        """Analyze heading structure"""
        h1_tags = soup.find_all('h1')
        h2_tags = soup.find_all('h2')
        h3_tags = soup.find_all('h3')
        
        analysis = {
            'h1_count': len(h1_tags),
            'h1_texts': [h.text.strip() for h in h1_tags[:3]],
            'h2_count': len(h2_tags),
            'h3_count': len(h3_tags),
            'has_hierarchy': len(h1_tags) > 0 and len(h2_tags) > 0,
            'optimal_h1': len(h1_tags) == 1,
            'score': 0
        }
        
        if analysis['optimal_h1']:
            analysis['score'] += 10
        if analysis['h2_count'] > 0:
            analysis['score'] += 10
        if analysis['has_hierarchy']:
            analysis['score'] += 10
            
        return analysis
        
    def _extract_keywords(self, soup: BeautifulSoup) -> Dict:
        """Extract keywords from content"""
        # Get text content
        text = soup.get_text().lower()
        
        # Remove common words
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text)
        keywords = [w for w in words if w not in stopwords]
        
        # Count frequency
        word_freq = Counter(keywords)
        top_keywords = word_freq.most_common(10)
        
        analysis = {
            'top_keywords': [w[0] for w in top_keywords],
            'keyword_frequency': dict(top_keywords),
            'unique_keywords': len(word_freq),
            'total_words': len(keywords),
            'score': min(len(word_freq) / 100 * 15, 15)  # Max 15 points
        }
        
        return analysis
        
    def _detect_structured_data(self, soup: BeautifulSoup) -> Dict:
        """Detect structured data (Schema.org, JSON-LD)"""
        json_ld = soup.find_all('script', {'type': 'application/ld+json'})
        schema_org = soup.find_all(attrs={'itemscope': True})
        
        analysis = {
            'json_ld_present': len(json_ld) > 0,
            'json_ld_count': len(json_ld),
            'schema_org_present': len(schema_org) > 0,
            'schema_org_count': len(schema_org),
            'types': [],
            'score': 0
        }
        
        # Extract types
        for schema in schema_org:
            itemtype = schema.get('itemtype', '')
            if itemtype:
                analysis['types'].append(itemtype.split('/')[-1])
                
        if analysis['json_ld_present']:
            analysis['score'] += 10
        if analysis['schema_org_present']:
            analysis['score'] += 5
            
        return analysis
        
    def _check_mobile_signals(self, soup: BeautifulSoup, headers: Dict) -> Dict:
        """Check mobile friendliness signals"""
        viewport = soup.find('meta', {'name': 'viewport'})
        
        analysis = {
            'viewport_present': bool(viewport),
            'responsive_design': bool(viewport),
            'mobile_friendly': bool(viewport),  # Simplified check
            'score': 0
        }
        
        if analysis['viewport_present']:
            analysis['score'] += 10
            
        return analysis
        
    def _analyze_technical_seo(self, soup: BeautifulSoup, headers: Dict) -> Dict:
        """Analyze technical SEO aspects"""
        canonical = soup.find('link', {'rel': 'canonical'})
        robots_meta = soup.find('meta', {'name': 'robots'})
        lang_attr = soup.find('html', {'lang': True})
        
        analysis = {
            'canonical_present': bool(canonical),
            'canonical_url': canonical.get('href', '') if canonical else None,
            'robots_meta_present': bool(robots_meta),
            'lang_attribute': lang_attr.get('lang', '') if lang_attr else None,
            'https_used': headers.get('X-Frame-Options') is not None,  # Proxy check
            'score': 0
        }
        
        if analysis['canonical_present']:
            analysis['score'] += 5
        if analysis['lang_attribute']:
            analysis['score'] += 5
            
        return analysis
        
    def _analyze_links(self, soup: BeautifulSoup, base_url: str) -> Dict:
        """Analyze internal and external links"""
        internal_links = 0
        external_links = 0
        broken_anchors = 0
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href.startswith('http'):
                external_links += 1
            elif href.startswith('/'):
                internal_links += 1
            elif href == '#':
                broken_anchors += 1
                
        analysis = {
            'internal_links': internal_links,
            'external_links': external_links,
            'broken_anchors': broken_anchors,
            'total_links': internal_links + external_links,
            'score': min((internal_links + external_links) / 10, 10)  # Max 10 points
        }
        
        return analysis
        
    def _analyze_content(self, soup: BeautifulSoup) -> Dict:
        """Analyze content quality"""
        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
            
        text = soup.get_text()
        words = len(text.split())
        paragraphs = len(soup.find_all('p'))
        images = len(soup.find_all('img'))
        
        analysis = {
            'word_count': words,
            'paragraph_count': paragraphs,
            'image_count': images,
            'images_with_alt': sum(1 for img in soup.find_all('img') if img.get('alt')),
            'adequate_content': words >= 300,
            'score': 0
        }
        
        if analysis['adequate_content']:
            analysis['score'] += 10
        if analysis['image_count'] > 0:
            analysis['score'] += 5
            
        return analysis
        
    def _calculate_seo_score(self, results: Dict) -> float:
        """Calculate overall SEO score (0-100)"""
        total_score = 0
        
        total_score += results['title'].get('score', 0)  # 0-25
        total_score += results['description'].get('score', 0)  # 0-25
        total_score += results['headings'].get('score', 0)  # 0-30
        total_score += results['keywords'].get('score', 0)  # 0-15
        total_score += results['structured_data'].get('score', 0)  # 0-15
        total_score += results['mobile_friendly'].get('score', 0)  # 0-10
        total_score += results['technical_seo'].get('score', 0)  # 0-10
        total_score += results['links'].get('score', 0)  # 0-10
        total_score += results['content'].get('score', 0)  # 0-15
        
        return min(total_score, 100)


def main():
    """Test SEO analyzer"""
    analyzer = SEOAnalyzer()
    
    html = '''
    <html lang="en">
    <head>
        <title>Example Page - Best Content Here</title>
        <meta name="description" content="This is an example page with good SEO optimization for search engines and users.">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="canonical" href="https://example.com/page">
        <script type="application/ld+json">
        {"@context": "https://schema.org"}
        </script>
    </head>
    <body>
        <h1>Main Heading</h1>
        <h2>Sub Heading 1</h2>
        <p>Content paragraph with keywords about the topic.</p>
        <p>Another paragraph with more relevant information.</p>
        <img src="image.jpg" alt="Example image">
        <a href="/">Internal Link</a>
        <a href="https://external.com">External Link</a>
    </body>
    </html>
    '''
    
    headers = {'X-Frame-Options': 'SAMEORIGIN'}
    
    results = analyzer.analyze(html, headers)
    print(f"SEO Score: {results['seo_score']:.0f}/100")
    print(f"Title: {results['title']['title']}")
    print(f"Heading Structure: H1={results['headings']['h1_count']}, H2={results['headings']['h2_count']}")
    print(f"Top Keywords: {results['keywords']['top_keywords']}")
    print(f"Content: {results['content']['word_count']} words")


if __name__ == "__main__":
    main()
