#!/bin/bash

# Script to remove debug console logs from webapp files
# This script removes console.log, console.error, console.warn statements

echo "Removing debug console logs from webapp files..."

# Find all Vue and JS files in webapp/src
find webapp/src -name "*.vue" -o -name "*.js" | while read file; do
  echo "Processing: $file"
  
  # Create backup
  cp "$file" "$file.bak"
  
  # Remove console.log statements (but keep error handling)
  sed -i '' '/console\.log/d' "$file"
  
  # Remove console.warn statements
  sed -i '' '/console\.warn/d' "$file"
  
  # Replace console.error with comments (keep error handling structure)
  sed -i '' 's/console\.error([^)]*);/\/\/ Handle error/' "$file"
  
  # Clean up empty lines
  sed -i '' '/^[[:space:]]*$/N;/^\n$/d' "$file"
  
  echo "  ✓ Cleaned $file"
done

echo "Debug logs removal completed!"
echo "Backup files created with .bak extension"
