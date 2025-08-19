# API Gateway Routes Documentation

## Overview

The OpenPolicyPlatform API Gateway serves as the central entry point for all API requests. It routes requests to the appropriate microservices based on URL paths.

## Gateway Information

- **Base URL**: `http://api-gateway:9000` (internal) or `http://openpolicy.local/api` (external)
- **Health Check**: `/health`
- **Service Status**: `/api/status`

## Available Routes

### Core API Services

#### Authentication Service
- **Route**: `/api/auth/*`
- **Service**: auth-service:9002
- **Description**: User authentication, authorization, and session management
- **Endpoints**:
  - `POST /api/auth/login` - User login
  - `POST /api/auth/logout` - User logout
  - `POST /api/auth/register` - User registration
  - `GET /api/auth/profile` - Get user profile
  - `POST /api/auth/refresh` - Refresh access token

#### Configuration Service
- **Route**: `/api/config/*`
- **Service**: config-service:9001
- **Description**: Application configuration management
- **Endpoints**:
  - `GET /api/config/settings` - Get application settings
  - `GET /api/config/features` - Get feature flags
  - `PUT /api/config/settings` - Update settings (admin only)

#### Policy Service
- **Route**: `/api/policies/*`
- **Service**: policy-service:9003
- **Description**: Policy document management
- **Endpoints**:
  - `GET /api/policies` - List all policies
  - `GET /api/policies/{id}` - Get policy details
  - `POST /api/policies` - Create new policy
  - `PUT /api/policies/{id}` - Update policy
  - `DELETE /api/policies/{id}` - Delete policy

#### Notification Service
- **Route**: `/api/notifications/*`
- **Service**: notification-service:9004
- **Description**: Notification delivery and management
- **Endpoints**:
  - `GET /api/notifications` - Get user notifications
  - `POST /api/notifications/send` - Send notification
  - `PUT /api/notifications/{id}/read` - Mark as read
  - `DELETE /api/notifications/{id}` - Delete notification

### Business Logic Services

#### Analytics Service
- **Route**: `/api/analytics/*`
- **Service**: analytics-service:9005
- **Description**: Analytics and metrics tracking
- **Endpoints**:
  - `GET /api/analytics/dashboard` - Get dashboard metrics
  - `POST /api/analytics/events` - Track event
  - `GET /api/analytics/reports` - Get analytics reports

#### Monitoring Service
- **Route**: `/api/monitoring/*`
- **Service**: monitoring-service:9006
- **Description**: System monitoring and health checks
- **Endpoints**:
  - `GET /api/monitoring/health` - System health status
  - `GET /api/monitoring/metrics` - System metrics
  - `GET /api/monitoring/services` - Service status

#### ETL Service
- **Route**: `/api/etl/*`
- **Service**: etl-service:9007
- **Description**: Data extraction, transformation, and loading
- **Endpoints**:
  - `GET /api/etl/jobs` - List ETL jobs
  - `POST /api/etl/jobs` - Create ETL job
  - `GET /api/etl/jobs/{id}/status` - Get job status

#### Scraper Service
- **Route**: `/api/scrapers/*`
- **Service**: scraper-service:9008
- **Description**: Web scraping and data collection
- **Endpoints**:
  - `GET /api/scrapers` - List scrapers
  - `POST /api/scrapers/run` - Run scraper
  - `GET /api/scrapers/{id}/status` - Get scraper status

#### Search Service
- **Route**: `/api/search/*`
- **Service**: search-service:9009
- **Description**: Full-text search functionality
- **Endpoints**:
  - `GET /api/search` - Search all content
  - `GET /api/search/bills` - Search bills
  - `GET /api/search/politicians` - Search politicians
  - `GET /api/search/committees` - Search committees

#### Dashboard Service
- **Route**: `/api/dashboard/*`
- **Service**: dashboard-service:9010
- **Description**: Dashboard data and widgets
- **Endpoints**:
  - `GET /api/dashboard/stats` - Get dashboard statistics
  - `GET /api/dashboard/widgets` - Get dashboard widgets
  - `POST /api/dashboard/widgets` - Create custom widget

#### Files Service
- **Route**: `/api/files/*`
- **Service**: files-service:9011
- **Description**: File upload and management
- **Endpoints**:
  - `GET /api/files` - List files
  - `POST /api/files/upload` - Upload file
  - `GET /api/files/{id}` - Download file
  - `DELETE /api/files/{id}` - Delete file

#### Reporting Service
- **Route**: `/api/reports/*`
- **Service**: reporting-service:9012
- **Description**: Report generation and management
- **Endpoints**:
  - `GET /api/reports` - List reports
  - `POST /api/reports/generate` - Generate report
  - `GET /api/reports/{id}` - Get report
  - `GET /api/reports/{id}/download` - Download report

#### Workflow Service
- **Route**: `/api/workflows/*`
- **Service**: workflow-service:9013
- **Description**: Workflow automation and management
- **Endpoints**:
  - `GET /api/workflows` - List workflows
  - `POST /api/workflows` - Create workflow
  - `PUT /api/workflows/{id}` - Update workflow
  - `POST /api/workflows/{id}/execute` - Execute workflow

#### Integration Service
- **Route**: `/api/integrations/*`
- **Service**: integration-service:9014
- **Description**: Third-party integrations
- **Endpoints**:
  - `GET /api/integrations` - List integrations
  - `POST /api/integrations/connect` - Connect integration
  - `DELETE /api/integrations/{id}` - Disconnect integration

#### Data Management Service
- **Route**: `/api/data/*`
- **Service**: data-management-service:9015
- **Description**: Data import/export and management
- **Endpoints**:
  - `GET /api/data/exports` - List exports
  - `POST /api/data/export` - Export data
  - `POST /api/data/import` - Import data

### Data Processing Services

#### Representatives Service
- **Route**: `/api/representatives/*`
- **Service**: representatives-service:9016
- **Description**: Political representatives data
- **Endpoints**:
  - `GET /api/representatives` - List representatives
  - `GET /api/representatives/{id}` - Get representative details
  - `GET /api/representatives/{id}/votes` - Get voting record

#### Plotly Service
- **Route**: `/api/plotly/*`
- **Service**: plotly-service:9017
- **Description**: Data visualization with Plotly
- **Endpoints**:
  - `POST /api/plotly/charts` - Generate chart
  - `GET /api/plotly/templates` - Get chart templates

#### Committees Service
- **Route**: `/api/committees/*`
- **Service**: committees-service:9018
- **Description**: Parliamentary committees data
- **Endpoints**:
  - `GET /api/committees` - List committees
  - `GET /api/committees/{id}` - Get committee details
  - `GET /api/committees/{id}/members` - Get committee members

#### Debates Service
- **Route**: `/api/debates/*`
- **Service**: debates-service:9019
- **Description**: Parliamentary debates and hansard
- **Endpoints**:
  - `GET /api/debates` - List debates
  - `GET /api/debates/{id}` - Get debate details
  - `GET /api/debates/{id}/speeches` - Get speeches

#### Votes Service
- **Route**: `/api/votes/*`
- **Service**: votes-service:9020
- **Description**: Parliamentary voting data
- **Endpoints**:
  - `GET /api/votes` - List votes
  - `GET /api/votes/{id}` - Get vote details
  - `GET /api/votes/{id}/results` - Get voting results

#### Mobile API
- **Route**: `/api/mobile/*`
- **Service**: mobile-api:9021
- **Description**: Mobile app specific endpoints
- **Endpoints**:
  - `GET /api/mobile/feed` - Get mobile feed
  - `GET /api/mobile/notifications` - Get push notifications

### Legacy Services

#### Legacy Django
- **Route**: `/api/legacy/*`
- **Service**: legacy-django:9022
- **Description**: Legacy Django application endpoints

#### Docker Monitor
- **Route**: `/api/monitor/*`
- **Service**: docker-monitor:9023
- **Description**: Docker container monitoring
- **Endpoints**:
  - `GET /api/monitor/containers` - List containers
  - `GET /api/monitor/stats` - Get container stats

## Common Headers

All API requests should include:

```
Content-Type: application/json
Accept: application/json
```

Authenticated requests should include:

```
Authorization: Bearer <token>
```

## Error Responses

All services follow a standard error response format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {}
  }
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

## Rate Limiting

API endpoints are rate limited:
- Anonymous requests: 100 requests per hour
- Authenticated requests: 1000 requests per hour
- Admin requests: 10000 requests per hour

## Health Checks

Every service exposes standard health check endpoints:
- `/health` - Basic health check
- `/healthz` - Kubernetes liveness probe
- `/readyz` - Kubernetes readiness probe
- `/testedz` - Test status
- `/compliancez` - Compliance status