import React, { useState, useEffect, useContext, createContext, ReactNode } from 'react';
import { useAuth } from '../contexts/AuthContext';

// Types
interface ExperimentContext {
  userId: string;
  userAttributes: Record<string, any>;
}

interface VariantAssignment {
  experimentKey: string;
  variantKey: string;
  variantConfig: Record<string, any>;
  isControl: boolean;
}

interface ABTestContextValue {
  experiments: Map<string, VariantAssignment>;
  getVariant: (experimentKey: string) => string | null;
  trackEvent: (experimentKey: string, metricKey: string, value?: number) => Promise<void>;
  isLoading: boolean;
}

interface ABTestProviderProps {
  children: ReactNode;
  serviceUrl?: string;
  context?: Partial<ExperimentContext>;
}

interface ABTestProps {
  experiment: string;
  children: ReactNode;
  fallback?: ReactNode;
  onExposure?: (variant: string) => void;
}

interface VariantProps {
  name: string;
  children: ReactNode;
}

// Context
const ABTestContext = createContext<ABTestContextValue | null>(null);

// Provider Component
export function ABTestProvider({ 
  children, 
  serviceUrl = '/api/ab-testing',
  context: customContext 
}: ABTestProviderProps) {
  const { user } = useAuth();
  const [experiments, setExperiments] = useState<Map<string, VariantAssignment>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [assignmentQueue, setAssignmentQueue] = useState<Set<string>>(new Set());

  // Build experiment context
  const experimentContext: ExperimentContext = {
    userId: user?.id || 'anonymous',
    userAttributes: {
      ...user,
      ...customContext?.userAttributes
    }
  };

  // Get variant for experiment
  const getVariant = (experimentKey: string): string | null => {
    const assignment = experiments.get(experimentKey);
    return assignment?.variantKey || null;
  };

  // Assign variant
  const assignVariant = async (experimentKey: string): Promise<VariantAssignment | null> => {
    try {
      const response = await fetch(`${serviceUrl}/assign/${experimentKey}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(experimentContext),
      });

      if (!response.ok) {
        console.error(`Failed to assign variant for ${experimentKey}`);
        return null;
      }

      const assignment: VariantAssignment = await response.json();
      setExperiments(prev => new Map(prev).set(experimentKey, assignment));
      
      return assignment;
    } catch (error) {
      console.error('Error assigning variant:', error);
      return null;
    }
  };

  // Track event
  const trackEvent = async (
    experimentKey: string, 
    metricKey: string, 
    value: number = 1
  ): Promise<void> => {
    try {
      await fetch(`${serviceUrl}/track/${experimentKey}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: experimentContext.userId,
          metric_key: metricKey,
          value,
          metadata: {
            timestamp: new Date().toISOString(),
            ...experimentContext.userAttributes
          }
        }),
      });
    } catch (error) {
      console.error('Error tracking event:', error);
    }
  };

  // Process assignment queue
  useEffect(() => {
    if (assignmentQueue.size === 0 || isLoading) return;

    const processQueue = async () => {
      setIsLoading(true);
      
      const promises = Array.from(assignmentQueue).map(experimentKey => 
        assignVariant(experimentKey)
      );
      
      await Promise.all(promises);
      setAssignmentQueue(new Set());
      setIsLoading(false);
    };

    processQueue();
  }, [assignmentQueue, isLoading]);

  const value: ABTestContextValue = {
    experiments,
    getVariant,
    trackEvent,
    isLoading
  };

  return (
    <ABTestContext.Provider value={value}>
      {children}
    </ABTestContext.Provider>
  );
}

// Hook
export function useABTest(experimentKey: string): {
  variant: string | null;
  isLoading: boolean;
  trackEvent: (metricKey: string, value?: number) => Promise<void>;
} {
  const context = useContext(ABTestContext);
  
  if (!context) {
    throw new Error('useABTest must be used within ABTestProvider');
  }

  const [variant, setVariant] = useState<string | null>(null);

  useEffect(() => {
    const currentVariant = context.getVariant(experimentKey);
    setVariant(currentVariant);
  }, [experimentKey, context.experiments]);

  const trackEvent = (metricKey: string, value?: number) => 
    context.trackEvent(experimentKey, metricKey, value);

  return {
    variant,
    isLoading: context.isLoading,
    trackEvent
  };
}

// ABTest Component
export function ABTest({ 
  experiment, 
  children, 
  fallback = null,
  onExposure 
}: ABTestProps) {
  const context = useContext(ABTestContext);
  const [variant, setVariant] = useState<string | null>(null);
  const [isAssigning, setIsAssigning] = useState(false);

  if (!context) {
    throw new Error('ABTest must be used within ABTestProvider');
  }

  useEffect(() => {
    const currentVariant = context.getVariant(experiment);
    
    if (currentVariant) {
      setVariant(currentVariant);
      if (onExposure) {
        onExposure(currentVariant);
      }
    } else if (!isAssigning) {
      // Need to assign variant
      setIsAssigning(true);
      assignVariant();
    }
  }, [experiment, context.experiments]);

  const assignVariant = async () => {
    try {
      const response = await fetch(`/api/ab-testing/assign/${experiment}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: 'current-user-id', // Get from auth context
          userAttributes: {} // Get from user context
        }),
      });

      if (response.ok) {
        const assignment: VariantAssignment = await response.json();
        setVariant(assignment.variantKey);
        
        if (onExposure) {
          onExposure(assignment.variantKey);
        }
      }
    } catch (error) {
      console.error('Error assigning variant:', error);
    } finally {
      setIsAssigning(false);
    }
  };

  if (!variant || isAssigning) {
    return <>{fallback}</>;
  }

  // Find matching variant component
  const variantElements = React.Children.toArray(children).filter(
    child => React.isValidElement(child) && child.type === Variant
  );

  const matchingVariant = variantElements.find(
    child => React.isValidElement(child) && child.props.name === variant
  );

  return <>{matchingVariant || fallback}</>;
}

// Variant Component
export function Variant({ children }: VariantProps) {
  return <>{children}</>;
}

// Optimization Hook
export function useOptimization(
  experimentKey: string,
  variants: Record<string, any>,
  defaultValue: any
): any {
  const { variant } = useABTest(experimentKey);
  return variants[variant || ''] || defaultValue;
}

// Track Conversion Hook
export function useTrackConversion(experimentKey: string) {
  const { trackEvent } = useABTest(experimentKey);
  
  return {
    trackConversion: (metricKey: string = 'conversion') => 
      trackEvent(metricKey, 1),
    trackValue: (metricKey: string, value: number) => 
      trackEvent(metricKey, value),
  };
}

// Example Usage Component
export function ExampleABTestUsage() {
  const { trackConversion } = useTrackConversion('homepage-cta-test');

  return (
    <ABTest 
      experiment="homepage-cta-test"
      onExposure={(variant) => console.log('User exposed to variant:', variant)}
    >
      <Variant name="control">
        <button 
          onClick={() => trackConversion()}
          className="btn btn-primary"
        >
          Get Started
        </button>
      </Variant>
      
      <Variant name="variant-a">
        <button 
          onClick={() => trackConversion()}
          className="btn btn-success btn-lg"
        >
          Start Free Trial
        </button>
      </Variant>
      
      <Variant name="variant-b">
        <button 
          onClick={() => trackConversion()}
          className="btn btn-warning btn-lg animate-pulse"
        >
          Try It Free - No Credit Card
        </button>
      </Variant>
    </ABTest>
  );
}

// Hook for optimization values
export function ExampleOptimizationUsage() {
  const heroText = useOptimization('hero-text-test', {
    'control': 'Welcome to OpenPolicy Platform',
    'friendly': 'Your Government Data, Simplified',
    'action': 'Transform Policy Tracking Today',
  }, 'Welcome to OpenPolicy Platform');

  const buttonColor = useOptimization('button-color-test', {
    'control': 'blue',
    'green': 'green',
    'orange': 'orange',
  }, 'blue');

  return (
    <div>
      <h1>{heroText}</h1>
      <button className={`btn btn-${buttonColor}`}>
        Get Started
      </button>
    </div>
  );
}

// Results Dashboard Component
export function ABTestResults({ experimentKey }: { experimentKey: string }) {
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResults();
  }, [experimentKey]);

  const fetchResults = async () => {
    try {
      const response = await fetch(`/api/ab-testing/results/${experimentKey}`);
      if (response.ok) {
        const data = await response.json();
        setResults(data);
      }
    } catch (error) {
      console.error('Error fetching results:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading results...</div>;
  if (!results) return <div>No results available</div>;

  return (
    <div className="ab-test-results">
      <h3>Experiment: {experimentKey}</h3>
      <div className="results-grid">
        {results.variants.map((variant: any) => (
          <div key={variant.variant_key} className="variant-card">
            <h4>{variant.variant_name}</h4>
            {variant.is_control && <span className="badge">Control</span>}
            
            <div className="metrics">
              <div className="metric">
                <span>Visitors:</span>
                <strong>{variant.visitors.toLocaleString()}</strong>
              </div>
              <div className="metric">
                <span>Conversions:</span>
                <strong>{variant.conversions.toLocaleString()}</strong>
              </div>
              <div className="metric">
                <span>Conversion Rate:</span>
                <strong>{(variant.conversion_rate * 100).toFixed(2)}%</strong>
              </div>
              
              {!variant.is_control && (
                <>
                  <div className="metric">
                    <span>Improvement:</span>
                    <strong className={variant.relative_improvement > 0 ? 'positive' : 'negative'}>
                      {variant.relative_improvement > 0 ? '+' : ''}
                      {variant.relative_improvement.toFixed(2)}%
                    </strong>
                  </div>
                  <div className="metric">
                    <span>Statistical Significance:</span>
                    <strong className={variant.is_significant ? 'significant' : ''}>
                      {variant.is_significant ? 'Yes' : 'No'} 
                      (p={variant.p_value.toFixed(3)})
                    </strong>
                  </div>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {results.winner && (
        <div className="winner-announcement">
          🎉 Winner: {results.winner}
        </div>
      )}
    </div>
  );
}