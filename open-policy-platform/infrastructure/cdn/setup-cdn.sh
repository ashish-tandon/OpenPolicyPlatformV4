#!/bin/bash

# Unified CDN Setup Script for OpenPolicy Platform
# Supports both CloudFlare and Azure CDN

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show usage
usage() {
    echo "Usage: $0 [cloudflare|azure|both]"
    echo ""
    echo "Options:"
    echo "  cloudflare  - Setup CloudFlare CDN"
    echo "  azure       - Setup Azure CDN with Front Door"
    echo "  both        - Setup multi-CDN configuration"
    echo ""
    echo "Environment Variables Required:"
    echo "  For CloudFlare:"
    echo "    - CLOUDFLARE_EMAIL"
    echo "    - CLOUDFLARE_API_KEY"
    echo "  For Azure:"
    echo "    - AZURE_CLIENT_ID"
    echo "    - AZURE_CLIENT_SECRET"
    echo "    - AZURE_TENANT_ID"
    echo "    - AZURE_SUBSCRIPTION_ID"
    exit 1
}

# Validate environment
validate_environment() {
    local cdn_type=$1
    
    if [ "$cdn_type" == "cloudflare" ] || [ "$cdn_type" == "both" ]; then
        if [ -z "$CLOUDFLARE_EMAIL" ] || [ -z "$CLOUDFLARE_API_KEY" ]; then
            error "CloudFlare credentials not set"
            exit 1
        fi
    fi
    
    if [ "$cdn_type" == "azure" ] || [ "$cdn_type" == "both" ]; then
        if [ -z "$AZURE_CLIENT_ID" ] || [ -z "$AZURE_CLIENT_SECRET" ]; then
            error "Azure credentials not set"
            exit 1
        fi
    fi
}

# Setup multi-CDN configuration
setup_multi_cdn() {
    log "Setting up multi-CDN configuration..."
    
    # Create traffic management configuration
    cat > multi-cdn-config.yaml << 'EOF'
# Multi-CDN Configuration for OpenPolicy Platform

cdns:
  cloudflare:
    enabled: true
    weight: 60  # 60% traffic
    regions:
      - north_america
      - europe
    endpoints:
      assets: "cdn-cf.openpolicy.com"
      api: "api-cf.openpolicy.com"
    features:
      - waf
      - ddos_protection
      - image_optimization
      - workers
  
  azure:
    enabled: true
    weight: 40  # 40% traffic
    regions:
      - asia_pacific
      - south_america
      - africa
    endpoints:
      assets: "cdn-az.openpolicy.com"
      api: "api-az.openpolicy.com"
    features:
      - front_door
      - global_load_balancing
      - azure_integration

routing_rules:
  - name: "Geographic Routing"
    description: "Route based on user location"
    conditions:
      - type: "geo"
        regions: ["US", "CA", "MX"]
        action: "route_to_cloudflare"
      - type: "geo"
        regions: ["CN", "JP", "AU", "IN"]
        action: "route_to_azure"
  
  - name: "Performance Routing"
    description: "Route based on real-time performance"
    conditions:
      - type: "latency"
        threshold_ms: 100
        action: "route_to_fastest"
  
  - name: "Failover Routing"
    description: "Automatic failover between CDNs"
    conditions:
      - type: "health_check"
        endpoint: "cloudflare"
        status: "unhealthy"
        action: "failover_to_azure"

health_checks:
  interval_seconds: 30
  timeout_seconds: 5
  healthy_threshold: 2
  unhealthy_threshold: 3
  endpoints:
    - url: "https://cdn-cf.openpolicy.com/health"
      expected_status: 200
    - url: "https://cdn-az.openpolicy.com/health"
      expected_status: 200

cache_strategy:
  static_assets:
    ttl: 31536000  # 1 year
    patterns:
      - "*.css"
      - "*.js"
      - "*.jpg"
      - "*.png"
      - "*.woff2"
  
  api_responses:
    ttl: 300  # 5 minutes
    patterns:
      - "/api/v1/public/*"
      - "/api/v1/policies"
  
  dynamic_content:
    ttl: 0  # No cache
    patterns:
      - "/admin/*"
      - "/api/auth/*"
      - "/api/private/*"

monitoring:
  metrics:
    - cache_hit_ratio
    - origin_response_time
    - bandwidth_usage
    - error_rate
    - request_count
  
  alerts:
    - name: "Cache Hit Ratio Low"
      condition: "cache_hit_ratio < 0.8"
      severity: "warning"
    
    - name: "High Error Rate"
      condition: "error_rate > 0.01"
      severity: "critical"
    
    - name: "CDN Failover"
      condition: "failover_triggered"
      severity: "warning"
EOF

    # Create DNS configuration for multi-CDN
    cat > dns-multi-cdn.tf << 'EOF'
# Route53 configuration for multi-CDN setup

resource "aws_route53_zone" "main" {
  name = "openpolicy.com"
}

# Health checks for each CDN
resource "aws_route53_health_check" "cloudflare" {
  fqdn              = "cdn-cf.openpolicy.com"
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"
}

resource "aws_route53_health_check" "azure" {
  fqdn              = "cdn-az.openpolicy.com"
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"
}

# Weighted routing policy
resource "aws_route53_record" "cdn_weighted_cf" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "cdn.openpolicy.com"
  type    = "CNAME"
  ttl     = "60"
  
  weighted_routing_policy {
    weight = 60
  }
  
  set_identifier = "cloudflare"
  records        = ["cdn-cf.openpolicy.com"]
  
  health_check_id = aws_route53_health_check.cloudflare.id
}

resource "aws_route53_record" "cdn_weighted_az" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "cdn.openpolicy.com"
  type    = "CNAME"
  ttl     = "60"
  
  weighted_routing_policy {
    weight = 40
  }
  
  set_identifier = "azure"
  records        = ["cdn-az.openpolicy.com"]
  
  health_check_id = aws_route53_health_check.azure.id
}

# Geolocation routing
resource "aws_route53_record" "cdn_geo_na" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "cdn.openpolicy.com"
  type    = "CNAME"
  ttl     = "60"
  
  geolocation_routing_policy {
    continent = "NA"
  }
  
  set_identifier = "North-America"
  records        = ["cdn-cf.openpolicy.com"]
}

resource "aws_route53_record" "cdn_geo_as" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "cdn.openpolicy.com"
  type    = "CNAME"
  ttl     = "60"
  
  geolocation_routing_policy {
    continent = "AS"
  }
  
  set_identifier = "Asia"
  records        = ["cdn-az.openpolicy.com"]
}
EOF

    log "✅ Multi-CDN configuration created"
}

# Create monitoring dashboard for multi-CDN
create_multi_cdn_monitoring() {
    log "Creating multi-CDN monitoring dashboard..."
    
    cat > multi-cdn-dashboard.json << 'EOF'
{
  "dashboard": {
    "title": "Multi-CDN Performance Dashboard",
    "panels": [
      {
        "title": "CDN Traffic Distribution",
        "type": "pie",
        "targets": [
          {
            "expr": "sum(cdn_requests_total) by (cdn_provider)"
          }
        ]
      },
      {
        "title": "Cache Hit Ratio by CDN",
        "type": "graph",
        "targets": [
          {
            "expr": "cdn_cache_hit_ratio{provider=\"cloudflare\"}",
            "legendFormat": "CloudFlare"
          },
          {
            "expr": "cdn_cache_hit_ratio{provider=\"azure\"}",
            "legendFormat": "Azure CDN"
          }
        ]
      },
      {
        "title": "Response Time Comparison",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, cdn_response_time_bucket)",
            "legendFormat": "{{provider}} p95"
          }
        ]
      },
      {
        "title": "Error Rate by CDN",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(cdn_errors_total[5m])",
            "legendFormat": "{{provider}} {{status_code}}"
          }
        ]
      },
      {
        "title": "Bandwidth Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(cdn_bandwidth_bytes[5m])) by (provider)",
            "legendFormat": "{{provider}}"
          }
        ]
      },
      {
        "title": "Failover Events",
        "type": "table",
        "targets": [
          {
            "expr": "increase(cdn_failover_total[24h])"
          }
        ]
      }
    ]
  }
}
EOF

    # Create synthetic monitoring
    cat > synthetic-monitoring.yaml << 'EOF'
# Synthetic monitoring for multi-CDN setup
monitors:
  - name: "CloudFlare CDN Health"
    type: "http"
    url: "https://cdn-cf.openpolicy.com/health"
    interval: 60
    locations:
      - "us-east-1"
      - "eu-west-1"
      - "ap-southeast-1"
    assertions:
      - type: "status_code"
        operator: "equals"
        value: 200
      - type: "response_time"
        operator: "less_than"
        value: 1000
  
  - name: "Azure CDN Health"
    type: "http"
    url: "https://cdn-az.openpolicy.com/health"
    interval: 60
    locations:
      - "us-west-2"
      - "eu-central-1"
      - "ap-northeast-1"
    assertions:
      - type: "status_code"
        operator: "equals"
        value: 200
      - type: "response_time"
        operator: "less_than"
        value: 1000
  
  - name: "Global Asset Load Test"
    type: "browser"
    script: |
      // Test loading critical assets from both CDNs
      await page.goto('https://openpolicy.com');
      
      // Check CloudFlare assets
      const cfAsset = await page.evaluate(() => {
        return performance.getEntriesByName('https://cdn-cf.openpolicy.com/css/main.css')[0];
      });
      
      assert(cfAsset.duration < 500, 'CloudFlare asset load too slow');
      
      // Check Azure assets
      const azAsset = await page.evaluate(() => {
        return performance.getEntriesByName('https://cdn-az.openpolicy.com/js/app.js')[0];
      });
      
      assert(azAsset.duration < 500, 'Azure asset load too slow');
    interval: 300
    locations:
      - "us-east-1"
      - "eu-west-1"
      - "ap-southeast-1"
EOF

    log "✅ Multi-CDN monitoring created"
}

# Generate unified documentation
generate_unified_docs() {
    log "Generating unified CDN documentation..."
    
    cat > CDN_SETUP_GUIDE.md << 'EOF'
# CDN Setup Guide for OpenPolicy Platform

## Overview

OpenPolicy Platform supports three CDN configurations:
1. **CloudFlare Only** - Global CDN with WAF and edge computing
2. **Azure CDN Only** - Integrated with Azure services and Front Door
3. **Multi-CDN** - Both providers with intelligent routing

## Quick Start

### Single CDN Setup

```bash
# CloudFlare
export CLOUDFLARE_EMAIL="admin@openpolicy.com"
export CLOUDFLARE_API_KEY="your-api-key"
./setup-cdn.sh cloudflare

# Azure CDN
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
./setup-cdn.sh azure
```

### Multi-CDN Setup

```bash
# Set all credentials
export CLOUDFLARE_EMAIL="admin@openpolicy.com"
export CLOUDFLARE_API_KEY="your-api-key"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"

# Run multi-CDN setup
./setup-cdn.sh both
```

## CDN Comparison

| Feature | CloudFlare | Azure CDN |
|---------|------------|-----------|
| Global PoPs | 200+ | 130+ |
| DDoS Protection | ✅ Advanced | ✅ Standard |
| WAF | ✅ Built-in | ✅ Front Door |
| Image Optimization | ✅ Polish/Mirage | ✅ Via Functions |
| Edge Computing | ✅ Workers | ✅ Front Door Rules |
| Video Streaming | ✅ Stream | ✅ Media Services |
| Analytics | ✅ Real-time | ✅ Azure Monitor |
| Cost | $20-200/mo | $35-875/mo |

## Architecture

### Single CDN
```
Users → CDN → Origin Servers
         ↓
    WAF Rules
```

### Multi-CDN
```
Users → DNS (Route53/Traffic Manager)
         ↓
    Weighted/Geo Routing
         ↓
    CloudFlare ← Health Checks → Azure CDN
         ↓                            ↓
    Origin Servers              Origin Servers
```

## Cache Strategy

### Static Assets
- **Pattern**: `\.(css|js|jpg|jpeg|png|gif|svg|woff|woff2|ttf|eot)$`
- **TTL**: 1 year (31536000 seconds)
- **Headers**: `Cache-Control: public, max-age=31536000, immutable`

### API Responses
- **Pattern**: `/api/v1/public/*`
- **TTL**: 5 minutes (300 seconds)
- **Headers**: `Cache-Control: public, max-age=300`
- **Vary**: `Accept, Accept-Encoding`

### Dynamic Content
- **Pattern**: `/admin/*, /api/auth/*, /api/private/*`
- **TTL**: 0 (no cache)
- **Headers**: `Cache-Control: no-cache, no-store, must-revalidate`

## Implementation

### Origin Configuration

```nginx
# Nginx configuration for CDN origins
server {
    listen 443 ssl http2;
    server_name origin.openpolicy.com;
    
    # CDN-specific headers
    add_header X-CDN-Tag $deployment_version;
    add_header X-Cache-Control-Override "true";
    
    # Static assets
    location ~* \.(css|js|jpg|jpeg|png|gif|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, max-age=31536000, immutable";
        add_header X-Content-Type-Options "nosniff";
    }
    
    # API endpoints
    location /api/v1/public {
        expires 5m;
        add_header Cache-Control "public, max-age=300";
        add_header Vary "Accept, Accept-Encoding";
    }
    
    # Dynamic content
    location /admin {
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
    }
}
```

### Application Integration

```javascript
// Express.js middleware for CDN
const cdnHeaders = (req, res, next) => {
  // Version-based cache busting
  res.setHeader('X-Deployment-Version', process.env.DEPLOYMENT_VERSION);
  
  // CDN-specific tags for purging
  res.setHeader('X-CDN-Tag', `deployment-${process.env.DEPLOYMENT_VERSION}`);
  
  // Determine cache policy
  if (req.path.match(/\.(css|js|jpg|jpeg|png|gif|svg|woff|woff2)$/)) {
    res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
  } else if (req.path.startsWith('/api/v1/public')) {
    res.setHeader('Cache-Control', 'public, max-age=300');
  } else if (req.path.startsWith('/admin') || req.path.startsWith('/api/auth')) {
    res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
  }
  
  next();
};

app.use(cdnHeaders);
```

### Cache Purging

```bash
# CloudFlare - Purge by URL
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/purge_cache" \
  -H "X-Auth-Email: $EMAIL" \
  -H "X-Auth-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  --data '{"files":["https://openpolicy.com/css/style.css"]}'

# Azure CDN - Purge by path
az cdn endpoint purge \
  --resource-group openpolicy-rg \
  --profile-name openpolicy-cdn \
  --name openpolicy-endpoint \
  --content-paths "/css/*" "/js/*"

# Multi-CDN - Purge both
./purge-multi-cdn.sh --tag "deployment-v1.2.3"
```

## Monitoring

### Key Metrics
1. **Cache Hit Ratio** - Target: > 80%
2. **Origin Response Time** - Target: < 200ms
3. **Edge Response Time** - Target: < 50ms
4. **Error Rate** - Target: < 0.1%
5. **Bandwidth Savings** - Target: > 70%

### Dashboards
- CloudFlare: Analytics → Performance
- Azure: CDN Profile → Metrics
- Multi-CDN: Grafana custom dashboard

### Alerts
```yaml
alerts:
  - name: "Low Cache Hit Ratio"
    condition: cache_hit_ratio < 0.7
    duration: 5m
    severity: warning
    
  - name: "High Origin Load"
    condition: origin_requests_per_second > 1000
    duration: 2m
    severity: critical
    
  - name: "CDN Errors"
    condition: error_rate > 0.01
    duration: 5m
    severity: critical
```

## Cost Optimization

### CloudFlare
1. Use appropriate plan tier
2. Enable Polish for image optimization
3. Use Workers for edge logic
4. Monitor bandwidth usage

### Azure CDN
1. Choose correct pricing tier
2. Enable compression
3. Use Rules Engine efficiently
4. Monitor data transfer by region

### Multi-CDN
1. Route traffic based on cost
2. Use cheaper CDN for large files
3. Geographic optimization
4. Monitor per-provider costs

## Security

### Headers
```nginx
# Security headers added by CDN
add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()";
```

### WAF Rules
- SQL Injection protection
- XSS protection
- Rate limiting
- Geo-blocking
- Custom rules for API

## Troubleshooting

### Cache Issues
```bash
# Check cache status
curl -I https://cdn.openpolicy.com/css/style.css | grep -i cache

# Expected headers:
# CF-Cache-Status: HIT (CloudFlare)
# X-Cache: TCP_HIT (Azure)
```

### Performance Issues
1. Check cache hit ratio
2. Verify compression is enabled
3. Review origin response times
4. Check for cache-busting parameters

### Multi-CDN Issues
1. Verify health checks are passing
2. Check DNS propagation
3. Review traffic distribution
4. Monitor failover logs

## Best Practices

1. **Version Assets** - Use version in filenames
2. **Set Proper Headers** - Be explicit about caching
3. **Monitor Actively** - Set up comprehensive monitoring
4. **Test Changes** - Always test in staging
5. **Document Everything** - Keep runbooks updated
6. **Plan for Failures** - Have fallback strategies
7. **Optimize Images** - Use modern formats (WebP, AVIF)
8. **Secure Origins** - Restrict access to CDN only
EOF

    log "✅ Unified documentation generated"
}

# Main execution
main() {
    CDN_TYPE=${1:-""}
    
    if [ -z "$CDN_TYPE" ]; then
        usage
    fi
    
    validate_environment "$CDN_TYPE"
    
    case "$CDN_TYPE" in
        "cloudflare")
            log "Setting up CloudFlare CDN..."
            ./cloudflare-setup.sh
            ;;
        "azure")
            log "Setting up Azure CDN..."
            ./azure-cdn-setup.sh
            ;;
        "both")
            log "Setting up multi-CDN configuration..."
            ./cloudflare-setup.sh
            ./azure-cdn-setup.sh
            setup_multi_cdn
            create_multi_cdn_monitoring
            ;;
        *)
            usage
            ;;
    esac
    
    generate_unified_docs
    
    log "✅ CDN setup complete!"
    log ""
    log "Configuration: $CDN_TYPE"
    log "Documentation: CDN_SETUP_GUIDE.md"
    log ""
    log "Next steps:"
    log "1. Update DNS records"
    log "2. Configure origin servers"
    log "3. Test cache behavior"
    log "4. Monitor performance"
}

# Run main function
main "$@"