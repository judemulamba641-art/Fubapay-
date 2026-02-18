# backend/apps/ipfs_storage/encrypt.py

import os
import json
import base64
from django.conf import settings
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import constant_time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hmac
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from os import urandom


class IPFSEncryptor:
    """
    AES-256 Encryption for FubaPay IPFS storage
    """

    def __init__(self):
        raw_key = getattr(settings, "IPFS_ENCRYPTION_KEY", None)

        if not raw_key:
            raise ValueError("IPFS_ENCRYPTION_KEY not set in settings")

        # Ensure 32 bytes key
        self.key = raw_key.encode()[:32].ljust(32, b'\0')

    # -------------------------
    # Encrypt Data
    # -------------------------
    def encrypt(self, data: dict) -> dict:
        """
        Encrypt dictionary before IPFS upload
        Returns base64 encoded payload
        """
        json_data = json.dumps(data).encode()

        iv = urandom(16)

        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )

        encryptor = cipher.encryptor()

        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(json_data) + padder.finalize()

        encrypted = encryptor.update(padded_data) + encryptor.finalize()

        return {
            "iv": base64.b64encode(iv).decode(),
            "payload": base64.b64encode(encrypted).decode()
        }

    # -------------------------
    # Decrypt Data
    # -------------------------
    def decrypt(self, encrypted_data: dict) -> dict:
        """
        Decrypt IPFS data
        """
        iv = base64.b64decode(encrypted_data["iv"])
        encrypted_payload = base64.b64decode(encrypted_data["payload"])

        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )

        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(encrypted_payload) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()

        return json.loads(decrypted.decode())