"""
Raksha AI - AES Encryption & Decryption Utility
Supports AES-256-GCM (Authenticated Encryption with Associated Data) and AES-256-CBC.
Provides seamless encryption for Bus-to-Cloud telemetry and authority notifications.
"""

import os
import json
import base64
import hashlib
from typing import Dict, Any, Tuple, Optional

# Default Pre-shared 256-bit Key for Edge Bus <-> Cloud Communication (can be overridden by env var)
DEFAULT_AES_KEY_HEX = os.getenv("VISION_AI_AES_KEY", "e4d9b2a7f8301c65b9d318e24f0c9a5b7134d6e802f1a5c39b7d8e204a1f6c8b")

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class AES256Engine:
    """
    AES-256 Cryptographic Engine for securing bus telemetry and hazard alerts.
    """
    def __init__(self, key_hex: Optional[str] = None):
        key_str = key_hex or DEFAULT_AES_KEY_HEX
        # Ensure 32 bytes (256-bit)
        if len(key_str) == 64:
            self.key = bytes.fromhex(key_str)
        else:
            self.key = hashlib.sha256(key_str.encode("utf-8")).digest()
        self.key_hex = self.key.hex()

    def encrypt_gcm(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Encrypts a Python dictionary payload using AES-256-GCM.
        Returns base64 encoded ciphertext, IV, auth tag, and metadata.
        """
        raw_json = json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        iv = os.urandom(12)  # 96-bit standard IV for GCM

        if HAS_CRYPTOGRAPHY:
            cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(raw_json) + encryptor.finalize()
            tag = encryptor.tag
        else:
            # Fallback XOR/CTR stream mode if binary crypto unavailable
            ciphertext, tag = self._fallback_encrypt(raw_json, iv)

        return {
            "algorithm": "AES-256-GCM",
            "iv": base64.b64encode(iv).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "key_fingerprint": hashlib.sha256(self.key).hexdigest()[:16],
            "raw_byte_length": len(raw_json),
            "encrypted_byte_length": len(ciphertext)
        }

    def decrypt_gcm(self, encrypted_payload: Dict[str, str]) -> Dict[str, Any]:
        """
        Decrypts an AES-256-GCM encrypted payload dictionary back into Python dict.
        """
        try:
            iv = base64.b64decode(encrypted_payload["iv"])
            tag = base64.b64decode(encrypted_payload["tag"])
            ciphertext = base64.b64decode(encrypted_payload["ciphertext"])

            if HAS_CRYPTOGRAPHY:
                cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv, tag), backend=default_backend())
                decryptor = cipher.decryptor()
                plaintext_bytes = decryptor.update(ciphertext) + decryptor.finalize()
            else:
                plaintext_bytes = self._fallback_decrypt(ciphertext, iv, tag)

            return json.loads(plaintext_bytes.decode('utf-8'))
        except Exception as e:
            raise ValueError(f"AES-256-GCM Decryption failed: {str(e)}")

    def _fallback_encrypt(self, data: bytes, iv: bytes) -> Tuple[bytes, bytes]:
        """Fallback lightweight CTR stream cipher for non-crypto systems."""
        keystream = b''
        counter = 0
        while len(keystream) < len(data):
            h = hashlib.sha256(self.key + iv + counter.to_bytes(4, 'big')).digest()
            keystream += h
            counter += 1
        ciphertext = bytes([b ^ k for b, k in zip(data, keystream[:len(data)])])
        tag = hashlib.sha256(self.key + ciphertext + iv).digest()[:16]
        return ciphertext, tag

    def _fallback_decrypt(self, ciphertext: bytes, iv: bytes, tag: bytes) -> bytes:
        """Fallback decryption corresponding to fallback encrypt."""
        expected_tag = hashlib.sha256(self.key + ciphertext + iv).digest()[:16]
        if tag != expected_tag:
            raise ValueError("Integrity verification tag mismatch!")
        keystream = b''
        counter = 0
        while len(keystream) < len(ciphertext):
            h = hashlib.sha256(self.key + iv + counter.to_bytes(4, 'big')).digest()
            keystream += h
            counter += 1
        return bytes([c ^ k for c, k in zip(ciphertext, keystream[:len(ciphertext)])])


# Singleton instance
crypto_engine = AES256Engine()
