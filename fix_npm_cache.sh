#!/bin/bash
# Fix npm cache permission issues

echo "Fixing npm cache permissions..."

# Get current user
USER=$(whoami)

# Fix ownership of npm cache directory
if [ -d "$HOME/.npm" ]; then
    echo "Fixing ownership of ~/.npm directory..."
    sudo chown -R $USER:$USER ~/.npm
    echo "✓ Ownership fixed"
fi

# Clear npm cache
echo "Clearing npm cache..."
npm cache clean --force
echo "✓ Cache cleared"

# Verify npm cache location
echo ""
echo "npm cache location:"
npm config get cache

echo ""
echo "========================================="
echo "npm cache fixed!"
echo "========================================="
echo ""
echo "Now try running:"
echo "  cd frontend"
echo "  npm install"
echo ""
