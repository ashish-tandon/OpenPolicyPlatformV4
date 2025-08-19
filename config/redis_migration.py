#!/usr/bin/env python3
"""
Redis Migration Manager for OpenPolicyPlatform V4
Handles the transition from local Redis to Azure Cache for Redis
"""

import redis
import os
import time
import logging
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationMode(Enum):
    """Redis migration modes"""
    LOCAL = "local"
    DUAL = "dual"
    AZURE = "azure"

@dataclass
class RedisConnection:
    """Redis connection configuration"""
    url: str
    ssl: bool = False
    ssl_cert_reqs: Optional[str] = None
    decode_responses: bool = True
    socket_connect_timeout: int = 5
    socket_timeout: int = 5
    retry_on_timeout: bool = True
    max_connections: int = 20

class RedisMigrationManager:
    """
    Manages Redis migration from local to Azure with fallback support
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.local_redis: Optional[redis.Redis] = None
        self.azure_redis: Optional[redis.Redis] = None
        self.migration_mode = MigrationMode(
            os.getenv('REDIS_MIGRATION_MODE', 'local')
        )
        
        # Initialize connections
        self._initialize_connections()
        
        # Migration statistics
        self.stats = {
            'local_operations': 0,
            'azure_operations': 0,
            'fallback_operations': 0,
            'errors': 0,
            'last_error': None
        }
    
    def _initialize_connections(self):
        """Initialize Redis connections based on configuration"""
        try:
            # Initialize local Redis (fallback)
            local_url = os.getenv('LOCAL_REDIS_URL')
            if local_url:
                self.local_redis = redis.Redis.from_url(
                    local_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                logger.info("Local Redis connection initialized")
            
            # Initialize Azure Redis
            azure_url = os.getenv('AZURE_REDIS_URL')
            if azure_url:
                self.azure_redis = redis.Redis.from_url(
                    azure_url,
                    decode_responses=True,
                    ssl=True,
                    ssl_cert_reqs=None,
                    socket_connect_timeout=10,
                    socket_timeout=10,
                    retry_on_timeout=True
                )
                logger.info("Azure Redis connection initialized")
            
        except Exception as e:
            logger.error(f"Error initializing Redis connections: {e}")
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
    
    def get(self, key: str) -> Optional[str]:
        """
        Get value with intelligent fallback strategy
        """
        try:
            # Try Azure Redis first if in dual or azure mode
            if self.migration_mode in [MigrationMode.AZURE, MigrationMode.DUAL] and self.azure_redis:
                try:
                    start_time = time.time()
                    value = self.azure_redis.get(key)
                    response_time = (time.time() - start_time) * 1000
                    
                    if value is not None:
                        self.stats['azure_operations'] += 1
                        logger.debug(f"Azure Redis GET {key}: {response_time:.2f}ms")
                        return value
                    
                except Exception as e:
                    logger.warning(f"Azure Redis GET failed for {key}: {e}")
                    self.stats['errors'] += 1
            
            # Fallback to local Redis
            if self.local_redis:
                try:
                    start_time = time.time()
                    value = self.local_redis.get(key)
                    response_time = (time.time() - start_time) * 1000
                    
                    if value is not None:
                        self.stats['local_operations'] += 1
                        logger.debug(f"Local Redis GET {key}: {response_time:.2f}ms")
                        return value
                    
                except Exception as e:
                    logger.warning(f"Local Redis GET failed for {key}: {e}")
                    self.stats['errors'] += 1
            
            return None
            
        except Exception as e:
            logger.error(f"Redis GET operation failed for {key}: {e}")
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            return None
    
    def set(self, key: str, value: str, ex: Optional[int] = None, nx: bool = False, xx: bool = False) -> bool:
        """
        Set value with dual-write strategy based on migration mode
        """
        success = True
        
        try:
            # Write to Azure Redis if in dual or azure mode
            if self.migration_mode in [MigrationMode.AZURE, MigrationMode.DUAL] and self.azure_redis:
                try:
                    start_time = time.time()
                    result = self.azure_redis.set(key, value, ex=ex, nx=nx, xx=xx)
                    response_time = (time.time() - start_time) * 1000
                    
                    if result:
                        self.stats['azure_operations'] += 1
                        logger.debug(f"Azure Redis SET {key}: {response_time:.2f}ms")
                    else:
                        success = False
                        
                except Exception as e:
                    logger.warning(f"Azure Redis SET failed for {key}: {e}")
                    self.stats['errors'] += 1
                    success = False
            
            # Write to local Redis (fallback or dual-write)
            if self.local_redis:
                try:
                    start_time = time.time()
                    result = self.local_redis.set(key, value, ex=ex, nx=nx, xx=xx)
                    response_time = (time.time() - start_time) * 1000
                    
                    if result:
                        self.stats['local_operations'] += 1
                        logger.debug(f"Local Redis SET {key}: {response_time:.2f}ms")
                    else:
                        success = False
                        
                except Exception as e:
                    logger.warning(f"Local Redis SET failed for {key}: {e}")
                    self.stats['errors'] += 1
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Redis SET operation failed for {key}: {e}")
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            return False
    
    def delete(self, *keys) -> int:
        """
        Delete keys with dual-write strategy
        """
        deleted_count = 0
        
        try:
            # Delete from Azure Redis if in dual or azure mode
            if self.migration_mode in [MigrationMode.AZURE, MigrationMode.DUAL] and self.azure_redis:
                try:
                    start_time = time.time()
                    count = self.azure_redis.delete(*keys)
                    response_time = (time.time() - start_time) * 1000
                    
                    if count > 0:
                        self.stats['azure_operations'] += 1
                        logger.debug(f"Azure Redis DELETE {keys}: {response_time:.2f}ms")
                        deleted_count = max(deleted_count, count)
                        
                except Exception as e:
                    logger.warning(f"Azure Redis DELETE failed for {keys}: {e}")
                    self.stats['errors'] += 1
            
            # Delete from local Redis
            if self.local_redis:
                try:
                    start_time = time.time()
                    count = self.local_redis.delete(*keys)
                    response_time = (time.time() - start_time) * 1000
                    
                    if count > 0:
                        self.stats['local_operations'] += 1
                        logger.debug(f"Local Redis DELETE {keys}: {response_time:.2f}ms")
                        deleted_count = max(deleted_count, count)
                        
                except Exception as e:
                    logger.warning(f"Local Redis DELETE failed for {keys}: {e}")
                    self.stats['errors'] += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Redis DELETE operation failed for {keys}: {e}")
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            return 0
    
    def exists(self, *keys) -> int:
        """
        Check if keys exist with fallback strategy
        """
        try:
            # Try Azure Redis first if in dual or azure mode
            if self.migration_mode in [MigrationMode.AZURE, MigrationMode.DUAL] and self.azure_redis:
                try:
                    start_time = time.time()
                    count = self.azure_redis.exists(*keys)
                    response_time = (time.time() - start_time) * 1000
                    
                    self.stats['azure_operations'] += 1
                    logger.debug(f"Azure Redis EXISTS {keys}: {response_time:.2f}ms")
                    return count
                    
                except Exception as e:
                    logger.warning(f"Azure Redis EXISTS failed for {keys}: {e}")
                    self.stats['errors'] += 1
            
            # Fallback to local Redis
            if self.local_redis:
                try:
                    start_time = time.time()
                    count = self.local_redis.exists(*keys)
                    response_time = (time.time() - start_time) * 1000
                    
                    self.stats['local_operations'] += 1
                    logger.debug(f"Local Redis EXISTS {keys}: {response_time:.2f}ms")
                    return count
                    
                except Exception as e:
                    logger.warning(f"Local Redis EXISTS failed for {keys}: {e}")
                    self.stats['errors'] += 1
            
            return 0
            
        except Exception as e:
            logger.error(f"Redis EXISTS operation failed for {keys}: {e}")
            self.stats['errors'] += 1
            self.stats['last_error'] = str(e)
            return 0
    
    def ping(self) -> Dict[str, Any]:
        """
        Health check for both Redis instances
        """
        health_status = {
            'local_redis': {'status': 'unknown', 'response_time': None, 'error': None},
            'azure_redis': {'status': 'unknown', 'response_time': None, 'error': None},
            'overall_status': 'unknown',
            'migration_mode': self.migration_mode.value
        }
        
        # Check local Redis
        if self.local_redis:
            try:
                start_time = time.time()
                self.local_redis.ping()
                response_time = (time.time() - start_time) * 1000
                
                health_status['local_redis'] = {
                    'status': 'healthy',
                    'response_time': f"{response_time:.2f}ms",
                    'error': None
                }
            except Exception as e:
                health_status['local_redis'] = {
                    'status': 'unhealthy',
                    'response_time': None,
                    'error': str(e)
                }
        
        # Check Azure Redis
        if self.azure_redis:
            try:
                start_time = time.time()
                self.azure_redis.ping()
                response_time = (time.time() - start_time) * 1000
                
                health_status['azure_redis'] = {
                    'status': 'healthy',
                    'response_time': f"{response_time:.2f}ms",
                    'error': None
                }
            except Exception as e:
                health_status['azure_redis'] = {
                    'status': 'unhealthy',
                    'response_time': None,
                    'error': str(e)
                }
        
        # Determine overall status
        if (health_status['local_redis']['status'] == 'healthy' or 
            health_status['azure_redis']['status'] == 'healthy'):
            health_status['overall_status'] = 'healthy'
        else:
            health_status['overall_status'] = 'unhealthy'
        
        return health_status
    
    def get_stats(self) -> Dict[str, Any]:
        """Get migration statistics"""
        return {
            **self.stats,
            'migration_mode': self.migration_mode.value,
            'local_redis_available': self.local_redis is not None,
            'azure_redis_available': self.azure_redis is not None
        }
    
    def set_migration_mode(self, mode: str):
        """Change migration mode dynamically"""
        try:
            self.migration_mode = MigrationMode(mode)
            logger.info(f"Migration mode changed to: {mode}")
        except ValueError:
            logger.error(f"Invalid migration mode: {mode}")
    
    def close(self):
        """Close Redis connections"""
        try:
            if self.local_redis:
                self.local_redis.close()
            if self.azure_redis:
                self.azure_redis.close()
            logger.info("Redis connections closed")
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")

# Convenience function for quick Redis operations
def get_redis_manager() -> RedisMigrationManager:
    """Get a Redis migration manager instance"""
    return RedisMigrationManager()

# Example usage
if __name__ == "__main__":
    # Test the Redis migration manager
    redis_manager = RedisMigrationManager()
    
    # Test basic operations
    print("Testing Redis operations...")
    
    # Set a test key
    success = redis_manager.set("test_key", "test_value", ex=60)
    print(f"SET operation: {'SUCCESS' if success else 'FAILED'}")
    
    # Get the test key
    value = redis_manager.get("test_key")
    print(f"GET operation: {value}")
    
    # Check health
    health = redis_manager.ping()
    print(f"Health check: {health}")
    
    # Get stats
    stats = redis_manager.get_stats()
    print(f"Statistics: {stats}")
    
    # Clean up
    redis_manager.delete("test_key")
    redis_manager.close()
