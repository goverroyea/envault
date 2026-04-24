"""Tests for envault.crypto encryption/decryption utilities."""

import pytest
from envault.crypto import encrypt, decrypt


PASSPHRASE = "super-secret-passphrase"
PLAINTEXT = "MY_SECRET=hunter2"


def test_encrypt_returns_string():
    token = encrypt(PLAINTEXT, PASSPHRASE)
    assert isinstance(token, str)
    assert len(token) > 0


def test_encrypt_produces_different_ciphertexts_each_call():
    """Random salt/nonce means two encryptions of the same value differ."""
    token1 = encrypt(PLAINTEXT, PASSPHRASE)
    token2 = encrypt(PLAINTEXT, PASSPHRASE)
    assert token1 != token2


def test_decrypt_round_trip():
    token = encrypt(PLAINTEXT, PASSPHRASE)
    result = decrypt(token, PASSPHRASE)
    assert result == PLAINTEXT


def test_decrypt_wrong_passphrase_raises():
    token = encrypt(PLAINTEXT, PASSPHRASE)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(token, "wrong-passphrase")


def test_decrypt_corrupted_payload_raises():
    token = encrypt(PLAINTEXT, PASSPHRASE)
    # Flip a character in the middle of the token to corrupt ciphertext.
    corrupted = token[:-4] + "AAAA"
    with pytest.raises(ValueError):
        decrypt(corrupted, PASSPHRASE)


def test_decrypt_invalid_base64_raises():
    with pytest.raises(ValueError, match="Invalid encoded payload"):
        decrypt("not-valid-base64!!!", PASSPHRASE)


def test_decrypt_too_short_payload_raises():
    import base64
    short = base64.b64encode(b"tooshort").decode()
    with pytest.raises(ValueError, match="too short"):
        decrypt(short, PASSPHRASE)


def test_encrypt_empty_string():
    token = encrypt("", PASSPHRASE)
    assert decrypt(token, PASSPHRASE) == ""


def test_encrypt_unicode_secret():
    secret = "UNICODE_VAR=caf\u00e9_中文_🔑"
    token = encrypt(secret, PASSPHRASE)
    assert decrypt(token, PASSPHRASE) == secret
