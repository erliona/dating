#!/usr/bin/env bash
# Deploy the application to a remote server over SSH.
#
# The script packages the dockerised application, copies it to the
# remote host and restarts the Docker Compose stack. It mirrors the
# behaviour of the GitHub Actions workflow so you can trigger a
# deployment from your local machine.
#
# IMPORTANT: For production deployments with HTTPS:
# - Ensure your .env file includes: DOMAIN, ACME_EMAIL, WEBAPP_URL (https://)
# - DNS must point to your server IP
# - Ports 80 and 443 must be open in firewall
# - Traefik will automatically obtain Let's Encrypt SSL certificates

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/deploy.sh -H <host> -u <user> -d <remote_path> -e <env_file> [options]

Required arguments:
  -H <host>         SSH host name or IP address.
  -u <user>         SSH user name with Docker permissions.
  -d <remote_path>  Directory on the remote host where the project should live.
  -e <env_file>     Path to the local .env file that will be uploaded.
                    For HTTPS: Must include DOMAIN, ACME_EMAIL, and WEBAPP_URL (https://)

Optional arguments:
  -p <port>         SSH port (default: 22).
  -i <identity>     Path to a private SSH key. Falls back to ssh-agent if omitted.
  -h                Show this help message.

Example:
  scripts/deploy.sh -H server.example.com -u deploy \
    -d /opt/dating -e .env.production -i ~/.ssh/id_ed25519

For local development without HTTPS:
  Use docker-compose.dev.yml instead of this script.
USAGE
}

HOST=""
USER=""
PORT="22"
REMOTE_PATH=""
ENV_FILE=""
IDENTITY=""

while getopts ":H:u:d:e:p:i:h" opt; do
  case "$opt" in
    H) HOST="$OPTARG" ;;
    u) USER="$OPTARG" ;;
    d) REMOTE_PATH="$OPTARG" ;;
    e) ENV_FILE="$OPTARG" ;;
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

if [[ -z "$HOST" || -z "$USER" || -z "$REMOTE_PATH" || -z "$ENV_FILE" ]]; then
  echo "Error: host, user, remote path and env file are required." >&2
  usage >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: environment file '$ENV_FILE' does not exist." >&2
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

cp "$ENV_FILE" "$TMP_DIR/.env.deploy"

# Create an archive mirroring the GitHub Actions workflow.
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

SSH_ARGS=(-p "$PORT")
SCP_ARGS=(-P "$PORT")
if [[ -n "$IDENTITY" ]]; then
  SSH_ARGS+=(-i "$IDENTITY")
  SCP_ARGS+=(-i "$IDENTITY")
fi

REMOTE="${USER}@${HOST}"

echo "Creating remote directory $REMOTE_PATH"
ssh "${SSH_ARGS[@]}" "$REMOTE" "mkdir -p '$REMOTE_PATH'"

echo "Uploading release archive"
scp "${SCP_ARGS[@]}" "$TMP_DIR/release.tar.gz" "$REMOTE:$REMOTE_PATH/release.tar.gz"

echo "Deploying on remote host"
REMOTE_PATH_ESCAPED=$(printf '%q' "$REMOTE_PATH")
ssh "${SSH_ARGS[@]}" "$REMOTE" "REMOTE_PATH=$REMOTE_PATH_ESCAPED bash -s" <<'REMOTE_EOF'
set -euo pipefail
cd "$REMOTE_PATH"

tar -xzf release.tar.gz --overwrite
rm -f release.tar.gz
mv .env.deploy .env

run_docker() {
  if command -v docker >/dev/null 2>&1; then
    docker "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo docker "$@"
  else
    echo "Docker is not installed. Install Docker before deploying." >&2
    exit 1
  fi
}

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found. Installing Docker..."
  curl -fsSL https://get.docker.com | sh
fi

if ! run_docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
  echo "docker compose plugin not found. Installing..."
  if command -v sudo >/dev/null 2>&1; then
    sudo mkdir -p /usr/local/lib/docker/cli-plugins
    sudo curl -SL https://github.com/docker/compose/releases/download/v2.24.7/docker-compose-linux-x86_64 \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
  else
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL https://github.com/docker/compose/releases/download/v2.24.7/docker-compose-linux-x86_64 \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
  fi
fi

run_docker compose pull || true
run_docker compose build --pull
run_docker compose up -d --remove-orphans
run_docker image prune -f
REMOTE_EOF

echo "Deployment completed successfully."
