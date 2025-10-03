#!/usr/bin/env bash
# Deploy the application to a remote server over SSH.
#
# This script now mirrors the simplified CI/CD workflow: it only requires
# user, host, and SSH key. The script handles all server preparation
# (Docker installation, directory setup) automatically.
#
# IMPORTANT: For production deployments with HTTPS:
# - Set environment variables: DOMAIN, ACME_EMAIL
# - DNS must point to your server IP
# - Ports 80 and 443 must be open in firewall
# - Traefik will automatically obtain Let's Encrypt SSL certificates

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/deploy.sh -H <host> -u <user> [options]

Required arguments:
  -H <host>         SSH host name or IP address.
  -u <user>         SSH user name with sudo permissions.

Optional arguments:
  -t <bot_token>    Telegram bot token (can also use BOT_TOKEN env var).
  -D <domain>       Domain name for HTTPS (can also use DOMAIN env var).
  -E <email>        Email for Let's Encrypt (can also use ACME_EMAIL env var).
  -d <remote_path>  Directory on the remote host (default: /opt/dating).
  -p <port>         SSH port (default: 22).
  -i <identity>     Path to a private SSH key. Falls back to ssh-agent if omitted.
  -h                Show this help message.

Environment variables (alternatives to command-line options):
  BOT_TOKEN         Telegram bot token
  DOMAIN            Domain name for HTTPS
  ACME_EMAIL        Email for Let's Encrypt notifications
  POSTGRES_DB       PostgreSQL database name (default: dating)
  POSTGRES_USER     PostgreSQL user (default: dating)
  POSTGRES_PASSWORD PostgreSQL password (auto-generated if not set)

Examples:
  # Minimal deployment (bot token required)
  BOT_TOKEN="123456:ABC" scripts/deploy.sh -H server.example.com -u deploy

  # With HTTPS
  BOT_TOKEN="123456:ABC" DOMAIN="example.com" ACME_EMAIL="admin@example.com" \
    scripts/deploy.sh -H server.example.com -u deploy

  # Using command-line arguments
  scripts/deploy.sh -H server.example.com -u deploy \
    -t "123456:ABC" -D example.com -E admin@example.com

For local development without HTTPS:
  Use docker-compose.dev.yml instead of this script.
USAGE
}

HOST=""
USER=""
PORT="22"
REMOTE_PATH="/opt/dating"
BOT_TOKEN="${BOT_TOKEN:-}"
DOMAIN="${DOMAIN:-}"
ACME_EMAIL="${ACME_EMAIL:-}"
IDENTITY=""

while getopts ":H:u:t:D:E:d:p:i:h" opt; do
  case "$opt" in
    H) HOST="$OPTARG" ;;
    u) USER="$OPTARG" ;;
    t) BOT_TOKEN="$OPTARG" ;;
    D) DOMAIN="$OPTARG" ;;
    E) ACME_EMAIL="$OPTARG" ;;
    d) REMOTE_PATH="$OPTARG" ;;
    p) PORT="$OPTARG" ;;
    i) IDENTITY="$OPTARG" ;;
    h)
      usage
      exit 0
      ;;
    :)
      echo "Missing argument for -$OPTARG" >&2
      usage >&2
      exit 1
      ;;
    *)
      echo "Unknown option: -$OPTARG" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$HOST" || -z "$USER" ]]; then
  echo "Error: host and user are required." >&2
  usage >&2
  exit 1
fi

if [[ -z "$BOT_TOKEN" ]]; then
  echo "Error: BOT_TOKEN is required (use -t option or BOT_TOKEN env var)." >&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

# Setup SSH connection parameters before using them
SSH_ARGS=(-p "$PORT")
SCP_ARGS=(-P "$PORT")
if [[ -n "$IDENTITY" ]]; then
  SSH_ARGS+=(-i "$IDENTITY")
  SCP_ARGS+=(-i "$IDENTITY")
fi

REMOTE="${USER}@${HOST}"

# Generate .env file
echo "🔧 Generating environment configuration"

POSTGRES_DB="${POSTGRES_DB:-dating}"
POSTGRES_USER="${POSTGRES_USER:-dating}"

# Try to get existing POSTGRES_PASSWORD from server to avoid database connection issues
EXISTING_PASSWORD=""
echo "🔍 Checking for existing database password on server..."
if ssh "${SSH_ARGS[@]}" "$REMOTE" "test -f $REMOTE_PATH/.env" 2>/dev/null; then
  EXISTING_PASSWORD=$(ssh "${SSH_ARGS[@]}" "$REMOTE" "grep '^POSTGRES_PASSWORD=' $REMOTE_PATH/.env 2>/dev/null | cut -d'=' -f2-" || echo "")
  if [ -n "$EXISTING_PASSWORD" ]; then
    echo "✓ Found existing database password, reusing it to maintain database connectivity"
  fi
fi

# Use existing password if found, otherwise use provided or generate new one
if [ -n "$EXISTING_PASSWORD" ]; then
  POSTGRES_PASSWORD="$EXISTING_PASSWORD"
elif [ -n "${POSTGRES_PASSWORD:-}" ]; then
  POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
else
  # Generate a URL-safe password to avoid special characters that need encoding
  # Use alphanumeric characters only to prevent issues with URL parsing
  POSTGRES_PASSWORD="$(openssl rand -base64 32 | tr -dc 'A-Za-z0-9' | head -c 32)"
  echo "⚠️  Generated new database password (this may require database reset on first deployment)"
fi

cat > "$TMP_DIR/.env.deploy" <<EOF
# Bot Configuration (Required)
BOT_TOKEN=${BOT_TOKEN}

# Database Configuration
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
EOF

# Add HTTPS config if DOMAIN is provided
if [ -n "${DOMAIN}" ]; then
  cat >> "$TMP_DIR/.env.deploy" <<EOF

# HTTPS Configuration (Production)
DOMAIN=${DOMAIN}
WEBAPP_URL=https://${DOMAIN}
ACME_EMAIL=${ACME_EMAIL:-admin@${DOMAIN}}
EOF
  
  # Add staging CA server if specified
  if [ -n "${ACME_CA_SERVER:-}" ]; then
    echo "ACME_CA_SERVER=${ACME_CA_SERVER}" >> "$TMP_DIR/.env.deploy"
  fi
  
  echo "✓ HTTPS configuration enabled for domain: ${DOMAIN}"
else
  cat >> "$TMP_DIR/.env.deploy" <<EOF

# HTTPS Configuration (Development)
DOMAIN=localhost
WEBAPP_URL=https://localhost
EOF
  echo "⚠️  No DOMAIN specified - using localhost (HTTPS certificates won't be issued)"
fi

# Create an archive of the project
echo "📦 Creating deployment archive"
tar -czf "$TMP_DIR/release.tar.gz" \
  Dockerfile \
  docker-compose.yml \
  requirements.txt \
  alembic.ini \
  bot \
  docker \
  migrations \
  webapp \
  -C "$TMP_DIR" .env.deploy

echo ""
echo "🚀 Deploying to $REMOTE:$REMOTE_PATH"
echo ""

# Step 1: Prepare server (install Docker, create directories)
echo "📦 Preparing server..."
ssh "${SSH_ARGS[@]}" "$REMOTE" "REMOTE_PATH=$(printf '%q' "$REMOTE_PATH") bash -s" <<'REMOTE_PREP'
set -euo pipefail

echo "=== Server Preparation Started ==="

# Create deployment directory
echo "📁 Creating deployment directory: $REMOTE_PATH"
sudo mkdir -p "$REMOTE_PATH"
sudo chown -R "$USER:$USER" "$REMOTE_PATH"

# Check and install Docker
if ! command -v docker >/dev/null 2>&1; then
  echo "🐋 Docker not found. Installing Docker..."
  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  sudo sh /tmp/get-docker.sh
  rm /tmp/get-docker.sh
  
  # Add current user to docker group
  sudo usermod -aG docker "$USER"
  echo "✓ Docker installed successfully"
else
  echo "✓ Docker is already installed"
  docker --version
fi

# Check and install Docker Compose plugin
if ! docker compose version >/dev/null 2>&1; then
  echo "🔧 Installing Docker Compose plugin..."
  COMPOSE_VERSION="v2.24.7"
  sudo mkdir -p /usr/local/lib/docker/cli-plugins
  sudo curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
    -o /usr/local/lib/docker/cli-plugins/docker-compose
  sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
  echo "✓ Docker Compose plugin installed successfully"
else
  echo "✓ Docker Compose plugin is already installed"
  docker compose version
fi

# Ensure docker service is running
if ! sudo systemctl is-active --quiet docker; then
  echo "🚀 Starting Docker service..."
  sudo systemctl start docker
  sudo systemctl enable docker
fi

echo "=== Server Preparation Completed ==="
REMOTE_PREP

# Step 2: Upload release archive
echo ""
echo "📤 Uploading project..."
scp "${SCP_ARGS[@]}" "$TMP_DIR/release.tar.gz" "$REMOTE:$REMOTE_PATH/release.tar.gz"

# Step 3: Deploy on remote host
echo ""
echo "🚀 Starting deployment on remote host..."
REMOTE_PATH_ESCAPED=$(printf '%q' "$REMOTE_PATH")
ssh "${SSH_ARGS[@]}" "$REMOTE" "REMOTE_PATH=$REMOTE_PATH_ESCAPED bash -s" <<'REMOTE_EOF'
set -euo pipefail
cd "$REMOTE_PATH"

echo "=== Deployment Started ==="

# Extract archive
echo "📦 Extracting release archive..."
tar -xzf release.tar.gz --overwrite
rm -f release.tar.gz
mv .env.deploy .env
chmod 600 .env
echo "✓ Files extracted and secured"

# Helper function to run docker with sudo fallback
run_docker() {
  # Try without sudo first (if user is in docker group)
  if docker "$@" 2>/dev/null; then
    return 0
  fi
  # Fall back to sudo
  sudo docker "$@"
}

# Function to update database password if it changed
update_database_password_if_needed() {
  # Check if database is running
  if ! run_docker compose ps db 2>/dev/null | grep -q "Up"; then
    # Database not running, no need to update password
    return 0
  fi
  
  # Get new password from .env
  NEW_PASSWORD=$(grep '^POSTGRES_PASSWORD=' .env | cut -d'=' -f2-)
  DB_USER=$(grep '^POSTGRES_USER=' .env | cut -d'=' -f2- || echo "dating")

  # Escape single quotes for SQL (replace ' with '')
  ESCAPED_PASSWORD=${NEW_PASSWORD//\'/\'\'}

  if [ -z "$NEW_PASSWORD" ]; then
    return 0
  fi

  echo "🔐 Checking if database password needs to be updated..."

  # Try to update the password (safe operation, idempotent)
  # This ensures the password in the database matches the .env file
  if run_docker compose exec -T db env PGPASSWORD="$NEW_PASSWORD" psql -U "$DB_USER" -d "$DB_USER" -c "ALTER USER $DB_USER WITH PASSWORD '$ESCAPED_PASSWORD';" 2>/dev/null; then
    echo "✓ Database password synchronized with configuration"
  else
    echo "⚠️  Could not verify/update database password (container may not be ready)"
  fi
}

# Update database password before stopping containers if it changed
update_database_password_if_needed

# Stop old containers gracefully
if run_docker compose ps -q 2>/dev/null | grep -q .; then
  echo "🛑 Stopping existing containers..."
  run_docker compose down --timeout 30
fi

# Pull latest base images in parallel
echo "📥 Pulling base images..."
run_docker compose pull --parallel db webapp traefik 2>/dev/null || run_docker compose pull db webapp traefik || true

# Build and start services
echo "🏗️  Building and starting services..."
run_docker compose up -d --build --remove-orphans

# Wait for services with smarter health checking
echo "⏳ Waiting for services to start..."
MAX_WAIT=60
WAIT_COUNT=0
ALL_HEALTHY=false

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
  if run_docker compose ps --format json 2>/dev/null | grep -q "healthy" || \
     run_docker compose ps 2>/dev/null | grep -qE "Up.*healthy|Up.*starting"; then
    sleep 5
    if run_docker compose ps 2>/dev/null | grep -qE "Up.*healthy"; then
      ALL_HEALTHY=true
      break
    fi
  fi
  WAIT_COUNT=$((WAIT_COUNT + 5))
  echo "   Waiting... ${WAIT_COUNT}s elapsed"
  sleep 5
done

if [ "$ALL_HEALTHY" = true ]; then
  echo "✓ Services are healthy"
else
  echo "⚠️  Services started but health status unclear (waited ${WAIT_COUNT}s)"
fi

# Check service status
echo ""
echo "=== Service Status ==="
run_docker compose ps

# Check bot logs
echo ""
echo "=== Bot Startup Logs ==="
run_docker compose logs --tail=30 bot

# Verify database
echo ""
echo "=== Database Status ==="
if run_docker compose exec -T db pg_isready -U "${POSTGRES_USER:-dating}" 2>/dev/null; then
  echo "✓ Database is ready"
else
  echo "⚠️  Database health check unavailable (may still be starting)"
fi

# Cleanup old images in background
echo ""
echo "🧹 Cleaning up old images..."
(run_docker image prune -f > /dev/null 2>&1 &)

echo ""
echo "=== Deployment Completed Successfully ==="
REMOTE_EOF

echo ""
echo "✅ Deployment finished successfully!"
echo ""
if [ -n "${DOMAIN}" ]; then
  echo "🌐 Your app should be available at: https://${DOMAIN}"
  echo "⚠️  Note: It may take a few minutes for SSL certificate to be issued"
else
  echo "⚠️  Running in localhost mode (no HTTPS certificate)"
fi
echo ""
echo "To check logs:"
echo "  ssh ${SSH_ARGS[@]} $REMOTE 'cd $REMOTE_PATH && docker compose logs -f bot'"
echo ""
