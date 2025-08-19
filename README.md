# 🏛️ OpenPolicy Platform V4

> A comprehensive platform for tracking Canadian parliamentary data, bills, representatives, votes, and democratic processes.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](docker-compose.yml)
[![API Docs](https://img.shields.io/badge/API-documented-orange.svg)](docs/API_DOCUMENTATION.md)

## 🎯 Overview

OpenPolicy Platform is a modern, scalable system designed to democratize access to Canadian parliamentary information. It provides real-time access to:

- 📋 Parliamentary bills and legislation
- 👥 Representatives (MPs) information
- 🗳️ Voting records and results
- 🏛️ Committee activities
- 📜 Parliamentary debates (Hansard)
- 🔍 Advanced search capabilities

## 🏗️ Architecture

The platform follows a microservices architecture with 5 core services:

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACES                          │
├─────────────────────────────────────────────────────────────┤
│  Web App (Port 3000)  │  Admin Dashboard  │  Mobile Apps   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   GATEWAY LAYER (Port 80)                   │
├─────────────────────────────────────────────────────────────┤
│  Nginx Gateway  │  Rate Limiting  │  Load Balancing        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 CORE SERVICES LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  API (8000)  │  PostgreSQL (5432)  │  Redis (6379)        │
│  Scrapers    │  Queue Workers      │  Scheduler           │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- 4GB RAM minimum
- 10GB disk space

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/OpenPolicyPlatformV4.git
cd OpenPolicyPlatformV4
```

2. Run the deployment script:
```bash
./deploy.sh
```

3. Access the platform:
- Main Application: http://localhost
- Admin Dashboard: http://localhost:3001
- API Documentation: http://localhost/api/docs

### Default Credentials

- **Admin**: admin@openpolicy.ca / admin123
- **User**: user@example.com / user123

## 📦 Services

### Core Services

| Service | Port | Description |
|---------|------|-------------|
| Nginx Gateway | 80 | Reverse proxy and load balancer |
| API Service | 8000 | RESTful API backend (Laravel) |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache and session storage |
| Web App | 3000 | React user interface |
| Admin Dashboard | 3001 | Admin management interface |

### Background Services

- **Scraper Service**: Fetches parliamentary data hourly
- **Queue Worker**: Processes background jobs
- **Scheduler**: Runs periodic tasks

## 🛠️ Development

### Running Locally

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Run database migrations
docker-compose exec api php artisan migrate

# Run scrapers manually
docker-compose exec scraper python orchestrator.py
```

### Project Structure

```
OpenPolicyPlatformV4/
├── apps/                    # Frontend applications
│   └── mobile/             
│       ├── admin-open-policy/   # Admin dashboard (Vite + React)
│       └── open-policy-web/     # Main web app (React)
├── backend/                 # Backend services
│   └── api/                # API endpoints
├── infrastructure/         # Laravel backend
│   ├── app/               # Application code
│   ├── database/          # Migrations and seeds
│   └── routes/            # API routes
├── scrapers/              # Parliamentary data scrapers
├── database/              # Database schemas and init scripts
├── config/                # Configuration files
└── docs/                  # Documentation
```

## 📊 Features

### For Citizens

- **Browse Bills**: View all parliamentary bills with status tracking
- **Representative Profiles**: Find your MP and their voting record
- **Vote Tracking**: See how bills are voted on in Parliament
- **Search**: Full-text search across all parliamentary data
- **Notifications**: Get alerts on bills and topics you care about

### For Administrators

- **Dashboard**: Real-time system metrics and health monitoring
- **User Management**: Manage platform users and permissions
- **Scraper Control**: Monitor and control data collection
- **Content Moderation**: Review and manage user-generated content

### For Developers

- **RESTful API**: Full API access to all parliamentary data
- **Webhooks**: Real-time notifications for data changes
- **SDKs**: Official libraries for popular languages
- **GraphQL**: Alternative query interface (coming soon)

## 🔧 Monitoring

### Health Checks

```bash
# Check all services
./monitor.sh

# Continuous monitoring
./monitor.sh --continuous
```

### Key Metrics

- Service uptime and response times
- Database query performance
- Cache hit rates
- Scraper success rates
- API request volumes

## 🔒 Security

- JWT-based authentication
- Rate limiting on all endpoints
- CORS protection
- SQL injection prevention
- XSS protection
- Regular security updates

## 📈 Performance

- Response time: < 200ms (p95)
- Uptime: 99.9% target
- Concurrent users: 10,000+
- Data freshness: < 1 hour

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/development/contributing.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Parliamentary data sourced from official government websites
- Built with open-source technologies
- Community-driven development

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/OpenPolicyPlatformV4/issues)
- **Email**: support@openpolicy.ca
- **Community**: [Discord Server](https://discord.gg/openpolicy)

---

Built with ❤️ for Canadian democracy