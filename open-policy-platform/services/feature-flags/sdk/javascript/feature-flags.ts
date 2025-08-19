/**
 * TypeScript SDK for OpenPolicy Platform Feature Flags
 */

export interface FlagContext {
  userId?: string;
  userEmail?: string;
  userRole?: string;
  organizationId?: string;
  environment?: string;
  ipAddress?: string;
  userAgent?: string;
  customAttributes?: Record<string, any>;
}

export interface FlagEvaluation {
  key: string;
  value: any;
  variationIndex?: number;
  reason: string;
  source: 'local' | 'launchdarkly';
}

export interface FeatureFlagClientConfig {
  serviceUrl?: string;
  apiKey?: string;
  defaultTimeout?: number;
  enableCache?: boolean;
  cacheTTL?: number;
  fallbackValues?: Record<string, any>;
  enableLogging?: boolean;
}

class Cache {
  private cache: Map<string, { value: any; timestamp: number }> = new Map();
  private ttl: number;

  constructor(ttl: number = 300000) { // 5 minutes default
    this.ttl = ttl;
  }

  set(key: string, value: any): void {
    this.cache.set(key, {
      value,
      timestamp: Date.now()
    });
  }

  get(key: string): any | undefined {
    const item = this.cache.get(key);
    if (!item) return undefined;

    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return undefined;
    }

    return item.value;
  }

  clear(): void {
    this.cache.clear();
  }
}

export class FeatureFlagClient {
  private serviceUrl: string;
  private apiKey?: string;
  private timeout: number;
  private enableCache: boolean;
  private cache: Cache;
  private fallbackValues: Record<string, any>;
  private enableLogging: boolean;

  constructor(config: FeatureFlagClientConfig = {}) {
    this.serviceUrl = config.serviceUrl || process.env.FEATURE_FLAG_SERVICE_URL || 'http://localhost:9024';
    this.apiKey = config.apiKey || process.env.FEATURE_FLAG_API_KEY;
    this.timeout = config.defaultTimeout || 5000;
    this.enableCache = config.enableCache !== false;
    this.cache = new Cache(config.cacheTTL);
    this.fallbackValues = config.fallbackValues || {};
    this.enableLogging = config.enableLogging || false;
  }

  private log(message: string, data?: any): void {
    if (this.enableLogging) {
      console.log(`[FeatureFlags] ${message}`, data || '');
    }
  }

  private generateCacheKey(flagKey: string, context: FlagContext): string {
    const contextStr = JSON.stringify(context, Object.keys(context).sort());
    return `${flagKey}:${this.hashCode(contextStr)}`;
  }

  private hashCode(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return hash;
  }

  private async makeRequest<T>(
    method: string,
    endpoint: string,
    data?: any
  ): Promise<T | null> {
    const url = `${this.serviceUrl}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      this.log('Request failed', { endpoint, error });
      return null;
    }
  }

  async evaluate(
    flagKey: string,
    context: FlagContext,
    defaultValue?: any
  ): Promise<any> {
    // Check cache first
    if (this.enableCache) {
      const cacheKey = this.generateCacheKey(flagKey, context);
      const cachedValue = this.cache.get(cacheKey);
      if (cachedValue !== undefined) {
        this.log('Cache hit', { flagKey, value: cachedValue });
        return cachedValue;
      }
    }

    // Make request
    const response = await this.makeRequest<FlagEvaluation>(
      'POST',
      `/evaluate/${flagKey}`,
      context
    );

    if (response) {
      const value = response.value;
      
      // Cache the result
      if (this.enableCache) {
        const cacheKey = this.generateCacheKey(flagKey, context);
        this.cache.set(cacheKey, value);
      }

      this.log('Evaluated flag', { flagKey, value });
      return value;
    }

    // Fall back to configured fallback or provided default
    const fallbackValue = this.fallbackValues[flagKey] ?? defaultValue;
    this.log('Using fallback value', { flagKey, value: fallbackValue });
    return fallbackValue;
  }

  async evaluateBatch(
    flagKeys: string[],
    context: FlagContext,
    defaultValues?: Record<string, any>
  ): Promise<Record<string, any>> {
    const results: Record<string, any> = {};
    const uncachedKeys: string[] = [];

    // Check cache for all flags
    if (this.enableCache) {
      for (const flagKey of flagKeys) {
        const cacheKey = this.generateCacheKey(flagKey, context);
        const cachedValue = this.cache.get(cacheKey);
        if (cachedValue !== undefined) {
          results[flagKey] = cachedValue;
        } else {
          uncachedKeys.push(flagKey);
        }
      }
    } else {
      uncachedKeys.push(...flagKeys);
    }

    // Fetch uncached flags
    if (uncachedKeys.length > 0) {
      const response = await this.makeRequest<{ evaluations: Record<string, FlagEvaluation> }>(
        'POST',
        '/evaluate/batch',
        {
          flag_keys: uncachedKeys,
          context
        }
      );

      if (response?.evaluations) {
        for (const [flagKey, evaluation] of Object.entries(response.evaluations)) {
          const value = evaluation.value;
          results[flagKey] = value;

          // Cache the result
          if (this.enableCache && value !== null) {
            const cacheKey = this.generateCacheKey(flagKey, context);
            this.cache.set(cacheKey, value);
          }
        }
      }
    }

    // Apply defaults for missing flags
    for (const flagKey of flagKeys) {
      if (!(flagKey in results)) {
        results[flagKey] = defaultValues?.[flagKey] ?? this.fallbackValues[flagKey];
      }
    }

    this.log('Batch evaluation complete', { flagKeys, results });
    return results;
  }

  async getAllFlags(): Promise<any[] | null> {
    const response = await this.makeRequest<{ flags: any[] }>('GET', '/flags');
    return response?.flags || null;
  }

  clearCache(): void {
    this.cache.clear();
    this.log('Cache cleared');
  }
}

// React hooks
import { useState, useEffect, useContext, createContext, ReactNode } from 'react';

interface FeatureFlagProviderProps {
  client: FeatureFlagClient;
  context: FlagContext;
  children: ReactNode;
}

interface FeatureFlagContextValue {
  client: FeatureFlagClient;
  context: FlagContext;
  flags: Record<string, any>;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

const FeatureFlagContext = createContext<FeatureFlagContextValue | null>(null);

export function FeatureFlagProvider({
  client,
  context,
  children
}: FeatureFlagProviderProps) {
  const [flags, setFlags] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchFlags = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get all flags first
      const allFlags = await client.getAllFlags();
      if (allFlags) {
        const flagKeys = allFlags.map(f => f.key);
        const evaluations = await client.evaluateBatch(flagKeys, context);
        setFlags(evaluations);
      }
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFlags();
  }, [context.userId, context.organizationId]); // Re-fetch when key context changes

  const value: FeatureFlagContextValue = {
    client,
    context,
    flags,
    loading,
    error,
    refetch: fetchFlags
  };

  return (
    <FeatureFlagContext.Provider value={value}>
      {children}
    </FeatureFlagContext.Provider>
  );
}

export function useFeatureFlag(flagKey: string, defaultValue?: any): any {
  const context = useContext(FeatureFlagContext);
  
  if (!context) {
    throw new Error('useFeatureFlag must be used within a FeatureFlagProvider');
  }

  const [value, setValue] = useState(context.flags[flagKey] ?? defaultValue);

  useEffect(() => {
    // If flag is not in the pre-fetched flags, fetch it individually
    if (!(flagKey in context.flags) && !context.loading) {
      context.client.evaluate(flagKey, context.context, defaultValue)
        .then(setValue);
    } else {
      setValue(context.flags[flagKey] ?? defaultValue);
    }
  }, [flagKey, context.flags, context.loading]);

  return value;
}

export function useFeatureFlags(flagKeys: string[], defaultValues?: Record<string, any>): Record<string, any> {
  const context = useContext(FeatureFlagContext);
  
  if (!context) {
    throw new Error('useFeatureFlags must be used within a FeatureFlagProvider');
  }

  const [values, setValues] = useState<Record<string, any>>({});

  useEffect(() => {
    const missingKeys = flagKeys.filter(key => !(key in context.flags));
    
    if (missingKeys.length > 0 && !context.loading) {
      context.client.evaluateBatch(missingKeys, context.context, defaultValues)
        .then(newValues => {
          setValues(prev => ({ ...prev, ...newValues }));
        });
    }

    // Set values for flags we already have
    const currentValues: Record<string, any> = {};
    for (const key of flagKeys) {
      currentValues[key] = context.flags[key] ?? defaultValues?.[key];
    }
    setValues(currentValues);
  }, [flagKeys.join(','), context.flags, context.loading]);

  return values;
}

// HOC for feature flags
export function withFeatureFlag<P extends object>(
  flagKey: string,
  defaultValue: boolean = false
) {
  return function (Component: React.ComponentType<P>) {
    return function WithFeatureFlagComponent(props: P) {
      const enabled = useFeatureFlag(flagKey, defaultValue);
      
      if (!enabled) {
        return null;
      }

      return <Component {...props} />;
    };
  };
}

// Default client instance
let defaultClient: FeatureFlagClient | null = null;

export function initFeatureFlags(config: FeatureFlagClientConfig): FeatureFlagClient {
  defaultClient = new FeatureFlagClient(config);
  return defaultClient;
}

export function getDefaultClient(): FeatureFlagClient {
  if (!defaultClient) {
    defaultClient = new FeatureFlagClient();
  }
  return defaultClient;
}