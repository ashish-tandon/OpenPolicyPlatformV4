#!/bin/bash

# 🚀 Fix All Services Script
# Fixes HTTPStatus import and get_current_user function placement issues

echo "🔧 Fixing all services with common issues..."

# List of services that need fixing
SERVICES=(
    "analytics-service"
    "data-management-service"
    "dashboard-service"
    "etl-service"
    "files-service"
    "integration-service"
    "legacy-django"
    "mobile-api"
    "notification-service"
    "plotly-service"
    "reporting-service"
    "representatives-service"
    "scraper-service"
    "search-service"
    "workflow-service"
)

# Function to fix a service
fix_service() {
    local service=$1
    local main_file="services/$service/src/main.py"
    
    if [ -f "$main_file" ]; then
        echo "🔧 Fixing $service..."
        
        # Fix HTTPStatus import
        sed -i '' 's/from fastapi import FastAPI, Response, HTTPException, Depends, HTTPStatus, Query/from fastapi import FastAPI, Response, HTTPException, Depends, Query\nfrom http import HTTPStatus/' "$main_file"
        sed -i '' 's/from fastapi import FastAPI, Response, HTTPException, Depends, HTTPStatus, Query, BackgroundTasks/from fastapi import FastAPI, Response, HTTPException, Depends, Query, BackgroundTasks\nfrom http import HTTPStatus/' "$main_file"
        sed -i '' 's/from fastapi import FastAPI, Response, HTTPException, Depends, HTTPStatus, Query, UploadFile, File/from fastapi import FastAPI, Response, HTTPException, Depends, Query, UploadFile, File\nfrom http import HTTPStatus/' "$main_file"
        
        # Add get_current_user function after app definition if it doesn't exist at the top
        if ! grep -q "def get_current_user" "$main_file" | head -20; then
            # Find the line after app definition
            local app_line=$(grep -n "app = FastAPI" "$main_file" | head -1 | cut -d: -f1)
            if [ ! -z "$app_line" ]; then
                local security_line=$(grep -n "security = HTTPBearer()" "$main_file" | head -1 | cut -d: -f1)
                if [ ! -z "$security_line" ]; then
                    # Insert get_current_user function after security line
                    local insert_line=$((security_line + 1))
                    cat > /tmp/get_current_user_function.txt << 'EOF'

# Mock authentication dependency (replace with real auth service integration)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Mock current user (replace with real JWT verification)"""
    # This is a mock implementation - replace with real JWT verification
    return {
        "id": "user_001",
        "username": "admin",
        "full_name": "System Administrator",
        "role": "admin"
    }

EOF
                    # Insert the function
                    sed -i '' "${insert_line}r /tmp/get_current_user_function.txt" "$main_file"
                    rm /tmp/get_current_user_function.txt
                fi
            fi
        fi
        
        echo "✅ $service fixed"
    else
        echo "❌ $main_file not found"
    fi
}

# Fix all services
for service in "${SERVICES[@]}"; do
    fix_service "$service"
done

echo "🎉 All services fixed!"
