#!/bin/bash

# Open Policy Platform - Merge Verification Script
# This script verifies that all repositories have been properly merged

echo "🔍 Open Policy Platform - Merge Verification"
echo "==========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if directories exist
check_directories() {
    echo "Checking directory structure..."
    
    directories=(
        "apps/open-policy-main"
        "apps/open-policy-app"
        "apps/open-policy-web"
        "apps/admin-open-policy"
        "backend/OpenPolicyAshBack"
        "infrastructure/open-policy-infra"
        "scrapers/openparliament"
        "scrapers/scrapers-ca"
        "scrapers/civic-scraper"
    )
    
    for dir in "${directories[@]}"; do
        if [ -d "$dir" ]; then
            print_success "Directory exists: $dir"
        else
            print_error "Directory missing: $dir"
        fi
    done
}

# Check for key files
check_key_files() {
    echo ""
    echo "Checking key files..."
    
    # Check main documentation
    if [ -f "README.md" ]; then
        print_success "Main README.md exists"
    else
        print_error "Main README.md missing"
    fi
    
    if [ -f "MERGE_DOCUMENTATION.md" ]; then
        print_success "Merge documentation exists"
    else
        print_error "Merge documentation missing"
    fi
    
    if [ -f "MERGE_SUMMARY.md" ]; then
        print_success "Merge summary exists"
    else
        print_error "Merge summary missing"
    fi
    
    if [ -f "setup.sh" ]; then
        print_success "Setup script exists"
    else
        print_error "Setup script missing"
    fi
    
    # Check package.json files
    package_count=$(find . -name "package.json" | wc -l)
    if [ "$package_count" -gt 0 ]; then
        print_success "Found $package_count package.json files"
    else
        print_error "No package.json files found"
    fi
    
    # Check requirements.txt files
    requirements_count=$(find . -name "requirements.txt" | wc -l)
    if [ "$requirements_count" -gt 0 ]; then
        print_success "Found $requirements_count requirements.txt files"
    else
        print_error "No requirements.txt files found"
    fi
}

# Check for README files in each component
check_readme_files() {
    echo ""
    echo "Checking README files in components..."
    
    components=(
        "apps/open-policy-main"
        "apps/open-policy-app"
        "apps/open-policy-web"
        "apps/admin-open-policy"
        "backend/OpenPolicyAshBack"
        "infrastructure/open-policy-infra"
        "scrapers/openparliament"
        "scrapers/scrapers-ca"
        "scrapers/civic-scraper"
    )
    
    for component in "${components[@]}"; do
        if [ -f "$component/README.md" ]; then
            print_success "README.md exists in $component"
        else
            print_warning "README.md missing in $component"
        fi
    done
}

# Check for configuration files
check_config_files() {
    echo ""
    echo "Checking configuration files..."
    
    # Check for Docker files
    docker_count=$(find . -name "Dockerfile" -o -name "docker-compose*.yml" | wc -l)
    if [ "$docker_count" -gt 0 ]; then
        print_success "Found $docker_count Docker configuration files"
    else
        print_warning "No Docker configuration files found"
    fi
    
    # Check for TypeScript configs
    tsconfig_count=$(find . -name "tsconfig*.json" | wc -l)
    if [ "$tsconfig_count" -gt 0 ]; then
        print_success "Found $tsconfig_count TypeScript configuration files"
    else
        print_warning "No TypeScript configuration files found"
    fi
    
    # Check for Python configs
    python_config_count=$(find . -name "*.py" | wc -l)
    if [ "$python_config_count" -gt 0 ]; then
        print_success "Found $python_config_count Python files"
    else
        print_warning "No Python files found"
    fi
}

# Check file counts
check_file_counts() {
    echo ""
    echo "Checking file counts..."
    
    # Count total files
    total_files=$(find . -type f | wc -l)
    print_info "Total files in repository: $total_files"
    
    # Count by type
    md_files=$(find . -name "*.md" | wc -l)
    print_info "Markdown files: $md_files"
    
    json_files=$(find . -name "*.json" | wc -l)
    print_info "JSON files: $json_files"
    
    py_files=$(find . -name "*.py" | wc -l)
    print_info "Python files: $py_files"
    
    js_files=$(find . -name "*.js" | wc -l)
    print_info "JavaScript files: $js_files"
    
    ts_files=$(find . -name "*.ts" -o -name "*.tsx" | wc -l)
    print_info "TypeScript files: $ts_files"
}

# Check for startup scripts
check_startup_scripts() {
    echo ""
    echo "Checking startup scripts..."
    
    scripts=(
        "start-backend.sh"
        "start-web.sh"
        "start-mobile.sh"
        "start-all.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                print_success "Executable script exists: $script"
            else
                print_warning "Script exists but not executable: $script"
            fi
        else
            print_error "Script missing: $script"
        fi
    done
}

# Main verification
main() {
    echo "Starting merge verification..."
    echo ""
    
    check_directories
    check_key_files
    check_readme_files
    check_config_files
    check_file_counts
    check_startup_scripts
    
    echo ""
    echo "🎉 Merge verification completed!"
    echo "================================"
    echo ""
    echo "If all checks passed, your merge was successful!"
    echo ""
    echo "Next steps:"
    echo "1. Run './setup.sh' to set up the entire platform"
    echo "2. Configure environment variables"
    echo "3. Start development with './start-all.sh'"
    echo ""
}

# Run verification
main "$@"
