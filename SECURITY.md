# Security Policy

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 3.1.x   | :white_check_mark: |
| < 3.1   | :x:                |

## Security Model

### Authentication & Authorization

- **JWT Tokens**: All API endpoints require valid JWT tokens for authentication
- **Telegram WebApp**: Authentication via Telegram's initData validation using HMAC-SHA256
- **Admin Panel**: Separate admin authentication with environment-based credentials
- **Rate Limiting**: Auth endpoints protected against brute force attacks (5 requests per 5 minutes)

### Data Protection

- **Input Validation**: All user inputs are validated and sanitized
- **SQL Injection Protection**: All database queries use parameterized statements via SQLAlchemy ORM
- **XSS Prevention**: HTML content is sanitized before storage
- **CORS**: Restricted to specific domains only (no wildcard origins)

### Infrastructure Security

- **HTTPS Enforcement**: All production traffic redirected to HTTPS
- **Environment Variables**: All secrets stored in environment variables, no hardcoded values
- **Database Security**: Strong passwords required, no default credentials
- **Network Segmentation**: Services communicate via internal Docker networks

## Security Features

### Implemented Security Measures

1. **JWT Authentication**
   - 24-hour token expiration
   - Strong secret key required (no defaults)
   - Signature verification on all protected endpoints

2. **Rate Limiting**
   - Auth endpoints: 5 requests per 5 minutes per IP
   - General endpoints: 10 requests per minute per user
   - Automatic cleanup of expired rate limit data

3. **Input Validation**
   - Profile data validation with length limits
   - Type checking for all inputs
   - Geographic coordinate validation
   - Username format validation (Telegram standards)

4. **Error Handling**
   - Generic error messages for clients
   - Detailed errors logged server-side only
   - No stack traces exposed to users

5. **File Upload Security**
   - File type validation
   - Size limits enforced
   - NSFW detection with configurable threshold
   - Path traversal protection

6. **Monitoring & Logging**
   - Security events logged with correlation IDs
   - Failed authentication attempts tracked
   - Rate limit violations monitored
   - Prometheus metrics for security events

## Reporting a Vulnerability

If you discover a security vulnerability, please follow these steps:

1. **DO NOT** create a public GitHub issue
2. **DO NOT** disclose the vulnerability publicly
3. Send details to: security@dating-app.com (or create a private security advisory)

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Fix Development**: Within 2 weeks (for critical issues)
- **Public Disclosure**: After fix is deployed and tested

## Security Best Practices

### For Developers

1. **Never commit secrets** to version control
2. **Use environment variables** for all configuration
3. **Validate all inputs** before processing
4. **Use parameterized queries** for database operations
5. **Log security events** for monitoring
6. **Keep dependencies updated** and scan for vulnerabilities

### For Deployment

1. **Use strong passwords** for all services
2. **Enable HTTPS** with valid certificates
3. **Configure CORS** to specific domains only
4. **Set up monitoring** for security events
5. **Regular security updates** of dependencies
6. **Backup encryption** for sensitive data

### For Users

1. **Use strong Telegram passwords**
2. **Enable 2FA** on Telegram account
3. **Report suspicious activity** immediately
4. **Keep Telegram app updated**
5. **Be cautious with personal information**

## Security Configuration

### Required Environment Variables

```bash
# Authentication
JWT_SECRET=your-strong-jwt-secret-here
BOT_TOKEN=your-telegram-bot-token

# Database
POSTGRES_PASSWORD=your-strong-database-password

# Admin Panel
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-strong-admin-password

# CORS
WEBAPP_DOMAIN=https://your-domain.com
```

### Security Headers

The application sets the following security headers:

- `Strict-Transport-Security`: Enforces HTTPS
- `X-Content-Type-Options`: Prevents MIME sniffing
- `X-Frame-Options`: Prevents clickjacking
- `X-XSS-Protection`: Enables XSS filtering

## Vulnerability Disclosure

We follow responsible disclosure practices:

1. **Private reporting** of vulnerabilities
2. **Coordinated disclosure** with security researchers
3. **Timely fixes** for critical issues
4. **Public acknowledgment** after fixes are deployed

## Security Updates

- **Critical**: Fixed within 24-48 hours
- **High**: Fixed within 1 week
- **Medium**: Fixed within 1 month
- **Low**: Fixed in next major release

## Contact

For security-related questions or concerns:

- **Security Team**: security@dating-app.com
- **General Support**: support@dating-app.com
- **Emergency**: Use GitHub private security advisory

---

**Last Updated**: October 23, 2025
**Version**: 3.1.0
