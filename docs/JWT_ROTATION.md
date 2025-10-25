# JWT Secret Rotation Guide

## Overview

This document outlines the JWT secret rotation strategy for the Dating Platform, including automated rotation procedures, emergency rotation, and rollback procedures.

## JWT Secret Management

### Current Configuration
- **JWT_SECRET**: Base64-encoded 256-bit secret
- **JWT_ALGORITHM**: HS256
- **JWT_ACCESS_TOKEN_EXPIRE_MINUTES**: 15
- **JWT_REFRESH_TOKEN_EXPIRE_DAYS**: 7
- **JWT_ISSUER**: dating-app
- **JWT_AUDIENCE**: dating-users

### Secret Storage
- **Environment Variable**: `JWT_SECRET` in all services
- **Backup Location**: `/secure/jwt-secret-backup.txt`
- **Rotation Log**: `/var/log/jwt-rotation.log`

## Rotation Schedule

### Planned Rotation
- **Frequency**: Every 90 days
- **Schedule**: First Sunday of each quarter
- **Notification**: 7 days advance notice to all services
- **Maintenance Window**: 2:00 AM - 4:00 AM UTC

### Emergency Rotation
- **Trigger**: Suspected compromise or security incident
- **Timeline**: Within 24 hours of detection
- **Process**: Immediate rotation with service restart
- **Communication**: Emergency notification to all teams

## Rotation Process

### Phase 1: Preparation (1 hour before)
1. **Backup Current Secret**
   ```bash
   # Backup current JWT secret
   cp /secure/jwt-secret.txt /secure/jwt-secret-backup-$(date +%Y%m%d).txt
   
   # Verify backup
   echo "Backup created: $(ls -la /secure/jwt-secret-backup-*.txt | tail -1)"
   ```

2. **Generate New Secret**
   ```bash
   # Generate new 256-bit secret
   NEW_JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
   echo "New JWT secret: $NEW_JWT_SECRET"
   
   # Store in secure location
   echo "$NEW_JWT_SECRET" > /secure/jwt-secret-new.txt
   chmod 600 /secure/jwt-secret-new.txt
   ```

3. **Validate New Secret**
   ```bash
   # Test new secret format
   python3 -c "
   import base64
   import secrets
   secret = secrets.token_urlsafe(32)
   print(f'Secret length: {len(secret)}')
   print(f'Base64 valid: {len(base64.b64decode(secret + \"==\")) == 32}')
   "
   ```

### Phase 2: Gradual Rollout (30 minutes)
1. **Update Environment Files**
   ```bash
   # Update all service environment files
   for service in auth-service profile-service discovery-service chat-service media-service admin-service notification-service data-service api-gateway telegram-bot; do
     echo "JWT_SECRET=$NEW_JWT_SECRET" >> /app/$service/.env
   done
   ```

2. **Deploy with Both Secrets**
   ```bash
   # Update docker-compose.yml with both secrets
   export JWT_SECRET_OLD=$CURRENT_JWT_SECRET
   export JWT_SECRET_NEW=$NEW_JWT_SECRET
   
   # Deploy services with dual secret support
   docker compose up -d
   ```

3. **Monitor Service Health**
   ```bash
   # Check all services are healthy
   docker compose ps | grep -v "healthy"
   
   # Test JWT validation with both secrets
   curl -H "Authorization: Bearer $OLD_TOKEN" http://localhost:8080/v1/auth/verify
   curl -H "Authorization: Bearer $NEW_TOKEN" http://localhost:8080/v1/auth/verify
   ```

### Phase 3: Full Migration (15 minutes)
1. **Remove Old Secret Support**
   ```bash
   # Update all services to use only new secret
   for service in auth-service profile-service discovery-service chat-service media-service admin-service notification-service data-service api-gateway telegram-bot; do
     sed -i 's/JWT_SECRET_OLD/# JWT_SECRET_OLD/' /app/$service/.env
   done
   ```

2. **Restart Services**
   ```bash
   # Restart all services with new secret only
   docker compose restart
   
   # Verify all services are healthy
   docker compose ps
   ```

3. **Cleanup Old Secret**
   ```bash
   # Remove old secret from environment
   unset JWT_SECRET_OLD
   
   # Archive old secret securely
   mv /secure/jwt-secret-backup-*.txt /secure/archive/
   ```

## Emergency Rotation

### Immediate Response
1. **Generate New Secret**
   ```bash
   # Emergency secret generation
   EMERGENCY_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
   echo "EMERGENCY: New JWT secret generated"
   ```

2. **Update All Services Immediately**
   ```bash
   # Update all services with emergency secret
   for service in auth-service profile-service discovery-service chat-service media-service admin-service notification-service data-service api-gateway telegram-bot; do
     echo "JWT_SECRET=$EMERGENCY_SECRET" > /app/$service/.env
     docker compose restart $service
   done
   ```

3. **Verify Rotation**
   ```bash
   # Test that old tokens are invalid
   curl -H "Authorization: Bearer $OLD_TOKEN" http://localhost:8080/v1/auth/verify
   # Should return 401 Unauthorized
   
   # Test that new tokens work
   curl -H "Authorization: Bearer $NEW_TOKEN" http://localhost:8080/v1/auth/verify
   # Should return 200 OK
   ```

### Post-Emergency Actions
1. **Notify All Users**
   - Send push notification about re-authentication required
   - Update frontend to handle 401 errors gracefully
   - Provide clear re-authentication flow

2. **Monitor for Issues**
   - Check error rates for authentication failures
   - Monitor user re-authentication success rates
   - Verify all services are functioning correctly

3. **Document Incident**
   - Record rotation reason and timeline
   - Update security procedures if needed
   - Schedule post-incident review

## Rollback Procedures

### Rollback to Previous Secret
1. **Stop All Services**
   ```bash
   # Stop all services
   docker compose down
   ```

2. **Restore Previous Secret**
   ```bash
   # Restore previous secret
   cp /secure/jwt-secret-backup-*.txt /secure/jwt-secret.txt
   
   # Update all services
   for service in auth-service profile-service discovery-service chat-service media-service admin-service notification-service data-service api-gateway telegram-bot; do
     echo "JWT_SECRET=$(cat /secure/jwt-secret.txt)" > /app/$service/.env
   done
   ```

3. **Restart Services**
   ```bash
   # Restart all services
   docker compose up -d
   
   # Verify services are healthy
   docker compose ps
   ```

### Rollback Verification
1. **Test Authentication**
   ```bash
   # Test with old tokens (should work)
   curl -H "Authorization: Bearer $OLD_TOKEN" http://localhost:8080/v1/auth/verify
   
   # Test with new tokens (should fail)
   curl -H "Authorization: Bearer $NEW_TOKEN" http://localhost:8080/v1/auth/verify
   ```

2. **Monitor Service Health**
   ```bash
   # Check all services are healthy
   docker compose ps | grep -v "healthy"
   
   # Monitor error rates
   docker compose logs | grep -i "jwt\|auth\|token"
   ```

## Monitoring and Alerting

### Rotation Monitoring
- **Secret Age**: Alert when secret is older than 85 days
- **Rotation Success**: Verify all services accept new secret
- **Token Validation**: Monitor JWT validation success rates
- **Service Health**: Check all services are healthy after rotation

### Alert Conditions
```yaml
# Prometheus alert rules
groups:
  - name: jwt-rotation
    rules:
      - alert: JWTSecretExpiring
        expr: time() - jwt_secret_created_timestamp > 7776000  # 90 days
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: JWT secret expiring soon
          description: JWT secret is older than 90 days and should be rotated
      
      - alert: JWTValidationFailure
        expr: rate(jwt_validation_failures_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High JWT validation failure rate
          description: JWT validation failure rate is above 10%
      
      - alert: JWTSecretRotationFailed
        expr: jwt_rotation_status != 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: JWT secret rotation failed
          description: JWT secret rotation did not complete successfully
```

## Security Considerations

### Secret Protection
- **File Permissions**: 600 (owner read/write only)
- **Backup Encryption**: GPG encryption for secret backups
- **Access Control**: Limited to security team and automation
- **Audit Logging**: All secret access logged

### Rotation Security
- **Dual Secret Period**: Maximum 24 hours
- **Old Secret Invalidation**: Immediate after rotation
- **Token Revocation**: All existing tokens invalidated
- **Re-authentication**: Users must re-authenticate

### Compliance
- **PCI DSS**: JWT secret rotation every 90 days
- **SOC 2**: Automated rotation with audit trail
- **GDPR**: Secure secret storage and rotation
- **ISO 27001**: Documented rotation procedures

## Automation

### Automated Rotation Script
```bash
#!/bin/bash
# scripts/rotate-jwt-secret.sh

set -euo pipefail

# Configuration
BACKUP_DIR="/secure/backups"
LOG_FILE="/var/log/jwt-rotation.log"
SERVICES=("auth-service" "profile-service" "discovery-service" "chat-service" "media-service" "admin-service" "notification-service" "data-service" "api-gateway" "telegram-bot")

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Generate new secret
generate_new_secret() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

# Backup current secret
backup_current_secret() {
    local backup_file="$BACKUP_DIR/jwt-secret-backup-$(date +%Y%m%d-%H%M%S).txt"
    cp /secure/jwt-secret.txt "$backup_file"
    chmod 600 "$backup_file"
    log "Backup created: $backup_file"
}

# Update service environment
update_service_env() {
    local service="$1"
    local new_secret="$2"
    
    echo "JWT_SECRET=$new_secret" > "/app/$service/.env"
    log "Updated $service environment"
}

# Restart service
restart_service() {
    local service="$1"
    
    docker compose restart "$service"
    sleep 5
    
    # Verify service is healthy
    if docker compose ps "$service" | grep -q "healthy"; then
        log "$service restarted successfully"
    else
        log "ERROR: $service failed to restart"
        exit 1
    fi
}

# Main rotation process
main() {
    log "Starting JWT secret rotation"
    
    # Generate new secret
    NEW_SECRET=$(generate_new_secret)
    log "Generated new JWT secret"
    
    # Backup current secret
    backup_current_secret
    
    # Update all services
    for service in "${SERVICES[@]}"; do
        update_service_env "$service" "$NEW_SECRET"
        restart_service "$service"
    done
    
    # Update main secret file
    echo "$NEW_SECRET" > /secure/jwt-secret.txt
    chmod 600 /secure/jwt-secret.txt
    
    log "JWT secret rotation completed successfully"
}

# Run main function
main "$@"
```

### Cron Job Configuration
```bash
# Add to crontab for automated rotation
# Rotate JWT secret every 90 days at 2:00 AM UTC
0 2 */90 * * /scripts/rotate-jwt-secret.sh >> /var/log/jwt-rotation.log 2>&1
```

## Testing

### Rotation Testing
1. **Test Secret Generation**
   ```bash
   # Test secret generation
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Test Service Updates**
   ```bash
   # Test updating service environments
   for service in auth-service profile-service; do
     echo "JWT_SECRET=test-secret" > /app/$service/.env
   done
   ```

3. **Test Service Restart**
   ```bash
   # Test service restart
   docker compose restart auth-service
   docker compose ps auth-service
   ```

### Validation Testing
1. **Test Token Validation**
   ```bash
   # Test with valid token
   curl -H "Authorization: Bearer $VALID_TOKEN" http://localhost:8080/v1/auth/verify
   
   # Test with invalid token
   curl -H "Authorization: Bearer $INVALID_TOKEN" http://localhost:8080/v1/auth/verify
   ```

2. **Test Service Health**
   ```bash
   # Test all services are healthy
   docker compose ps | grep -v "healthy"
   ```

## Troubleshooting

### Common Issues
1. **Service Won't Start**
   - Check JWT_SECRET format
   - Verify environment file permissions
   - Check service logs for errors

2. **Token Validation Fails**
   - Verify JWT_SECRET is consistent across services
   - Check token format and expiration
   - Verify service is using correct secret

3. **Rotation Fails**
   - Check backup creation
   - Verify service restart success
   - Monitor error logs

### Recovery Procedures
1. **Service Recovery**
   ```bash
   # Restart failed service
   docker compose restart <service-name>
   
   # Check service logs
   docker compose logs <service-name>
   ```

2. **Secret Recovery**
   ```bash
   # Restore from backup
   cp /secure/backups/jwt-secret-backup-*.txt /secure/jwt-secret.txt
   
   # Update all services
   for service in "${SERVICES[@]}"; do
     echo "JWT_SECRET=$(cat /secure/jwt-secret.txt)" > "/app/$service/.env"
     docker compose restart "$service"
   done
   ```

## Conclusion

JWT secret rotation is a critical security practice that must be performed regularly and safely. This guide provides comprehensive procedures for both planned and emergency rotation, ensuring the security of the Dating Platform while maintaining service availability.

Key points:
- **Regular Rotation**: Every 90 days
- **Emergency Response**: Within 24 hours
- **Automated Process**: Scripted rotation with monitoring
- **Rollback Capability**: Quick recovery from issues
- **Security Focus**: Protected secrets and audit trails
