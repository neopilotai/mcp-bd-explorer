# scripts/transformation_pipeline.py

"""
Transformation pipeline for data cleaning, deduplication, and categorization.
Implements the full ETL transformation layer using Pandas and PostgreSQL.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_batch
from difflib import SequenceMatcher
import json
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class WebsiteCategory(Enum):
    """Website category enumeration"""
    GOVERNMENT = "government"
    NEWS = "news"
    ECOMMERCE = "e-commerce"
    EDUCATION = "education"
    HEALTH = "health"
    FINANCE = "finance"
    TECHNOLOGY = "technology"
    ENTERTAINMENT = "entertainment"
    SOCIAL_MEDIA = "social_media"
    OTHER = "other"

class DataTransformationPipeline:
    """Main transformation pipeline orchestrator"""
    
    def __init__(self, db_params: Dict):
        self.db_params = db_params
        self.logger = logger
    
    def clean_domain_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize domain data"""
        
        df = df.copy()
        
        # Remove whitespace
        df['domain'] = df['domain'].str.strip().str.lower()
        
        # Remove www prefix
        df['domain'] = df['domain'].apply(self._remove_www)
        
        # Validate domains
        df['is_valid_domain'] = df['domain'].apply(self._validate_domain)
        df = df[df['is_valid_domain']].drop('is_valid_domain', axis=1)
        
        # Normalize metadata fields
        df['title'] = df.get('title', '').astype(str).str.strip().str.slice(0, 255)
        df['description'] = df.get('description', '').astype(str).str.strip().str.slice(0, 500)
        df['url'] = df['domain'].apply(self._normalize_url)
        
        # Handle null values
        df = df.fillna({
            'title': '',
            'description': '',
            'status_code': 0,
            'response_time_ms': 0
        })
        
        self.logger.info(f"Cleaned {len(df)} domains")
        return df
    
    def deduplicate_domains(self, df: pd.DataFrame, 
                           threshold: float = 0.95) -> pd.DataFrame:
        """Remove duplicate domains with smart merge logic"""
        
        df = df.copy()
        
        # Exact match deduplication
        initial_count = len(df)
        df = df.drop_duplicates(subset=['domain'], keep='first')
        exact_dupes = initial_count - len(df)
        self.logger.info(f"Removed {exact_dupes} exact duplicates")
        
        # Fuzzy matching for similar domains
        similar_pairs = self._find_similar_domains(df, threshold)
        
        domains_to_remove = set()
        for domain1, domain2 in similar_pairs:
            # Keep domain with higher quality score
            score1 = self._calculate_quality_score(df[df['domain'] == domain1].iloc[0])
            score2 = self._calculate_quality_score(df[df['domain'] == domain2].iloc[0])
            
            if score1 >= score2:
                domains_to_remove.add(domain2)
            else:
                domains_to_remove.add(domain1)
        
        df = df[~df['domain'].isin(domains_to_remove)]
        self.logger.info(f"Removed {len(domains_to_remove)} fuzzy duplicates")
        
        return df
    
    def categorize_websites(self, df: pd.DataFrame) -> pd.DataFrame:
        """Classify websites into categories"""
        
        df = df.copy()
        
        categories = []
        confidences = []
        
        for idx, row in df.iterrows():
            category, confidence = self._classify_website(row)
            categories.append(category.value)
            confidences.append(confidence)
        
        df['primary_category'] = categories
        df['category_confidence'] = confidences
        
        self.logger.info(f"Categorized {len(df)} websites")
        return df
    
    def calculate_quality_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute domain quality scores (0.0-1.0)"""
        
        df = df.copy()
        
        quality_scores = []
        for idx, row in df.iterrows():
            score = self._calculate_quality_score(row)
            quality_scores.append(score)
        
        df['quality_score'] = quality_scores
        
        self.logger.info(f"Calculated quality scores for {len(df)} domains")
        return df
    
    def detect_technologies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect technologies used on websites"""
        
        df = df.copy()
        
        # Placeholder for technology detection
        # In production, would call Wappalyzer, BuiltWith APIs, etc.
        df['technologies'] = df.apply(
            lambda row: self._detect_tech_stack(row),
            axis=1
        )
        
        return df
    
    def upsert_to_postgresql(self, df: pd.DataFrame) -> int:
        """Upsert transformed data to PostgreSQL"""
        
        try:
            conn = psycopg2.connect(**self.db_params)
            cursor = conn.cursor()
            
            # Prepare data for insertion
            data_tuples = []
            for idx, row in df.iterrows():
                data_tuples.append((
                    row['domain'],
                    row.get('url', f"https://{row['domain']}"),
                    row.get('title', ''),
                    row.get('description', ''),
                    row.get('primary_category', 'other'),
                    row.get('category_confidence', 0.0),
                    row.get('quality_score', 0.0),
                    row.get('status_code', 0),
                    row.get('response_time_ms', 0),
                    row.get('ssl_valid', False),
                    row.get('technologies', []),
                    datetime.now()
                ))
            
            # Execute upsert
            upsert_sql = """
                INSERT INTO domains 
                (domain, url, title, description, primary_category, 
                 category_confidence, quality_score, status_code, 
                 response_time_ms, ssl_valid, technologies, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (domain) DO UPDATE SET
                    url = EXCLUDED.url,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    primary_category = EXCLUDED.primary_category,
                    category_confidence = EXCLUDED.category_confidence,
                    quality_score = EXCLUDED.quality_score,
                    status_code = EXCLUDED.status_code,
                    response_time_ms = EXCLUDED.response_time_ms,
                    ssl_valid = EXCLUDED.ssl_valid,
                    technologies = EXCLUDED.technologies,
                    updated_at = EXCLUDED.updated_at
            """
            
            execute_batch(cursor, upsert_sql, data_tuples, page_size=1000)
            conn.commit()
            
            inserted = cursor.rowcount
            cursor.close()
            conn.close()
            
            self.logger.info(f"Upserted {inserted} domains to PostgreSQL")
            return inserted
        
        except psycopg2.Error as e:
            self.logger.error(f"Database error during upsert: {e}")
            return 0
    
    # Helper methods
    
    def _remove_www(self, domain: str) -> str:
        """Remove www prefix from domain"""
        if domain.startswith('www.'):
            return domain[4:]
        return domain
    
    def _validate_domain(self, domain: str) -> bool:
        """Validate domain format"""
        # Simple validation
        parts = domain.split('.')
        if len(parts) < 2:
            return False
        if any(len(part) == 0 for part in parts):
            return False
        if len(parts[-1]) < 2:
            return False
        return True
    
    def _normalize_url(self, domain: str) -> str:
        """Normalize domain to full URL"""
        if not domain.startswith('http'):
            return f"https://{domain}"
        return domain
    
    def _find_similar_domains(self, df: pd.DataFrame, 
                             threshold: float) -> List[Tuple[str, str]]:
        """Find similar domains using fuzzy matching"""
        
        similar_pairs = []
        domains = df['domain'].tolist()
        
        for i, domain1 in enumerate(domains):
            for domain2 in domains[i+1:]:
                similarity = SequenceMatcher(None, domain1, domain2).ratio()
                if similarity > threshold:
                    similar_pairs.append((domain1, domain2))
        
        return similar_pairs
    
    def _classify_website(self, row: dict) -> Tuple[WebsiteCategory, float]:
        """Classify website into category"""
        
        scores = {
            'government': self._score_government(row),
            'news': self._score_news(row),
            'ecommerce': self._score_ecommerce(row),
            'education': self._score_education(row),
            'health': self._score_health(row),
            'finance': self._score_finance(row),
        }
        
        primary_category = max(scores, key=scores.get)
        confidence = scores[primary_category]
        
        try:
            return WebsiteCategory(primary_category), confidence
        except ValueError:
            return WebsiteCategory.OTHER, 0.0
    
    def _calculate_quality_score(self, row: dict) -> float:
        """Calculate domain quality score (0.0-1.0)"""
        
        score = 0.0
        weights = {
            'domain_age': 0.15,
            'ssl_valid': 0.20,
            'response_time': 0.15,
            'content_quality': 0.20,
            'tech_stack': 0.15,
            'authority': 0.15
        }
        
        # SSL validity
        if row.get('ssl_valid', False):
            score += weights['ssl_valid']
        
        # Response time
        response_ms = row.get('response_time_ms', 5000)
        speed_score = max(1 - (response_ms / 5000), 0)
        score += speed_score * weights['response_time']
        
        # Content quality (word count, etc.)
        word_count = len(row.get('description', '').split())
        content_score = min(word_count / 100, 1.0)
        score += content_score * weights['content_quality']
        
        # Technology stack
        tech_count = len(row.get('technologies', []))
        tech_score = min(tech_count / 10, 1.0)
        score += tech_score * weights['tech_stack']
        
        return score
    
    def _detect_tech_stack(self, row: dict) -> List[str]:
        """Detect technology stack (placeholder)"""
        
        technologies = []
        
        # Simple detection based on headers, meta tags, etc.
        if 'wordpress' in row.get('title', '').lower():
            technologies.append('WordPress')
        
        if row.get('server_header'):
            technologies.append(row['server_header'])
        
        return technologies
    
    # Scoring methods
    def _score_government(self, row: dict) -> float:
        """Score likelihood of government website"""
        score = 0.0
        if '.gov.bd' in row.get('domain', ''):
            score += 0.8
        if 'ministry' in row.get('title', '').lower():
            score += 0.3
        return min(score, 1.0)
    
    def _score_news(self, row: dict) -> float:
        """Score likelihood of news website"""
        score = 0.0
        news_keywords = ['news', 'daily', 'post', 'bulletin', 'times']
        for keyword in news_keywords:
            if keyword in row.get('title', '').lower():
                score += 0.3
        return min(score, 1.0)
    
    def _score_ecommerce(self, row: dict) -> float:
        """Score likelihood of e-commerce website"""
        score = 0.0
        ecom_keywords = ['shop', 'store', 'buy', 'mall', 'cart']
        for keyword in ecom_keywords:
            if keyword in row.get('title', '').lower():
                score += 0.3
        return min(score, 1.0)
    
    def _score_education(self, row: dict) -> float:
        """Score likelihood of education website"""
        score = 0.0
        if '.edu.bd' in row.get('domain', ''):
            score += 0.8
        edu_keywords = ['university', 'college', 'school', 'institute']
        for keyword in edu_keywords:
            if keyword in row.get('title', '').lower():
                score += 0.3
        return min(score, 1.0)
    
    def _score_health(self, row: dict) -> float:
        """Score likelihood of health website"""
        score = 0.0
        health_keywords = ['hospital', 'clinic', 'doctor', 'medical', 'health']
        for keyword in health_keywords:
            if keyword in row.get('title', '').lower():
                score += 0.3
        return min(score, 1.0)
    
    def _score_finance(self, row: dict) -> float:
        """Score likelihood of finance website"""
        score = 0.0
        finance_keywords = ['bank', 'finance', 'investment', 'insurance']
        for keyword in finance_keywords:
            if keyword in row.get('title', '').lower():
                score += 0.3
        return min(score, 1.0)


def run_transformation_pipeline(input_data: pd.DataFrame, 
                               db_params: Dict) -> pd.DataFrame:
    """Execute complete transformation pipeline"""
    
    pipeline = DataTransformationPipeline(db_params)
    
    # Stage 1: Clean
    cleaned_df = pipeline.clean_domain_data(input_data)
    logger.info(f"Stage 1 Complete: {len(cleaned_df)} records cleaned")
    
    # Stage 2: Deduplicate
    deduped_df = pipeline.deduplicate_domains(cleaned_df)
    logger.info(f"Stage 2 Complete: {len(deduped_df)} unique records")
    
    # Stage 3: Categorize
    categorized_df = pipeline.categorize_websites(deduped_df)
    logger.info(f"Stage 3 Complete: {len(categorized_df)} records categorized")
    
    # Stage 4: Quality Score
    scored_df = pipeline.calculate_quality_scores(categorized_df)
    logger.info(f"Stage 4 Complete: Quality scores calculated")
    
    # Stage 5: Detect Technologies
    tech_df = pipeline.detect_technologies(scored_df)
    logger.info(f"Stage 5 Complete: Technologies detected")
    
    # Stage 6: Load to Database
    inserted = pipeline.upsert_to_postgresql(tech_df)
    logger.info(f"Stage 6 Complete: {inserted} records loaded to database")
    
    return tech_df


if __name__ == '__main__':
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'mcp_bd'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': int(os.getenv('DB_PORT', 5432))
    }
    
    # Example: Load sample data
    sample_data = pd.read_csv('sample_domains.csv')
    
    # Run pipeline
    result_df = run_transformation_pipeline(sample_data, db_params)
    print(f"Pipeline complete. Processed {len(result_df)} records.")
