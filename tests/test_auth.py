"""Tests for password hashing and the legacy-format migration path.

Requires a real, reachable SQL Server database configured the same way the
app itself is (see .env.example / config.py) — these are integration
tests, not pure unit tests, because the auth functions in models.py talk
to the database directly rather than through an injectable interface.
"""
import hashlib
import secrets
import uuid

import pytest

from models import (
    get_db_connection,
    register_user,
    authenticate_user,
    _hash_password,
    _verify_password,
    _is_legacy_hash,
    delete_account,
)


def _legacy_hash(password):
    """Build a password hash in the pre-migration salted-SHA-256 format,
    the same way the old _hash_password() used to."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hashed}"


@pytest.fixture
def test_user():
    """Registers a throwaway user via the real register flow and cleans it
    up afterward, regardless of what the test did to it."""
    email = f'pytest.{uuid.uuid4().hex[:10]}@example.com'
    password = 'PytestPass123'
    ok, msg = register_user('Pytest User', email, password)
    assert ok, msg
    yield email, password
    user = authenticate_user(email, password)
    if user:
        delete_account(user['id'])
    else:
        # Password may have been changed by the test (e.g. legacy-hash
        # overwrite tests) — clean up by email directly.
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM resumes WHERE user_id = (SELECT id FROM users WHERE email = ?)", (email,))
        cursor.execute("DELETE FROM users WHERE email = ?", (email,))
        conn.commit()
        cursor.close()
        conn.close()


class TestPasswordHashFormat:
    def test_new_hashes_are_werkzeug_format_not_legacy(self):
        h = _hash_password('SomePassword123')
        assert not _is_legacy_hash(h)
        assert ':' in h

    def test_legacy_format_is_detected(self):
        h = _legacy_hash('SomePassword123')
        assert _is_legacy_hash(h)

    def test_new_hash_round_trips(self):
        h = _hash_password('SomePassword123')
        assert _verify_password('SomePassword123', h) is True
        assert _verify_password('WrongPassword', h) is False

    def test_legacy_hash_round_trips(self):
        h = _legacy_hash('SomePassword123')
        assert _verify_password('SomePassword123', h) is True
        assert _verify_password('WrongPassword', h) is False


class TestRegisterAndLogin:
    def test_register_creates_a_werkzeug_hash(self, test_user):
        email, password = test_user
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
        stored = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        assert not _is_legacy_hash(stored)

    def test_login_with_correct_password_succeeds(self, test_user):
        email, password = test_user
        user = authenticate_user(email, password)
        assert user is not None
        assert user['email'] == email

    def test_login_with_wrong_password_fails(self, test_user):
        email, _ = test_user
        assert authenticate_user(email, 'DefinitelyWrongPassword') is None

    def test_duplicate_email_registration_is_rejected(self, test_user):
        email, password = test_user
        ok, msg = register_user('Someone Else', email, 'AnotherPassword123')
        assert ok is False
        assert 'already exists' in msg


class TestLegacyHashMigration:
    def test_login_with_legacy_hash_upgrades_it_transparently(self, test_user):
        email, password = test_user

        # Downgrade the stored hash to the pre-migration format, simulating
        # an account that hasn't logged in since the upgrade shipped.
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (_legacy_hash(password), email)
        )
        conn.commit()
        cursor.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
        before = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        assert _is_legacy_hash(before)

        # A single successful login should both succeed and rewrite the
        # hash to the new format — no forced password reset.
        user = authenticate_user(email, password)
        assert user is not None

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
        after = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        assert not _is_legacy_hash(after)

        # The new hash must still authenticate with the same password.
        assert authenticate_user(email, password) is not None
