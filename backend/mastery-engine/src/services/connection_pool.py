"""
Connection Pool Management
==========================

Manages connection pools for Redis and Kafka with optimized settings for production use.
Implements connection pooling for better resource management and performance.
"""

import logging
import os
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

import redis
from redis.asyncio import ConnectionPool as AsyncRedisPool
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


@dataclass
class RedisPoolConfig:
    """Configuration for Redis connection pool"""
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "0"))
    password: Optional[str] = os.getenv("REDIS_PASSWORD")
    max_connections: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    socket_timeout: float = float(os.getenv("REDIS_SOCKET_TIMEOUT", "5.0"))
    socket_connect_timeout: float = float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "2.0"))
    retry_on_timeout: bool = True
    health_check_interval: int = 30  # seconds
    pool_recycle: int = 3600  # recycle connections after 1 hour


@dataclass
class KafkaPoolConfig:
    """Configuration for Kafka connection pool/producer"""
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    client_id: str = os.getenv("KAFKA_CLIENT_ID", "mastery-engine")
    security_protocol: str = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
    sasl_mechanism: Optional[str] = os.getenv("KAFKA_SASL_MECHANISM")
    username: Optional[str] = os.getenv("KAFKA_USERNAME")
    password: Optional[str] = os.getenv("KAFKA_PASSWORD")
    max_block_ms: int = int(os.getenv("KAFKA_MAX_BLOCK_MS", "5000"))
    connections_max_idle_ms: int = int(os.getenv("KAFKA_CONNECTIONS_MAX_IDLE_MS", "540000"))  # 9 minutes
    request_timeout_ms: int = int(os.getenv("KAFKA_REQUEST_TIMEOUT_MS", "30000"))
    retry_backoff_ms: int = int(os.getenv("KAFKA_RETRY_BACKOFF_MS", "100"))
    linger_ms: int = int(os.getenv("KAFKA_LINGER_MS", "5"))  # Batch small messages
    batch_size: int = int(os.getenv("KAFKA_BATCH_SIZE", "16384"))  # 16KB


class RedisConnectionPool:
    """
    Redis connection pool manager with async support

    Features:
    - Single shared connection pool across application
    - Automatic connection health checking
    - Connection recycling to prevent stale connections
    - Optimized pool settings for high concurrency
    """

    _instance: Optional['RedisConnectionPool'] = None
    _pool: Optional[AsyncRedisPool] = None

    def __init__(self, config: Optional[RedisPoolConfig] = None):
        self.config = config or RedisPoolConfig()
        self._client = None
        logger.info(f"Redis connection pool initialized with: {self.config}")

    @classmethod
    def get_instance(cls, config: Optional[RedisPoolConfig] = None) -> 'RedisConnectionPool':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    def get_pool(self) -> AsyncRedisPool:
        """Get or create async connection pool"""
        if self._pool is None:
            self._pool = AsyncRedisPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=self.config.retry_on_timeout,
                health_check_interval=self.config.health_check_interval,
                socket_keepalive=True,
                socket_keepalive_options={},
                connection_kwargs={
                    "retry_on_timeout": self.config.retry_on_timeout,
                }
            )
            logger.info(f"Created Redis connection pool (max: {self.config.max_connections})")

        return self._pool

    def get_sync_client(self) -> redis.Redis:
        """Get synchronous Redis client for non-async operations"""
        return redis.Redis(
            host=self.config.host,
            port=self.config.port,
            db=self.config.db,
            password=self.config.password,
            socket_timeout=self.config.socket_timeout,
            socket_connect_timeout=self.config.socket_connect_timeout,
            retry_on_timeout=self.config.retry_on_timeout,
            health_check_interval=self.config.health_check_interval,
            max_connections=self.config.max_connections,
            pool_recycle=self.config.pool_recycle
        )

    async def health_check(self) -> bool:
        """Verify pool health"""
        try:
            pool = self.get_pool()
            # Try to acquire a connection from pool
            conn = await pool.get_connection("PING")
            await pool.release(conn)
            return True
        except Exception as e:
            logger.error(f"Redis pool health check failed: {e}")
            return False

    async def close(self):
        """Close all connections in pool"""
        if self._pool:
            await self._pool.disconnect()
            logger.info("Redis connection pool closed")


class KafkaConnectionManager:
    """
    Kafka connection manager for producers and consumers

    Features:
    - Connection reuse for producers
    - Optimized batch settings
    - SASL/SSL support
    - Connection validation
    """

    _instance: Optional['KafkaConnectionManager'] = None
    _producer: Optional[KafkaProducer] = None

    def __init__(self, config: Optional[KafkaPoolConfig] = None):
        self.config = config or KafkaPoolConfig()
        logger.info(f"Kafka connection manager initialized: {self.config.bootstrap_servers}")

    @classmethod
    def get_instance(cls, config: Optional[KafkaPoolConfig] = None) -> 'KafkaConnectionManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    def _get_auth_config(self) -> Dict[str, Any]:
        """Get authentication configuration"""
        config = {
            "bootstrap_servers": self.config.bootstrap_servers.split(","),
            "client_id": self.config.client_id,
            "security_protocol": self.config.security_protocol,
            "max_block_ms": self.config.max_block_ms,
            "connections_max_idle_ms": self.config.connections_max_idle_ms,
            "request_timeout_ms": self.config.request_timeout_ms,
            "retry_backoff_ms": self.config.retry_backoff_ms,
            "linger_ms": self.config.linger_ms,
            "batch_size": self.config.batch_size,
            "acks": "all",  # Ensure durability
            "retries": 3,
        }

        # Add SASL configuration if provided
        if self.config.sasl_mechanism and self.config.username and self.config.password:
            config.update({
                "sasl_mechanism": self.config.sasl_mechanism,
                "sasl_plain_username": self.config.username,
                "sasl_plain_password": self.config.password,
            })

        # Add SSL configuration if needed
        if self.config.security_protocol in ["SASL_SSL", "SSL"]:
            config["ssl_check_hostname"] = True
            config["ssl_cafile"] = os.getenv("KAFKA_SSL_CAFILE")
            config["ssl_certfile"] = os.getenv("KAFKA_SSL_CERTFILE")
            config["ssl_keyfile"] = os.getenv("KAFKA_SSL_KEYFILE")

        return config

    def get_producer(self) -> KafkaProducer:
        """Get or create Kafka producer with connection pooling"""
        if self._producer is None:
            try:
                config = self._get_auth_config()
                self._producer = KafkaProducer(**config)
                logger.info(f"Created Kafka producer for {self.config.bootstrap_servers}")
            except KafkaError as e:
                logger.error(f"Failed to create Kafka producer: {e}")
                raise

        return self._producer

    def create_consumer(self, group_id: str, topic: str, auto_offset_reset: str = "latest") -> KafkaConsumer:
        """Create a new Kafka consumer (consumers cannot be reused like producers)"""
        config = self._get_auth_config()
        config.update({
            "group_id": group_id,
            "auto_offset_reset": auto_offset_reset,
            "enable_auto_commit": False,  # Manual commit for reliability
            "value_deserializer": lambda m: json.loads(m.decode('utf-8')),
            "key_deserializer": lambda k: k.decode('utf-8') if k else None,
        })

        try:
            consumer = KafkaConsumer(topic, **config)
            logger.info(f"Created Kafka consumer for topic '{topic}' with group '{group_id}'")
            return consumer
        except KafkaError as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            raise

    def health_check(self) -> bool:
        """Verify Kafka connectivity"""
        try:
            producer = self.get_producer()
            # Test metadata fetch
            topics = producer.list_topics(timeout=5)
            logger.info(f"Kafka health check passed, topics available: {len(topics)}")
            return True
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return False

    def close(self):
        """Close producer connections"""
        if self._producer:
            try:
                self._producer.flush()
                self._producer.close()
                logger.info("Kafka producer closed")
            except Exception as e:
                logger.error(f"Error closing Kafka producer: {e}")
            finally:
                self._producer = None


# Global pool instances
redis_pool = RedisConnectionPool.get_instance()
kafka_manager = KafkaConnectionManager.get_instance()


def get_redis_pool() -> RedisConnectionPool:
    """Get global Redis pool instance"""
    return redis_pool


def get_kafka_manager() -> KafkaConnectionManager:
    """Get global Kafka manager instance"""
    return kafka_manager


# Connection factory functions for convenience
async def get_redis_client():
    """Get async Redis client using shared pool"""
    pool = redis_pool.get_pool()
    return pool


def get_redis_sync_client():
    """Get synchronous Redis client"""
    return redis_pool.get_sync_client()


def get_kafka_producer():
    """Get Kafka producer using shared manager"""
    return kafka_manager.get_producer()


def create_kafka_consumer(group_id: str, topic: str):
    """Create Kafka consumer"""
    return kafka_manager.create_consumer(group_id, topic)


# Health check functions
async def check_redis_health() -> bool:
    """Check Redis connection health"""
    return await redis_pool.health_check()


def check_kafka_health() -> bool:
    """Check Kafka connection health"""
    return kafka_manager.health_check()


# Cleanup functions
async def cleanup_connections():
    """Clean up all connection pools"""
    logger.info("Cleaning up connection pools...")
    await redis_pool.close()
    kafka_manager.close()
    logger.info("Connection cleanup completed")