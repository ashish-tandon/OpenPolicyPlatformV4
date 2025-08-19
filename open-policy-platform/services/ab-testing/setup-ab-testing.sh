#!/bin/bash

# A/B Testing Setup Script
# Configures A/B testing service and creates initial experiments

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Deploy A/B testing service
deploy_service() {
    log "Deploying A/B testing service..."
    
    # Create Dockerfile
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ab-testing-service.py .

# Expose port
EXPOSE 9025

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9025/health || exit 1

# Run service
CMD ["python", "ab-testing-service.py"]
EOF

    # Create requirements.txt
    cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
redis==5.0.1
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
numpy==1.26.2
scipy==1.11.4
statsmodels==0.14.0
pydantic==2.5.0
EOF

    # Build Docker image
    docker build -t openpolicy/ab-testing-service:latest .
    
    # Create Kubernetes deployment
    cat > ab-testing-service.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ab-testing-service
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ab-testing-service
  template:
    metadata:
      labels:
        app: ab-testing-service
    spec:
      containers:
      - name: ab-testing-service
        image: openpolicy/ab-testing-service:latest
        ports:
        - containerPort: 9025
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: FEATURE_FLAG_SERVICE
          value: "http://feature-flag-service:9024"
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: ab-testing-service
spec:
  selector:
    app: ab-testing-service
  ports:
  - port: 9025
    targetPort: 9025
EOF

    kubectl apply -f ab-testing-service.yaml
    
    log "✅ A/B testing service deployed"
}

# Create initial experiments
create_experiments() {
    log "Creating initial experiments..."
    
    SERVICE_URL="http://localhost:9025"
    
    # Homepage CTA Test
    curl -X POST "$SERVICE_URL/experiments" \
        -H "Content-Type: application/json" \
        -d '{
            "key": "homepage-cta-test",
            "name": "Homepage CTA Button Test",
            "description": "Test different CTA button texts and styles",
            "hypothesis": "More specific and urgent CTA text will increase click-through rate",
            "experiment_type": "ab",
            "audience_percentage": 50,
            "start_date": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
            "min_sample_size": 1000,
            "variants": [
                {
                    "key": "control",
                    "name": "Control - Get Started",
                    "allocation_percentage": 33.33,
                    "is_control": true,
                    "config": {
                        "button_text": "Get Started",
                        "button_class": "btn-primary"
                    }
                },
                {
                    "key": "variant-a",
                    "name": "Variant A - Start Free Trial",
                    "allocation_percentage": 33.33,
                    "config": {
                        "button_text": "Start Free Trial",
                        "button_class": "btn-success btn-lg"
                    }
                },
                {
                    "key": "variant-b",
                    "name": "Variant B - Try It Free",
                    "allocation_percentage": 33.34,
                    "config": {
                        "button_text": "Try It Free - No Credit Card",
                        "button_class": "btn-warning btn-lg animate-pulse"
                    }
                }
            ],
            "metrics": [
                {
                    "key": "cta_click",
                    "name": "CTA Click Rate",
                    "metric_type": "conversion",
                    "is_primary": true,
                    "minimum_detectable_effect": 0.02
                },
                {
                    "key": "signup_complete",
                    "name": "Signup Completion Rate",
                    "metric_type": "conversion"
                }
            ],
            "tags": ["homepage", "cta", "conversion"]
        }'

    # Search Algorithm Test
    curl -X POST "$SERVICE_URL/experiments" \
        -H "Content-Type: application/json" \
        -d '{
            "key": "search-algorithm-test",
            "name": "Search Algorithm Performance Test",
            "description": "Compare different search algorithms for relevance and speed",
            "hypothesis": "Elasticsearch will provide better relevance with acceptable latency",
            "experiment_type": "multivariate",
            "audience_percentage": 100,
            "audience_criteria": [
                {
                    "attribute": "user_role",
                    "operator": "not_equals",
                    "value": "admin"
                }
            ],
            "variants": [
                {
                    "key": "postgres-fts",
                    "name": "PostgreSQL Full Text Search",
                    "allocation_percentage": 20,
                    "is_control": true,
                    "feature_flags": {
                        "search_backend": "postgres"
                    }
                },
                {
                    "key": "elasticsearch",
                    "name": "Elasticsearch",
                    "allocation_percentage": 60,
                    "feature_flags": {
                        "search_backend": "elasticsearch"
                    }
                },
                {
                    "key": "algolia",
                    "name": "Algolia Search",
                    "allocation_percentage": 20,
                    "feature_flags": {
                        "search_backend": "algolia"
                    }
                }
            ],
            "metrics": [
                {
                    "key": "search_success_rate",
                    "name": "Search Success Rate",
                    "description": "Users who clicked on a search result",
                    "metric_type": "conversion",
                    "is_primary": true,
                    "minimum_detectable_effect": 0.05
                },
                {
                    "key": "search_latency",
                    "name": "Search Latency",
                    "metric_type": "continuous",
                    "improvement_direction": "decrease"
                },
                {
                    "key": "results_clicked",
                    "name": "Results Clicked Per Search",
                    "metric_type": "count"
                }
            ],
            "tags": ["search", "backend", "performance"]
        }'

    # Dark Mode Test
    curl -X POST "$SERVICE_URL/experiments" \
        -H "Content-Type: application/json" \
        -d '{
            "key": "dark-mode-adoption",
            "name": "Dark Mode Default Setting Test",
            "description": "Test if defaulting to dark mode increases user satisfaction",
            "hypothesis": "Users prefer dark mode by default, leading to longer sessions",
            "experiment_type": "ab",
            "audience_percentage": 30,
            "audience_criteria": [
                {
                    "attribute": "custom_attributes.device_type",
                    "operator": "equals",
                    "value": "desktop"
                }
            ],
            "variants": [
                {
                    "key": "light-default",
                    "name": "Light Mode Default",
                    "allocation_percentage": 50,
                    "is_control": true,
                    "feature_flags": {
                        "default_theme": "light"
                    }
                },
                {
                    "key": "dark-default",
                    "name": "Dark Mode Default",
                    "allocation_percentage": 50,
                    "feature_flags": {
                        "default_theme": "dark"
                    }
                }
            ],
            "metrics": [
                {
                    "key": "session_duration",
                    "name": "Average Session Duration",
                    "metric_type": "duration",
                    "is_primary": true,
                    "improvement_direction": "increase"
                },
                {
                    "key": "theme_switch",
                    "name": "Theme Switch Rate",
                    "description": "Users who changed from default theme",
                    "metric_type": "conversion",
                    "improvement_direction": "decrease"
                }
            ],
            "tags": ["ui", "theme", "user-preference"]
        }'

    log "✅ Initial experiments created"
}

# Create monitoring dashboard
create_dashboard() {
    log "Creating A/B testing dashboard..."
    
    cat > ab-testing-dashboard.json << 'EOF'
{
  "dashboard": {
    "title": "A/B Testing Dashboard",
    "panels": [
      {
        "title": "Active Experiments",
        "type": "stat",
        "targets": [{
          "expr": "count(ab_experiment_status{status=\"running\"})"
        }]
      },
      {
        "title": "Total Users in Experiments",
        "type": "gauge",
        "targets": [{
          "expr": "sum(ab_experiment_users_total)"
        }]
      },
      {
        "title": "Conversion Rates by Experiment",
        "type": "graph",
        "targets": [{
          "expr": "ab_experiment_conversion_rate"
        }]
      },
      {
        "title": "Statistical Significance",
        "type": "table",
        "targets": [{
          "expr": "ab_experiment_p_value < 0.05"
        }]
      }
    ]
  }
}
EOF

    log "✅ Dashboard created"
}

# Generate documentation
generate_docs() {
    log "Generating A/B testing documentation..."
    
    cat > AB_TESTING_GUIDE.md << 'EOF'
# A/B Testing Guide

## Overview

The OpenPolicy Platform A/B testing system enables data-driven decision making through controlled experiments.

## Quick Start

### 1. Create an Experiment

```javascript
const experiment = {
  key: "new-feature-test",
  name: "New Feature Rollout Test",
  variants: [
    {
      key: "control",
      name: "Current Version",
      allocation_percentage: 50,
      is_control: true
    },
    {
      key: "new-feature",
      name: "With New Feature",
      allocation_percentage: 50,
      feature_flags: {
        "enable_new_feature": true
      }
    }
  ],
  metrics: [
    {
      key: "feature_adoption",
      name: "Feature Adoption Rate",
      metric_type: "conversion",
      is_primary: true
    }
  ]
};
```

### 2. Implement in React

```jsx
import { ABTest, Variant, useTrackConversion } from '@/components/ABTest';

function MyComponent() {
  const { trackConversion } = useTrackConversion('new-feature-test');

  return (
    <ABTest experiment="new-feature-test">
      <Variant name="control">
        <OldFeature />
      </Variant>
      <Variant name="new-feature">
        <NewFeature onUse={() => trackConversion('feature_adoption')} />
      </Variant>
    </ABTest>
  );
}
```

### 3. Track Events

```javascript
// Track conversion
trackEvent('experiment-key', 'conversion', 1);

// Track revenue
trackEvent('experiment-key', 'revenue', 29.99);

// Track custom metric
trackEvent('experiment-key', 'time_on_page', 145.3);
```

## Experiment Types

### Simple A/B Test
- Two variants (control + treatment)
- Single change tested
- Clear hypothesis

### Multivariate Test
- Multiple variants
- Test combinations
- Requires larger sample size

### Split URL Test
- Different page versions
- Major layout changes
- Full page experiments

### Feature Flag Test
- Gradual rollout
- Easy rollback
- Integration with feature flags

## Statistical Methodology

### Sample Size Calculation

```python
from statsmodels.stats.power import NormalIndPower

def calculate_sample_size(baseline_rate, mde, alpha=0.05, power=0.8):
    """
    baseline_rate: Current conversion rate (e.g., 0.10 for 10%)
    mde: Minimum detectable effect (e.g., 0.02 for 2% absolute)
    alpha: Significance level (Type I error rate)
    power: Statistical power (1 - Type II error rate)
    """
    effect_size = mde / baseline_rate
    sample_size = NormalIndPower().solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power
    )
    return int(sample_size)
```

### Statistical Tests

#### Conversion Rate (Binary)
- **Test**: Two-proportion Z-test
- **Assumptions**: Independent observations, sufficient sample size
- **Metrics**: Conversion rate, click-through rate

#### Continuous Metrics
- **Test**: Welch's t-test
- **Assumptions**: Independent observations, approximately normal
- **Metrics**: Revenue, time on page, engagement score

#### Count Data
- **Test**: Poisson regression or negative binomial
- **Assumptions**: Count data, overdispersion check
- **Metrics**: Page views, actions per session

### Significance & Power

- **Significance Level (α)**: 0.05 (5% false positive rate)
- **Power (1-β)**: 0.80 (80% true positive rate)
- **Confidence Intervals**: 95% by default

## Best Practices

### 1. Experiment Design
- **Clear Hypothesis**: State what you expect and why
- **Single Variable**: Change one thing at a time
- **Sufficient Traffic**: Ensure statistical power
- **Random Assignment**: True randomization

### 2. Duration
- **Minimum**: 1 full business cycle (usually 1 week)
- **Maximum**: 4 weeks to avoid seasonality
- **Early Stopping**: Avoid peeking, use sequential testing

### 3. Segmentation
- **User Types**: New vs returning
- **Device**: Mobile vs desktop
- **Geography**: Regional differences
- **Behavior**: Power users vs casual

### 4. Metrics Selection
- **Primary Metric**: One main success metric
- **Secondary Metrics**: Supporting evidence
- **Guardrail Metrics**: Ensure no harm
- **Leading Indicators**: Early signals

## Common Pitfalls

### 1. Peeking Problem
**Issue**: Checking results too early
**Solution**: Pre-commit to duration, use sequential testing

### 2. Multiple Comparisons
**Issue**: Testing many metrics increases false positives
**Solution**: Bonferroni correction, focus on primary metric

### 3. Sample Ratio Mismatch
**Issue**: Uneven split indicates randomization problem
**Solution**: Monitor allocation, investigate technical issues

### 4. Novelty Effect
**Issue**: Users react to change itself
**Solution**: Run experiment longer, segment by user tenure

## Analysis & Interpretation

### Reading Results

```json
{
  "experiment": "homepage-cta-test",
  "status": "completed",
  "duration_days": 14,
  "variants": [
    {
      "name": "control",
      "visitors": 10000,
      "conversions": 200,
      "conversion_rate": 0.02,
      "confidence_interval": [0.017, 0.023]
    },
    {
      "name": "variant-a",
      "visitors": 10050,
      "conversions": 250,
      "conversion_rate": 0.0249,
      "confidence_interval": [0.022, 0.028],
      "relative_improvement": 24.5,
      "p_value": 0.023,
      "is_significant": true
    }
  ]
}
```

### Decision Framework

1. **Statistical Significance**: p < 0.05?
2. **Practical Significance**: Effect size meaningful?
3. **Confidence Intervals**: Range acceptable?
4. **Secondary Metrics**: Any negative impacts?
5. **Segments**: Consistent across groups?

## Integration

### With Feature Flags

```javascript
// Experiment determines feature flag value
const showNewUI = useOptimization('ui-redesign-test', {
  'control': false,
  'gradual': true,
  'full': true
}, false);
```

### With Analytics

```javascript
// Track experiment exposure
analytics.track('Experiment Viewed', {
  experiment_id: 'homepage-cta-test',
  variant: 'variant-a',
  user_id: user.id
});
```

### With Monitoring

```javascript
// Monitor experiment health
prometheus.gauge('ab_test_allocation_ratio', {
  experiment: 'homepage-cta-test',
  variant: 'control'
}, 0.333);
```

## Tools & Dashboards

### Experiment Dashboard
- Real-time metrics
- Statistical significance
- Segment analysis
- Historical results

### Power Calculator
- Sample size estimation
- Duration calculator
- MDE visualization

### Results Export
- CSV/Excel export
- Statistical summary
- Detailed segments
- Raw data access

## API Reference

### Create Experiment
```bash
POST /api/ab-testing/experiments
{
  "key": "experiment-key",
  "name": "Experiment Name",
  "variants": [...],
  "metrics": [...]
}
```

### Assign Variant
```bash
POST /api/ab-testing/assign/{experiment_key}
{
  "userId": "user-123",
  "userAttributes": {...}
}
```

### Track Event
```bash
POST /api/ab-testing/track/{experiment_key}
{
  "user_id": "user-123",
  "metric_key": "conversion",
  "value": 1
}
```

### Get Results
```bash
GET /api/ab-testing/results/{experiment_key}
```

## Troubleshooting

### No Statistical Significance
1. Check sample size
2. Verify metric tracking
3. Consider larger effect size
4. Extend duration

### Unexpected Results
1. Check implementation
2. Verify randomization
3. Look for bugs
4. Consider external factors

### Performance Issues
1. Use caching
2. Batch assignments
3. Optimize queries
4. Archive old experiments
EOF

    log "✅ Documentation generated"
}

# Main execution
main() {
    log "Starting A/B testing setup..."
    
    # Deploy service
    deploy_service
    
    # Create experiments
    create_experiments
    
    # Setup monitoring
    create_dashboard
    
    # Generate docs
    generate_docs
    
    log "✅ A/B testing setup complete!"
    log ""
    log "Service URL: http://ab-testing:9025"
    log "Documentation: AB_TESTING_GUIDE.md"
    log ""
    log "Active experiments:"
    log "  - homepage-cta-test (50% traffic)"
    log "  - search-algorithm-test (100% traffic)"
    log "  - dark-mode-adoption (30% traffic)"
}

# Run main function
main "$@"