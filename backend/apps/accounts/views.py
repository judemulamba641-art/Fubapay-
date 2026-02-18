from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import get_user_model

from .serializers import (
    GoogleLoginSerializer,
    UserSerializer,
    UserUpdateSerializer,
    AdminUserSerializer,
    RoleUpdateSerializer,
)

from .services.gmail_auth import authenticate_with_google
from .permissions import IsAdminUserRole

User = get_user_model()


# =====================================================
# GOOGLE LOGIN VIEW
# =====================================================

class GoogleLoginView(APIView):
    """
    POST /api/accounts/google-login/
    Body:
    {
        "id_token": "google_id_token_here"
    }
    """

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        id_token = serializer.validated_data["id_token"]

        try:
            auth_data = authenticate_with_google(id_token)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(auth_data, status=status.HTTP_200_OK)


# =====================================================
# USER PROFILE VIEW
# =====================================================

class ProfileView(APIView):
    """
    GET /api/accounts/me/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# =====================================================
# UPDATE PROFILE VIEW
# =====================================================

class UpdateProfileView(APIView):
    """
    PUT /api/accounts/me/update/
    """

    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================================
# ADMIN - LIST USERS
# =====================================================

class AdminUserListView(APIView):
    """
    GET /api/accounts/admin/users/
    """

    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def get(self, request):
        users = User.objects.all().order_by("-date_joined")
        serializer = AdminUserSerializer(users, many=True)
        return Response(serializer.data)


# =====================================================
# ADMIN - UPDATE USER ROLE
# =====================================================

class AdminRoleUpdateView(APIView):
    """
    PUT /api/accounts/admin/users/<id>/role/
    """

    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def put(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = RoleUpdateSerializer(data=request.data)

        if serializer.is_valid():
            user.role = serializer.validated_data["role"]
            user.save()
            return Response(
                {"message": "Role updated successfully"}
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)