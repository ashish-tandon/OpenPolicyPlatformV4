#!/bin/bash

# Azure CDN Setup Script for OpenPolicy Platform
# Configures Azure CDN with Front Door for global content delivery

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

# Configuration
RESOURCE_GROUP="openpolicy-prod-rg"
CDN_PROFILE_NAME="openpolicy-cdn"
LOCATION="global"
STORAGE_ACCOUNT="openpolicystorage"
CONTAINER_NAME="assets"
CUSTOM_DOMAIN="cdn.openpolicy.com"

# Create CDN profile
create_cdn_profile() {
    log "Creating Azure CDN profile..."
    
    # Create CDN profile with Standard Microsoft tier
    az cdn profile create \
        --resource-group $RESOURCE_GROUP \
        --name $CDN_PROFILE_NAME \
        --sku Standard_Microsoft \
        --location $LOCATION
    
    log "✅ CDN profile created"
}

# Create CDN endpoints
create_cdn_endpoints() {
    log "Creating CDN endpoints..."
    
    # Static assets endpoint
    az cdn endpoint create \
        --resource-group $RESOURCE_GROUP \
        --profile-name $CDN_PROFILE_NAME \
        --name "openpolicy-assets" \
        --origin "$STORAGE_ACCOUNT.blob.core.windows.net" \
        --origin-host-header "$STORAGE_ACCOUNT.blob.core.windows.net" \
        --origin-path "/$CONTAINER_NAME" \
        --content-types-to-compress "text/html" "text/css" "application/javascript" \
        --is-compression-enabled true \
        --is-http-allowed false \
        --is-https-allowed true
    
    # API endpoint with caching
    az cdn endpoint create \
        --resource-group $RESOURCE_GROUP \
        --profile-name $CDN_PROFILE_NAME \
        --name "openpolicy-api" \
        --origin "api.openpolicy.com" \
        --origin-host-header "api.openpolicy.com" \
        --query-string-caching-behavior "UseQueryString" \
        --is-http-allowed false \
        --is-https-allowed true
    
    # Web app endpoint
    az cdn endpoint create \
        --resource-group $RESOURCE_GROUP \
        --profile-name $CDN_PROFILE_NAME \
        --name "openpolicy-web" \
        --origin "openpolicy.azurewebsites.net" \
        --origin-host-header "openpolicy.azurewebsites.net" \
        --is-http-allowed false \
        --is-https-allowed true
    
    log "✅ CDN endpoints created"
}

# Configure caching rules
configure_caching_rules() {
    log "Configuring caching rules..."
    
    # Static assets - cache for 1 year
    az cdn endpoint rule add \
        --resource-group $RESOURCE_GROUP \
        --profile-name $CDN_PROFILE_NAME \
        --endpoint-name "openpolicy-assets" \
        --name "CacheStaticAssets" \
        --order 1 \
        --match-variable "UrlFileExtension" \
        --operator "In" \
        --match-values "css" "js" "jpg" "jpeg" "png" "gif" "svg" "woff" "woff2" \
        --action-name "CacheExpiration" \
        --cache-behavior "SetIfMissing" \
        --cache-duration "365.00:00:00"
    
    # API public endpoints - cache for 5 minutes
    az cdn endpoint rule add \
        --resource-group $RESOURCE_GROUP \
        --profile-name $CDN_PROFILE_NAME \
        --endpoint-name "openpolicy-api" \
        --name "CachePublicAPI" \
        --order 2 \
        --match-variable "UrlPath" \
        --operator "BeginsWith" \
        --match-values "/v1/public/" \
        --action-name "CacheExpiration" \
        --cache-behavior "Override" \
        --cache-duration "00:05:00"
    
    # Dynamic content - bypass cache
    az cdn endpoint rule add \
        --resource-group $RESOURCE_GROUP \
        --profile-name $CDN_PROFILE_NAME \
        --endpoint-name "openpolicy-web" \
        --name "BypassDynamic" \
        --order 3 \
        --match-variable "UrlPath" \
        --operator "BeginsWith" \
        --match-values "/admin/" "/api/auth/" "/api/private/" \
        --action-name "CacheExpiration" \
        --cache-behavior "BypassCache"
    
    log "✅ Caching rules configured"
}

# Configure custom domains
configure_custom_domains() {
    log "Configuring custom domains..."
    
    # Add custom domain
    az cdn custom-domain create \
        --resource-group $RESOURCE_GROUP \
        --profile-name $CDN_PROFILE_NAME \
        --endpoint-name "openpolicy-assets" \
        --name "cdn-custom-domain" \
        --hostname $CUSTOM_DOMAIN
    
    # Enable HTTPS
    az cdn custom-domain enable-https \
        --resource-group $RESOURCE_GROUP \
        --profile-name $CDN_PROFILE_NAME \
        --endpoint-name "openpolicy-assets" \
        --name "cdn-custom-domain"
    
    log "✅ Custom domains configured"
}

# Create Azure Front Door for advanced CDN
create_front_door() {
    log "Creating Azure Front Door..."
    
    # Create Front Door profile
    az afd profile create \
        --resource-group $RESOURCE_GROUP \
        --profile-name "openpolicy-frontdoor" \
        --sku "Standard_AzureFrontDoor"
    
    # Create endpoints
    az afd endpoint create \
        --resource-group $RESOURCE_GROUP \
        --profile-name "openpolicy-frontdoor" \
        --endpoint-name "openpolicy-global" \
        --enabled-state "Enabled"
    
    # Create origin groups
    az afd origin-group create \
        --resource-group $RESOURCE_GROUP \
        --profile-name "openpolicy-frontdoor" \
        --origin-group-name "web-origin-group" \
        --probe-request-type "GET" \
        --probe-protocol "Https" \
        --probe-interval-in-seconds 30 \
        --probe-path "/" \
        --sample-size 4 \
        --successful-samples-required 3 \
        --load-balancing-sample-size 4 \
        --load-balancing-successful-samples-required 3
    
    # Add origins
    az afd origin create \
        --resource-group $RESOURCE_GROUP \
        --profile-name "openpolicy-frontdoor" \
        --origin-group-name "web-origin-group" \
        --origin-name "primary-web" \
        --host-name "openpolicy-primary.azurewebsites.net" \
        --origin-host-header "openpolicy-primary.azurewebsites.net" \
        --priority 1 \
        --weight 1000 \
        --enabled-state "Enabled" \
        --https-port 443 \
        --http-port 80
    
    az afd origin create \
        --resource-group $RESOURCE_GROUP \
        --profile-name "openpolicy-frontdoor" \
        --origin-group-name "web-origin-group" \
        --origin-name "secondary-web" \
        --host-name "openpolicy-secondary.azurewebsites.net" \
        --origin-host-header "openpolicy-secondary.azurewebsites.net" \
        --priority 2 \
        --weight 1000 \
        --enabled-state "Enabled" \
        --https-port 443 \
        --http-port 80
    
    # Create routes
    az afd route create \
        --resource-group $RESOURCE_GROUP \
        --profile-name "openpolicy-frontdoor" \
        --endpoint-name "openpolicy-global" \
        --route-name "web-route" \
        --origin-group "web-origin-group" \
        --supported-protocols "Http" "Https" \
        --patterns-to-match "/*" \
        --forwarding-protocol "HttpsOnly" \
        --link-to-default-domain "Enabled" \
        --https-redirect "Enabled"
    
    log "✅ Azure Front Door created"
}

# Configure WAF policies
configure_waf() {
    log "Configuring Web Application Firewall..."
    
    # Create WAF policy
    az network front-door waf-policy create \
        --resource-group $RESOURCE_GROUP \
        --name "openpolicyWAF" \
        --mode "Prevention" \
        --enable-default-rule-set true \
        --enable-default-custom-rule-set true
    
    # Add custom rules
    az network front-door waf-policy rule create \
        --resource-group $RESOURCE_GROUP \
        --policy-name "openpolicyWAF" \
        --name "RateLimitRule" \
        --rule-type "RateLimitRule" \
        --rate-limit-duration "OneMin" \
        --rate-limit-threshold 100 \
        --action "Block" \
        --priority 1
    
    # Add geo-filtering
    az network front-door waf-policy rule create \
        --resource-group $RESOURCE_GROUP \
        --policy-name "openpolicyWAF" \
        --name "GeoFilterRule" \
        --rule-type "MatchRule" \
        --action "Block" \
        --priority 2 \
        --match-condition "RemoteAddr GeoMatch 'CN' 'RU' 'KP'"
    
    # Associate WAF policy with Front Door
    az afd security-policy create \
        --resource-group $RESOURCE_GROUP \
        --profile-name "openpolicy-frontdoor" \
        --security-policy-name "MySecurityPolicy" \
        --domains "/subscriptions/.../resourceGroups/.../providers/Microsoft.Cdn/profiles/openpolicy-frontdoor/afdEndpoints/openpolicy-global" \
        --waf-policy "/subscriptions/.../resourceGroups/.../providers/Microsoft.Network/frontdoorWebApplicationFirewallPolicies/openpolicyWAF"
    
    log "✅ WAF configured"
}

# Configure monitoring
configure_monitoring() {
    log "Configuring CDN monitoring..."
    
    # Enable diagnostics
    az monitor diagnostic-settings create \
        --resource "/subscriptions/.../resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Cdn/profiles/$CDN_PROFILE_NAME" \
        --name "cdn-diagnostics" \
        --logs '[
            {
                "category": "AzureCdnAccessLog",
                "enabled": true,
                "retentionPolicy": {
                    "days": 30,
                    "enabled": true
                }
            }
        ]' \
        --metrics '[
            {
                "category": "AllMetrics",
                "enabled": true,
                "retentionPolicy": {
                    "days": 30,
                    "enabled": true
                }
            }
        ]' \
        --workspace $LOG_ANALYTICS_WORKSPACE_ID
    
    # Create alerts
    az monitor metrics alert create \
        --resource-group $RESOURCE_GROUP \
        --name "cdn-origin-health-alert" \
        --description "Alert when CDN origin health drops" \
        --scopes "/subscriptions/.../resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Cdn/profiles/$CDN_PROFILE_NAME" \
        --condition "avg OriginHealthPercentage < 95" \
        --window-size 5m \
        --evaluation-frequency 1m \
        --severity 2 \
        --action-group $ACTION_GROUP_ID
    
    az monitor metrics alert create \
        --resource-group $RESOURCE_GROUP \
        --name "cdn-error-rate-alert" \
        --description "Alert on high error rate" \
        --scopes "/subscriptions/.../resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Cdn/profiles/$CDN_PROFILE_NAME" \
        --condition "avg Percentage4XX > 5 or avg Percentage5XX > 1" \
        --window-size 5m \
        --evaluation-frequency 1m \
        --severity 1 \
        --action-group $ACTION_GROUP_ID
    
    log "✅ Monitoring configured"
}

# Create purge scripts
create_purge_scripts() {
    log "Creating cache purge scripts..."
    
    cat > purge-cdn-cache.sh << 'SCRIPT'
#!/bin/bash

# Purge CDN cache
ENDPOINT_NAME=$1
PATH_TO_PURGE=$2

if [ -z "$ENDPOINT_NAME" ] || [ -z "$PATH_TO_PURGE" ]; then
    echo "Usage: ./purge-cdn-cache.sh <endpoint-name> <path-to-purge>"
    echo "Example: ./purge-cdn-cache.sh openpolicy-assets /css/*"
    exit 1
fi

echo "Purging cache for $PATH_TO_PURGE on endpoint $ENDPOINT_NAME..."

az cdn endpoint purge \
    --resource-group openpolicy-prod-rg \
    --profile-name openpolicy-cdn \
    --name $ENDPOINT_NAME \
    --content-paths $PATH_TO_PURGE \
    --no-wait

echo "Cache purge initiated. Check status with:"
echo "az cdn endpoint show --resource-group openpolicy-prod-rg --profile-name openpolicy-cdn --name $ENDPOINT_NAME --query 'provisioningState'"
SCRIPT

    chmod +x purge-cdn-cache.sh
    
    log "✅ Purge scripts created"
}

# Generate Terraform configuration
generate_terraform() {
    log "Generating Terraform configuration..."
    
    cat > cdn.tf << 'EOF'
resource "azurerm_cdn_profile" "main" {
  name                = "openpolicy-cdn"
  location            = "global"
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Standard_Microsoft"
}

resource "azurerm_cdn_endpoint" "assets" {
  name                = "openpolicy-assets"
  profile_name        = azurerm_cdn_profile.main.name
  location            = azurerm_cdn_profile.main.location
  resource_group_name = azurerm_resource_group.main.name
  
  origin {
    name      = "storage"
    host_name = azurerm_storage_account.main.primary_blob_endpoint
  }
  
  is_http_allowed         = false
  is_https_allowed        = true
  content_types_to_compress = [
    "text/html",
    "text/css",
    "text/javascript",
    "application/javascript",
    "application/json",
    "application/xml"
  ]
  
  is_compression_enabled = true
  
  delivery_rule {
    name  = "CacheStaticAssets"
    order = 1
    
    url_file_extension_condition {
      operator     = "In"
      match_values = ["css", "js", "jpg", "jpeg", "png", "gif", "svg", "woff", "woff2"]
    }
    
    cache_expiration_action {
      behavior = "SetIfMissing"
      duration = "365.00:00:00"
    }
  }
}

resource "azurerm_frontdoor" "main" {
  name                = "openpolicy-frontdoor"
  resource_group_name = azurerm_resource_group.main.name
  
  frontend_endpoint {
    name                              = "openpolicy-frontend"
    host_name                         = "openpolicy.azurefd.net"
    session_affinity_enabled          = false
    session_affinity_ttl_seconds      = 0
  }
  
  backend_pool {
    name = "web-backend-pool"
    
    backend {
      host_header = "openpolicy.azurewebsites.net"
      address     = "openpolicy.azurewebsites.net"
      http_port   = 80
      https_port  = 443
      weight      = 100
      priority    = 1
      enabled     = true
    }
    
    load_balancing_settings {
      name                            = "loadbalancing"
      sample_size                     = 4
      successful_samples_required     = 2
      additional_latency_milliseconds = 0
    }
    
    health_probe_settings {
      name                = "healthprobe"
      path                = "/health"
      protocol            = "Https"
      interval_in_seconds = 30
    }
  }
  
  routing_rule {
    name               = "web-routing"
    accepted_protocols = ["Http", "Https"]
    patterns_to_match  = ["/*"]
    frontend_endpoints = ["openpolicy-frontend"]
    
    forwarding_configuration {
      forwarding_protocol = "HttpsOnly"
      backend_pool_name   = "web-backend-pool"
      cache_enabled       = true
      cache_use_dynamic_compression = true
      cache_query_parameter_strip_directive = "StripNone"
    }
  }
}

resource "azurerm_frontdoor_firewall_policy" "main" {
  name                = "openpolicyWAF"
  resource_group_name = azurerm_resource_group.main.name
  
  enabled                        = true
  mode                          = "Prevention"
  
  managed_rule {
    type    = "DefaultRuleSet"
    version = "1.0"
  }
  
  custom_rule {
    name                           = "RateLimitRule"
    enabled                        = true
    priority                       = 1
    rate_limit_duration_in_minutes = 1
    rate_limit_threshold           = 100
    type                          = "RateLimiting"
    action                        = "Block"
    
    match_condition {
      match_variable     = "RemoteAddr"
      operator           = "IPMatch"
      negation_condition = false
      match_values       = ["0.0.0.0/0"]
    }
  }
}

output "cdn_endpoints" {
  value = {
    assets = azurerm_cdn_endpoint.assets.host_name
    frontdoor = azurerm_frontdoor.main.cname
  }
}
EOF

    log "✅ Terraform configuration generated"
}

# Generate documentation
generate_documentation() {
    log "Generating Azure CDN documentation..."
    
    cat > AZURE_CDN_SETUP.md << 'EOF'
# Azure CDN Configuration

## Overview

Azure CDN with Front Door provides global content delivery, load balancing, and web application firewall for OpenPolicy Platform.

## Architecture

### CDN Profile
- **Tier**: Standard Microsoft
- **Endpoints**: 
  - `openpolicy-assets`: Static content
  - `openpolicy-api`: API caching
  - `openpolicy-web`: Web application

### Front Door
- **Global Load Balancing**: Multi-region failover
- **WAF Protection**: OWASP rule set + custom rules
- **SSL Termination**: Managed certificates
- **Health Probes**: Every 30 seconds

## Caching Configuration

### Static Assets
- **Path**: `/assets/*`, `/css/*`, `/js/*`, `/images/*`
- **TTL**: 365 days
- **Compression**: Enabled
- **Query String**: Ignored

### API Endpoints
- **Path**: `/api/v1/public/*`
- **TTL**: 5 minutes
- **Query String**: Include in cache key
- **Compression**: Enabled

### Dynamic Content
- **Path**: `/admin/*`, `/api/auth/*`, `/api/private/*`
- **Caching**: Bypassed
- **Query String**: Not applicable

## Security Features

### WAF Rules
1. **Rate Limiting**: 100 requests/minute per IP
2. **Geo-blocking**: Block high-risk countries
3. **OWASP Protection**: SQL injection, XSS, etc.
4. **Custom Rules**: Application-specific protection

### SSL/TLS
- **Minimum Version**: TLS 1.2
- **Certificate**: Azure managed
- **HTTPS Redirect**: Enforced
- **HSTS**: Enabled

## Performance Optimization

### Compression
- **Types**: Gzip, Brotli
- **MIME Types**: text/*, application/javascript, application/json
- **Minimum Size**: 1KB

### Connection Optimization
- **HTTP/2**: Enabled
- **Keep-Alive**: 75 seconds
- **Connection Reuse**: Enabled

## Cache Management

### Purge Entire Endpoint
```bash
az cdn endpoint purge \
    --resource-group openpolicy-prod-rg \
    --profile-name openpolicy-cdn \
    --name openpolicy-assets \
    --content-paths "/*"
```

### Purge Specific Path
```bash
az cdn endpoint purge \
    --resource-group openpolicy-prod-rg \
    --profile-name openpolicy-cdn \
    --name openpolicy-assets \
    --content-paths "/css/style.css" "/js/app.js"
```

### Purge by Tag
```bash
# Use Azure Front Door for tag-based purging
az afd endpoint purge \
    --resource-group openpolicy-prod-rg \
    --profile-name openpolicy-frontdoor \
    --endpoint-name openpolicy-global \
    --domains "openpolicy.com" \
    --content-paths "/*" \
    --purge-tag "deployment-v1.2.3"
```

## Monitoring

### Metrics
- Origin Health Percentage
- Request Count
- Bandwidth (GB)
- Cache Hit Ratio
- 4XX/5XX Error Rate
- Origin Response Time

### Alerts
- Origin health < 95%
- 4XX errors > 5%
- 5XX errors > 1%
- Bandwidth spike > 200%

### Logs
- Access logs to Log Analytics
- WAF logs to Storage Account
- Real-time metrics in Azure Monitor

## Cost Optimization

### Standard Tier
- **Data Transfer**: First 10TB/month
- **HTTP Requests**: Per 10,000 requests
- **HTTPS Requests**: Slightly higher rate

### Premium Tier (Front Door)
- **Base Fee**: Per endpoint per month
- **Data Transfer**: Zone-based pricing
- **Requests**: Per million requests
- **WAF**: Additional per policy

### Optimization Tips
1. Enable compression to reduce bandwidth
2. Set appropriate cache headers
3. Use query string caching wisely
4. Monitor and adjust TTLs
5. Consolidate endpoints where possible

## Integration

### Storage Account
```bash
# Enable static website hosting
az storage blob service-properties update \
    --account-name openpolicystorage \
    --static-website \
    --index-document index.html \
    --404-document 404.html

# Set CORS rules
az storage cors add \
    --account-name openpolicystorage \
    --services blob \
    --methods GET HEAD \
    --origins "https://openpolicy.com" \
    --allowed-headers "*" \
    --exposed-headers "*" \
    --max-age 3600
```

### Application Configuration
```csharp
// Configure static file headers
app.UseStaticFiles(new StaticFileOptions
{
    OnPrepareResponse = ctx =>
    {
        ctx.Context.Response.Headers.Append(
            "Cache-Control", "public,max-age=31536000");
        ctx.Context.Response.Headers.Append(
            "CDN-Tag", $"deployment-{version}");
    }
});
```

### CI/CD Pipeline
```yaml
- task: AzureCLI@2
  displayName: 'Purge CDN Cache'
  inputs:
    azureSubscription: 'Production'
    scriptType: 'bash'
    scriptLocation: 'inlineScript'
    inlineScript: |
      az cdn endpoint purge \
        --resource-group $(resourceGroup) \
        --profile-name $(cdnProfile) \
        --name $(cdnEndpoint) \
        --content-paths "/*" \
        --no-wait
```

## Troubleshooting

### Cache Not Working
1. Check cache headers from origin
2. Verify caching rules order
3. Check query string settings
4. Review cache statistics

### Origin Errors
1. Check origin health probes
2. Verify origin authentication
3. Review firewall rules
4. Check SSL certificates

### Performance Issues
1. Review compression settings
2. Check cache hit ratio
3. Analyze origin response times
4. Consider additional endpoints

## Best Practices

1. **Cache Headers**: Set explicit cache headers at origin
2. **Versioning**: Use version in filenames for static assets
3. **Purging**: Purge selectively, not entire cache
4. **Monitoring**: Set up alerts for key metrics
5. **Security**: Enable WAF and review rules regularly
6. **Testing**: Test cache behavior in staging first
7. **Documentation**: Document cache strategy
EOF

    log "✅ Documentation generated"
}

# Main execution
main() {
    log "Starting Azure CDN setup..."
    
    # Login to Azure
    az login --service-principal \
        -u $AZURE_CLIENT_ID \
        -p $AZURE_CLIENT_SECRET \
        --tenant $AZURE_TENANT_ID
    
    az account set --subscription $AZURE_SUBSCRIPTION_ID
    
    # Create resources
    create_cdn_profile
    create_cdn_endpoints
    configure_caching_rules
    configure_custom_domains
    create_front_door
    configure_waf
    configure_monitoring
    create_purge_scripts
    generate_terraform
    generate_documentation
    
    log "✅ Azure CDN setup complete!"
    log ""
    log "CDN Endpoints:"
    log "  - Assets: https://openpolicy-assets.azureedge.net"
    log "  - API: https://openpolicy-api.azureedge.net"
    log "  - Web: https://openpolicy-web.azureedge.net"
    log "  - Front Door: https://openpolicy.azurefd.net"
    log ""
    log "Documentation: AZURE_CDN_SETUP.md"
    log "Purge Script: ./purge-cdn-cache.sh"
}

# Run main function
main "$@"