#!/bin/bash

# Semantic Release Setup Script
# Implements automated versioning and changelog generation

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Create semantic-release configuration
create_release_config() {
    log "Creating semantic-release configuration..."
    
    # Create .releaserc.json
    cat > .releaserc.json << 'EOF'
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    [
      "@semantic-release/changelog",
      {
        "changelogFile": "CHANGELOG.md"
      }
    ],
    [
      "@semantic-release/exec",
      {
        "prepareCmd": "npm version ${nextRelease.version} --no-git-tag-version"
      }
    ],
    [
      "@semantic-release/git",
      {
        "assets": ["CHANGELOG.md", "package.json", "package-lock.json"],
        "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
      }
    ],
    "@semantic-release/github",
    [
      "@semantic-release/npm",
      {
        "npmPublish": false
      }
    ],
    [
      "@semantic-release/github",
      {
        "assets": [
          {
            "path": "dist/**/*.tar.gz",
            "label": "Distribution package"
          }
        ]
      }
    ]
  ]
}
EOF

    # Create commitlint configuration
    cat > .commitlintrc.json << 'EOF'
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [
      2,
      "always",
      [
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "perf",
        "test",
        "chore",
        "revert",
        "build",
        "ci"
      ]
    ],
    "subject-case": [2, "always", "sentence-case"],
    "subject-full-stop": [2, "never", "."],
    "header-max-length": [2, "always", 100]
  }
}
EOF

    # Create husky pre-commit hook
    mkdir -p .husky
    cat > .husky/pre-commit << 'EOF'
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npx lint-staged
EOF
    chmod +x .husky/pre-commit

    # Create commit-msg hook
    cat > .husky/commit-msg << 'EOF'
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npx --no -- commitlint --edit "$1"
EOF
    chmod +x .husky/commit-msg

    # Create lint-staged configuration
    cat > .lintstagedrc.json << 'EOF'
{
  "*.{js,jsx,ts,tsx}": [
    "eslint --fix",
    "prettier --write"
  ],
  "*.{json,md,yml,yaml}": [
    "prettier --write"
  ],
  "*.py": [
    "black",
    "flake8"
  ]
}
EOF

    # Create version bump script
    cat > scripts/bump-version.sh << 'EOF'
#!/bin/bash

# Version bump script with changelog generation

CURRENT_VERSION=$(cat VERSION 2>/dev/null || echo "0.0.0")
echo "Current version: $CURRENT_VERSION"

# Determine version bump type
echo "Select version bump type:"
echo "1) Patch (bug fixes)"
echo "2) Minor (new features)"
echo "3) Major (breaking changes)"
read -p "Enter choice [1-3]: " choice

case $choice in
    1) BUMP_TYPE="patch" ;;
    2) BUMP_TYPE="minor" ;;
    3) BUMP_TYPE="major" ;;
    *) echo "Invalid choice"; exit 1 ;;
esac

# Calculate new version
IFS='.' read -r -a version_parts <<< "$CURRENT_VERSION"
MAJOR="${version_parts[0]}"
MINOR="${version_parts[1]}"
PATCH="${version_parts[2]}"

case $BUMP_TYPE in
    "patch")
        PATCH=$((PATCH + 1))
        ;;
    "minor")
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    "major")
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo "New version: $NEW_VERSION"

# Update VERSION file
echo "$NEW_VERSION" > VERSION

# Generate changelog entry
cat > CHANGELOG_ENTRY.md << EOL
## [$NEW_VERSION] - $(date +%Y-%m-%d)

### Added
- List new features here

### Changed
- List changes here

### Fixed
- List bug fixes here

### Removed
- List removed features here

EOL

# Prepend to CHANGELOG.md
if [ -f CHANGELOG.md ]; then
    cat CHANGELOG_ENTRY.md CHANGELOG.md > CHANGELOG.tmp
    mv CHANGELOG.tmp CHANGELOG.md
    rm CHANGELOG_ENTRY.md
else
    mv CHANGELOG_ENTRY.md CHANGELOG.md
fi

echo "Version bumped to $NEW_VERSION"
echo "Please update CHANGELOG.md with actual changes"
EOF
    chmod +x scripts/bump-version.sh

    log "✅ Semantic release configuration created"
}

# Create GitHub release workflow
create_release_workflow() {
    log "Creating GitHub release workflow..."
    
    mkdir -p .github/workflows
    cat > .github/workflows/release.yml << 'EOF'
name: Release

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  release:
    name: Release
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: |
          npm ci
          npm install -D @semantic-release/changelog @semantic-release/exec @semantic-release/git
      
      - name: Run tests
        run: npm test
      
      - name: Build
        run: npm run build
      
      - name: Create release package
        run: |
          mkdir -p dist
          tar -czf dist/open-policy-platform-${GITHUB_SHA::8}.tar.gz \
            --exclude='node_modules' \
            --exclude='.git' \
            --exclude='dist' \
            .
      
      - name: Semantic Release
        env:
          GITHUB_TOKEN: ${{ secrets.RELEASE_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
        run: npx semantic-release
      
      - name: Update Docker tags
        if: steps.semantic-release.outputs.new_release_published == 'true'
        run: |
          docker tag ${{ env.IMAGE_NAME }}:latest ${{ env.IMAGE_NAME }}:${{ steps.semantic-release.outputs.new_release_version }}
          docker push ${{ env.IMAGE_NAME }}:${{ steps.semantic-release.outputs.new_release_version }}
      
      - name: Deploy to production
        if: steps.semantic-release.outputs.new_release_published == 'true'
        run: |
          echo "Deploying version ${{ steps.semantic-release.outputs.new_release_version }} to production"
          # Add deployment commands here

  create-release-pr:
    name: Create Release PR
    runs-on: ubuntu-latest
    if: github.event_name == 'workflow_dispatch'
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      
      - name: Create Release Branch
        run: |
          git checkout -b release/$(date +%Y%m%d-%H%M%S)
          git push origin HEAD
      
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          title: "chore: prepare release"
          body: |
            ## Release Checklist
            - [ ] All tests passing
            - [ ] Documentation updated
            - [ ] CHANGELOG.md updated
            - [ ] Version bumped
            - [ ] Security scan completed
            - [ ] Performance benchmarks met
          branch: release/$(date +%Y%m%d-%H%M%S)
          labels: release
EOF

    log "✅ Release workflow created"
}

# Install dependencies
install_dependencies() {
    log "Installing semantic-release dependencies..."
    
    npm install --save-dev \
        @semantic-release/changelog \
        @semantic-release/commit-analyzer \
        @semantic-release/exec \
        @semantic-release/git \
        @semantic-release/github \
        @semantic-release/npm \
        @semantic-release/release-notes-generator \
        @commitlint/cli \
        @commitlint/config-conventional \
        husky \
        lint-staged
    
    # Initialize husky
    npx husky install
    
    log "✅ Dependencies installed"
}

# Main execution
main() {
    log "Setting up semantic release..."
    
    create_release_config
    create_release_workflow
    
    if [ -f "package.json" ]; then
        install_dependencies
    fi
    
    # Create initial CHANGELOG.md
    if [ ! -f "CHANGELOG.md" ]; then
        cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release

EOF
    fi
    
    # Create VERSION file
    echo "1.0.0" > VERSION
    
    log "✅ Semantic release setup complete!"
    log ""
    log "Next steps:"
    log "1. Create a personal access token with 'repo' scope"
    log "2. Add RELEASE_TOKEN secret to GitHub repository"
    log "3. Commit using conventional commits (feat:, fix:, etc.)"
    log "4. Push to main branch to trigger automatic release"
}

main "$@"