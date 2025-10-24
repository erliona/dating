#!/bin/bash
# Frontend Structure and Standards Validation Script
# Validates Vue 3 + Vite + Pinia frontend structure and standards

set -e

# Configuration
WEBAPP_DIR="webapp"
REQUIRED_FILES=("package.json" "vite.config.js" "index.html")
REQUIRED_DIRS=("src" "src/components" "src/stores" "src/views" "src/composables" "src/router")
VUE_COMPONENT_PATTERN="*.vue"
JS_FILE_PATTERN="*.js"

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

# Check if we're in the right directory
check_directory() {
    if [ ! -d "$WEBAPP_DIR" ]; then
        error_exit "webapp directory not found. Run from project root."
    fi
    success "Running in correct directory"
}

# Validate package.json
validate_package_json() {
    log "🔍 Validating package.json..."
    
    local package_file="$WEBAPP_DIR/package.json"
    
    if [ ! -f "$package_file" ]; then
        error_exit "package.json not found in $WEBAPP_DIR"
    fi
    
    # Check for required dependencies
    local required_deps=("vue" "vue-router" "pinia" "axios" "vite")
    
    for dep in "${required_deps[@]}"; do
        if ! grep -q "\"$dep\"" "$package_file"; then
            warning "Required dependency '$dep' not found in package.json"
        else
            success "Dependency '$dep' found"
        fi
    done
    
    # Check for dev dependencies
    local required_dev_deps=("@vitejs/plugin-vue" "terser")
    
    for dep in "${required_dev_deps[@]}"; do
        if ! grep -q "\"$dep\"" "$package_file"; then
            warning "Required dev dependency '$dep' not found in package.json"
        else
            success "Dev dependency '$dep' found"
        fi
    done
    
    # Check for scripts
    local required_scripts=("dev" "build" "preview")
    
    for script in "${required_scripts[@]}"; do
        if ! grep -q "\"$script\"" "$package_file"; then
            warning "Required script '$script' not found in package.json"
        else
            success "Script '$script' found"
        fi
    done
}

# Validate Vite configuration
validate_vite_config() {
    log "🔍 Validating Vite configuration..."
    
    local vite_config="$WEBAPP_DIR/vite.config.js"
    
    if [ ! -f "$vite_config" ]; then
        error_exit "vite.config.js not found in $WEBAPP_DIR"
    fi
    
    # Check for Vue plugin
    if ! grep -q "@vitejs/plugin-vue" "$vite_config"; then
        warning "Vue plugin not found in vite.config.js"
    else
        success "Vue plugin configured"
    fi
    
    # Check for build configuration
    if ! grep -q "build:" "$vite_config"; then
        warning "Build configuration not found in vite.config.js"
    else
        success "Build configuration found"
    fi
    
    success "Vite configuration validated"
}

# Validate directory structure
validate_directory_structure() {
    log "🔍 Validating directory structure..."
    
    local violations=0
    
    for dir in "${REQUIRED_DIRS[@]}"; do
        local full_path="$WEBAPP_DIR/$dir"
        if [ ! -d "$full_path" ]; then
            warning "Required directory '$dir' not found"
            violations=$((violations + 1))
        else
            success "Directory '$dir' found"
        fi
    done
    
    if [ $violations -eq 0 ]; then
        success "All required directories found"
    else
        warning "Found $violations missing directories"
    fi
}

# Validate Vue components
validate_vue_components() {
    log "🔍 Validating Vue components..."
    
    local violations=0
    local component_count=0
    
    # Find all Vue components
    local vue_files=$(find "$WEBAPP_DIR/src" -name "*.vue" -type f)
    
    if [ -z "$vue_files" ]; then
        warning "No Vue components found"
        return
    fi
    
    for vue_file in $vue_files; do
        component_count=$((component_count + 1))
        log "Checking $vue_file..."
        
        # Check for script setup
        if ! grep -q "<script setup>" "$vue_file"; then
            warning "No <script setup> found in $vue_file"
            violations=$((violations + 1))
        fi
        
        # Check for template
        if ! grep -q "<template>" "$vue_file"; then
            warning "No <template> found in $vue_file"
            violations=$((violations + 1))
        fi
        
        # Check for scoped styles
        if ! grep -q "<style scoped>" "$vue_file"; then
            warning "No scoped styles found in $vue_file"
        fi
        
        success "Vue component $vue_file checked"
    done
    
    log "Found $component_count Vue components"
    
    if [ $violations -eq 0 ]; then
        success "All Vue components passed validation"
    else
        warning "Found $violations Vue component issues"
    fi
}

# Validate Pinia stores
validate_pinia_stores() {
    log "🔍 Validating Pinia stores..."
    
    local stores_dir="$WEBAPP_DIR/src/stores"
    local violations=0
    
    if [ ! -d "$stores_dir" ]; then
        warning "Stores directory not found"
        return
    fi
    
    # Find all store files
    local store_files=$(find "$stores_dir" -name "*.js" -type f)
    
    if [ -z "$store_files" ]; then
        warning "No store files found"
        return
    fi
    
    for store_file in $store_files; do
        log "Checking store $store_file..."
        
        # Check for defineStore
        if ! grep -q "defineStore" "$store_file"; then
            warning "No defineStore found in $store_file"
            violations=$((violations + 1))
        fi
        
        # Check for composition API usage
        if ! grep -q "ref\|reactive\|computed" "$store_file"; then
            warning "No composition API usage found in $store_file"
            violations=$((violations + 1))
        fi
        
        success "Store $store_file checked"
    done
    
    if [ $violations -eq 0 ]; then
        success "All Pinia stores passed validation"
    else
        warning "Found $violations Pinia store issues"
    fi
}

# Validate composables
validate_composables() {
    log "🔍 Validating composables..."
    
    local composables_dir="$WEBAPP_DIR/src/composables"
    local violations=0
    
    if [ ! -d "$composables_dir" ]; then
        warning "Composables directory not found"
        return
    fi
    
    # Find all composable files
    local composable_files=$(find "$composables_dir" -name "*.js" -type f)
    
    if [ -z "$composable_files" ]; then
        warning "No composable files found"
        return
    fi
    
    for composable_file in $composable_files; do
        log "Checking composable $composable_file..."
        
        # Check for export function
        if ! grep -q "export function" "$composable_file"; then
            warning "No export function found in $composable_file"
            violations=$((violations + 1))
        fi
        
        # Check for composition API usage
        if ! grep -q "ref\|reactive\|computed\|watch" "$composable_file"; then
            warning "No composition API usage found in $composable_file"
            violations=$((violations + 1))
        fi
        
        success "Composable $composable_file checked"
    done
    
    if [ $violations -eq 0 ]; then
        success "All composables passed validation"
    else
        warning "Found $violations composable issues"
    fi
}

# Validate router configuration
validate_router() {
    log "🔍 Validating router configuration..."
    
    local router_dir="$WEBAPP_DIR/src/router"
    local violations=0
    
    if [ ! -d "$router_dir" ]; then
        warning "Router directory not found"
        return
    fi
    
    # Check for main router file
    if [ ! -f "$router_dir/index.js" ]; then
        warning "Main router file (index.js) not found"
        violations=$((violations + 1))
    else
        success "Main router file found"
        
        # Check for Vue Router imports
        if ! grep -q "vue-router" "$router_dir/index.js"; then
            warning "Vue Router not imported in main router"
            violations=$((violations + 1))
        fi
        
        # Check for route definitions
        if ! grep -q "routes:" "$router_dir/index.js"; then
            warning "No routes defined in main router"
            violations=$((violations + 1))
        fi
    fi
    
    if [ $violations -eq 0 ]; then
        success "Router configuration validated"
    else
        warning "Found $violations router issues"
    fi
}

# Validate main entry point
validate_main_entry() {
    log "🔍 Validating main entry point..."
    
    local main_file="$WEBAPP_DIR/src/main.js"
    
    if [ ! -f "$main_file" ]; then
        error_exit "main.js not found in $WEBAPP_DIR/src"
    fi
    
    # Check for Vue import
    if ! grep -q "import.*vue" "$main_file"; then
        warning "Vue not imported in main.js"
    else
        success "Vue import found"
    fi
    
    # Check for app mounting
    if ! grep -q "\.mount" "$main_file"; then
        warning "App mounting not found in main.js"
    else
        success "App mounting found"
    fi
    
    success "Main entry point validated"
}

# Validate HTML entry point
validate_html_entry() {
    log "🔍 Validating HTML entry point..."
    
    local html_file="$WEBAPP_DIR/index.html"
    
    if [ ! -f "$html_file" ]; then
        error_exit "index.html not found in $WEBAPP_DIR"
    fi
    
    # Check for Vue app div
    if ! grep -q 'id="app"' "$html_file"; then
        warning "App div not found in index.html"
    else
        success "App div found"
    fi
    
    # Check for script import
    if ! grep -q "main.js" "$html_file"; then
        warning "main.js not imported in index.html"
    else
        success "main.js import found"
    fi
    
    success "HTML entry point validated"
}

# Generate frontend report
generate_frontend_report() {
    log "📊 Generating frontend structure report..."
    
    local report_file="/tmp/frontend-structure-report-$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "Frontend Structure Report - $(date)"
        echo "====================================="
        echo ""
        
        echo "Package.json dependencies:"
        if [ -f "$WEBAPP_DIR/package.json" ]; then
            grep -A 10 '"dependencies"' "$WEBAPP_DIR/package.json" || echo "No dependencies found"
        fi
        echo ""
        
        echo "Vue components found:"
        find "$WEBAPP_DIR/src" -name "*.vue" -type f | wc -l
        find "$WEBAPP_DIR/src" -name "*.vue" -type f
        echo ""
        
        echo "Pinia stores found:"
        find "$WEBAPP_DIR/src/stores" -name "*.js" -type f 2>/dev/null || echo "No stores found"
        echo ""
        
        echo "Composables found:"
        find "$WEBAPP_DIR/src/composables" -name "*.js" -type f 2>/dev/null || echo "No composables found"
        echo ""
        
        echo "Router files found:"
        find "$WEBAPP_DIR/src/router" -name "*.js" -type f 2>/dev/null || echo "No router files found"
        echo ""
        
        echo "Directory structure:"
        tree "$WEBAPP_DIR/src" 2>/dev/null || find "$WEBAPP_DIR/src" -type d | sort
        echo ""
        
    } > "$report_file"
    
    log "📄 Frontend report generated: $report_file"
}

# Main validation function
validate_frontend() {
    log "🚀 Starting frontend structure validation..."
    
    check_directory
    validate_package_json
    validate_vite_config
    validate_directory_structure
    validate_vue_components
    validate_pinia_stores
    validate_composables
    validate_router
    validate_main_entry
    validate_html_entry
    generate_frontend_report
    
    log "✅ Frontend structure validation completed"
}

# Check specific component
check_component() {
    local component_name=$1
    
    if [ -z "$component_name" ]; then
        error_exit "Component name required"
    fi
    
    log "🔍 Checking specific component: $component_name"
    
    # Find component file
    local component_file=$(find "$WEBAPP_DIR/src" -name "$component_name.vue" -type f)
    
    if [ -z "$component_file" ]; then
        error_exit "Component $component_name not found"
    fi
    
    log "Component file: $component_file"
    
    # Check component structure
    log "Component structure:"
    grep -n "<template>\|<script\|<style" "$component_file" || echo "No sections found"
    
    success "Component $component_name checked"
}

# Main script logic
main() {
    case "${1:-validate}" in
        "validate")
            validate_frontend
            ;;
        "check")
            check_component "$2"
            ;;
        "report")
            generate_frontend_report
            ;;
        "help"|*)
            echo "Usage: $0 {validate|check|report|help} [component_name]"
            echo ""
            echo "Commands:"
            echo "  validate           - Run full frontend structure validation"
            echo "  check <component>  - Check specific Vue component"
            echo "  report             - Generate frontend structure report"
            echo "  help               - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 validate"
            echo "  $0 check SwipeCard"
            echo "  $0 report"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
