"""Test Admin model timezone handling."""

from datetime import datetime, timezone

import pytest

from bot.db import Admin

pytestmark = pytest.mark.unit


class TestAdminModelTimezone:
    """Test Admin model timezone-aware datetime handling."""

    def test_admin_model_accepts_timezone_aware_datetime(self):
        """Test that Admin model can be instantiated with timezone-aware datetimes."""
        # Create timezone-aware datetime
        now_utc = datetime.now(timezone.utc)

        # This should not raise any errors
        admin = Admin(
            id=1,
            username="test_admin",
            password_hash="hash",
            full_name="Test Admin",
            is_active=True,
            is_super_admin=False,
            last_login=now_utc,
            created_at=now_utc,
            updated_at=now_utc,
        )

        # Verify the datetime values are set correctly
        assert admin.last_login == now_utc
        assert admin.created_at == now_utc
        assert admin.updated_at == now_utc
        assert admin.last_login.tzinfo is not None
        assert admin.created_at.tzinfo is not None
        assert admin.updated_at.tzinfo is not None

    def test_admin_model_last_login_can_be_none(self):
        """Test that last_login can be None."""
        now_utc = datetime.now(timezone.utc)

        admin = Admin(
            id=1,
            username="test_admin",
            password_hash="hash",
            is_active=True,
            is_super_admin=False,
            last_login=None,
            created_at=now_utc,
            updated_at=now_utc,
        )

        assert admin.last_login is None

    def test_admin_model_fields_are_defined(self):
        """Test that Admin model has the expected timezone-aware fields."""
        # Check that the model has the expected columns
        assert hasattr(Admin, "last_login")
        assert hasattr(Admin, "created_at")
        assert hasattr(Admin, "updated_at")

        # Verify the columns have timezone=True
        last_login_col = Admin.__table__.columns["last_login"]
        created_at_col = Admin.__table__.columns["created_at"]
        updated_at_col = Admin.__table__.columns["updated_at"]

        assert last_login_col.type.timezone is True
        assert created_at_col.type.timezone is True
        assert updated_at_col.type.timezone is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
