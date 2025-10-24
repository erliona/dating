#!/bin/bash

# Script to optimize layout for Telegram Mini App
echo "Optimizing layout for Telegram Mini App..."

# Find all Vue files and optimize them
find webapp/src -name "*.vue" | while read file; do
  echo "Processing: $file"
  
  # Create backup
  cp "$file" "$file.bak"
  
  # Optimize spacing in CSS
  sed -i '' 's/var(--spacing-lg)/var(--spacing-md)/g' "$file"
  sed -i '' 's/var(--spacing-xl)/var(--spacing-lg)/g' "$file"
  sed -i '' 's/var(--spacing-xxl)/var(--spacing-xl)/g' "$file"
  
  # Optimize font sizes
  sed -i '' 's/var(--font-size-lg)/var(--font-size-md)/g' "$file"
  sed -i '' 's/var(--font-size-xl)/var(--font-size-lg)/g' "$file"
  sed -i '' 's/var(--font-size-xxl)/var(--font-size-xl)/g' "$file"
  sed -i '' 's/var(--font-size-xxxl)/var(--font-size-xxl)/g' "$file"
  
  # Optimize padding and margins
  sed -i '' 's/padding: var(--spacing-lg)/padding: var(--spacing-md)/g' "$file"
  sed -i '' 's/margin-bottom: var(--spacing-lg)/margin-bottom: var(--spacing-md)/g' "$file"
  sed -i '' 's/margin-top: var(--spacing-lg)/margin-top: var(--spacing-md)/g' "$file"
  
  # Optimize button sizes
  sed -i '' 's/min-height: 44px/min-height: 36px/g' "$file"
  sed -i '' 's/min-height: 48px/min-height: 40px/g' "$file"
  sed -i '' 's/min-height: 52px/min-height: 44px/g' "$file"
  
  # Optimize icon sizes
  sed -i '' 's/width: 24px/width: 20px/g' "$file"
  sed -i '' 's/height: 24px/height: 20px/g' "$file"
  sed -i '' 's/width: 20px/width: 16px/g' "$file"
  sed -i '' 's/height: 20px/height: 16px/g' "$file"
  
  echo "  ✓ Optimized $file"
done

echo "Layout optimization completed!"
echo "Backup files created with .bak extension"
