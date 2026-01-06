import base64
import hashlib

from django.conf import settings


def _derive_key() -> bytes:
    return hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()


def encrypt_api_key(raw_key: str) -> str:
    if not raw_key:
        return ""
    key = _derive_key()
    data = raw_key.encode("utf-8")
    encrypted = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(data))
    return base64.urlsafe_b64encode(encrypted).decode("utf-8")


def decrypt_api_key(encrypted_key: str) -> str:
    if not encrypted_key:
        return ""
    try:
        payload = base64.urlsafe_b64decode(encrypted_key.encode("utf-8"))
    except (ValueError, TypeError):
        return ""
    key = _derive_key()
    decrypted = bytes(byte ^ key[index % len(key)] for index, byte in enumerate(payload))
    return decrypted.decode("utf-8")
