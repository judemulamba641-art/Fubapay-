import pytest
import factory
from faker import Faker
from apps.transactions.models import Transaction
from tests.fixtures.users import UserFactory
from tests.fixtures.wallets import WalletFactory

fake = Faker()


# =========================
# Factory
# =========================

class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction

    user = factory.SubFactory(UserFactory)
    wallet = factory.SubFactory(WalletFactory)
    amount = factory.LazyAttribute(lambda _: fake.random_int(min=1, max=500))
    currency = "USDC"
    status = "approved"
    ipfs_hash = None


# =========================
# Pytest Fixtures
# =========================

@pytest.fixture
def transaction(db):
    return TransactionFactory()


@pytest.fixture
def approved_transaction(db):
    return TransactionFactory(status="approved")


@pytest.fixture
def blocked_transaction(db):
    return TransactionFactory(status="blocked")


@pytest.fixture
def high_value_transaction(db):
    return TransactionFactory(amount=10000)