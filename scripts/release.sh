#!/bin/bash
# Release Management Script
# Handles version bumping, changelog generation, and release creation

set -e

# Configuration
REPO_URL="https://github.com/erliona/dating.git"
REGISTRY_URL="ghcr.io/erliona/dating"
CHANGELOG_FILE="CHANGELOG.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Error handling
error_exit() {
    log "${RED}ERROR: $1${NC}"
    exit 1
}

# Success message
success() {
    log "${GREEN}✅ $1${NC}"
}

# Warning message
warning() {
    log "${YELLOW}⚠️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check if we're in a git repository
    if [ ! -d ".git" ]; then
        error_exit "Not in a git repository"
    fi
    
    # Check if we're on main branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "main" ]; then
        error_exit "Must be on main branch (currently on $current_branch)"
    fi
    
    # Check if working directory is clean
    if [ -n "$(git status --porcelain)" ]; then
        error_exit "Working directory is not clean. Commit or stash changes first."
    fi
    
    # Check if git cliff is installed
    if ! command -v git-cliff &> /dev/null; then
        warning "git-cliff not found. Install with: cargo install git-cliff"
        warning "Or use: wget https://github.com/orhun/git-cliff/releases/latest/download/git-cliff-1.4.0-x86_64-unknown-linux-gnu.tar.gz"
    fi
    
    success "Prerequisites check passed"
}

# Get current version
get_current_version() {
    local current_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
    echo "${current_tag#v}"
}

# Bump version
bump_version() {
    local version_type=$1
    local current_version=$(get_current_version)
    
    log "📈 Bumping version from $current_version ($version_type)"
    
    case $version_type in
        "patch")
            new_version=$(echo "$current_version" | awk -F. '{$NF = $NF + 1;} 1' | sed 's/ /./g')
            ;;
        "minor")
            new_version=$(echo "$current_version" | awk -F. '{$2 = $2 + 1; $3 = 0;} 1' | sed 's/ /./g')
            ;;
        "major")
            new_version=$(echo "$current_version" | awk -F. '{$1 = $1 + 1; $2 = 0; $3 = 0;} 1' | sed 's/ /./g')
            ;;
        *)
            error_exit "Invalid version type: $version_type. Use patch, minor, or major"
            ;;
    esac
    
    echo "v$new_version"
}

# Generate changelog
generate_changelog() {
    local version=$1
    
    log "📝 Generating changelog for $version..."
    
    if command -v git-cliff &> /dev/null; then
        git-cliff --output "$CHANGELOG_FILE"
        success "Changelog generated with git-cliff"
    else
        # Fallback to simple changelog
        cat > "$CHANGELOG_FILE" << EOF
## Changelog

## [$version] - $(date '+%Y-%m-%d')

### Changes
- See git log for details

Full Changelog: https://github.com/erliona/dating/compare/$(git describe --tags --abbrev=0)...$version
EOF
        warning "Using fallback changelog (install git-cliff for better changelogs)"
    fi
}

# Update version in files
update_version_files() {
    local version=$1
    
    log "📄 Updating version in files..."
    
    # Update pyproject.toml
    if [ -f "pyproject.toml" ]; then
        sed -i "s/version = \".*\"/version = \"${version#v}\"/" pyproject.toml
        success "Updated pyproject.toml"
    fi
    
    # Update package.json if exists
    if [ -f "package.json" ]; then
        sed -i "s/\"version\": \".*\"/\"version\": \"${version#v}\"/" package.json
        success "Updated package.json"
    fi
    
    # Update docker-compose.yml tags
    if [ -f "docker-compose.yml" ]; then
        # This would need more sophisticated replacement
        warning "Manual update of docker-compose.yml tags may be required"
    fi
}

# Create release commit
create_release_commit() {
    local version=$1
    
    log "💾 Creating release commit..."
    
    # Add all changes
    git add .
    
    # Create commit
    git commit -m "chore: release $version"
    
    success "Release commit created"
}

# Create and push tag
create_tag() {
    local version=$1
    
    log "🏷️  Creating tag $version..."
    
    # Create annotated tag
    git tag -a "$version" -m "Release $version"
    
    # Push tag
    git push origin "$version"
    
    success "Tag $version created and pushed"
}

# Build and push Docker images
build_and_push_images() {
    local version=$1
    
    log "🐳 Building and pushing Docker images..."
    
    # List of services to build
    services=(
        "api-gateway"
        "auth-service"
        "profile-service"
        "discovery-service"
        "media-service"
        "chat-service"
        "admin-service"
        "telegram-bot"
        "webapp"
    )
    
    for service in "${services[@]}"; do
        log "Building $service..."
        
        # Build image
        docker build -t "$REGISTRY_URL/$service:$version" -f "services/$service/Dockerfile" .
        docker build -t "$REGISTRY_URL/$service:latest" -f "services/$service/Dockerfile" .
        
        # Push images
        docker push "$REGISTRY_URL/$service:$version"
        docker push "$REGISTRY_URL/$service:latest"
        
        success "Pushed $service:$version and $service:latest"
    done
}

# Create GitHub release
create_github_release() {
    local version=$1
    
    log "🚀 Creating GitHub release..."
    
    if command -v gh &> /dev/null; then
        gh release create "$version" \
            --title "Release $version" \
            --notes-file "$CHANGELOG_FILE" \
            --latest
        success "GitHub release created"
    else
        warning "GitHub CLI not found. Create release manually at https://github.com/erliona/dating/releases"
    fi
}

# Deploy to staging
deploy_staging() {
    local version=$1
    
    log "🚀 Deploying to staging..."
    
    # This would typically SSH to staging server
    warning "Staging deployment not implemented. Manual deployment required."
    warning "Use: docker compose pull && docker compose up -d"
}

# Verify release
verify_release() {
    local version=$1
    
    log "🔍 Verifying release..."
    
    # Check if tag exists
    if git describe --tags --exact-match "$version" &>/dev/null; then
        success "Tag $version exists"
    else
        error_exit "Tag $version not found"
    fi
    
    # Check if images exist (basic check)
    if docker images | grep -q "$REGISTRY_URL/api-gateway:$version"; then
        success "Docker images built successfully"
    else
        warning "Docker images not found locally (may be pushed to registry)"
    fi
    
    success "Release verification completed"
}

# Rollback release
rollback_release() {
    local version=$1
    
    log "🔄 Rolling back release $version..."
    
    # Delete tag
    git tag -d "$version"
    git push origin --delete "$version"
    
    # Delete GitHub release
    if command -v gh &> /dev/null; then
        gh release delete "$version" --yes
    fi
    
    success "Release $version rolled back"
}

# Main release function
create_release() {
    local version_type=$1
    
    log "🚀 Starting release process ($version_type)"
    
    check_prerequisites
    
    local new_version=$(bump_version "$version_type")
    log "📦 New version: $new_version"
    
    generate_changelog "$new_version"
    update_version_files "$new_version"
    create_release_commit "$new_version"
    create_tag "$new_version"
    
    # Optional: Build and push images (can be done by CI)
    if [ "${BUILD_IMAGES:-false}" = "true" ]; then
        build_and_push_images "$new_version"
    fi
    
    # Optional: Create GitHub release
    if [ "${CREATE_GITHUB_RELEASE:-true}" = "true" ]; then
        create_github_release "$new_version"
    fi
    
    # Optional: Deploy to staging
    if [ "${DEPLOY_STAGING:-false}" = "true" ]; then
        deploy_staging "$new_version"
    fi
    
    verify_release "$new_version"
    
    success "Release $new_version created successfully!"
    log "📋 Next steps:"
    log "  1. Review the release at https://github.com/erliona/dating/releases"
    log "  2. Deploy to staging: ./scripts/deploy-staging.sh $new_version"
    log "  3. Deploy to production: ./scripts/deploy-production.sh $new_version"
}

# List releases
list_releases() {
    log "📋 Recent releases:"
    git tag --sort=-version:refname | head -10
}

# Show release info
show_release_info() {
    local version=$1
    
    if [ -z "$version" ]; then
        version=$(git describe --tags --abbrev=0)
    fi
    
    log "📦 Release info for $version:"
    echo "  Tag: $version"
    echo "  Commit: $(git rev-parse "$version")"
    echo "  Date: $(git log -1 --format=%ai "$version")"
    echo "  Author: $(git log -1 --format=%an "$version")"
    echo "  Message: $(git log -1 --format=%s "$version")"
}

# Main script logic
main() {
    case "${1:-help}" in
        "patch"|"minor"|"major")
            create_release "$1"
            ;;
        "list")
            list_releases
            ;;
        "info")
            show_release_info "$2"
            ;;
        "rollback")
            rollback_release "$2"
            ;;
        "help"|*)
            echo "Usage: $0 {patch|minor|major|list|info|rollback|help}"
            echo ""
            echo "Commands:"
            echo "  patch     - Create patch release (1.0.0 -> 1.0.1)"
            echo "  minor     - Create minor release (1.0.0 -> 1.1.0)"
            echo "  major     - Create major release (1.0.0 -> 2.0.0)"
            echo "  list      - List recent releases"
            echo "  info      - Show release information"
            echo "  rollback  - Rollback a release"
            echo "  help      - Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  BUILD_IMAGES=true          - Build and push Docker images"
            echo "  CREATE_GITHUB_RELEASE=true - Create GitHub release"
            echo "  DEPLOY_STAGING=true        - Deploy to staging"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
