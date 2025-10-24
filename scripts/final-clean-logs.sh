#!/bin/bash

echo "Final cleanup of console statements..."

# Find all files with console statements and clean them
find webapp/src -name "*.vue" -o -name "*.js" | while read file; do
  if grep -q "console\." "$file"; then
    echo "Cleaning: $file"
    
    # Replace all console.error with comments
    sed -i '' 's/.*console\.error.*/    \/\/ Handle error/' "$file"
    
    # Remove all console.log lines
    sed -i '' '/console\.log/d' "$file"
    
    # Remove all console.warn lines  
    sed -i '' '/console\.warn/d' "$file"
    
    echo "  ✓ Cleaned $file"
  fi
done

echo "Final cleanup completed!"
