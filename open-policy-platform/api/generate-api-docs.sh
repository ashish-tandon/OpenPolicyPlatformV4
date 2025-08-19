#!/bin/bash

# API Documentation Generator Script
# Generates comprehensive API documentation using OpenAPI/Swagger

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

# Create API documentation structure
setup_api_docs() {
    log "Setting up API documentation..."
    
    mkdir -p api-docs/{endpoints,schemas,examples,postman}
    
    # Create OpenAPI specification
    cat > api-docs/openapi.yaml << 'EOF'
openapi: 3.0.0
info:
  title: OpenPolicy Platform API
  version: 4.0.0
  description: |
    # OpenPolicy Platform API
    
    Welcome to the OpenPolicy Platform API documentation. This API provides comprehensive access to government policy data, legislative information, and political analytics.
    
    ## Authentication
    
    The API uses JWT bearer tokens for authentication. To get started:
    
    1. Register for an API account
    2. Obtain your API credentials
    3. Exchange credentials for a JWT token
    4. Include the token in the Authorization header
    
    ```
    Authorization: Bearer <your-jwt-token>
    ```
    
    ## Rate Limiting
    
    - **Free tier**: 100 requests per hour
    - **Basic tier**: 1,000 requests per hour
    - **Premium tier**: 10,000 requests per hour
    - **Enterprise**: Unlimited
    
    ## Versioning
    
    The API uses URL versioning. Current version is v1.
    
  contact:
    name: API Support Team
    email: api-support@openpolicy.com
    url: https://support.openpolicy.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.openpolicy.com/v1
    description: Production server
  - url: https://staging-api.openpolicy.com/v1
    description: Staging server
  - url: http://localhost:9000/api/v1
    description: Development server

tags:
  - name: Authentication
    description: User authentication and authorization
  - name: Policies
    description: Policy management and retrieval
  - name: Bills
    description: Legislative bills and proposals
  - name: Representatives
    description: Elected representatives information
  - name: Committees
    description: Committee information and membership
  - name: Votes
    description: Voting records and results
  - name: Search
    description: Advanced search functionality
  - name: Analytics
    description: Data analytics and insights
  - name: Notifications
    description: Real-time notifications
  - name: Admin
    description: Administrative operations

paths:
  /auth/register:
    post:
      tags: [Authentication]
      summary: Register a new user
      operationId: registerUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password, name]
              properties:
                email:
                  type: string
                  format: email
                  example: user@example.com
                password:
                  type: string
                  format: password
                  minLength: 8
                  example: SecurePass123!
                name:
                  type: string
                  example: John Doe
                organization:
                  type: string
                  example: ACME Corp
      responses:
        '201':
          description: User registered successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: string
                    format: uuid
                  email:
                    type: string
                  name:
                    type: string
                  created_at:
                    type: string
                    format: date-time
        '400':
          $ref: '#/components/responses/BadRequest'
        '409':
          $ref: '#/components/responses/Conflict'

  /auth/login:
    post:
      tags: [Authentication]
      summary: Login user
      operationId: loginUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password]
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  format: password
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  token:
                    type: string
                    description: JWT access token
                  refresh_token:
                    type: string
                    description: Refresh token
                  expires_in:
                    type: integer
                    description: Token expiry time in seconds
                  user:
                    $ref: '#/components/schemas/User'
        '401':
          $ref: '#/components/responses/Unauthorized'

  /policies:
    get:
      tags: [Policies]
      summary: List all policies
      operationId: listPolicies
      security:
        - bearerAuth: []
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
            minimum: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
            minimum: 1
            maximum: 100
        - name: category
          in: query
          schema:
            type: string
            enum: [healthcare, education, environment, economy, defense]
        - name: status
          in: query
          schema:
            type: string
            enum: [draft, active, archived]
        - name: search
          in: query
          schema:
            type: string
        - name: sort
          in: query
          schema:
            type: string
            enum: [created_at, updated_at, title]
            default: created_at
        - name: order
          in: query
          schema:
            type: string
            enum: [asc, desc]
            default: desc
      responses:
        '200':
          description: List of policies
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Policy'
                  pagination:
                    $ref: '#/components/schemas/Pagination'
        '401':
          $ref: '#/components/responses/Unauthorized'

    post:
      tags: [Policies]
      summary: Create a new policy
      operationId: createPolicy
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PolicyInput'
      responses:
        '201':
          description: Policy created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Policy'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'

  /policies/{id}:
    get:
      tags: [Policies]
      summary: Get policy by ID
      operationId: getPolicy
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Policy details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PolicyDetail'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'

  /bills:
    get:
      tags: [Bills]
      summary: List all bills
      operationId: listBills
      security:
        - bearerAuth: []
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/LimitParam'
        - name: status
          in: query
          schema:
            type: string
            enum: [introduced, committee, passed, failed, enacted]
        - name: sponsor
          in: query
          schema:
            type: string
        - name: committee
          in: query
          schema:
            type: string
      responses:
        '200':
          description: List of bills
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Bill'
                  pagination:
                    $ref: '#/components/schemas/Pagination'

  /representatives:
    get:
      tags: [Representatives]
      summary: List all representatives
      operationId: listRepresentatives
      security:
        - bearerAuth: []
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/LimitParam'
        - name: party
          in: query
          schema:
            type: string
        - name: state
          in: query
          schema:
            type: string
        - name: chamber
          in: query
          schema:
            type: string
            enum: [house, senate]
      responses:
        '200':
          description: List of representatives
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Representative'
                  pagination:
                    $ref: '#/components/schemas/Pagination'

  /search:
    get:
      tags: [Search]
      summary: Search across all resources
      operationId: globalSearch
      security:
        - bearerAuth: []
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
            minLength: 3
          description: Search query
        - name: type
          in: query
          schema:
            type: array
            items:
              type: string
              enum: [policy, bill, representative, committee, vote]
          style: form
          explode: true
        - name: date_from
          in: query
          schema:
            type: string
            format: date
        - name: date_to
          in: query
          schema:
            type: string
            format: date
      responses:
        '200':
          description: Search results
          content:
            application/json:
              schema:
                type: object
                properties:
                  results:
                    type: array
                    items:
                      $ref: '#/components/schemas/SearchResult'
                  facets:
                    type: object
                  total:
                    type: integer

  /analytics/summary:
    get:
      tags: [Analytics]
      summary: Get platform analytics summary
      operationId: getAnalyticsSummary
      security:
        - bearerAuth: []
      parameters:
        - name: period
          in: query
          schema:
            type: string
            enum: [day, week, month, year]
            default: month
      responses:
        '200':
          description: Analytics summary
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AnalyticsSummary'

  /notifications/subscribe:
    post:
      tags: [Notifications]
      summary: Subscribe to notifications
      operationId: subscribeNotifications
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                topics:
                  type: array
                  items:
                    type: string
                    enum: [policies, bills, votes, committees]
                channels:
                  type: array
                  items:
                    type: string
                    enum: [email, sms, push, webhook]
                webhook_url:
                  type: string
                  format: uri
      responses:
        '200':
          description: Subscription created
          content:
            application/json:
              schema:
                type: object
                properties:
                  subscription_id:
                    type: string
                  topics:
                    type: array
                    items:
                      type: string
                  channels:
                    type: array
                    items:
                      type: string

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT token obtained from /auth/login endpoint
    
    apiKey:
      type: apiKey
      in: header
      name: X-API-Key
      description: API key for service-to-service communication

  parameters:
    PageParam:
      name: page
      in: query
      schema:
        type: integer
        default: 1
        minimum: 1
      description: Page number for pagination
    
    LimitParam:
      name: limit
      in: query
      schema:
        type: integer
        default: 20
        minimum: 1
        maximum: 100
      description: Number of items per page

  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        name:
          type: string
        role:
          type: string
          enum: [user, admin, moderator]
        organization:
          type: string
        created_at:
          type: string
          format: date-time
        last_login:
          type: string
          format: date-time

    Policy:
      type: object
      properties:
        id:
          type: string
          format: uuid
        title:
          type: string
        description:
          type: string
        category:
          type: string
        status:
          type: string
          enum: [draft, active, archived]
        tags:
          type: array
          items:
            type: string
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    PolicyDetail:
      allOf:
        - $ref: '#/components/schemas/Policy'
        - type: object
          properties:
            content:
              type: string
            attachments:
              type: array
              items:
                $ref: '#/components/schemas/Attachment'
            related_bills:
              type: array
              items:
                $ref: '#/components/schemas/Bill'
            impact_analysis:
              type: object
            history:
              type: array
              items:
                $ref: '#/components/schemas/PolicyHistory'

    PolicyInput:
      type: object
      required: [title, description, category]
      properties:
        title:
          type: string
          minLength: 10
          maxLength: 200
        description:
          type: string
          minLength: 50
        category:
          type: string
        content:
          type: string
        tags:
          type: array
          items:
            type: string

    Bill:
      type: object
      properties:
        id:
          type: string
          format: uuid
        number:
          type: string
        title:
          type: string
        summary:
          type: string
        sponsor:
          $ref: '#/components/schemas/Representative'
        cosponsors:
          type: array
          items:
            $ref: '#/components/schemas/Representative'
        status:
          type: string
        introduced_date:
          type: string
          format: date
        committees:
          type: array
          items:
            type: string
        last_action:
          type: object
          properties:
            date:
              type: string
              format: date
            description:
              type: string

    Representative:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        title:
          type: string
        party:
          type: string
        state:
          type: string
        district:
          type: string
        chamber:
          type: string
          enum: [house, senate]
        photo_url:
          type: string
          format: uri
        contact:
          type: object
          properties:
            email:
              type: string
              format: email
            phone:
              type: string
            website:
              type: string
              format: uri
            office_address:
              type: string

    SearchResult:
      type: object
      properties:
        type:
          type: string
        id:
          type: string
        title:
          type: string
        snippet:
          type: string
        relevance_score:
          type: number
          format: float
        highlight:
          type: object
        metadata:
          type: object

    AnalyticsSummary:
      type: object
      properties:
        period:
          type: string
        metrics:
          type: object
          properties:
            total_policies:
              type: integer
            total_bills:
              type: integer
            total_votes:
              type: integer
            active_users:
              type: integer
        trends:
          type: array
          items:
            type: object
            properties:
              date:
                type: string
                format: date
              values:
                type: object
        top_categories:
          type: array
          items:
            type: object
            properties:
              category:
                type: string
              count:
                type: integer

    Attachment:
      type: object
      properties:
        id:
          type: string
        filename:
          type: string
        mime_type:
          type: string
        size:
          type: integer
        url:
          type: string
          format: uri

    PolicyHistory:
      type: object
      properties:
        version:
          type: integer
        timestamp:
          type: string
          format: date-time
        author:
          $ref: '#/components/schemas/User'
        changes:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              old_value:
                type: string
              new_value:
                type: string

    Pagination:
      type: object
      properties:
        page:
          type: integer
        limit:
          type: integer
        total:
          type: integer
        total_pages:
          type: integer
        has_next:
          type: boolean
        has_prev:
          type: boolean

    Error:
      type: object
      properties:
        code:
          type: string
        message:
          type: string
        details:
          type: object
        timestamp:
          type: string
          format: date-time
        request_id:
          type: string

  responses:
    BadRequest:
      description: Bad request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: BAD_REQUEST
            message: Invalid request parameters
            details:
              field: email
              reason: Invalid email format

    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: UNAUTHORIZED
            message: Authentication required

    Forbidden:
      description: Forbidden
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: FORBIDDEN
            message: Insufficient permissions

    NotFound:
      description: Not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: NOT_FOUND
            message: Resource not found

    Conflict:
      description: Conflict
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: CONFLICT
            message: Resource already exists

    RateLimitExceeded:
      description: Rate limit exceeded
      headers:
        X-RateLimit-Limit:
          schema:
            type: integer
          description: Request limit per hour
        X-RateLimit-Remaining:
          schema:
            type: integer
          description: Remaining requests
        X-RateLimit-Reset:
          schema:
            type: integer
          description: Reset time (Unix timestamp)
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            code: RATE_LIMIT_EXCEEDED
            message: Too many requests

  examples:
    PolicyExample:
      value:
        id: 550e8400-e29b-41d4-a716-446655440000
        title: Clean Energy Investment Act
        description: A comprehensive policy to promote renewable energy investments
        category: environment
        status: active
        tags: [renewable, energy, climate]
        created_at: 2024-01-15T10:30:00Z
        updated_at: 2024-01-20T14:45:00Z
EOF

    # Generate API documentation HTML
    log "Generating API documentation HTML..."
    
    cat > api-docs/generate-html.js << 'EOF'
const fs = require('fs');
const path = require('path');
const SwaggerUI = require('swagger-ui-dist');

// Copy Swagger UI assets
const swaggerUiPath = SwaggerUI.absolutePath();
const targetPath = path.join(__dirname, 'html');

// Create directory
if (!fs.existsSync(targetPath)) {
    fs.mkdirSync(targetPath, { recursive: true });
}

// Copy files
const files = fs.readdirSync(swaggerUiPath);
files.forEach(file => {
    if (file.endsWith('.html') || file.endsWith('.js') || file.endsWith('.css')) {
        fs.copyFileSync(
            path.join(swaggerUiPath, file),
            path.join(targetPath, file)
        );
    }
});

// Create custom index.html
const indexHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>OpenPolicy Platform API Documentation</title>
    <link rel="stylesheet" type="text/css" href="./swagger-ui.css" />
    <link rel="icon" type="image/png" href="./favicon-32x32.png" sizes="32x32" />
    <link rel="icon" type="image/png" href="./favicon-16x16.png" sizes="16x16" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin: 0;
            background: #fafafa;
        }
        .topbar-wrapper img {
            content: url('https://openpolicy.com/logo.png');
        }
        .swagger-ui .topbar {
            background-color: #1976d2;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="./swagger-ui-bundle.js"></script>
    <script src="./swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            window.ui = SwaggerUIBundle({
                url: "../openapi.yaml",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                persistAuthorization: true,
                tryItOutEnabled: true,
                requestSnippetsEnabled: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                validatorUrl: null
            });
        };
    </script>
</body>
</html>
`;

fs.writeFileSync(path.join(targetPath, 'index.html'), indexHtml);

console.log('API documentation generated successfully!');
console.log(`Open ${path.join(targetPath, 'index.html')} in a browser to view.`);
EOF

    # Create Postman collection
    log "Creating Postman collection..."
    
    cat > api-docs/postman/openpolicy-api.postman_collection.json << 'EOF'
{
    "info": {
        "name": "OpenPolicy Platform API",
        "description": "Complete API collection for OpenPolicy Platform V4",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "auth": {
        "type": "bearer",
        "bearer": [
            {
                "key": "token",
                "value": "{{access_token}}",
                "type": "string"
            }
        ]
    },
    "variable": [
        {
            "key": "base_url",
            "value": "https://api.openpolicy.com/v1",
            "type": "string"
        },
        {
            "key": "access_token",
            "value": "",
            "type": "string"
        }
    ],
    "item": [
        {
            "name": "Authentication",
            "item": [
                {
                    "name": "Register User",
                    "request": {
                        "method": "POST",
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": "{\n    \"email\": \"test@example.com\",\n    \"password\": \"SecurePass123!\",\n    \"name\": \"Test User\",\n    \"organization\": \"Test Org\"\n}"
                        },
                        "url": {
                            "raw": "{{base_url}}/auth/register",
                            "host": ["{{base_url}}"],
                            "path": ["auth", "register"]
                        }
                    }
                },
                {
                    "name": "Login",
                    "event": [
                        {
                            "listen": "test",
                            "script": {
                                "exec": [
                                    "if (pm.response.code === 200) {",
                                    "    const response = pm.response.json();",
                                    "    pm.collectionVariables.set('access_token', response.token);",
                                    "}"
                                ]
                            }
                        }
                    ],
                    "request": {
                        "method": "POST",
                        "header": [
                            {
                                "key": "Content-Type",
                                "value": "application/json"
                            }
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": "{\n    \"email\": \"test@example.com\",\n    \"password\": \"SecurePass123!\"\n}"
                        },
                        "url": {
                            "raw": "{{base_url}}/auth/login",
                            "host": ["{{base_url}}"],
                            "path": ["auth", "login"]
                        }
                    }
                }
            ]
        },
        {
            "name": "Policies",
            "item": [
                {
                    "name": "List Policies",
                    "request": {
                        "method": "GET",
                        "header": [],
                        "url": {
                            "raw": "{{base_url}}/policies?page=1&limit=20&category=healthcare",
                            "host": ["{{base_url}}"],
                            "path": ["policies"],
                            "query": [
                                {
                                    "key": "page",
                                    "value": "1"
                                },
                                {
                                    "key": "limit",
                                    "value": "20"
                                },
                                {
                                    "key": "category",
                                    "value": "healthcare"
                                }
                            ]
                        }
                    }
                }
            ]
        }
    ]
}
EOF

    # Create API client examples
    log "Creating API client examples..."
    
    # Python example
    cat > api-docs/examples/python_client.py << 'EOF'
"""
OpenPolicy Platform API Client Example
"""
import requests
import json
from typing import Dict, List, Optional

class OpenPolicyClient:
    def __init__(self, base_url: str = "https://api.openpolicy.com/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
    
    def login(self, email: str, password: str) -> Dict:
        """Authenticate and obtain access token"""
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        
        data = response.json()
        self.token = data["token"]
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}"
        })
        return data
    
    def get_policies(self, 
                    page: int = 1, 
                    limit: int = 20,
                    category: Optional[str] = None,
                    search: Optional[str] = None) -> Dict:
        """Retrieve policies with optional filters"""
        params = {
            "page": page,
            "limit": limit
        }
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        
        response = self.session.get(
            f"{self.base_url}/policies",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def search(self, query: str, types: Optional[List[str]] = None) -> Dict:
        """Search across all resources"""
        params = {"q": query}
        if types:
            params["type"] = types
        
        response = self.session.get(
            f"{self.base_url}/search",
            params=params
        )
        response.raise_for_status()
        return response.json()

# Example usage
if __name__ == "__main__":
    client = OpenPolicyClient()
    
    # Login
    client.login("user@example.com", "password123")
    
    # Get policies
    policies = client.get_policies(category="healthcare")
    print(f"Found {policies['pagination']['total']} policies")
    
    # Search
    results = client.search("climate change", types=["policy", "bill"])
    print(f"Found {len(results['results'])} search results")
EOF

    # JavaScript/TypeScript example
    cat > api-docs/examples/typescript_client.ts << 'EOF'
/**
 * OpenPolicy Platform API Client
 */
import axios, { AxiosInstance } from 'axios';

interface LoginResponse {
  token: string;
  refresh_token: string;
  expires_in: number;
  user: User;
}

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface Policy {
  id: string;
  title: string;
  description: string;
  category: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

class OpenPolicyClient {
  private client: AxiosInstance;
  private token?: string;

  constructor(baseURL: string = 'https://api.openpolicy.com/v1') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth interceptor
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle token refresh
          this.token = undefined;
        }
        return Promise.reject(error);
      }
    );
  }

  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/auth/login', {
      email,
      password,
    });
    
    this.token = response.data.token;
    return response.data;
  }

  async getPolicies(params?: {
    page?: number;
    limit?: number;
    category?: string;
    search?: string;
  }): Promise<PaginatedResponse<Policy>> {
    const response = await this.client.get<PaginatedResponse<Policy>>('/policies', {
      params,
    });
    return response.data;
  }

  async getPolicy(id: string): Promise<Policy> {
    const response = await this.client.get<Policy>(`/policies/${id}`);
    return response.data;
  }

  async search(query: string, types?: string[]): Promise<any> {
    const response = await this.client.get('/search', {
      params: {
        q: query,
        type: types,
      },
    });
    return response.data;
  }
}

// Example usage
async function example() {
  const client = new OpenPolicyClient();
  
  try {
    // Login
    const loginResponse = await client.login('user@example.com', 'password123');
    console.log('Logged in as:', loginResponse.user.name);
    
    // Get policies
    const policies = await client.getPolicies({
      category: 'healthcare',
      limit: 10,
    });
    console.log(`Found ${policies.pagination.total} policies`);
    
    // Search
    const searchResults = await client.search('climate change', ['policy', 'bill']);
    console.log('Search results:', searchResults);
    
  } catch (error) {
    console.error('API Error:', error);
  }
}

export default OpenPolicyClient;
EOF

    # Create README
    cat > api-docs/README.md << 'EOF'
# OpenPolicy Platform API Documentation

## Overview

The OpenPolicy Platform API provides programmatic access to government policy data, legislative information, and political analytics.

## Quick Start

1. **Register for an API account** at https://developer.openpolicy.com
2. **Get your API credentials** from the dashboard
3. **Make your first API call**:

```bash
curl -X POST https://api.openpolicy.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}'
```

## Documentation

- **Interactive API Docs**: https://api.openpolicy.com/docs
- **OpenAPI Specification**: [openapi.yaml](./openapi.yaml)
- **Postman Collection**: [postman/openpolicy-api.postman_collection.json](./postman/openpolicy-api.postman_collection.json)

## Client Libraries

Official client libraries are available for:
- Python: `pip install openpolicy-python`
- JavaScript/TypeScript: `npm install @openpolicy/client`
- Go: `go get github.com/openpolicy/go-client`
- Ruby: `gem install openpolicy`

## Examples

See the [examples](./examples) directory for sample code in various languages.

## Rate Limiting

| Tier | Requests/Hour | Cost |
|------|---------------|------|
| Free | 100 | $0 |
| Basic | 1,000 | $29/month |
| Premium | 10,000 | $99/month |
| Enterprise | Unlimited | Contact us |

## Support

- **Email**: api-support@openpolicy.com
- **Documentation**: https://docs.openpolicy.com
- **Status Page**: https://status.openpolicy.com
- **Community Forum**: https://community.openpolicy.com

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for API version history.
EOF

    log "✅ API documentation generated successfully!"
}

# Generate SDKs
generate_sdks() {
    log "Generating API SDKs..."
    
    # Generate using OpenAPI Generator
    if command -v openapi-generator-cli &> /dev/null; then
        # Python SDK
        openapi-generator-cli generate \
            -i api-docs/openapi.yaml \
            -g python \
            -o sdks/python \
            --package-name openpolicy_client
        
        # TypeScript SDK
        openapi-generator-cli generate \
            -i api-docs/openapi.yaml \
            -g typescript-axios \
            -o sdks/typescript \
            --package-name @openpolicy/client
        
        # Go SDK
        openapi-generator-cli generate \
            -i api-docs/openapi.yaml \
            -g go \
            -o sdks/go \
            --package-name openpolicy
    else
        info "OpenAPI Generator not installed. Install with: npm install -g @openapitools/openapi-generator-cli"
    fi
}

# Main execution
main() {
    setup_api_docs
    generate_sdks
    
    # Install dependencies and generate HTML
    if command -v npm &> /dev/null; then
        cd api-docs
        npm init -y &> /dev/null
        npm install swagger-ui-dist --save &> /dev/null
        node generate-html.js
        cd ..
    fi
    
    info "API documentation complete!"
    info "View documentation at: api-docs/html/index.html"
    info "OpenAPI spec at: api-docs/openapi.yaml"
    info "Postman collection at: api-docs/postman/openpolicy-api.postman_collection.json"
}

main "$@"
EOF
chmod +x api-docs/generate-api-docs.sh