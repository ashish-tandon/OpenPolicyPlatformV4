#!/bin/bash

# Script to create all OpenPolicyPlatform V5 repositories

set -e

echo "🚀 Creating OpenPolicyPlatform V5 Repositories..."

# GitHub organization/user
ORG="ashish-tandon"

# Repository names for OpenPolicyPlatform V5
REPOS=(
    "openpolicy-platform-v5-core"
    "openpolicy-platform-v5-services"
    "openpolicy-platform-v5-web"
    "openpolicy-platform-v5-monitoring"
    "openpolicy-platform-v5-deployment"
    "openpolicy-platform-v5-docs"
)

# Create each repository
for repo in "${REPOS[@]}"; do
    echo "📦 Creating $repo..."
    
    # Create repository using GitHub CLI
    gh repo create "$ORG/$repo" \
        --description "OpenPolicyPlatform V5 - $repo" \
        --public \
        --clone
    
    echo "✅ Created $repo"
done

echo ""
echo "🎉 All repositories created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Push code to each repository"
echo "2. Set up branch protection rules"
echo "3. Configure CI/CD workflows"
echo "4. Set up repository secrets"
echo "5. Enable security scanning"
