# Scraper Schema Documentation

## Overview
This document describes all schemas and tables required for the Open Policy Platform scrapers.

## Schemas

### 1. scrapers
- **Purpose**: Core scraper functionality and metadata
- **Tables**: scraper_validations, scraper_runs, data_quality_metrics

### 2. parliamentary
- **Purpose**: Federal parliamentary data
- **Tables**: bills, members, votes, committees, sessions

### 3. provincial
- **Purpose**: Provincial legislative data
- **Tables**: legislation, representatives, committees, sessions

### 4. municipal
- **Purpose**: Municipal government data
- **Tables**: councils, meetings, decisions, officials

### 5. civic
- **Purpose**: Civic organization data
- **Tables**: organizations, events, participants

### 6. analytics
- **Purpose**: Data analysis and reporting
- **Tables**: Various analytical tables

### 7. policies
- **Purpose**: Policy document storage
- **Tables**: Policy-related tables

### 8. users
- **Purpose**: User management
- **Tables**: User-related tables

### 9. audit
- **Purpose**: Audit logging
- **Tables**: Audit-related tables

## Data Flow
1. Scrapers collect data and store in appropriate schema
2. Data validation occurs in test database
3. Validated data moves to main database
4. Production services access main database

## Validation Process
- All scrapers must pass validation before production
- Data quality scores must be above threshold
- Manual approval required for production migration
