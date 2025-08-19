#!/bin/bash

# Feature Flags Setup Script
# Configures feature flag service and integrations

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Build and deploy feature flag service
deploy_service() {
    log "Deploying feature flag service..."
    
    # Create Dockerfile
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY feature-flag-service.py .

# Expose port
EXPOSE 9024

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9024/health || exit 1

# Run service
CMD ["python", "feature-flag-service.py"]
EOF

    # Create requirements.txt
    cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
redis==5.0.1
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
launchdarkly-server-sdk==8.2.1
pydantic==2.5.0
requests==2.31.0
EOF

    # Build Docker image
    docker build -t openpolicy/feature-flag-service:latest .
    
    log "✅ Feature flag service deployed"
}

# Create Kubernetes deployment
create_k8s_deployment() {
    log "Creating Kubernetes deployment..."
    
    cat > feature-flag-service.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: feature-flag-service
  namespace: default
  labels:
    app: feature-flag-service
    component: business-logic
spec:
  replicas: 3
  selector:
    matchLabels:
      app: feature-flag-service
  template:
    metadata:
      labels:
        app: feature-flag-service
    spec:
      containers:
      - name: feature-flag-service
        image: openpolicy/feature-flag-service:latest
        ports:
        - containerPort: 9024
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: LAUNCHDARKLY_SDK_KEY
          valueFrom:
            secretKeyRef:
              name: feature-flags
              key: launchdarkly-sdk-key
              optional: true
        - name: SERVICE_PORT
          value: "9024"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 9024
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 9024
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: feature-flag-service
  namespace: default
spec:
  selector:
    app: feature-flag-service
  ports:
  - name: http
    port: 9024
    targetPort: 9024
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: feature-flag-service-hpa
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: feature-flag-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF

    kubectl apply -f feature-flag-service.yaml
    
    log "✅ Kubernetes deployment created"
}

# Setup initial feature flags
setup_initial_flags() {
    log "Setting up initial feature flags..."
    
    # Wait for service to be ready
    sleep 10
    
    SERVICE_URL="http://localhost:9024"
    
    # Create feature flags
    flags=(
        '{
            "key": "new_ui",
            "name": "New UI Design",
            "description": "Enable the new responsive UI design",
            "flag_type": "boolean",
            "default_value": false,
            "percentage_rollout": {"true": 10, "false": 90},
            "tags": ["ui", "frontend"]
        }'
        '{
            "key": "dark_mode",
            "name": "Dark Mode",
            "description": "Enable dark mode theme",
            "flag_type": "boolean",
            "default_value": true,
            "targeting_rules": [
                {
                    "attribute": "user_role",
                    "operator": "in",
                    "values": ["admin", "premium"],
                    "serve": true
                }
            ],
            "tags": ["ui", "theme"]
        }'
        '{
            "key": "api_rate_limit",
            "name": "API Rate Limit",
            "description": "Requests per hour for API",
            "flag_type": "number",
            "default_value": 1000,
            "variations": [100, 1000, 5000, 10000],
            "targeting_rules": [
                {
                    "attribute": "custom_attributes.plan",
                    "operator": "eq",
                    "values": ["free"],
                    "serve": 100
                },
                {
                    "attribute": "custom_attributes.plan",
                    "operator": "eq",
                    "values": ["premium"],
                    "serve": 5000
                },
                {
                    "attribute": "custom_attributes.plan",
                    "operator": "eq",
                    "values": ["enterprise"],
                    "serve": 10000
                }
            ],
            "tags": ["api", "limits"]
        }'
        '{
            "key": "maintenance_mode",
            "name": "Maintenance Mode",
            "description": "Enable maintenance mode",
            "flag_type": "boolean",
            "default_value": false,
            "tags": ["operations", "critical"]
        }'
        '{
            "key": "search_algorithm",
            "name": "Search Algorithm",
            "description": "Which search algorithm to use",
            "flag_type": "string",
            "default_value": "elasticsearch",
            "variations": ["elasticsearch", "algolia", "postgres_fts"],
            "percentage_rollout": {
                "elasticsearch": 70,
                "algolia": 20,
                "postgres_fts": 10
            },
            "tags": ["search", "backend"]
        }'
        '{
            "key": "enable_analytics",
            "name": "Enable Analytics",
            "description": "Enable detailed analytics tracking",
            "flag_type": "boolean",
            "default_value": true,
            "targeting_rules": [
                {
                    "attribute": "environment",
                    "operator": "eq",
                    "values": ["development"],
                    "serve": false
                }
            ],
            "tags": ["analytics", "privacy"]
        }'
        '{
            "key": "max_upload_size_mb",
            "name": "Maximum Upload Size",
            "description": "Maximum file upload size in MB",
            "flag_type": "number",
            "default_value": 10,
            "targeting_rules": [
                {
                    "attribute": "user_role",
                    "operator": "eq",
                    "values": ["admin"],
                    "serve": 100
                },
                {
                    "attribute": "custom_attributes.plan",
                    "operator": "eq",
                    "values": ["enterprise"],
                    "serve": 50
                }
            ],
            "tags": ["files", "limits"]
        }'
    )
    
    for flag in "${flags[@]}"; do
        curl -X POST "$SERVICE_URL/flags" \
            -H "Content-Type: application/json" \
            -d "$flag" || true
    done
    
    log "✅ Initial feature flags created"
}

# Create SDK packages
create_sdk_packages() {
    log "Creating SDK packages..."
    
    # Python package
    cd sdk/python
    cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name="openpolicy-feature-flags",
    version="1.0.0",
    description="Feature flag SDK for OpenPolicy Platform",
    author="OpenPolicy Team",
    author_email="dev@openpolicy.com",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    python_requires=">=3.7",
)
EOF

    cat > README.md << 'EOF'
# OpenPolicy Feature Flags Python SDK

## Installation

```bash
pip install openpolicy-feature-flags
```

## Usage

```python
from feature_flags import FeatureFlagClient, FlagContext

# Initialize client
client = FeatureFlagClient(
    service_url="http://feature-flags:9024",
    api_key="your-api-key"
)

# Create context
context = FlagContext(
    user_id="user-123",
    user_role="admin",
    custom_attributes={"plan": "premium"}
)

# Evaluate flag
if client.evaluate("new_ui", context, default_value=False):
    # Show new UI
    pass
```
EOF
    cd ../..
    
    # JavaScript/TypeScript package
    cd sdk/javascript
    cat > package.json << 'EOF'
{
  "name": "@openpolicy/feature-flags",
  "version": "1.0.0",
  "description": "Feature flag SDK for OpenPolicy Platform",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "prepublish": "npm run build"
  },
  "keywords": ["feature-flags", "openpolicy"],
  "author": "OpenPolicy Team",
  "license": "MIT",
  "dependencies": {
    "react": "^18.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.0.0",
    "typescript": "^5.0.0",
    "jest": "^29.0.0"
  }
}
EOF

    cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020", "DOM"],
    "declaration": true,
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "jsx": "react"
  },
  "include": ["*.ts", "*.tsx"],
  "exclude": ["node_modules", "dist"]
}
EOF
    cd ../..
    
    log "✅ SDK packages created"
}

# Generate documentation
generate_documentation() {
    log "Generating documentation..."
    
    cat > FEATURE_FLAGS_GUIDE.md << 'EOF'
# Feature Flags Guide

## Overview

The OpenPolicy Platform uses feature flags to:
- Control feature rollouts
- A/B test new features
- Enable quick rollbacks
- Target specific user segments
- Manage operational switches

## Architecture

### Components

1. **Feature Flag Service** (Port 9024)
   - REST API for flag management
   - Local evaluation engine
   - LaunchDarkly integration
   - Redis caching
   - PostgreSQL storage

2. **SDKs**
   - Python SDK
   - JavaScript/TypeScript SDK
   - React hooks and components

3. **Integrations**
   - LaunchDarkly (optional)
   - Monitoring (Prometheus)
   - Logging (ELK)

## Usage

### Basic Flag Evaluation

```python
# Python
from feature_flags import evaluate, FlagContext

context = FlagContext(user_id="123", user_role="admin")
if evaluate("new_feature", context):
    # Feature is enabled
    pass
```

```typescript
// TypeScript
import { evaluate, FlagContext } from '@openpolicy/feature-flags';

const context: FlagContext = {
  userId: "123",
  userRole: "admin"
};

if (await evaluate("new_feature", context)) {
  // Feature is enabled
}
```

### React Integration

```tsx
import { FeatureFlagProvider, useFeatureFlag } from '@openpolicy/feature-flags';

// Wrap your app
function App() {
  return (
    <FeatureFlagProvider client={client} context={context}>
      <YourApp />
    </FeatureFlagProvider>
  );
}

// Use in components
function MyComponent() {
  const darkMode = useFeatureFlag('dark_mode', false);
  
  return (
    <div className={darkMode ? 'dark' : 'light'}>
      {/* Component content */}
    </div>
  );
}
```

## Flag Types

### Boolean Flags
- Simple on/off switches
- Most common type
- Example: `maintenance_mode`

### String Flags
- Multiple string values
- Good for algorithm selection
- Example: `search_algorithm`

### Number Flags
- Numeric configuration values
- Useful for limits and thresholds
- Example: `api_rate_limit`

### JSON Flags
- Complex configuration objects
- Flexible but use sparingly
- Example: `feature_config`

## Targeting

### User Targeting
```json
{
  "targeting_rules": [{
    "attribute": "user_id",
    "operator": "in",
    "values": ["user-123", "user-456"],
    "serve": true
  }]
}
```

### Role-Based Targeting
```json
{
  "targeting_rules": [{
    "attribute": "user_role",
    "operator": "eq",
    "values": ["admin"],
    "serve": true
  }]
}
```

### Custom Attributes
```json
{
  "targeting_rules": [{
    "attribute": "custom_attributes.plan",
    "operator": "in",
    "values": ["premium", "enterprise"],
    "serve": true
  }]
}
```

### Percentage Rollout
```json
{
  "percentage_rollout": {
    "true": 25,
    "false": 75
  }
}
```

## Best Practices

### 1. Flag Naming
- Use descriptive names: `enable_new_search_ui`
- Group related flags: `ui_dark_mode`, `ui_new_layout`
- Avoid generic names: ~~`flag1`~~, ~~`test`~~

### 2. Flag Lifecycle
1. **Create**: Define flag with safe default
2. **Test**: Verify in development
3. **Roll out**: Gradual percentage increase
4. **Monitor**: Watch metrics and errors
5. **Clean up**: Remove flag code when 100%

### 3. Context Design
- Include essential attributes only
- Keep context consistent across services
- Don't include sensitive data

### 4. Performance
- Use caching (enabled by default)
- Batch evaluations when possible
- Set appropriate cache TTLs

### 5. Safety
- Always provide default values
- Handle service failures gracefully
- Monitor flag evaluation metrics

## Operations

### Creating Flags

```bash
curl -X POST http://feature-flags:9024/flags \
  -H "Content-Type: application/json" \
  -d '{
    "key": "new_feature",
    "name": "New Feature",
    "flag_type": "boolean",
    "default_value": false
  }'
```

### Updating Flags

```bash
curl -X PUT http://feature-flags:9024/flags/new_feature \
  -H "Content-Type: application/json" \
  -d '{
    "percentage_rollout": {"true": 50, "false": 50}
  }'
```

### Emergency Kill Switch

```bash
# Disable feature immediately
curl -X PUT http://feature-flags:9024/flags/feature_name \
  -H "Content-Type: application/json" \
  -d '{"default_value": false, "targeting_rules": []}'
```

## Monitoring

### Metrics Available
- Flag evaluation count
- Cache hit rate
- Evaluation latency
- Error rate

### Grafana Dashboard
- Import `feature-flags-dashboard.json`
- Monitor rollout progress
- Track performance impact

### Alerts
- High error rate
- Service unavailable
- Cache failures

## Troubleshooting

### Flag Not Working
1. Check flag status (active/inactive)
2. Verify context attributes
3. Review targeting rules
4. Check cache state

### Performance Issues
1. Enable caching
2. Batch evaluations
3. Reduce context size
4. Use local defaults

### Service Errors
1. Check service health
2. Verify database connection
3. Check Redis availability
4. Review service logs

## Advanced Usage

### Custom Evaluation Logic

```python
class CustomEvaluator:
    def evaluate(self, flag, context):
        # Custom business logic
        if context.user_id in self.beta_users:
            return True
        return flag.default_value
```

### Event Tracking

```typescript
client.on('evaluation', (flag, value, context) => {
  analytics.track('Feature Flag Evaluated', {
    flag: flag.key,
    value: value,
    userId: context.userId
  });
});
```

### Multi-Environment Setup

```python
# Development
dev_client = FeatureFlagClient(
    service_url="http://dev-flags:9024"
)

# Production
prod_client = FeatureFlagClient(
    service_url="http://prod-flags:9024"
)
```

## Security

### API Authentication
- Use API keys for service-to-service
- Validate contexts server-side
- Don't expose internal flags

### Data Privacy
- Don't log sensitive context data
- Anonymize user IDs if needed
- Follow GDPR guidelines

## Migration Guide

### From LaunchDarkly
1. Export flags from LaunchDarkly
2. Import to local service
3. Update SDK initialization
4. Test thoroughly

### To LaunchDarkly
1. Set `LAUNCHDARKLY_SDK_KEY`
2. Flags automatically sync
3. Local flags act as fallback
EOF

    log "✅ Documentation generated"
}

# Create monitoring dashboard
create_monitoring_dashboard() {
    log "Creating monitoring dashboard..."
    
    cat > feature-flags-dashboard.json << 'EOF'
{
  "dashboard": {
    "title": "Feature Flags Dashboard",
    "panels": [
      {
        "title": "Flag Evaluations per Minute",
        "targets": [{
          "expr": "sum(rate(feature_flag_evaluations_total[1m])) by (flag)"
        }]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [{
          "expr": "rate(feature_flag_cache_hits_total[5m]) / (rate(feature_flag_cache_hits_total[5m]) + rate(feature_flag_cache_misses_total[5m]))"
        }]
      },
      {
        "title": "Evaluation Latency",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(feature_flag_evaluation_duration_seconds_bucket[5m]))"
        }]
      },
      {
        "title": "Active Flags",
        "targets": [{
          "expr": "feature_flags_active_total"
        }]
      }
    ]
  }
}
EOF

    log "✅ Monitoring dashboard created"
}

# Main execution
main() {
    log "Starting feature flags setup..."
    
    # Deploy service
    deploy_service
    create_k8s_deployment
    
    # Setup flags
    setup_initial_flags
    
    # Create packages
    create_sdk_packages
    
    # Documentation
    generate_documentation
    create_monitoring_dashboard
    
    log "✅ Feature flags setup complete!"
    log ""
    log "Service URL: http://feature-flags:9024"
    log "Documentation: FEATURE_FLAGS_GUIDE.md"
    log ""
    log "Next steps:"
    log "1. Install SDK: pip install ./sdk/python"
    log "2. Configure LaunchDarkly (optional)"
    log "3. Import monitoring dashboard"
    log "4. Start using feature flags!"
}

# Run main function
main "$@"