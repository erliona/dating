#!/bin/bash

echo "🧹 Squashing Git history..."

# Create a backup branch first
echo "📦 Creating backup branch..."
git branch backup-before-squash

# Interactive rebase to squash commits
echo "🔄 Starting interactive rebase..."
echo "This will open an editor where you can:"
echo "1. Keep the first commit as 'pick'"
echo "2. Change all other commits to 'squash' or 's'"
echo "3. Save and close the editor"
echo "4. Edit commit messages in the next editor"
echo ""
echo "Press Enter to continue..."
read

# Start interactive rebase from the beginning
git rebase -i --root
