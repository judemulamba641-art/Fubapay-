from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


# =====================================================
# USER SERIALIZER (Safe public version)
# =====================================================

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "profile_picture",
            "role",
            "trust_score",
            "risk_flag",
            "daily_limit",
            "single_transaction_limit",
            "date_joined",
        ]
        read_only_fields = [
            "email",
            "role",
            "trust_score",
            "risk_flag",
            "daily_limit",
            "single_transaction_limit",
            "date_joined",
        ]


# =====================================================
# GOOGLE LOGIN SERIALIZER
# =====================================================

class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()

    def validate_id_token(self, value):
        if not value:
            raise serializers.ValidationError("Google ID token is required.")
        return value


# =====================================================
# USER UPDATE SERIALIZER
# =====================================================

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "full_name",
            "profile_picture",
        ]

    def update(self, instance, validated_data):
        instance.full_name = validated_data.get(
            "full_name",
            instance.full_name
        )
        instance.profile_picture = validated_data.get(
            "profile_picture",
            instance.profile_picture
        )
        instance.save()
        return instance


# =====================================================
# ADMIN USER SERIALIZER (Full Access)
# =====================================================

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


# =====================================================
# ROLE CHANGE SERIALIZER (Admin Only)
# =====================================================

class RoleUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.Role.choices)

    def validate_role(self, value):
        return value