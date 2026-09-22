"""測試 2：密碼比對。不開 HTTP。不連資料庫。"""

import bcrypt

from backend.auth import password_matches


def test_correct_password_matches():
    hashed = bcrypt.hashpw(b"secret", bcrypt.gensalt()).decode()
    assert password_matches("secret", hashed) is True


def test_wrong_password_does_not_match():
    hashed = bcrypt.hashpw(b"secret", bcrypt.gensalt()).decode()
    assert password_matches("nope", hashed) is False


def test_not_bcrypt_hash_is_false():
    assert password_matches("teacher123", "pbkdf2$not-bcrypt") is False
