import pytest
import factory
from faker import Faker
from django.contrib.auth import get_user_model

fake = Faker()
User = get_user_model()


# =========================
# Factory
# =========================

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.LazyAttribute(lambda _: fake.unique.email())
    password = factory.PostGenerationMethodCall("set_password", "StrongPass123!")
    role = "client"
    is_active = True


# =========================
# Pytest Fixtures
# =========================

@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def agent_user(db):
    return UserFactory(role="agent")


@pytest.fixture
def merchant_user(db):
    return UserFactory(role="merchant")


@pytest.fixture
def inactive_user(db):
    return UserFactory(is_active=False)