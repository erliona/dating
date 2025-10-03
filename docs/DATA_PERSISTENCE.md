# Data Persistence and Backup Guide

## ⚠️ CRITICAL: Database Persistence

**The database IS persistent** - all user profiles, interactions, and settings are stored in Docker volumes that persist across container restarts and updates.

However, certain commands can **permanently delete all data**. This guide explains how to protect your data.

---

## 🚨 Dangerous Commands - NEVER Use Without Backup

### ⛔ The Most Dangerous Command

```bash
docker compose down -v
```

**This command will:**
- ✅ Stop all containers (safe)
- ❌ **DELETE ALL VOLUMES** (dangerous!)
  - All user profiles
  - All interactions and matches
  - All messages
  - All settings
  - All uploaded photos
  - **EVERYTHING** stored in the database

**Data deletion is PERMANENT and IRREVERSIBLE without a backup!**

### When This Command is Used

You might encounter this command in:
- ❌ **Troubleshooting guides** (old documentation)
- ❌ **Stack Overflow answers** (generic advice)
- ❌ **Quick fixes** (dangerous shortcuts)
- ❌ **"Clean slate" approaches** (destroys data)

**NEVER use this command in production without a backup!**

---

## ✅ Safe Commands - Use These Instead

### Stop Containers (Preserves Data)

```bash
# Safe: stops containers but keeps data
docker compose down

# Safe: restart without data loss
docker compose restart

# Safe: restart specific service
docker compose restart bot
```

### Update Application (Preserves Data)

```bash
# Safe: pull latest code
git pull

# Safe: rebuild and restart (data persists)
docker compose up -d --build

# Safe: check running containers
docker compose ps

# Safe: view logs
docker compose logs -f bot
```

---

## 💾 Backup Strategy

### Daily Automated Backups

Create a cron job for daily backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /opt/dating && docker compose exec -T db pg_dump -U dating dating | gzip > /opt/dating/backups/db_$(date +\%Y\%m\%d).sql.gz

# Add weekly cleanup (keep last 30 days)
0 3 * * 0 find /opt/dating/backups -name "db_*.sql.gz" -mtime +30 -delete
```

### Manual Backup

Before any risky operation, create a backup:

```bash
# Create backups directory
mkdir -p ./backups

# Create backup with timestamp
BACKUP_FILE="backups/db_backup_$(date +%Y%m%d_%H%M%S).sql"
docker compose exec db pg_dump -U dating dating > "$BACKUP_FILE"
echo "Backup created: $BACKUP_FILE"

# Compress backup (optional)
gzip "$BACKUP_FILE"

# Verify backup
if [ -f "${BACKUP_FILE}.gz" ]; then
    echo "✓ Backup successful: ${BACKUP_FILE}.gz"
    ls -lh "${BACKUP_FILE}.gz"
else
    echo "❌ Backup failed!"
fi
```

### Backup to Remote Storage

```bash
# Upload to another server
scp backups/db_backup_*.sql.gz user@backup-server:/backups/dating/

# Upload to S3 (requires aws-cli)
aws s3 cp backups/db_backup_*.sql.gz s3://your-bucket/dating-backups/

# Upload to Google Drive (requires rclone)
rclone copy backups/db_backup_*.sql.gz gdrive:dating-backups/
```

---

## 🔄 Restore from Backup

### Restore Recent Backup

```bash
# List available backups
ls -lh backups/

# Restore from backup (database must be running)
BACKUP_FILE="backups/db_backup_20241003_143000.sql"

# If compressed, decompress first
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip < "$BACKUP_FILE" | docker compose exec -T db psql -U dating dating
else
    docker compose exec -T db psql -U dating dating < "$BACKUP_FILE"
fi

# Verify restoration
docker compose exec db psql -U dating dating -c "SELECT COUNT(*) FROM users;"
docker compose exec db psql -U dating dating -c "SELECT COUNT(*) FROM profiles;"
```

### Restore After Data Loss

If you accidentally ran `docker compose down -v`:

```bash
# 1. Start services (creates new empty database)
docker compose up -d

# 2. Wait for database to be ready
sleep 10

# 3. Restore from backup
gunzip < backups/db_backup_latest.sql.gz | docker compose exec -T db psql -U dating dating

# 4. Restart bot to reconnect
docker compose restart bot

# 5. Verify data is back
docker compose exec db psql -U dating dating -c "SELECT COUNT(*) FROM users;"
```

---

## 🔐 Password Change (Safe Method)

If you need to change the database password:

### Method 1: Using PostgreSQL ALTER USER (Recommended)

```bash
# Change password without data loss
docker compose exec db psql -U dating dating -c "ALTER USER dating WITH PASSWORD 'new_password';"

# Update .env file
sed -i 's/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=new_password/' .env

# Restart bot with new password
docker compose restart bot
```

### Method 2: Backup and Restore (If Method 1 Fails)

```bash
# 1. Create backup
BACKUP_FILE="backups/db_backup_$(date +%Y%m%d_%H%M%S).sql"
docker compose exec db pg_dump -U dating dating > "$BACKUP_FILE"

# 2. Verify backup was created
ls -lh "$BACKUP_FILE"

# 3. Copy backup to safe location
cp "$BACKUP_FILE" ~/safe-backups/

# 4. Stop and remove volume
docker compose down -v

# 5. Update password in .env
nano .env  # Change POSTGRES_PASSWORD

# 6. Start with new password
docker compose up -d

# 7. Wait for database
sleep 15

# 8. Restore data
docker compose exec -T db psql -U dating dating < "$BACKUP_FILE"

# 9. Verify restoration
docker compose exec db psql -U dating dating -c "SELECT COUNT(*) FROM users;"
```

---

## 📊 Volume Management

### List Volumes

```bash
# List all Docker volumes
docker volume ls

# Inspect dating database volume
docker volume inspect dating_postgres_data

# Check volume size
docker system df -v | grep dating_postgres_data
```

### Volume Location

Docker volumes are stored in:
- **Linux**: `/var/lib/docker/volumes/`
- **Data path**: `/var/lib/docker/volumes/dating_postgres_data/_data/`

### Volume Backup (Alternative Method)

```bash
# Backup entire volume (slower but includes all PostgreSQL files)
docker run --rm \
  -v dating_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/volume_backup_$(date +%Y%m%d).tar.gz /data
```

---

## 🔍 Monitoring Data Persistence

### Check Database Status

```bash
# Check if database is running
docker compose ps db

# Check database size
docker compose exec db psql -U dating dating -c "
SELECT 
  pg_database.datname,
  pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'dating';"

# Check table sizes
docker compose exec db psql -U dating dating -c "
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Check number of records
docker compose exec db psql -U dating dating -c "
SELECT 
  'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'profiles', COUNT(*) FROM profiles
UNION ALL
SELECT 'interactions', COUNT(*) FROM interactions
UNION ALL
SELECT 'matches', COUNT(*) FROM matches;"
```

### Regular Health Checks

```bash
# Create a monitoring script
cat > scripts/check_db_health.sh << 'EOF'
#!/bin/bash
set -euo pipefail

echo "=== Database Health Check ==="
echo ""

# Check if database is running
if ! docker compose ps db | grep -q "Up"; then
    echo "❌ Database is not running!"
    exit 1
fi

# Check if database is accessible
if ! docker compose exec -T db pg_isready -U dating >/dev/null 2>&1; then
    echo "❌ Database is not ready!"
    exit 1
fi

echo "✓ Database is running and ready"
echo ""

# Check data
echo "Data Summary:"
docker compose exec -T db psql -U dating dating -c "
SELECT 
  'Users' as metric, COUNT(*)::text as value FROM users
UNION ALL
SELECT 'Profiles', COUNT(*)::text FROM profiles
UNION ALL
SELECT 'Matches', COUNT(*)::text FROM matches
UNION ALL
SELECT 'DB Size', pg_size_pretty(pg_database_size('dating'))::text
" -t | sed 's/^/  /'

echo ""
echo "=== Health Check Complete ==="
EOF

chmod +x scripts/check_db_health.sh

# Run the health check
./scripts/check_db_health.sh
```

---

## 📋 Pre-Deployment Checklist

Before any deployment or update:

- [ ] Create a fresh backup
- [ ] Verify backup file exists and is not empty
- [ ] Copy backup to safe location (another server/cloud)
- [ ] Test backup restoration in a separate environment (optional but recommended)
- [ ] Document what you're about to do
- [ ] Have rollback plan ready

---

## 🆘 Emergency Recovery

### If You Lost Data

1. **Don't Panic** - Stop all operations immediately
2. **Check for Backups**:
   ```bash
   ls -lh backups/
   ls -lh ~/safe-backups/
   find /opt/dating -name "*.sql*" -mtime -30
   ```
3. **Check Remote Backups** (if configured)
4. **Restore from Latest Backup** (see restore instructions above)
5. **Verify Restoration**:
   ```bash
   docker compose exec db psql -U dating dating -c "SELECT COUNT(*) FROM users;"
   ```

### If No Backup Exists

1. **Check if volume still exists**:
   ```bash
   docker volume ls | grep postgres_data
   ```
2. **If volume exists, data might be recoverable**:
   ```bash
   # Start services without changing password
   docker compose up -d
   
   # Immediately create backup
   docker compose exec db pg_dump -U dating dating > emergency_backup.sql
   ```

---

## 📚 Additional Resources

- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [Docker Volume Documentation](https://docs.docker.com/storage/volumes/)
- [Disaster Recovery Best Practices](https://www.postgresql.org/docs/current/backup-dump.html)

---

## 🔔 Important Reminders

1. **Volumes are persistent** - They survive container restarts and updates
2. **Only `docker compose down -v` deletes volumes** - Regular restarts are safe
3. **Always backup before risky operations** - Prevention is better than recovery
4. **Test your backups regularly** - A backup you haven't tested is not a real backup
5. **Store backups off-site** - Local backups don't protect against hardware failure

---

## Contact

If you experience data loss or need help with recovery:
1. Check this documentation first
2. Look for backup files in `backups/` directory
3. Contact your system administrator
4. Open an issue on GitHub with details (but never include passwords or sensitive data)
