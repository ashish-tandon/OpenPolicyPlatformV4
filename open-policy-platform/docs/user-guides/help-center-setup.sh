#!/bin/bash

# Help Center Setup Script
# Creates interactive documentation website using Docusaurus

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Create help center structure
setup_help_center() {
    log "Setting up interactive help center..."
    
    # Create Docusaurus project
    npx create-docusaurus@latest help-center classic --typescript
    
    cd help-center
    
    # Configure Docusaurus
    cat > docusaurus.config.js << 'EOF'
module.exports = {
  title: 'OpenPolicy Help Center',
  tagline: 'Everything you need to know about OpenPolicy Platform',
  url: 'https://help.openpolicy.com',
  baseUrl: '/',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  favicon: 'img/favicon.ico',
  organizationName: 'openpolicy',
  projectName: 'help-center',
  
  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/openpolicy/help-center/tree/main/',
          showLastUpdateAuthor: true,
          showLastUpdateTime: true,
        },
        blog: {
          showReadingTime: true,
          editUrl: 'https://github.com/openpolicy/help-center/tree/main/',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      },
    ],
  ],

  themeConfig: {
    navbar: {
      title: 'OpenPolicy Help',
      logo: {
        alt: 'OpenPolicy Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'doc',
          docId: 'intro',
          position: 'left',
          label: 'Documentation',
        },
        {
          to: '/tutorials',
          label: 'Tutorials',
          position: 'left'
        },
        {
          to: '/api',
          label: 'API Reference',
          position: 'left'
        },
        {
          to: '/faq',
          label: 'FAQ',
          position: 'left'
        },
        {
          href: 'https://github.com/openpolicy',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Getting Started',
              to: '/docs/intro',
            },
            {
              label: 'User Guide',
              to: '/docs/user-guide',
            },
            {
              label: 'API Reference',
              to: '/docs/api',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'Forum',
              href: 'https://community.openpolicy.com',
            },
            {
              label: 'Discord',
              href: 'https://discord.gg/openpolicy',
            },
            {
              label: 'Twitter',
              href: 'https://twitter.com/openpolicy',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'Blog',
              to: '/blog',
            },
            {
              label: 'GitHub',
              href: 'https://github.com/openpolicy',
            },
            {
              label: 'Status',
              href: 'https://status.openpolicy.com',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} OpenPolicy Platform. Built with Docusaurus.`,
    },
    prism: {
      theme: require('prism-react-renderer/themes/github'),
      darkTheme: require('prism-react-renderer/themes/dracula'),
      additionalLanguages: ['bash', 'python', 'json'],
    },
    algolia: {
      appId: 'YOUR_APP_ID',
      apiKey: 'YOUR_API_KEY',
      indexName: 'openpolicy_help',
      contextualSearch: true,
    },
  },
  
  plugins: [
    [
      '@docusaurus/plugin-pwa',
      {
        debug: true,
        offlineModeActivationStrategies: [
          'appInstalled',
          'standalone',
          'queryString',
        ],
        pwaHead: [
          {
            tagName: 'link',
            rel: 'icon',
            href: '/img/logo.png',
          },
          {
            tagName: 'link',
            rel: 'manifest',
            href: '/manifest.json',
          },
          {
            tagName: 'meta',
            name: 'theme-color',
            content: '#1976d2',
          },
        ],
      },
    ],
  ],
};
EOF

    # Create interactive tutorials
    mkdir -p docs/tutorials
    
    cat > docs/tutorials/interactive-search.mdx << 'EOF'
---
id: interactive-search
title: Interactive Search Tutorial
sidebar_label: Search Tutorial
---

import {SearchDemo} from '@site/src/components/SearchDemo';
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Interactive Search Tutorial

Learn how to use OpenPolicy's powerful search features with this interactive tutorial.

## Try It Yourself

<SearchDemo />

## Search Syntax

<Tabs>
  <TabItem value="basic" label="Basic Search" default>

### Simple Searches
Type any keyword to search across all content:
- `healthcare`
- `education funding`
- `climate change`

  </TabItem>
  <TabItem value="advanced" label="Advanced Search">

### Search Operators
Use operators for precise searches:

| Operator | Example | Description |
|----------|---------|-------------|
| AND | `healthcare AND reform` | Both terms must appear |
| OR | `climate OR environment` | Either term can appear |
| NOT | `tax NOT income` | Exclude terms |
| " " | `"affordable care act"` | Exact phrase |
| * | `educat*` | Wildcard |

  </TabItem>
  <TabItem value="filters" label="Filters">

### Available Filters
Narrow your results with filters:

- **Category**: Healthcare, Education, Environment, etc.
- **Date Range**: Last 24h, 7 days, 30 days, Custom
- **Status**: Draft, Active, Archived
- **Type**: Policy, Bill, Report, Analysis

  </TabItem>
</Tabs>

## Video Walkthrough

<iframe width="100%" height="400" src="https://www.youtube.com/embed/search-tutorial-id" frameborder="0" allowfullscreen></iframe>

## Practice Exercises

### Exercise 1: Find Healthcare Policies
Find all active healthcare policies from the last 30 days.

<details>
  <summary>Show Solution</summary>

1. Enter `healthcare` in search
2. Click Advanced Filters
3. Set Category to "Healthcare"
4. Set Date Range to "Last 30 days"
5. Set Status to "Active"
6. Click Search

</details>

### Exercise 2: Complex Search
Find education bills that mention "funding" but not "tax".

<details>
  <summary>Show Solution</summary>

Use this search query:
```
category:education AND funding NOT tax
```

</details>

## Tips & Tricks

:::tip Pro Tip
Save frequently used searches for quick access later!
:::

:::info
Search history is automatically saved and can be accessed from the search dropdown.
:::

## Next Steps

- [Advanced Filtering Guide](/docs/tutorials/advanced-filters)
- [Saved Searches](/docs/tutorials/saved-searches)
- [Search API](/docs/api/search)
EOF

    # Create interactive components
    mkdir -p src/components
    
    cat > src/components/SearchDemo.tsx << 'EOF'
import React, { useState } from 'react';
import { 
  TextField, 
  Button, 
  Card, 
  CardContent, 
  Chip,
  Stack,
  Typography,
  Box,
  Paper,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Collapse,
  Alert
} from '@mui/material';
import { 
  Search, 
  FilterList, 
  Clear,
  ExpandMore,
  ExpandLess
} from '@mui/icons-material';

export function SearchDemo() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    status: '',
    dateRange: ''
  });
  const [showFilters, setShowFilters] = useState(false);
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);

  const mockSearch = () => {
    setSearched(true);
    // Mock search results
    const mockResults = [
      {
        id: 1,
        title: 'Healthcare Reform Act 2024',
        type: 'Policy',
        status: 'Active',
        excerpt: 'Comprehensive healthcare reform addressing accessibility...'
      },
      {
        id: 2,
        title: 'Education Funding Bill',
        type: 'Bill',
        status: 'In Committee',
        excerpt: 'Proposes increased funding for public education...'
      }
    ];
    
    setResults(query ? mockResults : []);
  };

  const handleSearch = () => {
    mockSearch();
  };

  const clearSearch = () => {
    setQuery('');
    setFilters({ category: '', status: '', dateRange: '' });
    setResults([]);
    setSearched(false);
  };

  return (
    <Card sx={{ my: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Try the Search Interface
        </Typography>
        
        <Stack spacing={2}>
          <Stack direction="row" spacing={1}>
            <TextField
              fullWidth
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search policies, bills, representatives..."
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'action.active' }} />
              }}
            />
            <Button
              variant="contained"
              onClick={handleSearch}
              startIcon={<Search />}
            >
              Search
            </Button>
            {(query || searched) && (
              <IconButton onClick={clearSearch}>
                <Clear />
              </IconButton>
            )}
          </Stack>

          <Box>
            <Button
              onClick={() => setShowFilters(!showFilters)}
              startIcon={<FilterList />}
              endIcon={showFilters ? <ExpandLess /> : <ExpandMore />}
            >
              Advanced Filters
            </Button>
          </Box>

          <Collapse in={showFilters}>
            <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
              <Stack direction="row" spacing={2} flexWrap="wrap">
                <TextField
                  select
                  label="Category"
                  value={filters.category}
                  onChange={(e) => setFilters({...filters, category: e.target.value})}
                  sx={{ minWidth: 150 }}
                  SelectProps={{ native: true }}
                >
                  <option value="">All Categories</option>
                  <option value="healthcare">Healthcare</option>
                  <option value="education">Education</option>
                  <option value="environment">Environment</option>
                </TextField>

                <TextField
                  select
                  label="Status"
                  value={filters.status}
                  onChange={(e) => setFilters({...filters, status: e.target.value})}
                  sx={{ minWidth: 150 }}
                  SelectProps={{ native: true }}
                >
                  <option value="">All Statuses</option>
                  <option value="active">Active</option>
                  <option value="draft">Draft</option>
                  <option value="archived">Archived</option>
                </TextField>

                <TextField
                  select
                  label="Date Range"
                  value={filters.dateRange}
                  onChange={(e) => setFilters({...filters, dateRange: e.target.value})}
                  sx={{ minWidth: 150 }}
                  SelectProps={{ native: true }}
                >
                  <option value="">Any Time</option>
                  <option value="24h">Last 24 Hours</option>
                  <option value="7d">Last 7 Days</option>
                  <option value="30d">Last 30 Days</option>
                </TextField>
              </Stack>
            </Paper>
          </Collapse>

          {searched && (
            <Box>
              {results.length > 0 ? (
                <>
                  <Typography variant="subtitle2" gutterBottom>
                    Search Results ({results.length})
                  </Typography>
                  <List>
                    {results.map((result) => (
                      <ListItem key={result.id} sx={{ px: 0 }}>
                        <ListItemText
                          primary={
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Typography variant="subtitle1">
                                {result.title}
                              </Typography>
                              <Chip label={result.type} size="small" />
                              <Chip 
                                label={result.status} 
                                size="small" 
                                color={result.status === 'Active' ? 'success' : 'default'}
                              />
                            </Stack>
                          }
                          secondary={result.excerpt}
                        />
                      </ListItem>
                    ))}
                  </List>
                </>
              ) : (
                <Alert severity="info">
                  No results found for "{query}". Try different search terms or adjust filters.
                </Alert>
              )}
            </Box>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
EOF

    # Create FAQ page
    cat > docs/faq.md << 'EOF'
---
id: faq
title: Frequently Asked Questions
sidebar_label: FAQ
---

# Frequently Asked Questions

## General Questions

### What is OpenPolicy Platform?
OpenPolicy Platform is a comprehensive solution for tracking government policies, legislation, and political data in real-time.

### Is it free to use?
Basic access is free for all users. Premium features require a subscription.

### How often is data updated?
Most data is updated in real-time. Some reports and analytics refresh hourly.

### Can I export data?
Yes, you can export data in various formats including CSV, Excel, and PDF.

## Account & Security

### How do I reset my password?
Click "Forgot Password" on the login page and follow the email instructions.

### Is two-factor authentication available?
Yes, we strongly recommend enabling 2FA in your account settings.

### Can I have multiple accounts?
One account per email address. For teams, use our organization features.

### How do I delete my account?
Go to Settings > Account > Delete Account. This action is permanent.

## Features & Usage

### How do I track a specific bill?
Find the bill and click "Track This Bill". Configure your notification preferences.

### Can I save searches?
Yes, perform a search and click "Save Search" to receive regular updates.

### How do I contact my representative?
Go to their profile and click "Contact". We provide email, phone, and office information.

### Is there an API?
Yes, full REST API access is available. See our [API documentation](/api).

## Mobile App

### Where can I download the app?
Search "OpenPolicy" in the App Store (iOS) or Google Play (Android).

### Does it work offline?
Yes, you can download content for offline reading.

### How do I sync between devices?
All data syncs automatically when you're logged into the same account.

## Troubleshooting

### The site is loading slowly
Try clearing your browser cache, disabling extensions, or using a different browser.

### I can't log in
Check your email/password, clear cookies, or try resetting your password.

### Search returns no results
Try broader terms, check spelling, or remove filters.

### I'm not receiving notifications
Check your notification settings and email spam folder.

## Contact Support

Still need help? Contact us:
- Email: support@openpolicy.com
- Live Chat: Available 9 AM - 5 PM EST
- Phone: 1-800-POLICY-1
EOF

    # Create custom CSS
    cat > src/css/custom.css << 'EOF'
:root {
  --ifm-color-primary: #1976d2;
  --ifm-color-primary-dark: #1565c0;
  --ifm-color-primary-darker: #0d47a1;
  --ifm-color-primary-darkest: #0a3d91;
  --ifm-color-primary-light: #42a5f5;
  --ifm-color-primary-lighter: #64b5f6;
  --ifm-color-primary-lightest: #90caf9;
  --ifm-code-font-size: 95%;
}

/* Dark mode */
[data-theme='dark'] {
  --ifm-color-primary: #42a5f5;
  --ifm-color-primary-dark: #2196f3;
  --ifm-color-primary-darker: #1e88e5;
  --ifm-color-primary-darkest: #1976d2;
  --ifm-color-primary-light: #64b5f6;
  --ifm-color-primary-lighter: #90caf9;
  --ifm-color-primary-lightest: #bbdefb;
}

.hero--primary {
  --ifm-hero-background-color: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%);
}

.button--lg {
  font-size: 1.2rem;
  padding: 1rem 2rem;
}

/* Interactive elements */
.interactive-demo {
  border: 2px solid var(--ifm-color-primary);
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
  background-color: var(--ifm-background-surface-color);
}

/* Video embeds */
.video-container {
  position: relative;
  padding-bottom: 56.25%; /* 16:9 */
  height: 0;
  overflow: hidden;
}

.video-container iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

/* Custom admonitions */
.admonition-pro-tip {
  background-color: #e3f2fd;
  border-left: 4px solid #2196f3;
}

.admonition-pro-tip .admonition-icon {
  color: #2196f3;
}

/* Search */
.DocSearch-Button {
  border-radius: 8px;
}

/* Cards */
.card {
  border: 1px solid var(--ifm-color-emphasis-300);
  border-radius: 8px;
  padding: 1.5rem;
  margin: 1rem 0;
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

/* Feature grid */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin: 2rem 0;
}

.feature-item {
  text-align: center;
  padding: 2rem;
  border-radius: 8px;
  background-color: var(--ifm-background-surface-color);
  transition: all 0.3s ease;
}

.feature-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: var(--ifm-color-primary);
}
EOF

    # Install dependencies
    npm install @mui/material @emotion/react @emotion/styled @mui/icons-material

    log "✅ Help center setup complete!"
}

# Build and deploy
build_help_center() {
    log "Building help center..."
    
    npm run build
    
    # Deploy to GitHub Pages or Netlify
    # npm run deploy
    
    log "✅ Help center built successfully!"
}

# Main execution
main() {
    setup_help_center
    build_help_center
    
    log "Help center is ready!"
    log "Run 'npm start' in help-center directory to preview"
    log "Deploy to: https://help.openpolicy.com"
}

main "$@"