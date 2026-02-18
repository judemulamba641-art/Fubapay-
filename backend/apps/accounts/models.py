from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.utils import timezone


# =====================================================
# USER MANAGER
# =====================================================

class UserManager(BaseUserManager):

    def create_user(self, email, google_id=None, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            google_id=google_id,
            **extra_fields
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password=password, **extra_fields)


# =====================================================
# USER MODEL
# =====================================================

class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        CLIENT = "client", "Client"
        AGENT = "agent", "Agent"
        MERCHANT = "merchant", "Merchant"
        ADMIN = "admin", "Admin"

    # Core Identity
    email = models.EmailField(unique=True)
    google_id = models.CharField(max_length=255, blank=True, null=True)

    full_name = models.CharField(max_length=255, blank=True)
    profile_picture = models.URLField(blank=True, null=True)

    # Role system
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT
    )

    # AI & Trust system
    trust_score = models.FloatField(default=0.5)  # 0.0 to 1.0
    risk_flag = models.BooleanField(default=False)

    # Limits (No KYC mode)
    daily_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=500.00
    )

    single_transaction_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=200.00
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    # =====================================================
    # BUSINESS LOGIC METHODS
    # =====================================================

    def increase_trust(self, value=0.05):
        self.trust_score = min(1.0, self.trust_score + value)
        self.save()

    def decrease_trust(self, value=0.1):
        self.trust_score = max(0.0, self.trust_score - value)
        if self.trust_score < 0.3:
            self.risk_flag = True
        self.save()

    def can_transact(self, amount):
        if self.risk_flag:
            return False
        if amount > self.single_transaction_limit:
            return False
        return True