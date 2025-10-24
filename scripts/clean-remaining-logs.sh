#!/bin/bash

# Clean remaining console statements
echo "Cleaning remaining console statements..."

# List of files that still have console statements
files=(
  "webapp/src/components/chat/ConversationList.vue"
  "webapp/src/components/chat/ChatInput.vue"
  "webapp/src/components/profile/VerificationFlow.vue"
  "webapp/src/components/profile/PhotoUploader.vue"
  "webapp/src/components/onboarding/StepPhotos.vue"
  "webapp/src/views/ProfileView.vue"
  "webapp/src/views/AdminVerifications.vue"
  "webapp/src/views/SettingsView.vue"
  "webapp/src/views/ChatView.vue"
  "webapp/src/views/AdminReports.vue"
  "webapp/src/views/EditProfileView.vue"
  "webapp/src/views/LikesView.vue"
  "webapp/src/views/ConversationView.vue"
  "webapp/src/views/MatchesView.vue"
  "webapp/src/views/AdminPhotos.vue"
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo "Processing: $file"
    
    # Replace console.error with comments
    sed -i '' 's/console\.error([^)]*);/\/\/ Handle error/' "$file"
    
    # Remove console.log lines
    sed -i '' '/console\.log/d' "$file"
    
    # Remove console.warn lines
    sed -i '' '/console\.warn/d' "$file"
    
    echo "  ✓ Cleaned $file"
  fi
done

echo "Remaining console statements cleaned!"
