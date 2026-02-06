#!/usr/bin/env python3
"""
Redis Cache Strategy for MCP-BD Explorer

Implements a 3-tier caching architecture:
1. Query Result Cache - Expensive database queries
2. Session Cache - User sessions and preferences
3. Rate Limit Cache - API rate limiting
"""

import redis
import json
import hashlib
from typing import Any, Optional, Dict, List
from datetime import timedelta
from enum import Enum
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class CacheTier(Enum):
    """Cache tier levels with different TTL strategies"""
    HOT = "hot"  # 15 minutes - frequently accessed
    WARM = "warm"  # 1 hour - regular access
    COLD = "cold"  # 6 hours - occasional access


class RedisCache:
    """
    Production-grade Redis caching layer for MCP-BD Explorer
    
    Features:
    - Multi-tier caching with automatic TTL management
    - Distributed cache invalidation
    - Rate limiting with token bucket algorithm
    - Cache statistics and monitoring
    - Graceful degradation on cache miss
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """Initialize Redis connection with connection pooling"""
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            max_connections=50,
            retry_on_timeout=True,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        self.redis = redis.Redis(connection_pool=self.pool)
        self._verify_connection()

    def _verify_connection(self):
        """Verify Redis connection is working"""
        try:
            self.redis.ping()
            logger.info("Redis connection established successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    # ========================================================================
    # TIER 1: Query Result Cache
    # ========================================================================

    def cache_query_result(
        self,
        query_key: str,
        result: Any,
        tier: CacheTier = CacheTier.WARM,
        ttl_minutes: Optional[int] = None
    ) -> None:
        """
        Cache expensive query results with automatic TTL

        Args:
            query_key: Unique identifier for the query
            result: Query result to cache
            tier: Cache tier (determines default TTL)
            ttl_minutes: Override TTL (optional)
        """
        # Determine TTL based on tier
        ttl_map = {
            CacheTier.HOT: 15,     # 15 minutes
            CacheTier.WARM: 60,    # 1 hour
            CacheTier.COLD: 360    # 6 hours
        }
        ttl = ttl_minutes or ttl_map[tier]

        # Serialize result
        cached_value = json.dumps({
            "result": result,
            "tier": tier.value,
            "cached_at": self._get_timestamp()
        })

        # Store in Redis with expiration
        try:
            self.redis.setex(
                f"query:{query_key}",
                timedelta(minutes=ttl),
                cached_value
            )
            logger.debug(f"Cached query result: {query_key} (TTL: {ttl}m)")
        except redis.RedisError as e:
            logger.warning(f"Failed to cache query result: {e}")

    def get_cached_query(self, query_key: str) -> Optional[Any]:
        """
        Retrieve cached query result

        Args:
            query_key: Unique identifier for the query

        Returns:
            Cached result or None if not found/expired
        """
        try:
            cached_value = self.redis.get(f"query:{query_key}")
            if cached_value:
                data = json.loads(cached_value)
                logger.debug(f"Cache HIT: {query_key}")
                return data["result"]
            logger.debug(f"Cache MISS: {query_key}")
            return None
        except redis.RedisError as e:
            logger.warning(f"Failed to retrieve cached query: {e}")
            return None

    def invalidate_query_pattern(self, pattern: str) -> int:
        """
        Invalidate queries matching a pattern (wildcard)

        Args:
            pattern: Redis key pattern (e.g., "query:domain:*")

        Returns:
            Number of keys deleted
        """
        try:
            keys = self.redis.keys(f"query:{pattern}")
            if keys:
                deleted = self.redis.delete(*keys)
                logger.info(f"Invalidated {deleted} query cache entries")
                return deleted
            return 0
        except redis.RedisError as e:
            logger.warning(f"Failed to invalidate query cache: {e}")
            return 0

    # ========================================================================
    # TIER 2: Session Cache
    # ========================================================================

    def set_session(
        self,
        session_id: str,
        user_id: str,
        session_data: Dict[str, Any],
        ttl_days: int = 7
    ) -> None:
        """
        Store user session in cache

        Args:
            session_id: Unique session identifier
            user_id: User ID
            session_data: Session information (role, preferences, etc)
            ttl_days: Session TTL in days (default: 7 days)
        """
        session_payload = {
            "user_id": user_id,
            "data": session_data,
            "created_at": self._get_timestamp()
        }

        try:
            self.redis.setex(
                f"session:{session_id}",
                timedelta(days=ttl_days),
                json.dumps(session_payload)
            )
            # Also track active sessions by user
            self.redis.sadd(f"user_sessions:{user_id}", session_id)
            logger.debug(f"Session created: {session_id} for user {user_id}")
        except redis.RedisError as e:
            logger.warning(f"Failed to set session: {e}")

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session from cache

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found/expired
        """
        try:
            session_data = self.redis.get(f"session:{session_id}")
            if session_data:
                return json.loads(session_data)
            return None
        except redis.RedisError as e:
            logger.warning(f"Failed to retrieve session: {e}")
            return None

    def invalidate_user_sessions(self, user_id: str) -> int:
        """
        Invalidate all sessions for a user (on logout/account changes)

        Args:
            user_id: User ID

        Returns:
            Number of sessions deleted
        """
        try:
            session_ids = self.redis.smembers(f"user_sessions:{user_id}")
            deleted = 0
            for session_id in session_ids:
                self.redis.delete(f"session:{session_id}")
                deleted += 1
            self.redis.delete(f"user_sessions:{user_id}")
            logger.info(f"Invalidated {deleted} sessions for user {user_id}")
            return deleted
        except redis.RedisError as e:
            logger.warning(f"Failed to invalidate user sessions: {e}")
            return 0

    def extend_session(self, session_id: str, ttl_days: int = 7) -> bool:
        """Extend session TTL (on activity)"""
        try:
            return self.redis.expire(f"session:{session_id}", timedelta(days=ttl_days))
        except redis.RedisError as e:
            logger.warning(f"Failed to extend session: {e}")
            return False

    # ========================================================================
    # TIER 3: Rate Limiting
    # ========================================================================

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 1000,
        window_seconds: int = 60
    ) -> Dict[str, Any]:
        """
        Token bucket rate limiting algorithm

        Args:
            identifier: User/IP identifier
            max_requests: Max requests in time window
            window_seconds: Time window in seconds

        Returns:
            {
                "allowed": bool,
                "remaining": int,
                "reset_at": timestamp,
                "retry_after": int (only if blocked)
            }
        """
        rate_limit_key = f"ratelimit:{identifier}"

        try:
            current = self.redis.incr(rate_limit_key)

            # Set expiration on first request
            if current == 1:
                self.redis.expire(rate_limit_key, window_seconds)

            ttl = self.redis.ttl(rate_limit_key)

            if current <= max_requests:
                return {
                    "allowed": True,
                    "remaining": max_requests - current,
                    "reset_at": self._get_timestamp() + ttl
                }
            else:
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_at": self._get_timestamp() + ttl,
                    "retry_after": ttl
                }

        except redis.RedisError as e:
            logger.warning(f"Rate limit check failed: {e}")
            # Fail open (allow request if cache is down)
            return {"allowed": True, "remaining": max_requests}

    # ========================================================================
    # Monitoring & Statistics
    # ========================================================================

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            info = self.redis.info()
            stats = {
                "used_memory_mb": info["used_memory"] / 1024 / 1024,
                "used_memory_peak_mb": info["used_memory_peak"] / 1024 / 1024,
                "evicted_keys": info.get("evicted_keys", 0),
                "total_commands": info["total_commands_processed"],
                "connected_clients": info["connected_clients"],
                "keyspace": {}
            }

            # Count keys by pattern
            for pattern in ["query:", "session:", "ratelimit:"]:
                keys = self.redis.keys(f"{pattern}*")
                stats["keyspace"][pattern] = len(keys)

            return stats
        except redis.RedisError as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {}

    def get_hit_rate(self) -> Dict[str, float]:
        """Calculate cache hit rate"""
        try:
            info = self.redis.info("stats")
            hits = info["keyspace_hits"]
            misses = info["keyspace_misses"]
            total = hits + misses

            if total == 0:
                return {"hit_rate": 0.0, "miss_rate": 0.0}

            return {
                "hit_rate": (hits / total) * 100,
                "miss_rate": (misses / total) * 100,
                "total_requests": total
            }
        except redis.RedisError as e:
            logger.warning(f"Failed to calculate hit rate: {e}")
            return {}

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def flush_all(self) -> None:
        """DANGER: Flush all cache (for testing only)"""
        try:
            self.redis.flushdb()
            logger.warning("Cache flushed completely")
        except redis.RedisError as e:
            logger.error(f"Failed to flush cache: {e}")

    @staticmethod
    def _get_timestamp() -> float:
        """Get current Unix timestamp"""
        import time
        return time.time()

    @staticmethod
    def generate_query_key(
        query_type: str,
        domain_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate deterministic cache key for queries

        Args:
            query_type: Type of query (e.g., "domain_summary")
            domain_id: Domain ID (optional)
            filters: Query filters (optional)

        Returns:
            Cache key string
        """
        key_parts = [query_type]

        if domain_id:
            key_parts.append(domain_id)

        if filters:
            # Create hash of filters for deterministic key
            filter_str = json.dumps(filters, sort_keys=True)
            filter_hash = hashlib.md5(filter_str.encode()).hexdigest()[:8]
            key_parts.append(filter_hash)

        return ":".join(key_parts)


# ============================================================================
# Decorator for automatic caching
# ============================================================================

def cached_query(tier: CacheTier = CacheTier.WARM, ttl_minutes: Optional[int] = None):
    """
    Decorator for automatic query caching

    Usage:
        @cached_query(tier=CacheTier.HOT, ttl_minutes=30)
        def get_domain_summary(domain_id):
            # Expensive query here
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = RedisCache()

            # Generate cache key
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            key_hash = hashlib.md5(key.encode()).hexdigest()

            # Try to get from cache
            cached_result = cache.get_cached_query(key_hash)
            if cached_result is not None:
                return cached_result

            # Cache miss - execute function
            result = func(*args, **kwargs)

            # Cache the result
            cache.cache_query_result(key_hash, result, tier, ttl_minutes)

            return result

        return wrapper
    return decorator


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Initialize cache
    cache = RedisCache()

    # Example 1: Query result caching
    print("=== Query Result Caching ===")
    query_result = {"domain_id": "123", "name": "example.com.bd"}
    cache.cache_query_result("domain:example", query_result, CacheTier.WARM)
    print(f"Cached: {cache.get_cached_query('domain:example')}")

    # Example 2: Session management
    print("\n=== Session Management ===")
    session_data = {
        "role": "admin",
        "preferences": {"theme": "dark"}
    }
    cache.set_session("sess_abc123", "user_456", session_data)
    print(f"Session: {cache.get_session('sess_abc123')}")

    # Example 3: Rate limiting
    print("\n=== Rate Limiting ===")
    for i in range(5):
        result = cache.check_rate_limit("user:789", max_requests=3)
        print(f"Request {i+1}: {result}")

    # Example 4: Cache statistics
    print("\n=== Cache Statistics ===")
    stats = cache.get_cache_stats()
    print(f"Stats: {stats}")
    print(f"Hit Rate: {cache.get_hit_rate()}")
