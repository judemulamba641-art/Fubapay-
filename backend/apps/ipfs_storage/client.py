# backend/apps/ipfs_storage/client.py

import json
import ipfshttpclient
from django.conf import settings


class IPFSClient:
    """
    FubaPay IPFS Client
    Handles connection, upload, retrieval and pinning
    """

    def __init__(self):
        """
        Connect to IPFS daemon
        Default: local node (Docker or localhost)
        """
        self.address = getattr(
            settings,
            "IPFS_NODE_ADDRESS",
            "/ip4/127.0.0.1/tcp/5001"
        )

        try:
            self.client = ipfshttpclient.connect(self.address)
        except Exception as e:
            raise ConnectionError(f"IPFS connection failed: {e}")

    # --------------------------
    # Upload JSON Data
    # --------------------------
    def add_json(self, data: dict) -> str:
        """
        Upload JSON object to IPFS
        Returns CID
        """
        try:
            cid = self.client.add_json(data)
            return cid
        except Exception as e:
            raise Exception(f"IPFS JSON upload failed: {e}")

    # --------------------------
    # Upload File
    # --------------------------
    def add_file(self, file_path: str) -> str:
        """
        Upload file to IPFS
        Returns CID
        """
        try:
            result = self.client.add(file_path)
            return result["Hash"]
        except Exception as e:
            raise Exception(f"IPFS file upload failed: {e}")

    # --------------------------
    # Get JSON Data
    # --------------------------
    def get_json(self, cid: str) -> dict:
        """
        Retrieve JSON object from IPFS
        """
        try:
            data = self.client.get_json(cid)
            return data
        except Exception as e:
            raise Exception(f"IPFS JSON retrieval failed: {e}")

    # --------------------------
    # Get Raw File
    # --------------------------
    def get_file(self, cid: str, output_path: str):
        """
        Download file from IPFS
        """
        try:
            self.client.get(cid, target=output_path)
            return True
        except Exception as e:
            raise Exception(f"IPFS file retrieval failed: {e}")

    # --------------------------
    # Pin Content
    # --------------------------
    def pin(self, cid: str) -> bool:
        """
        Pin content to ensure persistence
        """
        try:
            self.client.pin.add(cid)
            return True
        except Exception as e:
            raise Exception(f"IPFS pin failed: {e}")

    # --------------------------
    # Remove Pin
    # --------------------------
    def unpin(self, cid: str) -> bool:
        """
        Unpin content
        """
        try:
            self.client.pin.rm(cid)
            return True
        except Exception as e:
            raise Exception(f"IPFS unpin failed: {e}")

    # --------------------------
    # Node Status
    # --------------------------
    def node_info(self) -> dict:
        """
        Check node status
        """
        try:
            return self.client.id()
        except Exception as e:
            raise Exception(f"IPFS node status failed: {e}")