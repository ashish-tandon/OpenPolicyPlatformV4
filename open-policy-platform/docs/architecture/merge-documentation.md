# Repository Merge Documentation

## Overview
This document details the successful merge of 9 repositories into a unified Open Policy Platform. All original code has been preserved and organized into a logical structure.

## Merged Repositories

### 1. Core Open Policy Repositories
- **open-policy** → `apps/open-policy-main/` (React Native mobile app)
- **open-policy-app** → `apps/open-policy-app/` (Policy application components)
- **open-policy-web** → `apps/open-policy-web/` (React web interface)
- **admin-open-policy** → `apps/admin-open-policy/` (Administrative interface)
- **open-policy-infra** → `infrastructure/open-policy-infra/` (Infrastructure config)

### 2. Backend Services
- **OpenPolicyAshBack** → `backend/OpenPolicyAshBack/` (Main backend API)

### 3. Data Collection & Scrapers
- **openparliament** → `scrapers/openparliament/` (Parliamentary data)
- **scrapers-ca** → `scrapers/scrapers-ca/` (Canadian government data)
- **civic-scraper** → `scrapers/civic-scraper/` (Civic data collection)

## Repository Structure

```
open-policy-platform/
├── README.md                    # Main project documentation
├── MERGE_DOCUMENTATION.md       # This file
├── setup.sh                     # Unified setup script
├── apps/                        # Frontend applications
│   ├── open-policy-main/        # React Native mobile app
│   ├── open-policy-app/         # Policy app components
│   ├── open-policy-web/         # React web interface
│   └── admin-open-policy/       # Admin interface
├── backend/                     # Backend services
│   └── OpenPolicyAshBack/       # Main API and services
├── infrastructure/              # Infrastructure & deployment
│   └── open-policy-infra/       # Infrastructure configuration
└── scrapers/                    # Data collection tools
    ├── openparliament/          # Parliamentary data scraping
    ├── scrapers-ca/             # Canadian government scrapers
    └── civic-scraper/           # Civic data collection
```

## Technology Stack

### Frontend
- **React Native** (Mobile): Expo-based mobile application
- **React** (Web): Vite-based web interface with Tailwind CSS
- **TypeScript**: Used across all frontend applications

### Backend
- **Python**: FastAPI-based backend with SQLAlchemy
- **Database**: PostgreSQL with Alembic migrations
- **Task Queue**: Celery with Redis
- **AI Integration**: OpenAI integration for enhanced features

### Data Collection
- **Python Scrapers**: BeautifulSoup, lxml for data extraction
- **Scheduling**: Cron-based data collection
- **Multiple Sources**: Parliamentary, Canadian government, civic data

## Merge Strategy

### 1. Preserved Original Structure
- All original repository structures maintained
- No code modifications during merge
- Original README files preserved in each directory

### 2. Logical Organization
- **apps/**: All frontend applications
- **backend/**: Backend services and APIs
- **infrastructure/**: Deployment and infrastructure configs
- **scrapers/**: Data collection and scraping tools

### 3. Conflict Resolution
- No conflicts encountered during merge
- Each repository was in its own directory
- Clear separation of concerns maintained

## Setup Instructions

### Prerequisites
- Node.js (v18+)
- Python (v3.8+)
- Docker
- PostgreSQL
- Redis

### Quick Setup
```bash
# Clone the repository
git clone <repository-url>
cd open-policy-platform

# Run unified setup
./setup.sh
```

### Manual Setup

#### Backend Setup
```bash
cd backend/OpenPolicyAshBack
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

#### Frontend Setup
```bash
# Web Interface
cd apps/open-policy-web
npm install
npm run dev

# Mobile App
cd apps/open-policy-main
npm install
npx expo start
```

## Key Features by Component

### Open Policy Main (Mobile App)
- React Native with Expo
- Policy browsing and analysis
- Offline capabilities
- Native mobile features

### Open Policy Web
- React with Vite
- Modern web interface
- Responsive design
- Real-time updates

### OpenPolicyAshBack
- FastAPI backend
- Comprehensive API
- Database management
- AI-powered features
- Task scheduling

### Scrapers
- **openparliament**: Parliamentary proceedings and data
- **scrapers-ca**: Canadian government data collection
- **civic-scraper**: General civic data collection

## Development Workflow

### Adding New Features
1. Identify the appropriate component directory
2. Follow the existing code structure
3. Update documentation in the component's README
4. Test thoroughly before committing

### Data Integration
1. Use existing scrapers as templates
2. Follow the established data models
3. Integrate with the main backend API
4. Update frontend components as needed

## Deployment

### Single Container Deployment
The backend includes Docker configurations for single-container deployment:
- `docker-compose.single.yml`
- `Dockerfile.single-container`
- Deployment scripts for various environments

### Multi-Service Deployment
Each component can be deployed independently:
- Frontend apps to Vercel/Netlify
- Backend to cloud providers
- Scrapers as scheduled tasks

## Monitoring and Maintenance

### Logging
- Structured logging with structlog
- Sentry integration for error tracking
- Comprehensive monitoring setup

### Testing
- Unit tests for all components
- Integration tests for API endpoints
- End-to-end testing for scrapers

## Future Enhancements

### Planned Integrations
- Additional government data sources
- Enhanced AI analysis capabilities
- Real-time policy tracking
- Advanced visualization features

### Scalability
- Microservices architecture ready
- Horizontal scaling capabilities
- Load balancing support
- Caching strategies

## Support and Documentation

Each component directory contains:
- Original README with setup instructions
- Component-specific documentation
- API documentation (where applicable)
- Testing instructions

## License Information

Each component maintains its original license. See individual component directories for specific license information.

---

**Merge Completed**: All 9 repositories successfully merged with zero conflicts. All original code preserved and organized for optimal development workflow.
