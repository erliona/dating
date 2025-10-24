#!/bin/bash

# Script to add 'from __future__ import annotations' to Python files
# This improves forward compatibility with Python type hints

set -e

echo "🔍 Adding 'from __future__ import annotations' to Python files..."

# Find all Python files in main directories
PYTHON_FILES=$(find . -name "*.py" \
    -not -path "./.git/*" \
    -not -path "./.venv/*" \
    -not -path "./venv/*" \
    -not -path "./env/*" \
    -not -path "./migrations/*" \
    -not -path "./tests/*" \
    -not -path "./monitoring/*" \
    -not -path "./node_modules/*" \
    | grep -E "^(./bot/|./core/|./gateway/|./services/)")

# Count total files
TOTAL_FILES=$(echo "$PYTHON_FILES" | wc -l)
echo "📊 Found $TOTAL_FILES Python files to process"

# Process each file
PROCESSED=0
SKIPPED=0

for file in $PYTHON_FILES; do
    # Check if file already has the import
    if grep -q "from __future__ import annotations" "$file"; then
        echo "⏭️  Skipping $file (already has future import)"
        ((SKIPPED++))
        continue
    fi
    
    # Check if file is empty or has only comments/docstrings
    if [ ! -s "$file" ] || grep -q "^#.*$" "$file" && ! grep -q "^[^#]" "$file"; then
        echo "⏭️  Skipping $file (empty or comments only)"
        ((SKIPPED++))
        continue
    fi
    
    echo "📝 Processing $file..."
    
    # Create temporary file
    TEMP_FILE=$(mktemp)
    
    # Add future import at the top
    echo "from __future__ import annotations" > "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    
    # Add rest of the file content
    cat "$file" >> "$TEMP_FILE"
    
    # Replace original file
    mv "$TEMP_FILE" "$file"
    
    ((PROCESSED++))
done

echo "✅ Processing complete!"
echo "📊 Processed: $PROCESSED files"
echo "⏭️  Skipped: $SKIPPED files"
echo "📈 Total: $TOTAL_FILES files"

# Verify the changes
echo ""
echo "🔍 Verifying changes..."
FILES_WITH_FUTURE=$(find . -name "*.py" \
    -not -path "./.git/*" \
    -not -path "./.venv/*" \
    -not -path "./venv/*" \
    -not -path "./env/*" \
    -not -path "./migrations/*" \
    -not -path "./tests/*" \
    -not -path "./monitoring/*" \
    -not -path "./node_modules/*" \
    | grep -E "^(./bot/|./core/|./gateway/|./services/)" \
    | xargs grep -l "from __future__ import annotations" | wc -l)

echo "✅ Files with future imports: $FILES_WITH_FUTURE/$TOTAL_FILES"
