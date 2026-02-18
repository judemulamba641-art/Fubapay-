import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_full_payment_flow():
    client = APIClient()

    # 1️⃣ Register user
    response = client.post("/api/accounts/register/", {
        "email": "test@gmail.com"
    })
    assert response.status_code == 201

    # 2️⃣ Create wallet
    response = client.post("/api/wallets/create/")
    assert response.status_code == 201

    # 3️⃣ Make transaction
    response = client.post("/api/transactions/pay/", {
        "amount": 10,
        "currency": "USDC"
    })
    assert response.status_code == 200

    # 4️⃣ AI decision check
    assert response.data["status"] in ["approved", "limited"]

    # 5️⃣ IPFS log check
    assert "ipfs_hash" in response.data
