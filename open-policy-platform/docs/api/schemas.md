# API Schemas (Examples)

Note: These are representative examples. See OpenAPI `dist/openapi.json` for the full machine-readable schema (export via `scripts/export-openapi.sh`).

## Auth
### POST /api/v1/auth/login (form)
Request: username, password
```json
{"username":"admin","password":"admin"}
```
Response 200:
```json
{"access_token":"<jwt>","refresh_token":"<jwt>","token_type":"bearer","expires_in":1800,"user":{"id":1,"username":"admin","email":"admin@openpolicy.com","full_name":"System Administrator","role":"admin","permissions":["read","write","admin","delete"]}}
```

### POST /api/v1/auth/register
```json
{"username":"user1","email":"u1@example.com","password":"pass","full_name":"User One","role":"user"}
```

### POST /api/v1/auth/refresh
```json
{"refresh_token":"<jwt>"}
```

### GET /api/v1/auth/me
Response 200 (example):
```json
{"id":1,"username":"admin","email":"admin@openpolicy.com","full_name":"System Administrator","role":"admin","permissions":["read","write","admin","delete"],"is_active":true}
```

### PUT /api/v1/auth/me
```json
{"email":"new@example.com","full_name":"New Name","password":"newpass","is_active":true}
```

### POST /api/v1/auth/change-password
```json
{"current_password":"old","new_password":"new"}
```

### POST /api/v1/auth/logout
```json
{}
```

### POST /api/v1/auth/forgot-password
```json
{"email":"user@example.com"}
```

### GET /api/v1/auth/users (admin)
Response 200:
```json
{"users":[{"id":1,"username":"admin","email":"admin@openpolicy.com","role":"admin","status":"active"}],"total_users":2,"active_users":2}
```

### GET /api/v1/auth/permissions
Response 200:
```json
{"permissions":["read","write"],"role":"user"}
```

## Health
### GET /api/v1/health
```json
{"status":"healthy","service":"Open Policy Platform API","version":"1.0.0","environment":"development","timestamp":"2024-08-08T00:00:00Z","uptime":"1:23:45"}
```

### GET /api/v1/health/detailed
```json
{"status":"healthy","database":"healthy","system_metrics":{"cpu_percent":12.3,"memory_percent":45.6,"disk_percent":70.1,"active_processes":200}}
```

### GET /api/v1/health/database
```json
{"database_size":"2 GB","table_count":123,"politician_records":50000}
```

### GET /api/v1/health/scrapers
```json
{"status":"warning","total_scrapers":150,"active_scrapers":120,"success_rate":68.5,"last_run":"2024-08-08T00:00:00Z"}
```

### GET /api/v1/health/system
```json
{"status":"healthy","cpu_usage":10.5,"memory_usage":52.1,"disk_usage":71.3}
```

### GET /api/v1/health/api
```json
{"status":"healthy","service":"Open Policy Platform API","version":"1.0.0","environment":"development"}
```

### GET /api/v1/health/comprehensive
```json
{"status":"warning","components":{"api":{},"database":{},"scrapers":{},"system":{}},"summary":{"total_components":4,"healthy_components":3,"warning_components":1,"unhealthy_components":0}}
```

### GET /api/v1/health/metrics
```json
{"system":{"cpu_percent":10},"database":{"connected":true,"politician_records":50000},"scrapers":{"success_rate":70.0}}
```

## Policies
### GET /api/v1/policies
```json
{"policies":[{"id":"1","title":"An Act ...","category":"health","status":"introduced"}],"total":100,"page":1,"limit":10}
```

### GET /api/v1/policies/{id}
```json
{"id":"1","title":"An Act ...","content":"...","category":"health","jurisdiction":"federal","status":"introduced","created_at":"...","updated_at":"..."}
```

### GET /api/v1/policies/search/advanced
Query: `q=health&category=...&jurisdiction=...&date_from=...&date_to=...&limit=50`
Response same shape as list

### GET /api/v1/policies/categories
```json
{"categories":["health","education"],"total_categories":2}
```

### GET /api/v1/policies/jurisdictions
```json
{"jurisdictions":["federal","ON"],"total_jurisdictions":2}
```

### GET /api/v1/policies/stats
```json
{"total_policies":10000,"recent_policies_30_days":123,"categories_distribution":{"health":50}}
```

### GET /api/v1/policies/{id}/analysis
```json
{"policy_id":1,"title":"An Act ...","category":"health","text_analysis":{"word_count":1234}}
```

### POST /api/v1/policies
```json
{"title":"New Bill","content":"...","category":"health","jurisdiction":"federal","status":"draft","tags":["tag1"]}
```

### PUT /api/v1/policies/{id}
```json
{"title":"Updated title","status":"passed"}
```

### DELETE /api/v1/policies/{id}
No body

## Scrapers
### GET /api/v1/scrapers
```json
{"scrapers":[{"name":"BC People","category":"Provincial","status":"available"}],"total_scrapers":150}
```

### GET /api/v1/scrapers/categories
```json
{"categories":{"Provincial":{"count":10,"active":8,"success_rate":80.0}}}
```

### POST /api/v1/scrapers/{id}/run
```json
{"scraper_id":"BC People","category":"Provincial","max_records":500,"force_run":false}
```

### GET /api/v1/scrapers/{id}/status
```json
{"scraper_id":"BC People","status":"success","last_run":"...","success_rate":95.0}
```

### GET /api/v1/scrapers/{id}/logs
```json
{"scraper_id":"BC People","logs":[{"log_file":"...","line":"..."}],"total_logs":50}
```

### POST /api/v1/scrapers/run/category/{category}
```json
{"category":"Provincial","max_records":500,"force_run":false}
```

### GET /api/v1/scrapers/performance
```json
{"total_scrapers":150,"active_scrapers":120,"success_rate":75.5,"category_performance":{"Provincial":{"total":50,"successful":45}}}
```

### Monitoring subset
- `GET /api/v1/scrapers/status`
- `GET /api/v1/scrapers/health`
- `GET /api/v1/scrapers/stats`
- `POST /api/v1/scrapers/run`
- `GET /api/v1/scrapers/logs`
- `GET /api/v1/scrapers/failures`
- `GET /api/v1/scrapers/database/status`

## Data
### GET /api/v1/data/tables
```json
[{"table_name":"core_politician","record_count":12345,"size_mb":512.5,"last_updated":"..."}]
```

### GET /api/v1/data/tables/{table}/records
```json
{"table_name":"core_politician","records":[["1","Jane Doe","..."], ["2","John Doe","..."]],"total_returned":100,"limit":100,"offset":0}
```

### POST /api/v1/data/export
```json
{"table_name":"core_politician","format":"json","limit":100}
```

### GET /api/v1/data/analysis/politicians
```json
{"analysis_type":"politicians","results":{"total_politicians":50000,"total_parties":6,"total_districts":338},"timestamp":"..."}
```

### GET /api/v1/data/analysis/bills
```json
{"analysis_type":"bills","results":{"total_bills":10000,"total_sessions":44,"total_classifications":20}}
```

### GET /api/v1/data/analysis/hansards
```json
{"analysis_type":"hansards","results":{"total_statements":1000000,"total_speakers":250,"total_dates":5000}}
```

### GET /api/v1/data/search
```json
{"query":"health","table_name":"bills_bill","results":[["1","..."]],"total_found":10,"limit":50}
```

### GET /api/v1/data/database/size
```json
{"total_size":"10 GB","politicians_size":"2 GB","bills_size":"5 GB","hansards_size":"3 GB"}
```

## Admin (admin only)
### GET /api/v1/admin/dashboard
```json
{"database":{"total_politicians":50000},"scrapers":{"total_scrapers":150,"success_rate":75.5},"system":{"cpu_usage":10.5}}
```

### GET /api/v1/admin/system/status
```json
{"database":"healthy","api":"healthy","scrapers":"active","system":{"cpu_percent":10.5}}
```

### POST /api/v1/admin/system/restart
```json
{"services":["api","database"],"force":false}
```

### GET /api/v1/admin/users
```json
{"users":[{"id":1,"username":"admin"}],"total_users":2,"active_users":2}
```

### POST /api/v1/admin/users
```json
{"username":"newadmin","email":"new@x.com","password":"pass","role":"admin","permissions":["admin"]}
```

### GET /api/v1/admin/logs
```json
{"logs":[{"file":"api.log","line":"..."}],"total_logs":100,"log_type":"all"}
```

### POST /api/v1/admin/backup
```json
{"include_database":true,"include_logs":true,"include_reports":true,"backup_name":"backup_20240808"}
```

### GET /api/v1/admin/backups
```json
{"backups":[{"name":"backup_db.sql","size":123456,"created_at":"...","type":"database"}],"total_backups":1,"total_size":123456}
```

### GET /api/v1/admin/performance
```json
{"system":{"cpu_percent":10.5,"memory_percent":45.1},"network":{"bytes_sent":123456}}
```

### GET /api/v1/admin/alerts
```json
{"alerts":[{"type":"warning","message":"Elevated CPU usage","timestamp":"..."}],"total_alerts":1}
```