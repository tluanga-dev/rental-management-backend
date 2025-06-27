"""
Custom permission classes for conditional authentication.
"""
from rest_framework.permissions import BasePermission, IsAuthenticated, AllowAny
from django.conf import settings


class ConditionalAuthentication(BasePermission):
    """
    Permission class that checks authentication based on ENABLE_AUTHENTICATION setting.
    
    - If ENABLE_AUTHENTICATION is True: Requires authentication
    - If ENABLE_AUTHENTICATION is False: Allows any access
    """
    
    def has_permission(self, request, view):
        """Check permission based on authentication setting."""
        enable_auth = getattr(settings, 'ENABLE_AUTHENTICATION', True)
        
        if enable_auth:
            # Authentication required
            return IsAuthenticated().has_permission(request, view)
        else:
            # No authentication required
            return AllowAny().has_permission(request, view)
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permission based on authentication setting."""
        enable_auth = getattr(settings, 'ENABLE_AUTHENTICATION', True)
        
        if enable_auth:
            # Authentication required
            return IsAuthenticated().has_permission(request, view)
        else:
            # No authentication required  
            return True


class DevelopmentOnlyPermission(BasePermission):
    """
    Permission that only allows access when ENABLE_AUTHENTICATION is False.
    Useful for development-only endpoints.
    """
    
    def has_permission(self, request, view):
        """Only allow access when authentication is disabled (development mode)."""
        enable_auth = getattr(settings, 'ENABLE_AUTHENTICATION', True)
        return not enable_auth


def get_permission_classes_for_action(action, default_authenticated=True):
    """
    Utility function to get appropriate permission classes based on action and auth setting.
    
    Args:
        action: The view action (list, create, retrieve, update, destroy)
        default_authenticated: Whether to require authentication by default when enabled
    
    Returns:
        List of permission classes
    """
    enable_auth = getattr(settings, 'ENABLE_AUTHENTICATION', True)
    
    if not enable_auth:
        # Development mode - no authentication required
        return [AllowAny]
    
    # Production mode - use default authentication
    if default_authenticated:
        return [IsAuthenticated]
    else:
        return [AllowAny]
