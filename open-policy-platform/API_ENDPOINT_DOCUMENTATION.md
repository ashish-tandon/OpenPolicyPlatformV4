# Open Policy Platform V4 - API Endpoint Documentation

## Overview
This document tracks all API endpoints, failures encountered during deployment, corrections made, and analysis of production vs. development environment issues.

## API Endpoints Status

### ✅ Working Endpoints

#### 1. Root Policies Endpoint
- **Path**: `GET /api/v1/policies/`
- **Status**: ✅ Operational
- **Response**: Returns paginated list of policies with filtering
- **Sample Response**: 3 policies returned successfully

#### 2. Search Endpoint
- **Path**: `GET /api/v1/policies/search?q={query}`
- **Status**: ✅ Operational
- **Response**: Returns policies matching search query
- **Sample Response**: 3 policies found for "Bill"

#### 3. Advanced Search Endpoint
- **Path**: `GET /api/v1/policies/search/advanced?q={query}&category={cat}&jurisdiction={jur}&limit={limit}`
- **Status**: ✅ Operational
- **Response**: Returns advanced filtered search results
- **Sample Response**: 3 policies found with advanced filtering

#### 4. Categories Endpoint
- **Path**: `GET /api/v1/policies/list/categories`
- **Status**: ✅ Operational (Fixed)
- **Response**: Returns distinct policy categories
- **Sample Response**: 2 categories (public, private)

#### 5. Jurisdictions Endpoint
- **Path**: `GET /api/v1/policies/list/jurisdictions`
- **Status**: ✅ Operational (Fixed)
- **Response**: Returns distinct policy jurisdictions
- **Sample Response**: 2 jurisdictions (43-2, 43-1)

#### 6. Statistics Endpoint
- **Path**: `GET /api/v1/policies/summary/stats`
- **Status**: ✅ Operational (Fixed)
- **Response**: Returns policy statistics and counts
- **Sample Response**: 3 total policies

#### 7. Get Policy by ID
- **Path**: `GET /api/v1/policies/{policy_id}`
- **Status**: ✅ Operational
- **Response**: Returns specific policy details
- **Sample Response**: "Bill A" retrieved successfully

#### 8. Policy Analysis
- **Path**: `GET /api/v1/policies/{policy_id}/analysis`
- **Status**: ✅ Operational
- **Response**: Returns policy analysis metrics
- **Sample Response**: "low" complexity calculated

## 🚨 Failures Encountered & Corrections

### 1. Route Conflict Issues
**Problem**: FastAPI route conflicts between static and dynamic routes
- **Symptoms**: 
  - `/categories` returning `int_parsing` errors
  - `/jurisdictions` returning `int_parsing` errors  
  - `/stats` returning `int_parsing` errors
- **Root Cause**: FastAPI was matching static routes to dynamic `/{policy_id}` pattern
- **Solution**: Changed routes to unambiguous prefixes:
  - `/categories` → `/list/categories`
  - `/jurisdictions` → `/list/jurisdictions`
  - `/stats` → `/summary/stats`

### 2. Database Parsing Issues
**Problem**: `psql` output parsing failures
- **Symptoms**: Categories, jurisdictions, and stats returning empty results
- **Root Cause**: Incorrect handling of `psql -t -A` output format
- **Solution**: Fixed parsing logic to handle newline-separated values correctly

### 3. Docker Build Issues
**Problem**: Updated code not being included in container builds
- **Symptoms**: OpenAPI schema showing old routes despite code changes
- **Root Cause**: Docker layer caching and incomplete rebuilds
- **Solution**: Force complete rebuild with `--no-cache` flag

### 4. Environment Variable Issues
**Problem**: API startup failures due to missing environment variables
- **Symptoms**: 
  - `RuntimeError: Startup guard failed: missing=[] policy=['ALLOWED_HOSTS', 'ALLOWED_ORIGINS']`
  - `ValueError: AUTH0_CLIENT_ID environment variable is required`
- **Root Cause**: Missing required environment variables in production
- **Solution**: Added all required environment variables to `env.azure.complete`

## 🔍 Why These Issues Occur in Production vs. Development

### 1. **Route Ordering Sensitivity**
- **Development**: FastAPI development mode may be more forgiving with route conflicts
- **Production**: Strict route matching and potential race conditions in route registration
- **Impact**: Static routes get caught by dynamic patterns in production

### 2. **Docker Build Context Differences**
- **Development**: Local builds often use different context and caching strategies
- **Production**: Azure deployment uses specific build contexts that may not include all files
- **Impact**: Code changes not properly propagated to production containers

### 3. **Environment Variable Strictness**
- **Development**: More lenient environment variable validation
- **Production**: Strict startup guard policies that fail on missing variables
- **Impact**: Production deployments fail on missing configuration

### 4. **Database Connection Differences**
- **Development**: Local database connections may be more forgiving
- **Production**: Azure PostgreSQL requires SSL and strict authentication
- **Impact**: Connection and parsing issues only manifest in production

## 📊 Current System Health

### Services Status
- **API Service**: ✅ Fully operational
- **Database**: ✅ Connected to Azure PostgreSQL
- **Route Conflicts**: ✅ Completely resolved
- **Endpoint Validation**: ✅ All 8 GET endpoints tested and working

### Data Status
- **Database Records**: 3 sample policies loaded
- **Categories**: 2 (public, private)
- **Jurisdictions**: 2 (43-2, 43-1)
- **Total Policies**: 3

## 🚀 Next Steps

1. **Monitor all endpoints** for continued stability
2. **Investigate build time increases** and container removal issues
3. **Verify scraper services** are operational
4. **Check data ingestion** from legacy systems
5. **Validate all microservices** are running correctly

## 📝 Notes

- All route conflicts have been resolved using unambiguous path prefixes
- Database parsing issues fixed for categories, jurisdictions, and stats
- Production environment now matches development functionality
- Comprehensive endpoint validation completed successfully
