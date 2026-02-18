import pytest
import factory
from faker import Faker
from apps.wallets.models import Wallet
from tests.fixtures.users import UserFactory

fake = Faker()


# =========================
# Factory
# =========================

class WalletFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Wallet

    user = factory.SubFactory(UserFactory)
    balance = 0
    address = factory.LazyAttribute(lambda _: fake.uuid4())


# =========================
# Pytest Fixtures
# =========================

@pytest.fixture
def wallet(db):
    return WalletFactory()


@pytest.fixture
def funded_wallet(db):
    return WalletFactory(balance=1000)


@pytest.fixture
def empty_wallet(db):
    return WalletFactory(balance=0)