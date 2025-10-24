#!/usr/bin/env bash
# Backup PostgreSQL database
# This script creates a timestamped backup of the database

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
DB_NAME="${POSTGRES_DB:-dating}"
DB_USER="${POSTGRES_USER:-dating}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql"

echo "========================================"
echo "Database Backup Utility"
echo "========================================"
echo ""

# Check if Docker Compose is running
if ! docker compose -f "$COMPOSE_FILE" ps db | grep -q "Up"; then
    echo -e "${RED}❌ Database container is not running!${NC}"
    echo ""
    echo "Start the database with:"
    echo "  docker compose up -d db"
    exit 1
fi

echo "📋 Backup Configuration:"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Backup file: $BACKUP_FILE"
echo ""

# Check database connectivity
echo "🔍 Checking database connectivity..."
if ! docker compose -f "$COMPOSE_FILE" exec -T db pg_isready -U "$DB_USER" >/dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to database!${NC}"
    echo ""
    echo "Possible causes:"
    echo "  - Database is still starting up (wait a few seconds and try again)"
    echo "  - Wrong credentials in .env file"
    echo "  - Database container is unhealthy"
    exit 1
fi

echo -e "${GREEN}✓ Database is ready${NC}"
echo ""

# Get database statistics before backup
echo "📊 Database Statistics:"
docker compose -f "$COMPOSE_FILE" exec -T db psql -U "$DB_USER" "$DB_NAME" -t -c "
SELECT 
  'Users: ' || COUNT(*)::text FROM users
UNION ALL
SELECT 'Profiles: ' || COUNT(*)::text FROM profiles
UNION ALL
SELECT 'Interactions: ' || COUNT(*)::text FROM interactions
UNION ALL
SELECT 'Matches: ' || COUNT(*)::text FROM matches
UNION ALL
SELECT 'Database Size: ' || pg_size_pretty(pg_database_size('$DB_NAME'))::text
" 2>/dev/null | sed 's/^/  /'

echo ""

# Create backup
echo "💾 Creating backup..."
if docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null; then
    # Verify backup file is not empty
    if [ -s "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo -e "${GREEN}✓ Backup created successfully!${NC}"
        echo ""
        echo "📁 Backup Details:"
        echo "  File: $BACKUP_FILE"
        echo "  Size: $BACKUP_SIZE"
        echo ""
        
        # Compress backup
        echo "🗜️  Compressing backup..."
        if gzip -f "$BACKUP_FILE"; then
            COMPRESSED_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
            echo -e "${GREEN}✓ Backup compressed successfully!${NC}"
            echo ""
            echo "📦 Compressed Backup:"
            echo "  File: ${BACKUP_FILE}.gz"
            echo "  Size: $COMPRESSED_SIZE"
            echo ""
        else
            echo -e "${YELLOW}⚠️  Compression failed, keeping uncompressed backup${NC}"
            echo ""
        fi
        
        # List recent backups
        echo "📋 Recent Backups:"
        ls -lht "$BACKUP_DIR"/*.sql.gz 2>/dev/null | head -5 | awk '{print "  " $9 " (" $5 ", " $6 " " $7 " " $8 ")"}' || echo "  No other backups found"
        echo ""
        
        echo -e "${GREEN}========================================"
        echo "Backup Complete!"
        echo "========================================${NC}"
        echo ""
        echo "💡 Next Steps:"
        echo "  1. Copy backup to safe location:"
        echo "     scp ${BACKUP_FILE}.gz user@backup-server:/backups/"
        echo ""
        echo "  2. Test restoration (in separate environment):"
        echo "     gunzip < ${BACKUP_FILE}.gz | docker compose exec -T db psql -U $DB_USER $DB_NAME"
        echo ""
        echo "  3. Set up automated daily backups:"
        echo "     See docs/DATA_PERSISTENCE.md for cron configuration"
        echo ""
    else
        echo -e "${RED}❌ Backup file is empty!${NC}"
        rm -f "$BACKUP_FILE"
        exit 1
    fi
else
    echo -e "${RED}❌ Backup failed!${NC}"
    echo ""
    echo "Check:"
    echo "  - Database logs: docker compose logs db"
    echo "  - Disk space: df -h"
    echo "  - Permissions: ls -la $BACKUP_DIR"
    rm -f "$BACKUP_FILE"
    exit 1
fi
