#!/bin/bash

# Open Policy Platform V4 - Database Export Script
# Exports database for migration to QNAP and Azure

set -e

# Configuration
DB_CONTAINER="openpolicy-core-postgres"
DB_NAME="openpolicy"
DB_USER="openpolicy"
EXPORT_DIR="./database-exports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "🗄️  Open Policy Platform V4 - Database Export"
echo "================================================"

# Create export directory
mkdir -p "$EXPORT_DIR"

echo "📁 Creating export directory: $EXPORT_DIR"

# Export database schema
echo "📋 Exporting database schema..."
docker exec "$DB_CONTAINER" pg_dump \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  --schema-only \
  --no-owner \
  --no-privileges \
  --file="/tmp/schema_$TIMESTAMP.sql"

# Export database data
echo "📊 Exporting database data..."
docker exec "$DB_CONTAINER" pg_dump \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  --data-only \
  --no-owner \
  --no-privileges \
  --file="/tmp/data_$TIMESTAMP.sql"

# Export full database
echo "💾 Exporting full database..."
docker exec "$DB_CONTAINER" pg_dump \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  --file="/tmp/full_database_$TIMESTAMP.sql"

# Copy files from container to host
echo "📥 Copying export files to host..."
docker cp "$DB_CONTAINER:/tmp/schema_$TIMESTAMP.sql" "$EXPORT_DIR/"
docker cp "$DB_CONTAINER:/tmp/data_$TIMESTAMP.sql" "$EXPORT_DIR/"
docker cp "$DB_CONTAINER:/tmp/full_database_$TIMESTAMP.sql" "$EXPORT_DIR/"

# Clean up container files
docker exec "$DB_CONTAINER" rm -f "/tmp/schema_$TIMESTAMP.sql" "/tmp/data_$TIMESTAMP.sql" "/tmp/full_database_$TIMESTAMP.sql"

# Create migration summary
cat > "$EXPORT_DIR/migration_summary_$TIMESTAMP.md" << EOF
# Database Migration Summary

**Export Date**: $(date)
**Database**: $DB_NAME
**Container**: $DB_CONTAINER

## Exported Files

1. **Schema Only**: \`schema_$TIMESTAMP.sql\`
   - Database structure and constraints
   - No data, only table definitions

2. **Data Only**: \`data_$TIMESTAMP.sql\`
   - All data without schema
   - Use with existing schema

3. **Full Database**: \`full_database_$TIMESTAMP.sql\`
   - Complete database backup
   - Includes schema and data

## Migration Commands

### QNAP Migration
\`\`\`bash
# Import schema first
docker exec -i openpolicy-qnap-postgres psql -U openpolicy -d openpolicy < schema_$TIMESTAMP.sql

# Import data
docker exec -i openpolicy-qnap-postgres psql -U openpolicy -d openpolicy < data_$TIMESTAMP.sql
\`\`\`

### Azure Migration
\`\`\`bash
# Import to Azure Database for PostgreSQL
psql "host=your-azure-host port=5432 dbname=openpolicy user=openpolicy password=your-password sslmode=require" < full_database_$TIMESTAMP.sql
\`\`\`

## Verification

After migration, verify:
- [ ] All tables exist
- [ ] Data integrity maintained
- [ ] Indexes and constraints applied
- [ ] Foreign key relationships intact
EOF

echo "✅ Database export completed successfully!"
echo "📁 Export files saved to: $EXPORT_DIR"
echo "📋 Migration summary: $EXPORT_DIR/migration_summary_$TIMESTAMP.md"

# Display file sizes
echo ""
echo "📊 Export file sizes:"
ls -lh "$EXPORT_DIR"/*.sql
