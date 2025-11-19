import hashlib
import os
from typing import Optional


class AccessControl:
    def __init__(self):
        self.password_hash = None

    def set_password(self, password: str) -> bytes:
        random = os.urandom(16)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            random,
            100000
        )
        self.password_hash = random + password_hash
        return self.password_hash

    def verify_password(self, password: str, stored_hash: bytes) -> bool:
        if not stored_hash or len(stored_hash) != 48:
            return False
        random = stored_hash[:16]
        stored_password_hash = stored_hash[16:]
        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            random,
            100000
        )
        return new_hash == stored_password_hash

    def is_protected(self, stored_hash: Optional[bytes]) -> bool:
        return stored_hash is not None and len(stored_hash) == 48