# backend/apps/ipfs_storage/uploader.py

import os
import json
import tempfile
from typing import Union

from .client import IPFSClient
from .encrypt import IPFSEncryptor


class IPFSUploader:
    """
    FubaPay Secure IPFS Uploader
    Encrypts data before uploading and ensures pinning.
    """

    def __init__(self):
        self.client = IPFSClient()
        self.encryptor = IPFSEncryptor()

    # ---------------------------------
    # Upload Dictionary (JSON)
    # ---------------------------------
    def upload_json(self, data: dict, encrypt: bool = True) -> dict:
        """
        Upload dictionary to IPFS (encrypted by default)
        Returns structured response
        """
        try:
            payload = data

            if encrypt:
                payload = self.encryptor.encrypt(data)

            cid = self.client.add_json(payload)
            self.client.pin(cid)

            return {
                "status": "success",
                "cid": cid,
                "encrypted": encrypt
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    # ---------------------------------
    # Upload Raw File
    # ---------------------------------
    def upload_file(self, file_path: str, encrypt: bool = True) -> dict:
        """
        Upload file to IPFS
        If encrypt=True, file is encrypted before upload
        """

        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": "File does not exist"
            }

        try:
            if encrypt:
                with open(file_path, "rb") as f:
                    raw_data = f.read()

                encrypted_payload = self.encryptor.encrypt({
                    "filename": os.path.basename(file_path),
                    "content": raw_data.decode(errors="ignore")
                })

                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp:
                    json.dump(encrypted_payload, tmp)
                    temp_path = tmp.name

                cid = self.client.add_file(temp_path)
                os.remove(temp_path)

            else:
                cid = self.client.add_file(file_path)

            self.client.pin(cid)

            return {
                "status": "success",
                "cid": cid,
                "encrypted": encrypt
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


# ---------------------------------
# Simple helper function (shortcut)
# ---------------------------------
def upload_to_ipfs(data: Union[dict, str], encrypt: bool = True):
    """
    Quick upload helper
    Accepts dict or file path
    """
    uploader = IPFSUploader()

    if isinstance(data, dict):
        return uploader.upload_json(data, encrypt=encrypt)

    elif isinstance(data, str):
        return uploader.upload_file(data, encrypt=encrypt)

    else:
        return {
            "status": "error",
            "message": "Unsupported data type"
        }