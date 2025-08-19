#!/bin/bash

# OpenPolicy Platform - Quick Start Script
# The easiest way to get everything running!

echo "🚀 Starting OpenPolicy Platform..."
echo "================================="
echo ""

# Run the deployment
./deploy.sh

echo ""
echo "✅ Platform is ready!"
echo ""
echo "📱 Open these in your browser:"
echo "   - User Dashboard: http://localhost"
echo "   - Admin Panel: http://localhost:3001"
echo ""
echo "🔑 Login with:"
echo "   - Admin: admin@openpolicy.ca / admin123"
echo "   - User: user@example.com / user123"
echo ""
echo "📊 To monitor the platform, run: ./monitor.sh"
echo "🧪 To test everything, run: ./test-platform.sh"
echo ""