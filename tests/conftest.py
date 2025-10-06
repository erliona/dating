"""Pytest configuration and fixtures for test suite."""

import os

import pytest


@pytest.fixture(scope="function", autouse=True)
def clear_module_caches():
    """Clear module-level caches before each test to prevent state pollution.
    
    This ensures that patching works correctly even when tests run in sequence.
    """
    # Clear bot.main API client cache
    try:
        from bot import main
        if hasattr(main, '_clear_api_client_cache'):
            main._clear_api_client_cache()
    except ImportError:
        pass  # Module not imported yet
    
    yield
    
    # Clear cache after test as well
    try:
        from bot import main
        if hasattr(main, '_clear_api_client_cache'):
            main._clear_api_client_cache()
    except ImportError:
        pass


@pytest.fixture(scope="function", autouse=True)
def ensure_test_environment():
    """Ensure required environment variables are set for all tests.
    
    This fixture automatically runs before each test to ensure the environment
    is properly configured. It prevents tests from hanging when load_config()
    is called without proper environment setup.
    """
    # Save original environment
    original_env = {}
    required_vars = {
        "BOT_TOKEN": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz-test-token",
        "API_GATEWAY_URL": "http://localhost:8080",
        "JWT_SECRET": "test-secret-key-for-testing-32chars",
    }
    
    for key, default_value in required_vars.items():
        original_env[key] = os.environ.get(key)
        # Set the default value if not already set
        if key not in os.environ:
            os.environ[key] = default_value
    
    yield
    
    # Restore original environment after test
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value
