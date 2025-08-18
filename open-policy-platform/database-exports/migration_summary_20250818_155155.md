# Database Migration Summary

**Export Date**: Mon Aug 18 15:51:56 EDT 2025
**Database**: openpolicy
**Container**: openpolicy-core-postgres

## Exported Files

1. **Schema Only**: `schema_20250818_155155.sql`
   - Database structure and constraints
   - No data, only table definitions

2. **Data Only**: `data_20250818_155155.sql`
   - All data without schema
   - Use with existing schema

3. **Full Database**: `full_database_20250818_155155.sql`
   - Complete database backup
   - Includes schema and data

## Migration Commands

### QNAP Migration
```bash
# Import schema first
docker exec -i openpolicy-qnap-postgres psql -U openpolicy -d openpolicy < schema_20250818_155155.sql

# Import data
docker exec -i openpolicy-qnap-postgres psql -U openpolicy -d openpolicy < data_20250818_155155.sql
```

### Azure Migration
```bash
# Import to Azure Database for PostgreSQL
psql "host=your-azure-host port=5432 dbname=openpolicy user=openpolicy password=your-password sslmode=require" < full_database_20250818_155155.sql
```

## Verification

After migration, verify:
- [ ] All tables exist
- [ ] Data integrity maintained
- [ ] Indexes and constraints applied
- [ ] Foreign key relationships intact
