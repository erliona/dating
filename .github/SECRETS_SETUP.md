# GitHub Secrets Setup Guide

This guide explains how to configure GitHub Secrets for CI/CD workflows.

## Required Secrets

The following secrets must be configured in the GitHub repository settings:

### 1. TEST_JWT_SECRET
**Description**: JWT secret key for testing environment  
**How to generate**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
**Example output**: `wUZg5LFQv3nVxp3WWROJxoXaSCgu5dvIYcIU1GH4UzU`

### 2. TEST_BOT_TOKEN
**Description**: Telegram bot token for testing (can be fake, just valid format)  
**Format**: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`  
**Example**: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz-test-token`

**Note**: For tests, you don't need a real bot token. Just use any string in the correct format.

### 3. CODECOV_TOKEN
**Description**: Token for uploading coverage reports to Codecov  
**How to get**:
1. Go to [codecov.io](https://codecov.io)
2. Sign in with GitHub
3. Add your repository: `erliona/dating`
4. Copy the upload token from repository settings

## How to Add Secrets to GitHub

### Step-by-Step Instructions

1. Navigate to your GitHub repository: `https://github.com/erliona/dating`

2. Click on **Settings** (top navigation bar)

3. In the left sidebar, click on **Secrets and variables** → **Actions**

4. Click **New repository secret** button

5. Add each secret:
   - **Name**: `TEST_JWT_SECRET`
   - **Secret**: Paste the generated value
   - Click **Add secret**

6. Repeat steps 4-5 for `TEST_BOT_TOKEN` and `CODECOV_TOKEN`

### Verification

After adding all secrets, you should see them listed in the Actions secrets page:
- ✅ TEST_JWT_SECRET
- ✅ TEST_BOT_TOKEN
- ✅ CODECOV_TOKEN

**Note**: Secret values are hidden and cannot be viewed after creation. You can only update or delete them.

## Using Secrets in Workflows

Secrets are accessed in GitHub Actions workflows using the syntax:
```yaml
env:
  JWT_SECRET: ${{ secrets.TEST_JWT_SECRET }}
  BOT_TOKEN: ${{ secrets.TEST_BOT_TOKEN }}
```

GitHub automatically:
- ✅ Encrypts secrets at rest
- ✅ Masks secret values in logs (shows as `***`)
- ✅ Prevents forks from accessing secrets (security protection)

## Security Best Practices

1. **Never commit secrets** to git repository
2. **Use different secrets** for test, staging, and production
3. **Rotate secrets regularly** (every 90 days recommended)
4. **Limit secret access** using environments if needed
5. **Audit secret usage** in workflow run logs

## Environment-Specific Secrets (Optional)

For more complex setups, you can create separate environments:

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name it (e.g., `test`, `staging`, `production`)
4. Add environment-specific secrets

Then in your workflow:
```yaml
jobs:
  deploy:
    environment: production
    steps:
      - uses: actions/checkout@v4
      # Secrets from 'production' environment are now available
```

## Troubleshooting

### "Secret not found" error
- Check secret name spelling in workflow matches exactly
- Verify secret was added in repository settings
- Check if workflow is running from a fork (forks don't have access to secrets)

### Tests fail with authentication errors
- Verify `TEST_JWT_SECRET` is set and has sufficient length (>32 chars)
- Verify `TEST_BOT_TOKEN` follows correct format
- Check workflow logs (secrets will be masked as `***`)

### Coverage upload fails
- Verify `CODECOV_TOKEN` is correct
- Check that repository is registered on codecov.io
- Verify token hasn't expired

## Additional Resources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Codecov Documentation](https://docs.codecov.com/docs)
- [Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

