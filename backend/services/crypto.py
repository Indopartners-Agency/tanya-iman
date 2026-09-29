"""Crypto utilities for phone number encryption, HMAC lookup, and masking.

PIP Task 3.1 & PRD §7.4:
- Phone numbers are stored AES-GCM encrypted, never plaintext.
- Indexed via HMAC-SHA256 (phone_hash) for O(1) lookup without decryption.
- Masked in logs and admin exports.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config import get_settings


def _derive_key(secret: str) -> bytes:
    """Derive a 32-byte AES-256 key from config string or fallback."""
    if not secret:
        secret = "dev-insecure-phone-encryption-key-32b"
    # If 64-character hex string:
    if len(secret) == 64:
        try:
            return bytes.fromhex(secret)
        except ValueError:
            pass
    # Otherwise use SHA-256 digest of secret to guarantee 32 bytes
    return hashlib.sha256(secret.encode("utf-8")).digest()


def normalize_phone_e164(phone: str) -> str:
    """Normalize Indonesian phone input to E.164 (+628...)."""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("62"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = digits[1:]
    if not digits.startswith("8"):
        raise ValueError("Indonesian mobile numbers must start with 8 (or 08 / +628)")
    if not (9 <= len(digits) <= 13):
        raise ValueError("Invalid Indonesian mobile phone number length")
    return f"+62{digits}"


def encrypt_phone(phone_e164: str) -> str:
    """Encrypt phone number with AES-GCM; returns base64(nonce + ciphertext)."""
    settings = get_settings()
    key = _derive_key(settings.phone_encryption_key)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, phone_e164.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decrypt_phone(encrypted_b64: str) -> str:
    """Decrypt base64(nonce + ciphertext) to plaintext phone number."""
    settings = get_settings()
    key = _derive_key(settings.phone_encryption_key)
    aesgcm = AESGCM(key)
    raw = base64.b64decode(encrypted_b64)
    if len(raw) < 12:
        raise ValueError("Invalid encrypted data format")
    nonce = raw[:12]
    ciphertext = raw[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def hash_phone(phone_e164: str) -> str:
    """Deterministic HMAC-SHA256 hex string for lookup without decryption."""
    settings = get_settings()
    key = _derive_key(settings.phone_encryption_key)
    return hmac.new(key, phone_e164.encode("utf-8"), hashlib.sha256).hexdigest()


def mask_phone(phone_e164: str) -> str:
    """Mask phone number: e.g. +6281234567890 -> +62 812-****-**90."""
    if not phone_e164.startswith("+62") or len(phone_e164) < 7:
        return "+62 ****"
    # Show first 6 chars (+62812) and last 2 chars
    prefix = phone_e164[:6]
    suffix = phone_e164[-2:]
    return f"{prefix}****{suffix}"
