/**
 * Express.js Rate Limiting Middleware for OpenPolicy Platform
 * Integrates with the central rate limiting service
 */

const axios = require('axios');
const Redis = require('ioredis');

class RateLimiter {
  constructor(options = {}) {
    this.serviceUrl = options.serviceUrl || process.env.RATE_LIMIT_SERVICE_URL || 'http://rate-limiter:9026';
    this.redis = new Redis(options.redisUrl || process.env.REDIS_URL || 'redis://localhost:6379');
    this.localCache = new Map();
    this.cacheTimeout = options.cacheTimeout || 1000; // 1 second local cache
    this.enableLocalRateLimit = options.enableLocalRateLimit !== false;
    this.skipRoutes = options.skipRoutes || ['/health', '/metrics'];
    this.keyGenerator = options.keyGenerator || this.defaultKeyGenerator;
    this.onRateLimited = options.onRateLimited || this.defaultRateLimitHandler;
    this.extractUser = options.extractUser || this.defaultUserExtractor;
  }

  defaultKeyGenerator(req) {
    // Generate rate limit key based on user or IP
    const user = this.extractUser(req);
    if (user && user.id) {
      return `user:${user.id}`;
    }
    return `ip:${req.ip || req.connection.remoteAddress}`;
  }

  defaultUserExtractor(req) {
    // Extract user from common auth patterns
    return req.user || req.session?.user || null;
  }

  defaultRateLimitHandler(req, res, result) {
    res.status(429).json({
      error: 'Too Many Requests',
      message: result.reason || 'Rate limit exceeded',
      retryAfter: result.retry_after
    });
  }

  async checkRateLimit(context) {
    try {
      // Check local cache first
      const cacheKey = `${context.client_ip}:${context.endpoint}`;
      const cached = this.localCache.get(cacheKey);
      
      if (cached && cached.timestamp > Date.now() - this.cacheTimeout) {
        return cached.result;
      }

      // Call rate limiting service
      const response = await axios.post(`${this.serviceUrl}/check`, context, {
        timeout: 100, // 100ms timeout for rate limit checks
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const result = response.data;
      
      // Cache result locally
      this.localCache.set(cacheKey, {
        result,
        timestamp: Date.now()
      });

      // Clean up old cache entries periodically
      if (this.localCache.size > 10000) {
        this.cleanupCache();
      }

      return result;
    } catch (error) {
      console.error('Rate limit service error:', error.message);
      
      // Fallback to local rate limiting if service is down
      if (this.enableLocalRateLimit) {
        return this.localRateLimit(context);
      }
      
      // Allow request if rate limit service is down
      return {
        allowed: true,
        limit: 1000,
        remaining: 1000,
        reset_at: new Date(Date.now() + 3600000)
      };
    }
  }

  async localRateLimit(context) {
    // Simple local rate limiting as fallback
    const key = `local:${context.client_ip}:${context.endpoint}`;
    const limit = 100; // 100 requests per minute
    const window = 60; // 60 seconds

    const current = await this.redis.incr(key);
    
    if (current === 1) {
      await this.redis.expire(key, window);
    }

    const ttl = await this.redis.ttl(key);
    const resetAt = new Date(Date.now() + ttl * 1000);

    return {
      allowed: current <= limit,
      limit: limit,
      remaining: Math.max(0, limit - current),
      reset_at: resetAt,
      retry_after: current > limit ? ttl : null
    };
  }

  cleanupCache() {
    const now = Date.now();
    const timeout = this.cacheTimeout;
    
    for (const [key, value] of this.localCache.entries()) {
      if (value.timestamp < now - timeout) {
        this.localCache.delete(key);
      }
    }
  }

  middleware() {
    return async (req, res, next) => {
      // Skip rate limiting for certain routes
      if (this.skipRoutes.includes(req.path)) {
        return next();
      }

      // Extract context
      const user = this.extractUser(req);
      const context = {
        client_ip: req.ip || req.connection.remoteAddress,
        user_id: user?.id || null,
        user_role: user?.role || null,
        endpoint: req.path,
        method: req.method,
        api_key: req.headers['x-api-key'] || null,
        request_size: req.headers['content-length'] || 0,
        custom_attributes: {
          user_agent: req.headers['user-agent'],
          referer: req.headers['referer'],
          origin: req.headers['origin']
        }
      };

      // Check rate limit
      const result = await this.checkRateLimit(context);

      // Add rate limit headers
      res.setHeader('X-RateLimit-Limit', result.limit);
      res.setHeader('X-RateLimit-Remaining', result.remaining);
      res.setHeader('X-RateLimit-Reset', Math.floor(new Date(result.reset_at).getTime() / 1000));

      if (!result.allowed) {
        res.setHeader('Retry-After', result.retry_after);
        return this.onRateLimited(req, res, result);
      }

      next();
    };
  }

  // Utility methods for specific rate limiting scenarios
  
  async limitByUser(userId, action, limit = 10, window = 60) {
    const key = `rate:user:${userId}:${action}`;
    const current = await this.redis.incr(key);
    
    if (current === 1) {
      await this.redis.expire(key, window);
    }
    
    return {
      allowed: current <= limit,
      current,
      limit,
      remaining: Math.max(0, limit - current)
    };
  }

  async limitByIP(ip, action, limit = 100, window = 60) {
    const key = `rate:ip:${ip}:${action}`;
    const current = await this.redis.incr(key);
    
    if (current === 1) {
      await this.redis.expire(key, window);
    }
    
    return {
      allowed: current <= limit,
      current,
      limit,
      remaining: Math.max(0, limit - current)
    };
  }

  async limitByApiKey(apiKey, limit = 1000, window = 3600) {
    const key = `rate:api:${apiKey}`;
    const current = await this.redis.incr(key);
    
    if (current === 1) {
      await this.redis.expire(key, window);
    }
    
    return {
      allowed: current <= limit,
      current,
      limit,
      remaining: Math.max(0, limit - current)
    };
  }

  // Advanced rate limiting patterns
  
  async slidingWindowLimit(key, limit, window) {
    const now = Date.now();
    const windowStart = now - window * 1000;
    
    // Remove old entries
    await this.redis.zremrangebyscore(key, 0, windowStart);
    
    // Count current window
    const count = await this.redis.zcard(key);
    
    if (count < limit) {
      // Add current request
      await this.redis.zadd(key, now, now);
      await this.redis.expire(key, window + 1);
      
      return {
        allowed: true,
        current: count + 1,
        limit,
        remaining: limit - count - 1
      };
    }
    
    return {
      allowed: false,
      current: count,
      limit,
      remaining: 0
    };
  }

  async tokenBucket(key, rate, capacity, requested = 1) {
    const now = Date.now() / 1000; // Convert to seconds
    
    const bucket = await this.redis.hgetall(key);
    let tokens = parseFloat(bucket.tokens) || capacity;
    const lastUpdate = parseFloat(bucket.lastUpdate) || now;
    
    // Calculate tokens to add
    const elapsed = Math.max(0, now - lastUpdate);
    const newTokens = Math.min(capacity, tokens + (elapsed * rate));
    
    if (newTokens >= requested) {
      // Allow request
      tokens = newTokens - requested;
      await this.redis.hmset(key, {
        tokens: tokens,
        lastUpdate: now
      });
      await this.redis.expire(key, 3600);
      
      return {
        allowed: true,
        tokens: Math.floor(tokens),
        capacity
      };
    }
    
    // Deny request
    await this.redis.hmset(key, {
      tokens: newTokens,
      lastUpdate: now
    });
    await this.redis.expire(key, 3600);
    
    return {
      allowed: false,
      tokens: Math.floor(newTokens),
      capacity
    };
  }
}

// Express middleware factory functions

function createRateLimiter(options = {}) {
  const limiter = new RateLimiter(options);
  return limiter.middleware();
}

function createStrictRateLimiter(options = {}) {
  return createRateLimiter({
    ...options,
    enableLocalRateLimit: true,
    cacheTimeout: 500,
    onRateLimited: (req, res, result) => {
      res.status(429).json({
        error: 'Rate Limit Exceeded',
        message: 'You have made too many requests. Please try again later.',
        retryAfter: result.retry_after,
        limit: result.limit,
        remaining: result.remaining,
        reset: new Date(result.reset_at).toISOString()
      });
    }
  });
}

function createApiRateLimiter(options = {}) {
  return createRateLimiter({
    ...options,
    keyGenerator: (req) => {
      // Prefer API key over user ID over IP
      if (req.headers['x-api-key']) {
        return `api:${req.headers['x-api-key']}`;
      }
      if (req.user?.id) {
        return `user:${req.user.id}`;
      }
      return `ip:${req.ip}`;
    },
    extractUser: (req) => {
      // Extract user from JWT token
      if (req.headers.authorization) {
        try {
          const token = req.headers.authorization.split(' ')[1];
          const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64').toString());
          return { id: payload.sub, role: payload.role };
        } catch (e) {
          // Invalid token
        }
      }
      return null;
    }
  });
}

// Specific limiters for different scenarios

function loginRateLimiter(options = {}) {
  const limiter = new RateLimiter(options);
  
  return async (req, res, next) => {
    const ip = req.ip || req.connection.remoteAddress;
    const email = req.body.email || req.body.username;
    
    // Limit by IP
    const ipLimit = await limiter.limitByIP(ip, 'login', 5, 300); // 5 attempts per 5 minutes
    
    // Limit by email/username
    const emailLimit = email ? 
      await limiter.limitByUser(email, 'login', 3, 300) : // 3 attempts per 5 minutes
      { allowed: true };
    
    if (!ipLimit.allowed || !emailLimit.allowed) {
      return res.status(429).json({
        error: 'Too Many Login Attempts',
        message: 'Please wait before trying again',
        retryAfter: 300
      });
    }
    
    next();
  };
}

function searchRateLimiter(options = {}) {
  const limiter = new RateLimiter(options);
  
  return async (req, res, next) => {
    const key = req.user?.id ? `user:${req.user.id}` : `ip:${req.ip}`;
    
    // Use token bucket for burst allowance
    const result = await limiter.tokenBucket(
      `search:${key}`,
      0.5, // 0.5 tokens per second (30 per minute)
      10,  // Burst of 10 searches
      1
    );
    
    if (!result.allowed) {
      return res.status(429).json({
        error: 'Search Rate Limit Exceeded',
        message: 'Please slow down your search requests',
        tokensRemaining: result.tokens,
        capacity: result.capacity
      });
    }
    
    res.setHeader('X-Search-Tokens-Remaining', result.tokens);
    next();
  };
}

module.exports = {
  RateLimiter,
  createRateLimiter,
  createStrictRateLimiter,
  createApiRateLimiter,
  loginRateLimiter,
  searchRateLimiter
};