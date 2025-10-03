# Scripts Directory

Utility scripts for managing the Dating Mini App.

## 🔧 Available Scripts

### Database Management

#### `backup_database.sh`
Create a timestamped backup of the PostgreSQL database.

**Usage:**
```bash
./scripts/backup_database.sh
```

**Features:**
- ✅ Checks database connectivity
- ✅ Shows current database statistics
- ✅ Creates timestamped backup
- ✅ Automatically compresses backup with gzip
- ✅ Shows backup details and size
- ✅ Lists recent backups

**Output:**
- Backup saved to: `backups/db_backup_YYYYMMDD_HHMMSS.sql.gz`

**Example:**
```bash
$ ./scripts/backup_database.sh
========================================
Database Backup Utility
========================================

📋 Backup Configuration:
  Database: dating
  User: dating
  Backup file: backups/db_backup_20241003_120000.sql

🔍 Checking database connectivity...
✓ Database is ready

📊 Database Statistics:
  Users: 1234
  Profiles: 1200
  Interactions: 5678
  Matches: 234
  Database Size: 42 MB

💾 Creating backup...
✓ Backup created successfully!

📦 Compressed Backup:
  File: backups/db_backup_20241003_120000.sql.gz
  Size: 8.4M
```

---

#### `restore_database.sh`
Restore the database from a backup file.

**Usage:**
```bash
# Interactive mode (asks for confirmation)
./scripts/restore_database.sh backups/db_backup_20241003.sql.gz

# Force mode (no confirmation)
./scripts/restore_database.sh -f backups/db_backup_20241003.sql.gz

# Drop existing database and restore (⚠️ dangerous!)
./scripts/restore_database.sh --drop-existing backups/db_backup_20241003.sql.gz
```

**Features:**
- ✅ Validates backup file exists
- ✅ Checks database connectivity
- ✅ Shows current data statistics
- ✅ Creates pre-restore backup for safety
- ✅ Restores from compressed or uncompressed backups
- ✅ Automatically restarts bot after restore
- ✅ Shows restored data statistics

**Options:**
- `-f, --force` - Skip confirmation prompt
- `--drop-existing` - Drop and recreate database before restore (⚠️ deletes current data)
- `-h, --help` - Show help message

**Example:**
```bash
$ ./scripts/restore_database.sh backups/db_backup_20241003.sql.gz
========================================
Database Restore Utility
========================================

📋 Restore Configuration:
  Database: dating
  User: dating
  Backup file: backups/db_backup_20241003.sql.gz
  File size: 8.4M

🔍 Checking database connectivity...
✓ Database is ready

📊 Current Database Statistics:
  Users: 1234
  Profiles: 1200
  ...

⚠️  WARNING: This will restore the database from backup.
Do you want to continue? [y/N] y

💾 Creating pre-restore backup for safety...
✓ Pre-restore backup created: backups/pre_restore_backup_20241003_120100.sql.gz

📥 Restoring database from backup...
✓ Restore completed successfully!

📊 Restored Database Statistics:
  Users: 1100
  Profiles: 1050
  ...

🔄 Restarting bot to reconnect to database...
✓ Bot restarted

========================================
Restore Complete!
========================================
```

---

### Deployment

#### `deploy.sh`
Deploy the application to a remote server over SSH.

**Usage:**
```bash
# Minimal deployment
BOT_TOKEN="123456:ABC" scripts/deploy.sh -H server.example.com -u deploy

# With HTTPS
BOT_TOKEN="123456:ABC" DOMAIN="example.com" ACME_EMAIL="admin@example.com" \
  scripts/deploy.sh -H server.example.com -u deploy
```

See [Deployment Guide](../docs/DEPLOYMENT.md) for details.

---

### Validation

#### `verify-idempotency.sh`
Verify that deployments are idempotent (safe to run multiple times).

**Usage:**
```bash
./scripts/verify-idempotency.sh
```

**Tests:**
- Database migration idempotency
- Log rotation configuration
- Grafana provisioning
- Volume persistence

---

#### `validate-monitoring.sh`
Validate monitoring stack configuration and health.

**Usage:**
```bash
./scripts/validate-monitoring.sh
```

**Checks:**
- Prometheus configuration
- Grafana dashboards
- Loki configuration
- Service health

---

## 🚀 Quick Start

### First-time Setup
```bash
# Make all scripts executable
chmod +x scripts/*.sh
```

### Regular Maintenance
```bash
# Create daily backup (recommended to run via cron)
./scripts/backup_database.sh

# Restore if needed
./scripts/restore_database.sh backups/latest_backup.sql.gz
```

### Set Up Automated Backups
Add to crontab (`crontab -e`):
```bash
# Daily backup at 2 AM
0 2 * * * cd /opt/dating && ./scripts/backup_database.sh >> /var/log/db-backup.log 2>&1

# Weekly cleanup (keep last 30 days)
0 3 * * 0 find /opt/dating/backups -name "db_backup_*.sql.gz" -mtime +30 -delete
```

---

## ⚠️ Safety Notes

### Before Any Risky Operation

Always create a backup first:
```bash
./scripts/backup_database.sh
```

### Before Password Changes

1. Create backup
2. Test restore in development environment
3. Then change password (see [Data Persistence Guide](../docs/DATA_PERSISTENCE.md))

### Before Major Updates

1. Create backup
2. Test update in staging environment
3. Create another backup just before production update
4. Then deploy

---

## 📚 Related Documentation

- [Data Persistence & Backup Guide](../docs/DATA_PERSISTENCE.md) - Comprehensive backup/restore procedures
- [Deployment Guide](../docs/DEPLOYMENT.md) - Production deployment instructions
- [Deployment Idempotency](../docs/DEPLOYMENT_IDEMPOTENCY.md) - Safe deployment practices
- [Quick Reference](../QUICK_REFERENCE.md) - Common commands and operations

---

## 🆘 Troubleshooting

### Script Not Executable
```bash
chmod +x scripts/backup_database.sh
chmod +x scripts/restore_database.sh
```

### Database Connection Failed
```bash
# Check if database is running
docker compose ps db

# Check database logs
docker compose logs db

# Wait for database to be ready
docker compose up -d db
sleep 10
```

### Backup File Not Found
```bash
# List available backups
ls -lh backups/

# Check if backups directory exists
mkdir -p backups
```

### Restore Failed
```bash
# Check backup file integrity
gunzip -t backups/db_backup_*.sql.gz

# Try manual restore
gunzip < backups/db_backup_*.sql.gz | docker compose exec -T db psql -U dating dating
```

---

## 💡 Tips

1. **Store backups off-site** - Don't keep all backups on the same server
2. **Test restores regularly** - A backup you haven't tested is not a real backup
3. **Automate backups** - Set up cron jobs for daily automated backups
4. **Monitor backup size** - Sudden changes might indicate issues
5. **Document your process** - Keep notes on when/why you restore backups

---

## 🔗 Quick Links

- [Main README](../README.md)
- [Project Status](../PROJECT_STATUS.md)
- [Contributing Guide](../CONTRIBUTING.md)
