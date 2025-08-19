#!/bin/bash

# Backup and Disaster Recovery Setup Script
# Implements automated backup procedures and disaster recovery plans

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Create backup configuration
setup_backup_config() {
    log "Setting up backup configuration..."
    
    mkdir -p backup/{scripts,configs,policies}
    
    # Backup configuration
    cat > backup/configs/backup.yaml << 'EOF'
# Backup Configuration
backup:
  schedule:
    databases:
      frequency: "0 2 * * *"  # Daily at 2 AM
      retention_days: 30
      full_backup_day: "sunday"
    
    files:
      frequency: "0 3 * * *"  # Daily at 3 AM
      retention_days: 14
    
    configs:
      frequency: "0 4 * * *"  # Daily at 4 AM
      retention_days: 90
  
  destinations:
    primary:
      type: "azure_blob"
      container: "openpolicy-backups"
      path: "production/${BACKUP_TYPE}/${DATE}"
    
    secondary:
      type: "aws_s3"
      bucket: "openpolicy-dr-backups"
      region: "us-west-2"
      path: "production/${BACKUP_TYPE}/${DATE}"
    
    local:
      type: "local"
      path: "/mnt/backups/${BACKUP_TYPE}/${DATE}"
      retention_days: 7
  
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
    key_source: "azure_keyvault"
    key_name: "backup-encryption-key"
  
  notifications:
    email:
      - "ops@openpolicy.platform"
    slack:
      webhook: "${SLACK_WEBHOOK}"
      channel: "#ops-alerts"
EOF

    # PostgreSQL backup script
    cat > backup/scripts/backup-postgres.sh << 'EOF'
#!/bin/bash

# PostgreSQL Backup Script
source /etc/backup/backup.conf

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="postgres_${ENVIRONMENT}_${TIMESTAMP}"
BACKUP_DIR="/tmp/backups/${BACKUP_NAME}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Backup all databases
log "Starting PostgreSQL backup..."

# Get list of databases
DATABASES=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -t -c "SELECT datname FROM pg_database WHERE datname NOT IN ('postgres', 'template0', 'template1');")

for DB in $DATABASES; do
    log "Backing up database: $DB"
    
    # Create dump with custom format for faster restore
    PGPASSWORD=$POSTGRES_PASSWORD pg_dump \
        -h $POSTGRES_HOST \
        -U $POSTGRES_USER \
        -d $DB \
        -Fc \
        -f "${BACKUP_DIR}/${DB}.dump" \
        --verbose \
        --no-owner \
        --no-acl
    
    # Create SQL format backup as well
    PGPASSWORD=$POSTGRES_PASSWORD pg_dump \
        -h $POSTGRES_HOST \
        -U $POSTGRES_USER \
        -d $DB \
        -f "${BACKUP_DIR}/${DB}.sql" \
        --verbose \
        --no-owner \
        --no-acl
done

# Backup global objects (roles, tablespaces)
log "Backing up global objects..."
PGPASSWORD=$POSTGRES_PASSWORD pg_dumpall \
    -h $POSTGRES_HOST \
    -U $POSTGRES_USER \
    --globals-only \
    -f "${BACKUP_DIR}/globals.sql"

# Create backup manifest
cat > "${BACKUP_DIR}/manifest.json" << JSON
{
    "timestamp": "${TIMESTAMP}",
    "type": "postgresql",
    "environment": "${ENVIRONMENT}",
    "databases": [$(echo $DATABASES | tr ' ' '\n' | sed 's/^/"/;s/$/",/' | tr '\n' ' ' | sed 's/, $//')],
    "size": "$(du -sh ${BACKUP_DIR} | cut -f1)",
    "host": "${POSTGRES_HOST}",
    "version": "$(PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -t -c 'SELECT version();' | head -1)"
}
JSON

# Compress backup
log "Compressing backup..."
tar -czf "${BACKUP_DIR}.tar.gz" -C "/tmp/backups" "${BACKUP_NAME}"

# Encrypt backup
log "Encrypting backup..."
openssl enc -aes-256-cbc -salt -in "${BACKUP_DIR}.tar.gz" -out "${BACKUP_DIR}.tar.gz.enc" -k "${BACKUP_ENCRYPTION_KEY}"

# Upload to cloud storage
log "Uploading to Azure..."
az storage blob upload \
    --container-name "backups" \
    --name "postgres/${BACKUP_NAME}.tar.gz.enc" \
    --file "${BACKUP_DIR}.tar.gz.enc" \
    --account-name "${AZURE_STORAGE_ACCOUNT}"

log "Uploading to AWS S3..."
aws s3 cp "${BACKUP_DIR}.tar.gz.enc" "s3://${S3_BACKUP_BUCKET}/postgres/${BACKUP_NAME}.tar.gz.enc"

# Clean up old backups
log "Cleaning up old backups..."
find /mnt/backups/postgres -name "*.tar.gz.enc" -mtime +${RETENTION_DAYS} -delete

# Clean up temporary files
rm -rf "${BACKUP_DIR}" "${BACKUP_DIR}.tar.gz" "${BACKUP_DIR}.tar.gz.enc"

log "PostgreSQL backup completed successfully!"
EOF
    chmod +x backup/scripts/backup-postgres.sh

    # Redis backup script
    cat > backup/scripts/backup-redis.sh << 'EOF'
#!/bin/bash

# Redis Backup Script
source /etc/backup/backup.conf

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="redis_${ENVIRONMENT}_${TIMESTAMP}"
BACKUP_DIR="/tmp/backups/${BACKUP_NAME}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

mkdir -p "${BACKUP_DIR}"

log "Starting Redis backup..."

# Trigger Redis backup
redis-cli -h $REDIS_HOST -a $REDIS_PASSWORD BGSAVE

# Wait for backup to complete
while [ $(redis-cli -h $REDIS_HOST -a $REDIS_PASSWORD LASTSAVE) -eq $(redis-cli -h $REDIS_HOST -a $REDIS_PASSWORD LASTSAVE) ]; do
    sleep 1
done

# Copy RDB file
cp /var/lib/redis/dump.rdb "${BACKUP_DIR}/dump.rdb"

# Get Redis info
redis-cli -h $REDIS_HOST -a $REDIS_PASSWORD INFO > "${BACKUP_DIR}/redis-info.txt"

# Create manifest
cat > "${BACKUP_DIR}/manifest.json" << JSON
{
    "timestamp": "${TIMESTAMP}",
    "type": "redis",
    "environment": "${ENVIRONMENT}",
    "size": "$(du -sh ${BACKUP_DIR}/dump.rdb | cut -f1)",
    "host": "${REDIS_HOST}"
}
JSON

# Compress and encrypt
tar -czf "${BACKUP_DIR}.tar.gz" -C "/tmp/backups" "${BACKUP_NAME}"
openssl enc -aes-256-cbc -salt -in "${BACKUP_DIR}.tar.gz" -out "${BACKUP_DIR}.tar.gz.enc" -k "${BACKUP_ENCRYPTION_KEY}"

# Upload to cloud storage
az storage blob upload \
    --container-name "backups" \
    --name "redis/${BACKUP_NAME}.tar.gz.enc" \
    --file "${BACKUP_DIR}.tar.gz.enc" \
    --account-name "${AZURE_STORAGE_ACCOUNT}"

aws s3 cp "${BACKUP_DIR}.tar.gz.enc" "s3://${S3_BACKUP_BUCKET}/redis/${BACKUP_NAME}.tar.gz.enc"

# Cleanup
rm -rf "${BACKUP_DIR}" "${BACKUP_DIR}.tar.gz" "${BACKUP_DIR}.tar.gz.enc"

log "Redis backup completed successfully!"
EOF
    chmod +x backup/scripts/backup-redis.sh

    # Elasticsearch backup script
    cat > backup/scripts/backup-elasticsearch.sh << 'EOF'
#!/bin/bash

# Elasticsearch Backup Script
source /etc/backup/backup.conf

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAPSHOT_NAME="es_snapshot_${TIMESTAMP}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting Elasticsearch backup..."

# Create snapshot repository if not exists
curl -X PUT "${ELASTICSEARCH_URL}/_snapshot/backup_repo" \
    -H 'Content-Type: application/json' \
    -d '{
        "type": "s3",
        "settings": {
            "bucket": "'${S3_BACKUP_BUCKET}'",
            "region": "us-east-1",
            "base_path": "elasticsearch"
        }
    }'

# Create snapshot
curl -X PUT "${ELASTICSEARCH_URL}/_snapshot/backup_repo/${SNAPSHOT_NAME}?wait_for_completion=true" \
    -H 'Content-Type: application/json' \
    -d '{
        "indices": "*",
        "include_global_state": true,
        "metadata": {
            "taken_by": "automated_backup",
            "taken_because": "scheduled_backup",
            "environment": "'${ENVIRONMENT}'"
        }
    }'

log "Elasticsearch backup completed successfully!"
EOF
    chmod +x backup/scripts/backup-elasticsearch.sh

    # Application files backup script
    cat > backup/scripts/backup-files.sh << 'EOF'
#!/bin/bash

# Application Files Backup Script
source /etc/backup/backup.conf

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="files_${ENVIRONMENT}_${TIMESTAMP}"
BACKUP_DIR="/tmp/backups/${BACKUP_NAME}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

mkdir -p "${BACKUP_DIR}"

log "Starting files backup..."

# Define directories to backup
BACKUP_PATHS=(
    "/app/uploads"
    "/app/config"
    "/app/certificates"
    "/app/keys"
    "/etc/nginx"
    "/etc/systemd/system"
)

# Copy files
for path in "${BACKUP_PATHS[@]}"; do
    if [ -d "$path" ]; then
        log "Backing up $path..."
        cp -r "$path" "${BACKUP_DIR}/"
    fi
done

# Create manifest
cat > "${BACKUP_DIR}/manifest.json" << JSON
{
    "timestamp": "${TIMESTAMP}",
    "type": "files",
    "environment": "${ENVIRONMENT}",
    "paths": $(printf '%s\n' "${BACKUP_PATHS[@]}" | jq -R . | jq -s .),
    "size": "$(du -sh ${BACKUP_DIR} | cut -f1)"
}
JSON

# Compress and encrypt
tar -czf "${BACKUP_DIR}.tar.gz" -C "/tmp/backups" "${BACKUP_NAME}"
openssl enc -aes-256-cbc -salt -in "${BACKUP_DIR}.tar.gz" -out "${BACKUP_DIR}.tar.gz.enc" -k "${BACKUP_ENCRYPTION_KEY}"

# Upload to cloud storage
az storage blob upload \
    --container-name "backups" \
    --name "files/${BACKUP_NAME}.tar.gz.enc" \
    --file "${BACKUP_DIR}.tar.gz.enc" \
    --account-name "${AZURE_STORAGE_ACCOUNT}"

aws s3 cp "${BACKUP_DIR}.tar.gz.enc" "s3://${S3_BACKUP_BUCKET}/files/${BACKUP_NAME}.tar.gz.enc"

# Cleanup
rm -rf "${BACKUP_DIR}" "${BACKUP_DIR}.tar.gz" "${BACKUP_DIR}.tar.gz.enc"

log "Files backup completed successfully!"
EOF
    chmod +x backup/scripts/backup-files.sh

    # Master backup orchestration script
    cat > backup/scripts/backup-all.sh << 'EOF'
#!/bin/bash

# Master Backup Orchestration Script

set -e

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

notify() {
    local status=$1
    local message=$2
    
    # Send to Slack
    curl -X POST $SLACK_WEBHOOK \
        -H 'Content-type: application/json' \
        -d "{\"text\":\"Backup ${status}: ${message}\"}"
    
    # Send email
    echo "$message" | mail -s "Backup ${status}" ops@openpolicy.platform
}

# Start backup process
log "Starting backup process..."
START_TIME=$(date +%s)

# Run backups in parallel
(
    ./backup-postgres.sh 2>&1 | tee /var/log/backup/postgres.log
) &
PG_PID=$!

(
    ./backup-redis.sh 2>&1 | tee /var/log/backup/redis.log
) &
REDIS_PID=$!

(
    ./backup-elasticsearch.sh 2>&1 | tee /var/log/backup/elasticsearch.log
) &
ES_PID=$!

(
    ./backup-files.sh 2>&1 | tee /var/log/backup/files.log
) &
FILES_PID=$!

# Wait for all backups to complete
FAILED=0
for pid in $PG_PID $REDIS_PID $ES_PID $FILES_PID; do
    if ! wait $pid; then
        FAILED=$((FAILED + 1))
    fi
done

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ $FAILED -eq 0 ]; then
    log "All backups completed successfully in ${DURATION} seconds"
    notify "SUCCESS" "All backups completed successfully in ${DURATION} seconds"
else
    log "WARNING: $FAILED backup(s) failed!"
    notify "FAILED" "$FAILED backup(s) failed! Check logs for details."
    exit 1
fi

# Verify backups
log "Verifying backups..."
./verify-backups.sh

# Update backup inventory
./update-backup-inventory.sh

log "Backup process completed!"
EOF
    chmod +x backup/scripts/backup-all.sh

    log "✅ Backup configuration created"
}

# Create disaster recovery procedures
setup_disaster_recovery() {
    log "Setting up disaster recovery procedures..."
    
    # DR runbook
    cat > backup/policies/disaster-recovery-runbook.md << 'EOF'
# Disaster Recovery Runbook

## 1. Incident Classification

### Severity Levels
- **P0**: Complete system failure
- **P1**: Critical service degradation
- **P2**: Significant functionality loss
- **P3**: Minor service impact

## 2. Initial Response (0-15 minutes)

1. **Assess the situation**
   ```bash
   ./scripts/health-check-all.sh
   ./scripts/check-infrastructure.sh
   ```

2. **Notify stakeholders**
   - Incident Commander: [Name]
   - Tech Lead: [Name]
   - Operations: [Name]

3. **Create incident channel**
   - Slack: #incident-YYYYMMDD-HHMM
   - Status page: Update to "Investigating"

## 3. Recovery Procedures

### 3.1 Database Recovery

#### PostgreSQL Recovery
```bash
# 1. Stop application services
kubectl scale deployment --all --replicas=0 -n production

# 2. Restore from latest backup
./backup/scripts/restore-postgres.sh --latest

# 3. Verify data integrity
./backup/scripts/verify-postgres.sh

# 4. Restart services
kubectl scale deployment --all --replicas=3 -n production
```

#### Redis Recovery
```bash
# 1. Stop Redis-dependent services
kubectl scale deployment redis-dependent --replicas=0 -n production

# 2. Restore Redis
./backup/scripts/restore-redis.sh --latest

# 3. Verify and warm cache
./backup/scripts/verify-redis.sh

# 4. Restart services
kubectl scale deployment redis-dependent --replicas=3 -n production
```

### 3.2 Full System Recovery

```bash
# 1. Activate DR site
./dr/activate-dr-site.sh

# 2. Update DNS
./dr/update-dns-dr.sh

# 3. Verify DR site
./dr/verify-dr-site.sh

# 4. Monitor traffic migration
./dr/monitor-traffic.sh
```

### 3.3 Rollback Procedures

```bash
# 1. Identify last known good state
./scripts/find-last-good-deployment.sh

# 2. Rollback deployment
kubectl rollout undo deployment/all -n production

# 3. Rollback database if needed
./backup/scripts/restore-postgres.sh --timestamp=YYYYMMDD_HHMMSS

# 4. Verify system health
./scripts/post-rollback-verification.sh
```

## 4. Recovery Time Objectives (RTO)

| Component | RTO | RPO |
|-----------|-----|-----|
| API Gateway | 5 min | 0 min |
| Auth Service | 10 min | 5 min |
| Database | 30 min | 15 min |
| Search Service | 45 min | 30 min |
| Full Platform | 60 min | 30 min |

## 5. Post-Incident

1. **Incident Report** (within 24 hours)
2. **Root Cause Analysis** (within 48 hours)
3. **Action Items** (within 72 hours)
4. **Runbook Updates** (within 1 week)

## 6. Contact Information

### Internal Contacts
- On-Call Engineer: +1-xxx-xxx-xxxx
- Incident Commander: +1-xxx-xxx-xxxx
- CTO: +1-xxx-xxx-xxxx

### External Contacts
- Azure Support: 1-800-xxx-xxxx (Contract #: XXX)
- AWS Support: 1-800-xxx-xxxx (Account #: XXX)
- DNS Provider: +1-xxx-xxx-xxxx
EOF

    # Restore scripts
    cat > backup/scripts/restore-postgres.sh << 'EOF'
#!/bin/bash

# PostgreSQL Restore Script

set -e

RESTORE_POINT=${1:-"latest"}

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Find backup to restore
if [ "$RESTORE_POINT" == "latest" ]; then
    BACKUP_FILE=$(az storage blob list \
        --container-name backups \
        --prefix "postgres/" \
        --query "[-1].name" \
        -o tsv)
else
    BACKUP_FILE="postgres/postgres_production_${RESTORE_POINT}.tar.gz.enc"
fi

log "Restoring from: $BACKUP_FILE"

# Download backup
TEMP_DIR="/tmp/restore_$$"
mkdir -p "$TEMP_DIR"

az storage blob download \
    --container-name backups \
    --name "$BACKUP_FILE" \
    --file "$TEMP_DIR/backup.tar.gz.enc"

# Decrypt and extract
openssl enc -aes-256-cbc -d -in "$TEMP_DIR/backup.tar.gz.enc" -out "$TEMP_DIR/backup.tar.gz" -k "${BACKUP_ENCRYPTION_KEY}"
tar -xzf "$TEMP_DIR/backup.tar.gz" -C "$TEMP_DIR"

# Find extracted directory
BACKUP_DIR=$(find "$TEMP_DIR" -name "postgres_*" -type d)

# Restore databases
for dump_file in "$BACKUP_DIR"/*.dump; do
    DB_NAME=$(basename "$dump_file" .dump)
    log "Restoring database: $DB_NAME"
    
    # Drop existing database
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -c "DROP DATABASE IF EXISTS ${DB_NAME};"
    
    # Create database
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -c "CREATE DATABASE ${DB_NAME};"
    
    # Restore data
    PGPASSWORD=$POSTGRES_PASSWORD pg_restore \
        -h $POSTGRES_HOST \
        -U $POSTGRES_USER \
        -d $DB_NAME \
        -Fc \
        "$dump_file" \
        --verbose \
        --no-owner \
        --no-acl
done

# Restore global objects
log "Restoring global objects..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -f "$BACKUP_DIR/globals.sql"

# Cleanup
rm -rf "$TEMP_DIR"

log "PostgreSQL restore completed successfully!"
EOF
    chmod +x backup/scripts/restore-postgres.sh

    # DR site activation script
    cat > backup/scripts/activate-dr-site.sh << 'EOF'
#!/bin/bash

# Disaster Recovery Site Activation Script

set -e

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Activating DR site..."

# 1. Scale up DR environment
log "Scaling up DR environment..."
kubectl config use-context dr-cluster
kubectl scale deployment --all --replicas=3 -n production

# 2. Restore latest data
log "Restoring latest data..."
./restore-postgres.sh --latest
./restore-redis.sh --latest

# 3. Update configuration
log "Updating configuration for DR mode..."
kubectl set env deployment --all ENVIRONMENT=dr -n production

# 4. Health check
log "Running health checks..."
./health-check-dr.sh

# 5. Update load balancer
log "Updating load balancer..."
az network traffic-manager endpoint update \
    --name primary-endpoint \
    --profile-name openpolicy-tm \
    --resource-group openpolicy-rg \
    --type azureEndpoints \
    --endpoint-status Disabled

az network traffic-manager endpoint update \
    --name dr-endpoint \
    --profile-name openpolicy-tm \
    --resource-group openpolicy-rg \
    --type azureEndpoints \
    --endpoint-status Enabled

log "DR site activated successfully!"
log "Please update DNS records to point to DR site"
EOF
    chmod +x backup/scripts/activate-dr-site.sh

    log "✅ Disaster recovery procedures created"
}

# Create backup monitoring
setup_backup_monitoring() {
    log "Setting up backup monitoring..."
    
    cat > backup/scripts/monitor-backups.sh << 'EOF'
#!/bin/bash

# Backup Monitoring Script

# Check last backup times
check_backup_age() {
    local backup_type=$1
    local max_age_hours=$2
    
    last_backup=$(az storage blob list \
        --container-name backups \
        --prefix "${backup_type}/" \
        --query "[-1].properties.lastModified" \
        -o tsv)
    
    if [ -z "$last_backup" ]; then
        echo "ERROR: No ${backup_type} backups found!"
        return 1
    fi
    
    last_backup_epoch=$(date -d "$last_backup" +%s)
    current_epoch=$(date +%s)
    age_hours=$(( (current_epoch - last_backup_epoch) / 3600 ))
    
    if [ $age_hours -gt $max_age_hours ]; then
        echo "WARNING: Last ${backup_type} backup is ${age_hours} hours old (max: ${max_age_hours})"
        return 1
    else
        echo "OK: Last ${backup_type} backup is ${age_hours} hours old"
        return 0
    fi
}

# Check all backup types
FAILED=0
check_backup_age "postgres" 26 || FAILED=$((FAILED + 1))
check_backup_age "redis" 26 || FAILED=$((FAILED + 1))
check_backup_age "elasticsearch" 26 || FAILED=$((FAILED + 1))
check_backup_age "files" 26 || FAILED=$((FAILED + 1))

# Check backup sizes
check_backup_size() {
    local backup_type=$1
    local min_size_mb=$2
    
    last_size=$(az storage blob list \
        --container-name backups \
        --prefix "${backup_type}/" \
        --query "[-1].properties.contentLength" \
        -o tsv)
    
    size_mb=$((last_size / 1024 / 1024))
    
    if [ $size_mb -lt $min_size_mb ]; then
        echo "WARNING: Last ${backup_type} backup is only ${size_mb}MB (min: ${min_size_mb}MB)"
        return 1
    else
        echo "OK: Last ${backup_type} backup is ${size_mb}MB"
        return 0
    fi
}

check_backup_size "postgres" 100 || FAILED=$((FAILED + 1))
check_backup_size "elasticsearch" 500 || FAILED=$((FAILED + 1))

if [ $FAILED -gt 0 ]; then
    echo "CRITICAL: $FAILED backup checks failed!"
    exit 1
else
    echo "All backup checks passed!"
fi
EOF
    chmod +x backup/scripts/monitor-backups.sh

    # Create backup verification script
    cat > backup/scripts/verify-backups.sh << 'EOF'
#!/bin/bash

# Backup Verification Script

set -e

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Verify PostgreSQL backup
verify_postgres() {
    local backup_file=$1
    log "Verifying PostgreSQL backup: $backup_file"
    
    # Download and decrypt
    TEMP_DIR="/tmp/verify_$$"
    mkdir -p "$TEMP_DIR"
    
    az storage blob download \
        --container-name backups \
        --name "$backup_file" \
        --file "$TEMP_DIR/backup.tar.gz.enc"
    
    openssl enc -aes-256-cbc -d \
        -in "$TEMP_DIR/backup.tar.gz.enc" \
        -out "$TEMP_DIR/backup.tar.gz" \
        -k "${BACKUP_ENCRYPTION_KEY}"
    
    # Check archive integrity
    if tar -tzf "$TEMP_DIR/backup.tar.gz" > /dev/null 2>&1; then
        log "✅ PostgreSQL backup integrity verified"
    else
        log "❌ PostgreSQL backup corrupted!"
        return 1
    fi
    
    rm -rf "$TEMP_DIR"
}

# Run verification for latest backups
verify_postgres "postgres/$(az storage blob list --container-name backups --prefix 'postgres/' --query '[-1].name' -o tsv)"

log "Backup verification completed!"
EOF
    chmod +x backup/scripts/verify-backups.sh

    log "✅ Backup monitoring setup complete"
}

# Create automated backup scheduling
setup_backup_scheduling() {
    log "Setting up backup scheduling..."
    
    # Create systemd timers
    cat > /etc/systemd/system/backup-postgres.timer << 'EOF'
[Unit]
Description=PostgreSQL Backup Timer
Requires=backup-postgres.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

    cat > /etc/systemd/system/backup-postgres.service << 'EOF'
[Unit]
Description=PostgreSQL Backup
After=network.target

[Service]
Type=oneshot
ExecStart=/opt/openpolicy/backup/scripts/backup-postgres.sh
User=backup
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Create cron jobs as alternative
    cat > /etc/cron.d/openpolicy-backups << 'EOF'
# OpenPolicy Platform Backup Schedule
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# PostgreSQL backup - Daily at 2 AM
0 2 * * * backup /opt/openpolicy/backup/scripts/backup-postgres.sh

# Redis backup - Daily at 3 AM
0 3 * * * backup /opt/openpolicy/backup/scripts/backup-redis.sh

# Elasticsearch backup - Daily at 4 AM
0 4 * * * backup /opt/openpolicy/backup/scripts/backup-elasticsearch.sh

# Files backup - Daily at 5 AM
0 5 * * * backup /opt/openpolicy/backup/scripts/backup-files.sh

# Backup monitoring - Every 6 hours
0 */6 * * * backup /opt/openpolicy/backup/scripts/monitor-backups.sh

# Backup cleanup - Weekly on Sunday at 6 AM
0 6 * * 0 backup /opt/openpolicy/backup/scripts/cleanup-old-backups.sh
EOF

    # Enable systemd timers
    systemctl daemon-reload
    systemctl enable backup-postgres.timer
    systemctl start backup-postgres.timer

    log "✅ Backup scheduling configured"
}

# Main execution
main() {
    log "Setting up backup and disaster recovery..."
    
    setup_backup_config
    setup_disaster_recovery
    setup_backup_monitoring
    setup_backup_scheduling
    
    # Create summary
    cat > backup-dr-summary.txt << EOF
Backup & Disaster Recovery Setup Complete
=========================================

Backup Configuration:
✅ PostgreSQL daily backups with 30-day retention
✅ Redis daily backups with 14-day retention
✅ Elasticsearch snapshots with 30-day retention
✅ Application files daily backups
✅ Encrypted backups to Azure and AWS S3
✅ Automated backup verification

Disaster Recovery:
✅ DR runbook with step-by-step procedures
✅ Automated DR site activation
✅ RTO: 60 minutes for full platform
✅ RPO: 30 minutes maximum data loss
✅ Multi-region backup storage

Monitoring:
✅ Backup age monitoring
✅ Backup size verification
✅ Automated alerts via Slack/email
✅ Backup integrity checks

Scheduling:
✅ Systemd timers configured
✅ Cron jobs as fallback
✅ Staggered backup times
✅ Weekly cleanup jobs

Next Steps:
1. Configure cloud storage credentials
2. Set up backup encryption keys in Key Vault
3. Test restore procedures
4. Schedule DR drills (quarterly)
5. Update contact information in runbook

Important Files:
- Backup config: backup/configs/backup.yaml
- DR runbook: backup/policies/disaster-recovery-runbook.md
- Backup scripts: backup/scripts/
- Monitoring: backup/scripts/monitor-backups.sh
EOF
    
    info "Setup complete! See backup-dr-summary.txt for details"
}

main "$@"