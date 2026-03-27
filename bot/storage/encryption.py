# Rica - API Key Encryption
# Uses Fernet symmetric encryption. Master key stored locally at ~/.rica/secret.key

import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet


RICA_HOME = Path(os.environ.get("RICA_HOME", Path.home() / ".rica"))
KEY_PATH = RICA_HOME / "secret.key"


class Encryption:
    """Encrypt/decrypt API keys using Fernet with a locally stored master key."""

    def __init__(self):
        self._fernet = None
        self._key = None

    def _get_key(self) -> bytes:
        """Load or generate master encryption key from local file."""
        if self._key:
            return self._key

        # Try loading from local file first
        if KEY_PATH.exists():
            self._key = KEY_PATH.read_bytes().strip()
            return self._key

        # Try env var (for backward compatibility / testing)
        fallback = os.getenv("ENCRYPTION_KEY")
        if fallback:
            self._key = fallback.encode()
            return self._key

        # Generate a new key and save it
        new_key = Fernet.generate_key()
        RICA_HOME.mkdir(parents=True, exist_ok=True)
        KEY_PATH.write_bytes(new_key)
        # Restrict file permissions (best-effort on Windows)
        try:
            os.chmod(KEY_PATH, 0o600)
        except (OSError, AttributeError):
            pass  # Windows may not support Unix permissions
        self._key = new_key
        print(f"[Encryption] Generated new master key at {KEY_PATH}")
        return self._key

    def _get_fernet(self) -> Fernet:
        """Get or create Fernet instance."""
        if self._fernet is None:
            key = self._get_key()
            # Ensure key is valid Fernet key (32 url-safe base64 bytes)
            if len(key) == 32:
                key = base64.urlsafe_b64encode(key)
            self._fernet = Fernet(key)
        return self._fernet

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string (e.g., API key). Returns base64-encoded ciphertext."""
        if not plaintext:
            return ""
        f = self._get_fernet()
        encrypted = f.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a base64-encoded ciphertext back to plaintext."""
        if not ciphertext:
            return ""
        f = self._get_fernet()
        decrypted = f.decrypt(ciphertext.encode())
        return decrypted.decode()

    def has_key(self) -> bool:
        """Check if a master key exists."""
        return KEY_PATH.exists() or bool(os.getenv("ENCRYPTION_KEY"))


# Global instance
encryption = Encryption()
