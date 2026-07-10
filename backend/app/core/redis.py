import json
import logging
import time
from typing import Any, Dict, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("app.core.redis")


class UpstashRedisClient:
    """
    HTTP REST Client for Upstash Redis with a resilient in-memory local cache fallback.
    """
    def __init__(self):
        self.url = settings.UPSTASH_REDIS_REST_URL.strip().rstrip("/") if settings.UPSTASH_REDIS_REST_URL else ""
        self.token = settings.UPSTASH_REDIS_REST_TOKEN.strip() if settings.UPSTASH_REDIS_REST_TOKEN else ""
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        self.is_active = bool(self.url and self.token)
        
        # Resilient local fallbacks
        self._local_cache: Dict[str, Any] = {}
        self._local_expires: Dict[str, float] = {}

        if not self.is_active:
            logger.warning(
                "Upstash Redis REST configurations not found. Running session caches and rate limit counters in-memory."
            )

    def _execute_rest(self, cmd: list) -> Optional[Any]:
        """
        Submits a Redis command array to the Upstash REST endpoint.
        """
        if not self.is_active:
            return None
        try:
            with httpx.Client() as client:
                res = client.post(self.url, json=cmd, headers=self.headers, timeout=4.0)
                if res.status_code == 200:
                    data = res.json()
                    if "error" in data:
                        logger.error(f"Upstash Redis REST command error: {data['error']}")
                        return None
                    return data.get("result")
                else:
                    logger.error(f"Upstash Redis HTTP error {res.status_code}: {res.text}")
                    return None
        except Exception as e:
            logger.error(f"Failed to execute Redis REST call: {e}")
            return None

    def _check_local_expiry(self, key: str) -> None:
        """
        Evicts a key from local memory cache if its TTL has expired.
        """
        if key in self._local_expires:
            if time.time() > self._local_expires[key]:
                self._local_cache.pop(key, None)
                self._local_expires.pop(key, None)

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves a string value by key.
        """
        if self.is_active:
            val = self._execute_rest(["GET", key])
            if val is not None:
                return val
        
        # Local fallback lookup
        self._check_local_expiry(key)
        return self._local_cache.get(key)

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """
        Sets a value with optional expiration TTL in seconds.
        """
        # Parse value to string for Redis compatibility
        str_val = str(value)

        if self.is_active:
            cmd = ["SET", key, str_val]
            if ex is not None:
                cmd += ["EX", str(ex)]
            res = self._execute_rest(cmd)
            if res == "OK":
                return True

        # Local fallback execution
        self._local_cache[key] = str_val
        if ex is not None:
            self._local_expires[key] = time.time() + ex
        else:
            self._local_expires.pop(key, None)
        return True

    def delete(self, key: str) -> bool:
        """
        Deletes a key.
        """
        if self.is_active:
            res = self._execute_rest(["DEL", key])
            if res is not None:
                return bool(res)

        # Local fallback execution
        existed = key in self._local_cache
        self._local_cache.pop(key, None)
        self._local_expires.pop(key, None)
        return existed

    def incr(self, key: str) -> int:
        """
        Increments a numeric key value.
        """
        if self.is_active:
            res = self._execute_rest(["INCR", key])
            if res is not None:
                try:
                    return int(res)
                except ValueError:
                    pass

        # Local fallback execution
        self._check_local_expiry(key)
        val = self._local_cache.get(key, "0")
        try:
            num = int(val) + 1
        except ValueError:
            num = 1
        self._local_cache[key] = str(num)
        return num

    def expire(self, key: str, seconds: int) -> bool:
        """
        Sets an expiration timeout on a key.
        """
        if self.is_active:
            res = self._execute_rest(["EXPIRE", key, str(seconds)])
            if res is not None:
                return bool(res)

        # Local fallback execution
        if key in self._local_cache:
            self._local_expires[key] = time.time() + seconds
            return True
        return False


# Global singleton instance
redis_client = UpstashRedisClient()
