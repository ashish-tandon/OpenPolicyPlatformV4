#!/bin/bash

# Database Migration Setup Script
# Configures and runs Flyway and Alembic migrations

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_DB=${POSTGRES_DB:-openpolicy_prod}
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}

FLYWAY_VERSION="9.22.3"
MIGRATIONS_DIR="migrations"

# Install Flyway
install_flyway() {
    log "Installing Flyway..."
    
    if [ ! -d "flyway-$FLYWAY_VERSION" ]; then
        wget -qO- "https://repo1.maven.org/maven2/org/flywaydb/flyway-commandline/$FLYWAY_VERSION/flyway-commandline-$FLYWAY_VERSION-linux-x64.tar.gz" | tar xz
        ln -sf "flyway-$FLYWAY_VERSION/flyway" /usr/local/bin/flyway || true
    fi
    
    log "✅ Flyway installed"
}

# Setup Python environment for Alembic
setup_python_env() {
    log "Setting up Python environment..."
    
    cd services/python
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install --upgrade pip
    pip install alembic sqlalchemy psycopg2-binary black
    
    cd ../..
    
    log "✅ Python environment ready"
}

# Run Flyway migrations
run_flyway_migrations() {
    log "Running Flyway migrations..."
    
    cd database
    
    # Create Flyway configuration with environment variables
    cat > flyway.conf << EOF
flyway.url=jdbc:postgresql://${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
flyway.user=${POSTGRES_USER}
flyway.password=${POSTGRES_PASSWORD}
flyway.schemas=public,auth,policy,analytics,audit
flyway.defaultSchema=public
flyway.locations=filesystem:./migrations/sql
flyway.baselineOnMigrate=true
flyway.baselineVersion=0
flyway.validateOnMigrate=true
flyway.sqlMigrationPrefix=V
flyway.repeatableSqlMigrationPrefix=R
flyway.table=schema_history
flyway.outOfOrder=false
flyway.cleanDisabled=true
EOF

    # Run migrations
    flyway migrate
    
    # Show migration info
    flyway info
    
    cd ..
    
    log "✅ Flyway migrations completed"
}

# Initialize Alembic
init_alembic() {
    log "Initializing Alembic..."
    
    cd services/python
    source venv/bin/activate
    
    # Create initial migration if needed
    if [ ! -d "alembic/versions" ]; then
        mkdir -p alembic/versions
        
        # Generate initial migration
        alembic revision --autogenerate -m "Initial Python models migration"
    fi
    
    cd ../..
    
    log "✅ Alembic initialized"
}

# Run Alembic migrations
run_alembic_migrations() {
    log "Running Alembic migrations..."
    
    cd services/python
    source venv/bin/activate
    
    # Set database URL
    export DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
    
    # Run migrations
    alembic upgrade head
    
    # Show current version
    alembic current
    
    cd ../..
    
    log "✅ Alembic migrations completed"
}

# Create migration documentation
create_migration_docs() {
    log "Creating migration documentation..."
    
    cat > database/MIGRATION_GUIDE.md << 'EOF'
# Database Migration Guide

## Overview

The OpenPolicy Platform uses two migration systems:
1. **Flyway** - For core database schema (SQL migrations)
2. **Alembic** - For Python service models (SQLAlchemy migrations)

## Flyway Migrations

### Creating a New Migration

1. Create a new SQL file in `database/migrations/sql/`:
   ```
   V{version}__{description}.sql
   ```
   Example: `V3__add_user_preferences.sql`

2. Write your SQL migration:
   ```sql
   -- V3__add_user_preferences.sql
   CREATE TABLE auth.user_preferences (
       user_id UUID PRIMARY KEY REFERENCES auth.users(id),
       theme VARCHAR(20) DEFAULT 'light',
       notifications_enabled BOOLEAN DEFAULT true,
       language VARCHAR(10) DEFAULT 'en',
       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );
   ```

3. Run the migration:
   ```bash
   cd database
   flyway migrate
   ```

### Repeatable Migrations

For views, functions, and procedures, use repeatable migrations:
```
R__views_and_functions.sql
```

These run whenever their checksum changes.

### Rollback

Flyway doesn't support automatic rollback. Create a new forward migration:
```sql
-- V4__rollback_user_preferences.sql
DROP TABLE IF EXISTS auth.user_preferences;
```

## Alembic Migrations

### Creating a New Migration

1. Auto-generate from model changes:
   ```bash
   cd services/python
   source venv/bin/activate
   alembic revision --autogenerate -m "Add user preferences model"
   ```

2. Or create manually:
   ```bash
   alembic revision -m "Add custom index"
   ```

3. Edit the generated file in `alembic/versions/`

4. Run the migration:
   ```bash
   alembic upgrade head
   ```

### Downgrade

```bash
# Downgrade one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade abc123

# Downgrade to beginning
alembic downgrade base
```

### Common Commands

```bash
# Show current version
alembic current

# Show history
alembic history

# Show SQL without running
alembic upgrade head --sql

# Stamp database with version
alembic stamp head
```

## Best Practices

### 1. Migration Naming
- Use descriptive names
- Include ticket numbers: `V5__JIRA_123_add_audit_fields.sql`
- Keep names under 100 characters

### 2. Migration Content
- One logical change per migration
- Include rollback considerations
- Add comments for complex logic
- Test on a copy first

### 3. Schema Changes
- Add columns as nullable first
- Backfill data in separate migration
- Then add constraints
- Drop columns in stages

### 4. Performance
- Create indexes CONCURRENTLY in PostgreSQL
- Run vacuum/analyze after large changes
- Consider migration timing (off-peak)

### 5. Data Migrations
```sql
-- Safe data migration pattern
BEGIN;
-- Add new column
ALTER TABLE users ADD COLUMN full_name VARCHAR(255);

-- Populate from existing data
UPDATE users SET full_name = first_name || ' ' || last_name;

-- Add NOT NULL after data is populated
ALTER TABLE users ALTER COLUMN full_name SET NOT NULL;

COMMIT;
```

## Environment-Specific Migrations

### Development
```bash
export ENVIRONMENT=development
flyway migrate
```

### Staging
```bash
export ENVIRONMENT=staging
flyway -configFiles=flyway-staging.conf migrate
```

### Production
```bash
export ENVIRONMENT=production
# Dry run first
flyway -configFiles=flyway-prod.conf validate
flyway -configFiles=flyway-prod.conf info

# Run with approval
flyway -configFiles=flyway-prod.conf migrate
```

## Troubleshooting

### Flyway Issues

1. **Checksum mismatch**
   ```bash
   flyway repair
   ```

2. **Migration failed**
   - Check `schema_history` table
   - Fix the issue
   - Re-run migration

3. **Out of order**
   - Enable in config: `flyway.outOfOrder=true`
   - Use sparingly

### Alembic Issues

1. **Multiple heads**
   ```bash
   alembic merge -m "Merge heads"
   ```

2. **Can't detect changes**
   - Ensure all models imported in env.py
   - Check table naming
   - Verify schema settings

3. **Version conflict**
   ```bash
   alembic stamp head
   alembic history
   ```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Flyway migrations
  run: |
    flyway -url=${{ secrets.DB_URL }} \
           -user=${{ secrets.DB_USER }} \
           -password=${{ secrets.DB_PASS }} \
           migrate

- name: Run Alembic migrations
  run: |
    cd services/python
    alembic upgrade head
```

### Pre-deployment Checks
1. Validate migrations: `flyway validate`
2. Check for conflicts: `alembic check`
3. Review generated SQL: `alembic upgrade head --sql`
4. Backup database
5. Run in transaction when possible

## Monitoring Migrations

### Track Migration Metrics
- Migration duration
- Success/failure rate
- Schema version per environment
- Pending migrations alert

### Audit Trail
All migrations are logged in:
- `schema_history` (Flyway)
- `alembic_version` (Alembic)
- Application logs
- Audit tables

## Emergency Procedures

### Failed Production Migration
1. Stop deployment
2. Assess impact
3. If safe, fix and retry
4. If not, create fix migration
5. Document incident

### Rollback Strategy
1. Have rollback migration ready
2. Test rollback in staging
3. Execute with monitoring
4. Verify data integrity
5. Update documentation
EOF

    log "✅ Migration documentation created"
}

# Setup migration monitoring
setup_monitoring() {
    log "Setting up migration monitoring..."
    
    # Create monitoring queries
    cat > database/migration-monitoring.sql << 'EOF'
-- Flyway migration status
SELECT 
    version,
    description,
    type,
    script,
    checksum,
    installed_on,
    execution_time,
    success
FROM schema_history
ORDER BY installed_rank DESC
LIMIT 10;

-- Alembic migration status
SELECT 
    version_num,
    -- Calculate time since migration
    AGE(CURRENT_TIMESTAMP, 
        TO_TIMESTAMP(SUBSTRING(version_num, 1, 14), 'YYYYMMDDHH24MISS')
    ) as migration_age
FROM alembic_version;

-- Check for pending Flyway migrations
SELECT COUNT(*) as pending_migrations
FROM (
    SELECT script FROM schema_history WHERE success = false
) pending;

-- Migration performance metrics
SELECT 
    AVG(execution_time) as avg_migration_time_ms,
    MAX(execution_time) as max_migration_time_ms,
    COUNT(*) as total_migrations,
    COUNT(CASE WHEN success = false THEN 1 END) as failed_migrations
FROM schema_history;

-- Recent schema changes
SELECT 
    schemaname,
    tablename,
    tableowner,
    hasindexes,
    hasrules,
    hastriggers
FROM pg_tables
WHERE schemaname IN ('public', 'auth', 'policy', 'analytics', 'audit')
ORDER BY schemaname, tablename;
EOF

    log "✅ Monitoring queries created"
}

# Test migrations
test_migrations() {
    log "Testing migrations..."
    
    # Create test database
    createdb -h $POSTGRES_HOST -U $POSTGRES_USER openpolicy_test || true
    
    # Run Flyway on test database
    POSTGRES_DB=openpolicy_test run_flyway_migrations
    
    # Verify critical tables exist
    psql -h $POSTGRES_HOST -U $POSTGRES_USER -d openpolicy_test -c "
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema IN ('public', 'auth', 'policy', 'analytics', 'audit')
    "
    
    # Drop test database
    dropdb -h $POSTGRES_HOST -U $POSTGRES_USER openpolicy_test
    
    log "✅ Migration tests passed"
}

# Main execution
main() {
    log "Starting database migration setup..."
    
    # Check prerequisites
    if ! command -v psql &> /dev/null; then
        error "PostgreSQL client (psql) is required"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required"
        exit 1
    fi
    
    # Setup steps
    install_flyway
    setup_python_env
    
    # Run migrations
    run_flyway_migrations
    init_alembic
    run_alembic_migrations
    
    # Additional setup
    create_migration_docs
    setup_monitoring
    test_migrations
    
    # Summary
    log "✅ Database migration setup complete!"
    log ""
    log "Flyway version: $FLYWAY_VERSION"
    log "Migration location: database/migrations/sql/"
    log "Alembic location: services/python/alembic/"
    log ""
    log "Next steps:"
    log "1. Review MIGRATION_GUIDE.md"
    log "2. Create your first migration"
    log "3. Set up CI/CD integration"
    log "4. Configure production access"
}

# Run main function
main "$@"