from __future__ import annotations

"""Audit logging middleware for critical operations tracking."""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from aiohttp import web

logger = logging.getLogger(__name__)

# Critical operations that require audit logging
CRITICAL_OPERATIONS = {
    # Authentication operations
    'user_login': {'level': 'INFO', 'category': 'authentication'},
    'user_logout': {'level': 'INFO', 'category': 'authentication'},
    'token_refresh': {'level': 'INFO', 'category': 'authentication'},
    'password_change': {'level': 'WARNING', 'category': 'authentication'},
    
    # Profile operations
    'profile_create': {'level': 'INFO', 'category': 'profile'},
    'profile_update': {'level': 'INFO', 'category': 'profile'},
    'profile_delete': {'level': 'WARNING', 'category': 'profile'},
    
    # Media operations
    'file_upload': {'level': 'INFO', 'category': 'media'},
    'file_delete': {'level': 'WARNING', 'category': 'media'},
    'nsfw_detection': {'level': 'WARNING', 'category': 'media'},
    
    # Discovery operations
    'profile_like': {'level': 'INFO', 'category': 'discovery'},
    'profile_dislike': {'level': 'INFO', 'category': 'discovery'},
    'match_created': {'level': 'INFO', 'category': 'discovery'},
    
    # Chat operations
    'message_sent': {'level': 'INFO', 'category': 'chat'},
    'conversation_started': {'level': 'INFO', 'category': 'chat'},
    
    # Admin operations
    'admin_login': {'level': 'WARNING', 'category': 'admin'},
    'admin_user_ban': {'level': 'CRITICAL', 'category': 'admin'},
    'admin_user_unban': {'level': 'WARNING', 'category': 'admin'},
    'admin_data_export': {'level': 'WARNING', 'category': 'admin'},
    
    # Security operations
    'rate_limit_exceeded': {'level': 'WARNING', 'category': 'security'},
    'suspicious_activity': {'level': 'WARNING', 'category': 'security'},
    'unauthorized_access': {'level': 'WARNING', 'category': 'security'},
}


def audit_log(
    operation: str,
    user_id: Optional[str] = None,
    service: str = "unknown",
    details: Optional[Dict[str, Any]] = None,
    request: Optional[web.Request] = None,
    **kwargs
) -> None:
    """
    Log critical operations for audit trail.
    
    Args:
        operation: The operation being performed
        user_id: ID of the user performing the operation
        service: Name of the service
        details: Additional operation details
        request: HTTP request object (for extracting metadata)
        **kwargs: Additional fields to include in audit log
    """
    # Check if this is a critical operation
    if operation not in CRITICAL_OPERATIONS:
        return
    
    operation_config = CRITICAL_OPERATIONS[operation]
    log_level = getattr(logging, operation_config['level'])
    category = operation_config['category']
    
    # Build audit log entry
    audit_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "audit_log",
        "operation": operation,
        "category": category,
        "service": service,
        "user_id": user_id,
        "severity": operation_config['level'],
    }
    
    # Add request metadata if available
    if request:
        audit_entry.update({
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote,
            "user_agent": request.headers.get('User-Agent', ''),
            "correlation_id": request.headers.get('X-Correlation-ID', ''),
        })
    
    # Add operation details
    if details:
        audit_entry["details"] = details
    
    # Add any additional fields
    audit_entry.update(kwargs)
    
    # Log the audit entry
    logger.log(
        log_level,
        f"AUDIT: {operation} by user {user_id}",
        extra=audit_entry
    )


@web.middleware
async def audit_logging_middleware(request: web.Request, handler) -> web.Response:
    """
    Middleware to automatically log critical operations.
    
    This middleware checks the response and logs audit events for
    critical operations based on the endpoint and response status.
    """
    # Extract user context
    user_id = request.get('user_id')
    service_name = request.app.get('service_name', 'unknown')
    
    # Determine operation based on path and method
    operation = _determine_operation(request)
    
    # Process the request
    response = await handler(request)
    
    # Log audit event if this is a critical operation
    if operation and response.status < 400:  # Only log successful operations
        audit_log(
            operation=operation,
            user_id=str(user_id) if user_id else None,
            service=service_name,
            request=request,
            status_code=response.status,
            response_size=response.content_length,
        )
    
    return response


def _determine_operation(request: web.Request) -> Optional[str]:
    """Determine the operation type based on request path and method."""
    path = request.path
    method = request.method
    
    # Authentication operations
    if path.startswith('/auth/validate') and method == 'POST':
        return 'user_login'
    elif path.startswith('/auth/refresh') and method == 'POST':
        return 'token_refresh'
    
    # Profile operations
    elif path.startswith('/profiles') and method == 'POST':
        return 'profile_create'
    elif path.startswith('/profiles') and method == 'PUT':
        return 'profile_update'
    elif path.startswith('/profiles') and method == 'DELETE':
        return 'profile_delete'
    
    # Media operations
    elif path.startswith('/media/upload') and method == 'POST':
        return 'file_upload'
    elif path.startswith('/media/') and method == 'DELETE':
        return 'file_delete'
    
    # Discovery operations
    elif path.startswith('/discovery/like') and method == 'POST':
        return 'profile_like'
    elif path.startswith('/discovery/dislike') and method == 'POST':
        return 'profile_dislike'
    
    # Chat operations
    elif path.startswith('/chat/messages') and method == 'POST':
        return 'message_sent'
    
    # Admin operations
    elif path.startswith('/admin/login') and method == 'POST':
        return 'admin_login'
    elif path.startswith('/admin/users/') and 'ban' in path and method == 'POST':
        return 'admin_user_ban'
    elif path.startswith('/admin/users/') and 'unban' in path and method == 'POST':
        return 'admin_user_unban'
    
    return None


def log_security_event(
    event_type: str,
    user_id: Optional[str] = None,
    service: str = "unknown",
    severity: str = "WARNING",
    details: Optional[Dict[str, Any]] = None,
    request: Optional[web.Request] = None,
    **kwargs
) -> None:
    """
    Log security-related events for audit trail.
    
    Args:
        event_type: Type of security event
        user_id: ID of the user involved
        service: Name of the service
        severity: Severity level (INFO, WARNING, ERROR, CRITICAL)
        details: Additional event details
        request: HTTP request object
        **kwargs: Additional fields
    """
    audit_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "security_audit",
        "security_event": event_type,
        "service": service,
        "user_id": user_id,
        "severity": severity,
    }
    
    if request:
        audit_entry.update({
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote,
            "user_agent": request.headers.get('User-Agent', ''),
        })
    
    if details:
        audit_entry["details"] = details
    
    audit_entry.update(kwargs)
    
    log_level = getattr(logging, severity, logging.WARNING)
    logger.log(
        log_level,
        f"SECURITY AUDIT: {event_type}",
        extra=audit_entry
    )


def log_data_access(
    operation: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    service: str = "unknown",
    details: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Log data access operations for audit trail.
    
    Args:
        operation: Type of data operation (read, write, delete)
        resource_type: Type of resource being accessed
        resource_id: ID of the specific resource
        user_id: ID of the user performing the operation
        service: Name of the service
        details: Additional operation details
        **kwargs: Additional fields
    """
    audit_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "data_access_audit",
        "operation": operation,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "service": service,
        "user_id": user_id,
    }
    
    if details:
        audit_entry["details"] = details
    
    audit_entry.update(kwargs)
    
    # Determine log level based on operation
    if operation in ['delete', 'update']:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    
    logger.log(
        log_level,
        f"DATA ACCESS: {operation} {resource_type} {resource_id}",
        extra=audit_entry
    )
