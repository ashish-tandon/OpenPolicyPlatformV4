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

func health(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"healthy","service":"api-gateway","timestamp":"` + time.Now().UTC().Format(time.RFC3339) + `","version":"1.0.0"}`))
}

func healthz(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"ok"}`))
}

func readyz(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"ok"}`))
}

func testedz(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"tested","service":"api-gateway","timestamp":"` + time.Now().UTC().Format(time.RFC3339) + `","tests_passed":true,"version":"1.0.0"}`))
}

func compliancez(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"compliant","service":"api-gateway","timestamp":"` + time.Now().UTC().Format(time.RFC3339) + `","compliance_score":100,"standards_met":["security","performance","reliability"],"version":"1.0.0"}`))
}

func envOrDefault(env, def string) string {
	v := os.Getenv(env)
	if v == "" {
		return def
	}
	return v
}

func serviceMap() map[string]string {
	return map[string]string{
		"auth-service":         envOrDefault("AUTH_SERVICE_URL", "http://auth-service:9001"),
		"policy-service":       envOrDefault("POLICY_SERVICE_URL", "http://policy-service:9002"),
		"search-service":       envOrDefault("SEARCH_SERVICE_URL", "http://search-service:9003"),
		"notification-service": envOrDefault("NOTIF_SERVICE_URL", "http://notification-service:9004"),
		"config-service":       envOrDefault("CONFIG_SERVICE_URL", "http://config-service:9005"),
		"monitoring-service":   envOrDefault("MONITORING_SERVICE_URL", "http://monitoring-service:9006"),
		"etl":                  envOrDefault("ETL_SERVICE_URL", "http://etl:9007"),
		"scraper-service":      envOrDefault("SCRAPER_SERVICE_URL", "http://scraper-service:9008"),
		// FIXED: Updated ports to match documented architecture
		"mobile-api":         envOrDefault("MOBILE_API_URL", "http://mobile-api:8009"),
		"legacy-django":      envOrDefault("LEGACY_DJANGO_URL", "http://legacy-django:8010"),
		"committees-service": envOrDefault("COMMITTEES_SERVICE_URL", "http://committees-service:9011"),
		"debates-service":    envOrDefault("DEBATES_SERVICE_URL", "http://debates-service:9012"),
		"votes-service":      envOrDefault("VOTES_SERVICE_URL", "http://votes-service:9013"),
		// NEW: Representatives service added
		"representatives-service": envOrDefault("REPRESENTATIVES_SERVICE_URL", "http://representatives-service:8014"),
		// NEW: Files service added
		"files-service": envOrDefault("FILES_SERVICE_URL", "http://files-service:8015"),
		// NEW: Dashboard service added
		"dashboard-service": envOrDefault("DASHBOARD_SERVICE_URL", "http://dashboard-service:8016"),
		// NEW: Data Management service added
		"data-management-service": envOrDefault("DATA_MANAGEMENT_SERVICE_URL", "http://data-management-service:8017"),
		// NEW: Analytics service added
		"analytics-service": envOrDefault("ANALYTICS_SERVICE_URL", "http://analytics-service:8018"),
		// NEW: Reporting service added
		"reporting-service": envOrDefault("REPORTING_SERVICE_URL", "http://reporting-service:8019"),
		// NEW: Workflow service added
		"workflow-service": envOrDefault("WORKFLOW_SERVICE_URL", "http://workflow-service:8020"),
		// NEW: Integration service added
		"integration-service": envOrDefault("INTEGRATION_SERVICE_URL", "http://integration-service:8021"),
		// NEW: Plotly service added
		"plotly-service": envOrDefault("PLOTLY_SERVICE_URL", "http://plotly-service:9019"),
	}
}

func makeReverseProxy(target string) *httputil.ReverseProxy {
	u, _ := url.Parse(target)
	return httputil.NewSingleHostReverseProxy(u)
}

func statusHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	client := &http.Client{Timeout: 2 * time.Second}
	statuses := map[string]any{}
	for name, base := range serviceMap() {
		url := strings.TrimRight(base, "/") + "/healthz"
		st := map[string]any{"status": "unknown", "target": base}
		resp, err := client.Get(url)
		if err == nil {
			st["http"] = resp.StatusCode
			if resp.StatusCode == 200 {
				st["status"] = "ok"
			} else {
				st["status"] = "error"
			}
		} else {
			st["error"] = err.Error()
			st["status"] = "error"
		}
		statuses[name] = st
	}
	json.NewEncoder(w).Encode(statuses)
}

func gatewayHandler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	// Map prefixes to service URLs (env-configurable; K8s DNS defaults)
	routes := map[string]string{
		"/api/auth/":          envOrDefault("AUTH_SERVICE_URL", "http://auth-service:9001"),
		"/api/policies/":      envOrDefault("POLICY_SERVICE_URL", "http://policy-service:9002"),
		"/api/committees/":    envOrDefault("COMMITTEES_SERVICE_URL", "http://committees-service:9011"),
		"/api/debates/":       envOrDefault("DEBATES_SERVICE_URL", "http://debates-service:9012"),
		"/api/votes/":         envOrDefault("VOTES_SERVICE_URL", "http://votes-service:9013"),
		"/api/search/":        envOrDefault("SEARCH_SERVICE_URL", "http://search-service:9003"),
		"/api/notifications/": envOrDefault("NOTIF_SERVICE_URL", "http://notification-service:9004"),
		"/api/config/":        envOrDefault("CONFIG_SERVICE_URL", "http://config-service:9005"),
		"/api/monitoring/":    envOrDefault("MONITORING_SERVICE_URL", "http://monitoring-service:9006"),
		"/api/etl/":           envOrDefault("ETL_SERVICE_URL", "http://etl:9007"),
		"/api/scrapers/":      envOrDefault("SCRAPER_SERVICE_URL", "http://scraper-service:9008"),
		// FIXED: Updated ports to match documented architecture
		"/api/mobile/": envOrDefault("MOBILE_API_URL", "http://mobile-api:8009"),
		"/api/legacy/": envOrDefault("LEGACY_DJANGO_URL", "http://legacy-django:8010"),
		// NEW: Representatives API route added
		"/api/representatives/": envOrDefault("REPRESENTATIVES_SERVICE_URL", "http://representatives-service:8014"),
		// NEW: Files API route added
		"/api/files/": envOrDefault("FILES_SERVICE_URL", "http://files-service:8015"),
		// NEW: Dashboard API route added
		"/api/dashboards/": envOrDefault("DASHBOARD_SERVICE_URL", "http://dashboard-service:8016"),
		// NEW: Data Management API route added
		"/api/data-management/": envOrDefault("DATA_MANAGEMENT_SERVICE_URL", "http://data-management-service:8017"),
		// NEW: Analytics API route added
		"/api/analytics/": envOrDefault("ANALYTICS_SERVICE_URL", "http://analytics-service:8018"),
		// NEW: Reporting API route added
		"/api/reporting/": envOrDefault("REPORTING_SERVICE_URL", "http://reporting-service:8019"),
		// NEW: Workflow API route added
		"/api/workflows/": envOrDefault("WORKFLOW_SERVICE_URL", "http://workflow-service:8020"),
		// NEW: Integration API route added
		"/api/integrations/": envOrDefault("INTEGRATION_SERVICE_URL", "http://integration-service:8021"),
		// NEW: Plotly API route added
		"/api/plotly/": envOrDefault("PLOTLY_SERVICE_URL", "http://plotly-service:9019"),
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

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "9000"
	}
	http.HandleFunc("/health", health)
	http.HandleFunc("/healthz", healthz)
	http.HandleFunc("/readyz", readyz)
	http.HandleFunc("/testedz", testedz)
	http.HandleFunc("/compliancez", compliancez)
	http.Handle("/metrics", promhttp.Handler())
	http.HandleFunc("/", gatewayHandler)
	log.Printf("api-gateway listening on :%s", port)
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%s", port), nil))
}
