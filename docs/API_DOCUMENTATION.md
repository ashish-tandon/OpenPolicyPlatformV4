# OpenPolicy Platform API Documentation

## Overview

The OpenPolicy Platform API provides programmatic access to Canadian parliamentary data including bills, representatives, votes, committees, and debates. The API follows RESTful principles and returns JSON responses.

## Base URL

```
Production: https://api.openpolicy.ca
Development: http://localhost/api
```

## Authentication

Most endpoints require authentication using Bearer tokens. Include your token in the Authorization header:

```
Authorization: Bearer YOUR_TOKEN_HERE
```

### Getting a Token

```bash
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "email": "user@example.com",
    "role": "user"
  }
}
```

## Endpoints

### Health Check

Check API health status.

```
GET /api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00Z",
  "checks": {
    "database": {"healthy": true, "response_time_ms": 5.2},
    "redis": {"healthy": true, "response_time_ms": 1.1},
    "services": {"healthy": true}
  }
}
```

### Authentication

#### Login

```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=email@example.com&password=password123
```

#### Get Current User

```
GET /api/v1/auth/me
Authorization: Bearer YOUR_TOKEN
```

#### Logout

```
POST /api/v1/auth/logout
Authorization: Bearer YOUR_TOKEN
```

### Bills

#### List Bills

Get a paginated list of parliamentary bills.

```
GET /api/v1/bills?page=1&per_page=20&status=First%20Reading&search=climate
```

Query Parameters:
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Items per page (default: 20, max: 100)
- `status` (string): Filter by bill status
- `search` (string): Search bills by number, title, or summary

Response:
```json
{
  "success": true,
  "bills": [
    {
      "id": 1,
      "bill_number": "C-5",
      "title": "An Act to amend the Bills of Exchange Act",
      "summary": "This enactment establishes September 30 as a federal statutory holiday",
      "sponsor": "Minister of Canadian Heritage",
      "status": "Committee",
      "parliament": 44,
      "session": 1,
      "introduction_date": "2021-12-13",
      "latest_activity_date": "2024-01-15"
    }
  ],
  "pagination": {
    "total": 150,
    "per_page": 20,
    "current_page": 1,
    "last_page": 8
  }
}
```

#### Get Bill Details

```
GET /api/v1/bills/{id}
```

Response includes full bill details and associated votes.

### Representatives

#### List Representatives

```
GET /api/v1/representatives?party=Liberal&province=Ontario&search=toronto
```

Query Parameters:
- `party` (string): Filter by political party
- `province` (string): Filter by province
- `search` (string): Search by name or constituency

Response:
```json
{
  "success": true,
  "representatives": [
    {
      "id": 1,
      "name": "Justin Trudeau",
      "email": "justin.trudeau@parl.gc.ca",
      "phone": "613-995-0253",
      "party": "Liberal",
      "constituency": "Papineau",
      "province": "Quebec",
      "photo_url": "https://www.parl.ca/members/photos/trudeau-justin.jpg",
      "bio": "Prime Minister of Canada",
      "active": true
    }
  ],
  "total": 338
}
```

### Votes

#### List Votes

```
GET /api/v1/votes?page=1&date_from=2024-01-01&date_to=2024-01-31
```

Query Parameters:
- `page` (integer): Page number
- `per_page` (integer): Items per page
- `date_from` (date): Filter votes from this date
- `date_to` (date): Filter votes until this date

### Committees

#### List Committees

```
GET /api/v1/committees
```

Response:
```json
{
  "success": true,
  "committees": [
    {
      "id": 1,
      "name": "Standing Committee on Finance",
      "abbreviation": "FINA",
      "type": "standing",
      "description": "Reviews and reports on finance matters",
      "active": true
    }
  ]
}
```

### Search

Search across all data types.

```
GET /api/v1/search?q=climate%20change
```

Response includes results from bills, representatives, and committees.

### Admin Endpoints

Admin endpoints require admin role authentication.

#### Dashboard Statistics

```
GET /api/v1/admin/dashboard
Authorization: Bearer ADMIN_TOKEN
```

Response:
```json
{
  "success": true,
  "data": {
    "totalPolicies": 245,
    "totalScrapers": 5,
    "activeScrapers": 3,
    "lastUpdate": "2024-01-20T10:30:00Z",
    "statistics": {
      "users": {"total": 1250, "recent": 45},
      "bills": {"total": 245, "recent": 12},
      "representatives": {"total": 338}
    }
  }
}
```

## Rate Limiting

API requests are rate limited to prevent abuse:
- Public endpoints: 100 requests per minute
- Authenticated endpoints: 300 requests per minute
- Auth endpoints: 5 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642680000
```

## Error Responses

Errors follow a consistent format:

```json
{
  "success": false,
  "message": "Detailed error message",
  "error": "ERRO | _CODE",
  "errors": {
    "field": ["Validation error message"]
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
- `422` - Validation Error
- `429` - Too Many Requests
- `500` - Internal Server Error
- `503` - Service Unavailable

## Pagination

Paginated endpoints return a consistent structure:

```json
{
  "data": [...],
  "pagination": {
    "total": 1000,
    "per_page": 20,
    "current_page": 1,
    "last_page": 50,
    "from": 1,
    "to": 20
  }
}
```

## Webhooks (Coming Soon)

Subscribe to real-time updates for bills, votes, and other parliamentary activities.

## SDKs

Official SDKs are available for:
- JavaScript/TypeScript
- Python
- PHP
- Ruby

## Support

- Email: api@openpolicy.ca
- Documentation: https://docs.openpolicy.ca
- Status Page: https://status.openpolicy.ca

## Changelog

### Version 1.0.0 (2024-01-20)
- Initial API release
- Authentication system
- Bills, representatives, votes, committees endpoints
- Search functionality
- Admin dashboard endpoints