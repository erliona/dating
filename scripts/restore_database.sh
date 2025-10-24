#!/usr/bin/env bash
# Restore PostgreSQL database from backup
# This script restores a database from a backup file

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
DB_NAME="${POSTGRES_DB:-dating}"
DB_USER="${POSTGRES_USER:-dating}"

usage() {
    cat <<EOF
Usage: $0 [OPTIONS] BACKUP_FILE

Restore PostgreSQL database from a backup file.

Arguments:
  BACKUP_FILE          Path to backup file (.sql or .sql.gz)

Options:
  -h, --help          Show this help message
  -f, --force         Skip confirmation prompt
  --drop-existing     Drop and recreate database before restore (⚠️  dangerous!)

Examples:
  # Restore from compressed backup
  $0 backups/db_backup_20241003.sql.gz

  # Restore without confirmation
  $0 -f backups/db_backup_20241003.sql.gz

  # Drop existing database and restore (⚠️  DELETES ALL CURRENT DATA!)
  $0 --drop-existing backups/db_backup_20241003.sql.gz

Environment Variables:
  COMPOSE_FILE        Docker Compose file to use (default: docker-compose.yml)
  POSTGRES_DB         Database name (default: dating)
  POSTGRES_USER       Database user (default: dating)

EOF
    exit 0
}

# Parse arguments
FORCE=false
DROP_EXISTING=false
BACKUP_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        --drop-existing)
            DROP_EXISTING=true
            shift
            ;;
        -*)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
        *)
            if [ -z "$BACKUP_FILE" ]; then
                BACKUP_FILE="$1"
            else
                echo -e "${RED}Error: Multiple backup files specified${NC}"
                exit 1
            fi
            shift
            ;;
    esac
done

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: No backup file specified${NC}"
    echo "Use -h or --help for usage information"
    exit 1
fi

echo "========================================"
echo "Database Restore Utility"
echo "========================================"
echo ""

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup file not found: $BACKUP_FILE${NC}"
    echo ""
    echo "Available backups:"
    ls -lht backups/*.sql* 2>/dev/null | head -10 | awk '{print "  " $9 " (" $5 ", " $6 " " $7 " " $8 ")"}' || echo "  No backups found in ./backups/"
    exit 1
fi

# Check if Docker Compose is running
if ! docker compose -f "$COMPOSE_FILE" ps db | grep -q "Up"; then
    echo -e "${RED}❌ Database container is not running!${NC}"
    echo ""
    echo "Start the database with:"
    echo "  docker compose up -d db"
    exit 1
fi

echo "📋 Restore Configuration:"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Backup file: $BACKUP_FILE"
echo "  File size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo ""

# Check database connectivity
echo "🔍 Checking database connectivity..."
if ! docker compose -f "$COMPOSE_FILE" exec -T db pg_isready -U "$DB_USER" >/dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to database!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database is ready${NC}"
echo ""

# Get current database statistics
echo "📊 Current Database Statistics:"
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
" 2>/dev/null | sed 's/^/  /' || echo "  (Could not retrieve statistics)"

echo ""

# Warning if not forced
if [ "$FORCE" = false ]; then
    echo -e "${YELLOW}⚠️  WARNING: This will restore the database from backup.${NC}"
    echo ""
    if [ "$DROP_EXISTING" = true ]; then
        echo -e "${RED}⚠️  DROP_EXISTING is enabled - this will DELETE ALL CURRENT DATA!${NC}"
        echo ""
    else
        echo "The restore will attempt to add data from the backup."
        echo "This may cause conflicts if data already exists."
        echo ""
    fi
    echo "Do you want to continue? [y/N]"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Restore cancelled."
        exit 0
    fi
    echo ""
fi

# Create a pre-restore backup
echo "💾 Creating pre-restore backup for safety..."
PRE_RESTORE_BACKUP="backups/pre_restore_backup_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p backups
if docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$PRE_RESTORE_BACKUP" 2>/dev/null; then
    gzip -f "$PRE_RESTORE_BACKUP" 2>/dev/null || true
    echo -e "${GREEN}✓ Pre-restore backup created: ${PRE_RESTORE_BACKUP}.gz${NC}"
else
    echo -e "${YELLOW}⚠️  Could not create pre-restore backup (continuing anyway)${NC}"
fi
echo ""

# Drop existing database if requested
if [ "$DROP_EXISTING" = true ]; then
    echo -e "${RED}🗑️  Dropping existing database...${NC}"
    docker compose -f "$COMPOSE_FILE" exec -T db psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || true
    echo "Creating new database..."
    docker compose -f "$COMPOSE_FILE" exec -T db psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null
    echo -e "${GREEN}✓ Database recreated${NC}"
    echo ""
fi

# Restore from backup
echo "📥 Restoring database from backup..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    # Compressed backup
    if gunzip -c "$BACKUP_FILE" | docker compose -f "$COMPOSE_FILE" exec -T db psql -U "$DB_USER" "$DB_NAME" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Restore completed successfully!${NC}"
    else
        echo -e "${RED}❌ Restore failed!${NC}"
        echo ""
        echo "You can try to restore manually:"
        echo "  gunzip -c $BACKUP_FILE | docker compose exec -T db psql -U $DB_USER $DB_NAME"
        exit 1
    fi
else
    # Uncompressed backup
    if docker compose -f "$COMPOSE_FILE" exec -T db psql -U "$DB_USER" "$DB_NAME" < "$BACKUP_FILE" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Restore completed successfully!${NC}"
    else
        echo -e "${RED}❌ Restore failed!${NC}"
        echo ""
        echo "You can try to restore manually:"
        echo "  docker compose exec -T db psql -U $DB_USER $DB_NAME < $BACKUP_FILE"
        exit 1
    fi
fi
echo ""

# Get restored database statistics
echo "📊 Restored Database Statistics:"
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

# Restart bot to reconnect
echo "🔄 Restarting bot to reconnect to database..."
docker compose -f "$COMPOSE_FILE" restart bot
sleep 2
echo -e "${GREEN}✓ Bot restarted${NC}"
echo ""

echo -e "${GREEN}========================================"
echo "Restore Complete!"
echo "========================================${NC}"
echo ""
echo "💡 Next Steps:"
echo "  1. Verify the data is correct:"
echo "     docker compose exec db psql -U $DB_USER $DB_NAME"
echo ""
echo "  2. Check bot logs:"
echo "     docker compose logs -f bot"
echo ""
echo "  3. Test the application to ensure everything works"
echo ""
