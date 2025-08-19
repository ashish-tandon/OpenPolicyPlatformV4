# 📊 COMPLETE SERVICES INVENTORY - OpenPolicyPlatformV4

## 🎯 Comprehensive Service Count: 40+ Components

### 📁 Services in `/open-policy-platform/services/` (27 services)
1. **api-gateway** - Central API gateway (Port 9000)
2. **auth-service** - Authentication service (Port 9001/9002)
3. **config-service** - Configuration management (Port 9001/9005)
4. **policy-service** - Policy management (Port 9002/9003)
5. **notification-service** - Notifications (Port 9004)
6. **monitoring-service** - System monitoring (Port 9006)
7. **etl-service** - Data pipeline (Port 9007)
8. **scraper-service** - Data collection (Port 9008)
9. **search-service** - Full-text search (Port 9003/9009)
10. **dashboard-service** - User dashboards (Port 9010)
11. **files-service** - File management (Port 9011)
12. **reporting-service** - Report generation (Port 9012)
13. **workflow-service** - Business automation (Port 9013)
14. **integration-service** - Third-party integrations (Port 9014)
15. **data-management-service** - Data governance (Port 9015)
16. **representatives-service** - User management (Port 9016)
17. **plotly-service** - Data visualization (Port 9017)
18. **mobile-api** - Mobile backend (Port 9018)
19. **legacy-django** - Legacy application (Port 9019)
20. **committees-service** - Committee management
21. **debates-service** - Debates management
22. **votes-service** - Voting management
23. **analytics-service** - Analytics engine (Port 9005)
24. **etl** - Alternative ETL service
25. **mcp-service** - MCP service
26. **docker-monitor** - Container monitoring
27. **web** - Web frontend service

### 🗂️ Core Infrastructure Services (12 services)
28. **postgres** - Main database (Port 5432)
29. **postgres-test** - Test database (Port 5433)
30. **redis** - Cache & message broker (Port 6379)
31. **elasticsearch** - Log storage (Port 9200)
32. **logstash** - Log processing (Ports 5044, 9600, 5001)
33. **kibana** - Log visualization (Port 5601)
34. **fluentd** - Log aggregation (Port 24224)
35. **prometheus** - Metrics collection (Port 9090)
36. **grafana** - Monitoring dashboards (Port 3001)
37. **nginx/gateway** - Reverse proxy (Port 80)
38. **api** - Main backend API (Port 8000)
39. **web** - React frontend (Port 3000/5173)

### 🔄 Background Processing Services (5 services)
40. **celery-worker** - Background tasks
41. **celery-beat** - Task scheduler
42. **flower** - Celery monitoring (Port 5555)
43. **scraper-runner** - Background scraper execution
44. **celery** - General Celery service

### 📱 Mobile & Frontend Components (4 apps)
- **open-policy-app** - React Native mobile app
- **open-policy-main** - Main mobile interface
- **open-policy-web** - Web interface
- **admin-open-policy** - Admin panel

### 🕷️ Scraper Systems (3 major systems)
- **scrapers-ca** - Canadian scrapers (109+ municipalities)
- **openparliament** - Parliamentary scrapers
- **civic-scraper** - Civic data scrapers

### 🏗️ Additional Components
- **OpenPolicyAshBack** - Comprehensive backend system
- **OpenPolicyMerge** - Unified platform implementation

## 📋 TOTAL COUNT: 45+ Distinct Services/Components

## 🎯 Mapping to 6-Layer Architecture

### Layer 1: openpolicy-infrastructure (15 services)
- auth-service
- monitoring-service
- config-service
- api-gateway
- nginx/gateway
- prometheus
- grafana
- elasticsearch
- logstash
- kibana
- fluentd
- redis
- postgres
- celery-worker
- celery-beat

### Layer 2: openpolicy-data (8 services)
- etl-service
- etl
- data-management-service
- scraper-service
- scraper-runner
- policy-service
- search-service
- files-service

### Layer 3: openpolicy-business (10 services)
- committees-service
- representatives-service
- votes-service
- debates-service
- analytics-service
- reporting-service
- dashboard-service
- plotly-service
- workflow-service
- integration-service

### Layer 4: openpolicy-frontend (3 services)
- web
- mobile-api
- api (main backend)

### Layer 5: openpolicy-legacy (3 services)
- legacy-django
- mcp-service
- docker-monitor

### Layer 6: openpolicy-orchestration
- CI/CD pipelines
- Deployment configurations
- Infrastructure as Code
- Monitoring rules