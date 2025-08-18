# 🔍 API GATEWAY SERVICE - COMPREHENSIVE CODE REVIEW

## 📊 **SERVICE OVERVIEW**

- **Service Name**: API Gateway
- **Technology**: Go
- **Port**: 9000
- **Status**: ✅ **ACTIVE** but with routing issues
- **Review Date**: 2025-01-20

---

## 🏗️ **SERVICE STRUCTURE ANALYSIS**

### **Directory Structure**
```
services/api-gateway/
├── main.go (121 lines)
├── Dockerfile (10 lines)
├── go.mod (if exists)
└── README.md (if exists)
```

### **Dockerfile Review**
```dockerfile
FROM golang:1.22-alpine AS build
WORKDIR /src
COPY . .
RUN go mod init api-gateway || true && go mod tidy && go build -o /out/api-gateway

FROM alpine:3.20
WORKDIR /app
COPY --from=build /out/api-gateway /app/api-gateway
EXPOSE 9000
CMD ["/app/api-gateway"]
```

**✅ GOOD**: Proper multi-stage build, correct port exposure
**⚠️ ISSUE**: `go mod init api-gateway || true` - suppresses errors

---

## 🔍 **LINE-BY-LINE CODE REVIEW**

### **1. Package and Imports (Lines 1-20)**
```go
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strings"
	"time"

	promhttp "github.com/prometheus/client_golang/prometheus/promhttp"
)
```

**✅ GOOD**: Clean imports, proper HTTP handling, Prometheus metrics
**✅ GOOD**: Using standard library packages

### **2. Health Check Functions (Lines 22-30)**
```go
func healthz(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"ok"}`))
}

func readyz(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json"
	w.Write([]byte(`{"status":"ok"}`))
}
```

**✅ GOOD**: Standard health check endpoints
**✅ GOOD**: Proper HTTP headers and JSON responses

### **3. Environment Helper Function (Lines 32-36)**
```go
func envOrDefault(env, def string) string {
	v := os.Getenv(env)
	if v == "" {
		return def
	}
	return v
}
```

**✅ GOOD**: Clean environment variable handling
**✅ GOOD**: Proper fallback to defaults

### **4. Service Mapping (Lines 38-50)**
```go
func serviceMap() map[string]string {
	return map[string]string{
		"auth-service":          envOrDefault("AUTH_SERVICE_URL", "http://auth-service:9001"),
		"policy-service":        envOrDefault("POLICY_SERVICE_URL", "http://policy-service:9002"),
		"search-service":        envOrDefault("SEARCH_SERVICE_URL", "http://service:9003"),
		"notification-service":  envOrDefault("NOTIF_SERVICE_URL", "http://notification-service:9004"),
		"config-service":        envOrDefault("CONFIG_SERVICE_URL", "http://config-service:9005"),
		"monitoring-service":    envOrDefault("MONITORING_SERVICE_URL", "http://monitoring-service:9006"),
		"etl":                   envOrDefault("ETL_SERVICE_URL", "http://etl:9007"),
		"scraper-service":       envOrDefault("ETL_SERVICE_URL", "http://scraper-service:9008"),
		"mobile-api":            envOrDefault("MOBILE_API_URL", "http://mobile-api:9009"),
		"legacy-django":         envOrDefault("LEGACY_DJANGO_URL", "http://legacy-django:9010"),
	}
}
```

**🚨 CRITICAL ISSUE**: Typo in search-service URL - `"http://service:9003"` should be `"http://search-service:9003"`
**🚨 CRITICAL ISSUE**: Duplicate environment variable for scraper-service - uses `ETL_SERVICE_URL` instead of `SCRAPER_SERVICE_URL`
**✅ GOOD**: Environment variable configuration for service URLs
**✅ GOOD**: Consistent naming convention

### **5. Reverse Proxy Function (Lines 52-56)**
```go
func makeReverseProxy(target string) *httputil.ReverseProxy {
	u, _ := url.Parse(target)
	return httputil.NewSingleHostReverseProxy(u)
}
```

**⚠️ ISSUE**: Ignores URL parsing errors with `_` - should handle errors
**✅ GOOD**: Proper reverse proxy creation

### **6. Status Handler (Lines 58-80)**
```go
func statusHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	client := &http.Client{Timeout: 2 * time.Second}
	statuses := map[string]any{}
	for name, base := range serviceMap() {
		url := strings.TrimRight(base, "/") + "/healthz"
		st := map[string]any{"status": "unknown", "target": base}
		resp, err := client.Get(url)
		if err != nil {
			st["error"] = err.Error()
			st["status"] = "error"
		} else {
			st["http"] = resp.StatusCode
			if resp.StatusCode == 200 {
				st["status"] = "ok"
			} else {
				st["status"] = "error"
			}
		}
		statuses[name] = st
	}
	json.NewEncoder(w).Encode(statuses)
}
```

**✅ GOOD**: Comprehensive service health checking
**✅ GOOD**: Proper error handling and status mapping
**✅ GOOD**: JSON response formatting
**⚠️ ISSUE**: No timeout handling for individual requests (only client timeout)

### **7. Gateway Handler (Lines 82-110)**
```go
func gatewayHandler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	// Map prefixes to service URLs (env-configurable; K8s DNS defaults)
	routes := map[string]string{
		"/api/auth/":          envOrDefault("AUTH_SERVICE_URL", "http://auth-service:9001"),
		"/api/policies/":      envOrDefault("POLICY_SERVICE_URL", "http://policy-service:9002"),
		"/api/committees/":    envOrDefault("POLICY_SERVICE_URL", "http://policy-service:9002"),
		"/api/debates/":       envOrDefault("POLICY_SERVICE_URL", "http://policy-service:9002"),
		"/api/votes/":         envOrDefault("POLICY_SERVICE_URL", "http://policy-service:9002"),
		"/api/search/":        envOrDefault("SEARCH_SERVICE_URL", "http://search-service:9003"),
		"/api/notifications/": envOrDefault("NOTIF_SERVICE_URL", "http://notification-service:9004"),
		"/api/config/":        envOrDefault("CONFIG_SERVICE_URL", "http://config-service:9005"),
		"/api/monitoring/":    envOrDefault("MONITORING_SERVICE_URL", "http://service:9006"),
		"/api/etl/":           envOrDefault("ETL_SERVICE_URL", "http://etl:9007"),
		"/api/scrapers/":      envOrDefault("SCRAPER_SERVICE_URL", "http://scraper-service:9008"),
		"/api/mobile/":        envOrDefault("MOBILE_API_URL", "http://mobile-api:9009"),
		"/api/legacy/":        envOrDefault("LEGACY_DJANGO_URL", "http://legacy-django:9010"),
	}
	if strings.HasPrefix(path, "/api/status") {
		statusHandler(w, r)
		return
	}
	for prefix, target := range routes {
		if strings.HasPrefix(path, prefix) {
			makeReverseProxy(target).ServeHTTP(w, r)
			return
		}
	}
	http.NotFound(w, r)
}
```

**🚨 CRITICAL ISSUE**: Multiple routes point to same service (committees, debates, votes all go to policy-service)
**🚨 CRITICAL ISSUE**: Typo in monitoring route - `"http://service:9006"` should be `"http://monitoring-service:9006"`
**🚨 CRITICAL ISSUE**: Missing environment variable for scraper service - uses `SCRAPER_SERVICE_URL` but not defined in serviceMap()
**✅ GOOD**: Proper route prefix matching
**✅ GOOD**: Status endpoint handling
**✅ GOOD**: 404 handling for unmatched routes

### **8. Main Function (Lines 112-121)**
```go
func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "9000"
	}
	http.HandleFunc("/healthz", healthz)
	http.HandleFunc("/readyz", readyz)
	http.Handle("/metrics", promhttp.Handler())
	http.HandleFunc("/", gatewayHandler)
	log.Printf("api-gateway listening on :%s", port)
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%s", port), nil))
}
```

**✅ GOOD**: Configurable port with default fallback
**✅ GOOD**: Proper endpoint registration
**✅ GOOD**: Prometheus metrics endpoint
**✅ GOOD**: Proper logging and error handling

---

## 🚨 **CRITICAL ISSUES IDENTIFIED**

### **1. Configuration Errors**
- **Search Service URL**: `"http://service:9003"` (missing "search-")
- **Monitoring Service URL**: `"http://service:9006"` (missing "monitoring-")
- **Scraper Service**: Uses `ETL_SERVICE_URL` instead of `SCRAPER_SERVICE_URL`

### **2. Service Routing Issues**
- **Multiple endpoints** route to same service (policy-service handles 4 different API paths)
- **Missing environment variables** for some services
- **Inconsistent naming** between serviceMap() and routes

### **3. Error Handling**
- **URL parsing errors** ignored in makeReverseProxy
- **No timeout handling** for individual health checks

---

## 🔧 **ARCHITECTURE COMPLIANCE ANALYSIS**

### **✅ COMPLIANT WITH MICROSERVICES PRINCIPLES**
- Service discovery via environment variables
- Proper routing and load balancing
- Health check aggregation
- Metrics collection
- Service isolation

### **❌ ARCHITECTURE VIOLATIONS**
- Multiple API paths route to same service (violates single responsibility)
- Hardcoded service URLs in fallbacks
- No circuit breaker or retry logic
- No authentication/authorization layer

---

## 📋 **RESOLUTION PLAN**

### **Immediate Fixes (High Priority)**
1. **Fix URL typos** in service mapping
2. **Correct environment variable** usage for scraper service
3. **Add missing environment variables** to serviceMap()
4. **Fix monitoring service URL**

### **Short-term Improvements (Medium Priority)**
1. **Implement proper error handling** for URL parsing
2. **Add timeout handling** for individual health checks
3. **Standardize service naming** conventions
4. **Add circuit breaker** pattern for service calls

### **Long-term Enhancements (Low Priority)**
1. **Add authentication middleware**
2. **Implement rate limiting**
3. **Add request/response logging**
4. **Implement service discovery** instead of hardcoded URLs

---

## 📊 **CODE QUALITY SCORE**

| Aspect | Score | Notes |
|--------|-------|-------|
| **Functionality** | 7/10 | Core routing works, but has configuration errors |
| **Error Handling** | 6/10 | Basic error handling, but ignores some errors |
| **Configuration** | 5/10 | Environment variable support, but has hardcoded fallbacks |
| **Architecture** | 8/10 | Good microservices principles, but some violations |
| **Code Style** | 9/10 | Clean, readable Go code |
| **Documentation** | 4/10 | No inline comments or README |

**Overall Score: 6.5/10**

---

## 🎯 **NEXT STEPS**

1. **Fix critical configuration errors** immediately
2. **Review service routing strategy** - should each API path have its own service?
3. **Implement proper error handling** for all edge cases
4. **Add comprehensive testing** for all routing scenarios
5. **Create service documentation** with API contracts

---

**🚨 This service has several critical configuration errors that must be fixed before it can function properly. The core architecture is sound, but implementation details need immediate attention.**
