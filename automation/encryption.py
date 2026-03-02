"""
encryption.py — Fernet symmetric encryption for sensitive fields (passwords).
Uses the ENCRYPTION_KEY environment variable.  To generate a key:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Add the output as ENCRYPTION_KEY to your .env and Hugging Face secrets.
"""

import os
from cryptography.fernet import Fernet, InvalidToken

_KEY = os.environ.get("ENCRYPTION_KEY", "").encode()


def _get_cipher() -> Fernet:
    if not _KEY:
        raise RuntimeError("ENCRYPTION_KEY environment variable is not set.")
    return Fernet(_KEY)


def encrypt_password(plain: str) -> str:
    """Return the Fernet-encrypted form of *plain* as a UTF-8 string."""
    if not plain:
        return plain
    return _get_cipher().encrypt(plain.encode()).decode()


def decrypt_password(token: str) -> str:
    """Return the original plaintext from an encrypted *token*."""
    if not token:
        return token
    try:
        return _get_cipher().decrypt(token.encode()).decode()
    except (InvalidToken, Exception):
        # If decryption fails (e.g. value was never encrypted), return as-is
        return token
