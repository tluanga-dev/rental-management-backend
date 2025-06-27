"""
Authentication URLs for JWT token management.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .auth_views import (
    CustomTokenObtainPairView,
    register_user,
    user_profile,
    test_token_endpoint,
)

urlpatterns = [
    # JWT Authentication endpoints
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User management endpoints
    path('register/', register_user, name='user_register'),
    path('profile/', user_profile, name='user_profile'),
    
    # Test endpoint
    path('test/', test_token_endpoint, name='auth_test'),
]
