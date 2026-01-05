"""Redis-based caching for workflow results"""

import hashlib
import json
from typing import Optional

import redis.asyncio as redis
from app.schemas.value_proposition import WorkflowResult
from app.config import settings
from app.observability.logger import get_logger

logger = get_logger(__name__)


class WorkflowCache:
    """
    Redis-based cache for workflow results.

    Caches results by a hash of the input to avoid re-running
    identical workflows.
    """

    def __init__(self, redis_url: str = settings.redis_url, ttl_seconds: int = 3600):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis"""
        if not self._client:
            self._client = await redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            logger.info("redis_connected", url=self.redis_url)

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self._client:
            await self._client.close()
            logger.info("redis_disconnected")

    def _generate_cache_key(self, content: str, provider: str, model: str) -> str:
        """
        Generate a cache key from input parameters.

        Args:
            content: Input content
            provider: Provider name
            model: Model name

        Returns:
            Cache key (hash)
        """
        key_data = f"{content}:{provider}:{model}"
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()
        return f"workflow:result:{key_hash}"

    async def get(
        self, content: str, provider: str, model: str
    ) -> Optional[WorkflowResult]:
        """
        Get cached workflow result.

        Args:
            content: Input content
            provider: Provider name
            model: Model name

        Returns:
            Cached WorkflowResult or None if not found
        """
        if not self._client:
            await self.connect()

        cache_key = self._generate_cache_key(content, provider, model)

        try:
            cached_data = await self._client.get(cache_key)  # type: ignore
            if cached_data:
                logger.info("cache_hit", cache_key=cache_key)
                result_dict = json.loads(cached_data)
                return WorkflowResult(**result_dict)

            logger.info("cache_miss", cache_key=cache_key)
            return None

        except Exception as e:
            logger.error("cache_get_error", error=str(e), cache_key=cache_key)
            return None

    async def set(
        self, content: str, provider: str, model: str, result: WorkflowResult
    ) -> None:
        """
        Cache a workflow result.

        Args:
            content: Input content
            provider: Provider name
            model: Model name
            result: WorkflowResult to cache
        """
        if not self._client:
            await self.connect()

        cache_key = self._generate_cache_key(content, provider, model)

        try:
            result_json = result.model_dump_json()
            await self._client.setex(cache_key, self.ttl_seconds, result_json)  # type: ignore
            logger.info(
                "cache_set",
                cache_key=cache_key,
                ttl_seconds=self.ttl_seconds,
            )

        except Exception as e:
            logger.error("cache_set_error", error=str(e), cache_key=cache_key)


# Singleton instance
workflow_cache = WorkflowCache()
