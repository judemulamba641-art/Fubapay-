import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from apps.ipfs_storage.uploader import upload_to_ipfs
from apps.ipfs_storage.encrypt import encrypt_data
from apps.transactions.models import Transaction
from apps.wallets.models import Wallet

User = get_user_model()


@pytest.mark.django_db
class TestIPFSStorage:

    def setup_method(self):
        self.test_payload = {
            "amount": 100,
            "currency": "USDC",
            "status": "approved"
        }

    # ✅ Test chiffrement avant upload
    def test_data_encryption(self):
        encrypted = encrypt_data(str(self.test_payload))

        assert encrypted != str(self.test_payload)
        assert isinstance(encrypted, bytes)

    # ✅ Upload IPFS mocké (succès)
    @patch("apps.ipfs_storage.client.ipfs_add")
    def test_successful_ipfs_upload(self, mock_ipfs_add):
        mock_ipfs_add.return_value = {
            "Hash": "QmTestCID123456789"
        }

        result = upload_to_ipfs(self.test_payload)

        assert result == "QmTestCID123456789"
        mock_ipfs_add.assert_called_once()

    # ❌ Erreur réseau IPFS
    @patch("apps.ipfs_storage.client.ipfs_add")
    def test_ipfs_network_failure(self, mock_ipfs_add):
        mock_ipfs_add.side_effect = Exception("IPFS node unreachable")

        with pytest.raises(Exception):
            upload_to_ipfs(self.test_payload)

    # 🔐 Intégrité du CID retourné
    @patch("apps.ipfs_storage.client.ipfs_add")
    def test_cid_format_validation(self, mock_ipfs_add):
        mock_ipfs_add.return_value = {
            "Hash": "QmValidCID987654321"
        }

        cid = upload_to_ipfs(self.test_payload)

        assert cid.startswith("Qm")
        assert len(cid) > 10

    # 🧾 Transaction liée à IPFS
    @patch("apps.ipfs_storage.client.ipfs_add")
    def test_transaction_logs_to_ipfs(self, mock_ipfs_add):
        mock_ipfs_add.return_value = {
            "Hash": "QmTransactionCID"
        }

        user = User.objects.create_user(
            email="ipfsuser@gmail.com",
            password="SecurePass123!"
        )

        wallet = Wallet.objects.create(user=user, balance=500)

        tx = Transaction.objects.create(
            user=user,
            amount=50,
            currency="USDC",
            status="approved"
        )

        cid = upload_to_ipfs({
            "transaction_id": tx.id,
            "amount": tx.amount
        })

        tx.ipfs_hash = cid
        tx.save()

        tx.refresh_from_db()

        assert tx.ipfs_hash == "QmTransactionCID"

    # 🔄 Upload multiple logs
    @patch("apps.ipfs_storage.client.ipfs_add")
    def test_multiple_ipfs_uploads(self, mock_ipfs_add):
        mock_ipfs_add.return_value = {
            "Hash": "QmMultiCID"
        }

        for i in range(5):
            cid = upload_to_ipfs({"log": i})
            assert cid == "QmMultiCID"

        assert mock_ipfs_add.call_count == 5