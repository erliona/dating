#!/usr/bin/env bash
# Diagnose Mini App Production Issues
#
# This script helps diagnose why the Telegram Mini App is not opening in production.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
  echo -e "${GREEN}✓${NC} $1"
}

print_error() {
  echo -e "${RED}✗${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
  echo -e "${BLUE}ℹ${NC} $1"
}

print_section() {
  echo ""
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
  print_error "Docker is not installed or not in PATH"
  exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
  print_error "Docker Compose is not available"
  exit 1
fi

print_section "1. Checking Docker Compose Configuration"

if docker compose config > /dev/null 2>&1; then
  print_success "Docker Compose configuration is valid"
else
  print_error "Docker Compose configuration has errors"
  docker compose config
  exit 1
fi

# Check if services are running
print_section "2. Checking Core Services Status"

CORE_SERVICES=(
  "traefik"
  "db"
  "api-gateway"
  "telegram-bot"
  "webapp"
)

ALL_RUNNING=true
for service in "${CORE_SERVICES[@]}"; do
  if docker compose ps "$service" 2>/dev/null | grep -q "Up"; then
    print_success "$service is running"
  else
    print_error "$service is not running"
    ALL_RUNNING=false
  fi
done

if [ "$ALL_RUNNING" = false ]; then
  print_warning "Some core services are not running"
  print_info "Start them with: docker compose up -d"
fi

# Check Traefik (reverse proxy)
print_section "3. Checking Traefik (Reverse Proxy)"

if curl -s http://localhost:8091/api/rawdata 2>/dev/null | grep -q "traefik"; then
  print_success "Traefik is running and accessible"
  
  # Check if webapp route is configured
  if curl -s http://localhost:8091/api/rawdata 2>/dev/null | grep -q "webapp"; then
    print_success "WebApp route is configured in Traefik"
  else
    print_warning "WebApp route is not configured in Traefik"
  fi
else
  print_error "Traefik is not accessible at http://localhost:8091"
fi

# Check WebApp accessibility
print_section "4. Checking WebApp Accessibility"

# Check if webapp container is running
if docker compose ps webapp 2>/dev/null | grep -q "Up"; then
  print_success "WebApp container is running"
  
  # Check if webapp responds internally
  if docker compose exec -T webapp curl -s http://localhost:3000 > /dev/null 2>&1; then
    print_success "WebApp responds internally on port 3000"
  else
    print_error "WebApp does not respond internally"
  fi
  
  # Check if webapp is accessible through Traefik
  if curl -s -I http://localhost/webapp 2>/dev/null | grep -q "200 OK"; then
    print_success "WebApp is accessible through Traefik at http://localhost/webapp"
  else
    print_warning "WebApp is not accessible through Traefik"
    print_info "Check Traefik configuration and labels"
  fi
else
  print_error "WebApp container is not running"
fi

# Check API Gateway
print_section "5. Checking API Gateway"

if curl -s http://localhost:8080/health 2>/dev/null | grep -q "ok"; then
  print_success "API Gateway is healthy"
else
  print_error "API Gateway is not responding"
fi

# Check Telegram Bot
print_section "6. Checking Telegram Bot"

if docker compose ps telegram-bot 2>/dev/null | grep -q "Up"; then
  print_success "Telegram Bot container is running"
  
  # Check bot logs for errors
  if docker compose logs telegram-bot --tail=10 2>/dev/null | grep -q "ERROR"; then
    print_warning "Telegram Bot has errors in logs"
    print_info "Check logs with: docker compose logs telegram-bot"
  else
    print_success "Telegram Bot logs look clean"
  fi
else
  print_error "Telegram Bot container is not running"
fi

# Check environment variables
print_section "7. Checking Environment Configuration"

# Check if .env file exists
if [ -f ".env" ]; then
  print_success ".env file exists"
  
  # Check critical environment variables
  if grep -q "BOT_TOKEN=" .env && ! grep -q "BOT_TOKEN=your-" .env; then
    print_success "BOT_TOKEN is configured"
  else
    print_error "BOT_TOKEN is not properly configured"
  fi
  
  if grep -q "WEBAPP_URL=" .env && ! grep -q "WEBAPP_URL=https://your-" .env; then
    print_success "WEBAPP_URL is configured"
  else
    print_error "WEBAPP_URL is not properly configured"
  fi
  
  if grep -q "DOMAIN=" .env && ! grep -q "DOMAIN=your-" .env; then
    print_success "DOMAIN is configured"
  else
    print_warning "DOMAIN is not configured (using localhost)"
  fi
else
  print_error ".env file does not exist"
  print_info "Copy .env.example to .env and configure it"
fi

# Check SSL certificates
print_section "8. Checking SSL Certificates"

if [ -d "traefik_certificates" ] || docker volume ls | grep -q "traefik_certificates"; then
  print_success "Traefik certificates volume exists"
else
  print_warning "Traefik certificates volume not found"
fi

# Check network connectivity
print_section "9. Checking Network Connectivity"

# Check if ports are accessible
PORTS=("80" "443" "8080" "8091")
for port in "${PORTS[@]}"; do
  if nc -z localhost "$port" 2>/dev/null; then
    print_success "Port $port is accessible"
  else
    print_warning "Port $port is not accessible"
  fi
done

# Summary and recommendations
print_section "Summary and Recommendations"

echo ""
print_info "Mini App Production Diagnosis Complete"
echo ""

if [ "$ALL_RUNNING" = true ]; then
  print_success "All core services are running!"
  echo ""
  print_info "If Mini App still doesn't open, check:"
  echo "  1. Telegram Bot token is valid and active"
  echo "  2. WebApp URL is correctly set in bot settings"
  echo "  3. Domain has valid SSL certificate"
  echo "  4. Traefik is routing requests correctly"
  echo ""
  print_info "Useful commands:"
  echo "  • View logs: docker compose logs -f"
  echo "  • Restart services: docker compose restart"
  echo "  • Check Traefik dashboard: http://localhost:8091"
  echo ""
else
  print_error "Some services are not running properly"
  echo ""
  print_info "Troubleshooting steps:"
  echo "  1. Start services: docker compose up -d"
  echo "  2. Check logs: docker compose logs"
  echo "  3. Verify .env configuration"
  echo "  4. Check Docker resources (memory, disk space)"
  echo ""
fi

print_info "For detailed logs, run:"
echo "  docker compose logs -f telegram-bot"
echo "  docker compose logs -f webapp"
echo "  docker compose logs -f traefik"
echo ""
