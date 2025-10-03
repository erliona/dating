"""Shared test utilities."""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode


def create_valid_init_data(bot_token: str, user_id: int, auth_date: int = None) -> str:
    """Helper to create valid initData with correct HMAC signature."""
    if auth_date is None:
        auth_date = int(time.time())
    
    user_data = {
        "id": user_id,
        "first_name": "Test",
        "username": "testuser"
    }
    
    data = {
        "user": json.dumps(user_data),
        "auth_date": str(auth_date),
        "hash": ""  # Will be calculated
    }
    
    # Calculate HMAC
    data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items()) if k != 'hash'])
    
    secret_key = hmac.new(
        key="WebAppData".encode(),
        msg=bot_token.encode(),
        digestmod=hashlib.sha256
    ).digest()
    
    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    data['hash'] = calculated_hash
    
    return urlencode(data)
