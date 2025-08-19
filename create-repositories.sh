#!/bin/bash

# Script to create all OpenPolicyPlatform V5 repositories

set -e

echo "🚀 Creating OpenPolicyPlatform V5 Repositories..."

# GitHub organization/user
ORG="ashish-tandon"

# Repository names
REPOS=(
    "openpolicy-platform-core"
    "openpolicy-platform-services"
    "openpolicy-platform-web"
    "openpolicy-platform-monitoring"
    "openpolicy-platform-deployment"
    "openpolicy-platform-docs"
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
