"""
Base ViewSet classes to eliminate code duplication across the application.
"""

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema
from apps.core.permissions import ConditionalAuthentication
from apps.base.paginated_base import StandardResultsSetPagination


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for standard CRUD operations with consistent configuration.
    
    Provides:
    - Standardized pagination (50 items per page)
    - Consistent authentication (ConditionalAuthentication)
    - Standard filter backends (DjangoFilter, Search, Ordering)
    - Base OpenAPI documentation structure
    
    Usage:
        class MyModelViewSet(BaseModelViewSet):
            queryset = MyModel.objects.all()
            serializer_class = MyModelSerializer
            filterset_fields = {'name': ['exact', 'icontains']}
            search_fields = ['name', 'description']
            ordering_fields = ['name', 'created_at']
    """
    
    # Standard configuration for all ViewSets
    permission_classes = [ConditionalAuthentication]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Default ordering by creation date (most recent first)
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """Standard create with user assignment if authenticated."""
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user)

    def perform_update(self, serializer):
        """Standard update with user assignment if authenticated."""
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(modified_by=user)


def create_standard_schema_view(resource_name: str, description: str = None, tags: list = None):
    """
    Factory function to create standardized OpenAPI schema decorators for ViewSets.
    
    Args:
        resource_name: Name of the resource (e.g., "customer", "inventory item master")
        description: Optional description for the resource
        tags: Optional list of tags for grouping in API docs
        
    Returns:
        @extend_schema_view decorator with standard CRUD documentation
        
    Usage:
        @create_standard_schema_view("customer", "Customer management", ["Customers"])
        class CustomerViewSet(BaseModelViewSet):
            ...
    """
    if not description:
        description = f"{resource_name.title()} management"
    
    if not tags:
        tags = [resource_name.title().replace(" ", " ")]
    
    return extend_schema_view(
        list=extend_schema(
            summary=f"List {resource_name}s",
            description=f"Retrieve a paginated list of all {resource_name}s with filtering and search capabilities.",
            tags=tags
        ),
        create=extend_schema(
            summary=f"Create {resource_name}",
            description=f"Create a new {resource_name} record.",
            tags=tags
        ),
        retrieve=extend_schema(
            summary=f"Get {resource_name}",
            description=f"Retrieve details of a specific {resource_name} by ID.",
            tags=tags
        ),
        update=extend_schema(
            summary=f"Update {resource_name}",
            description=f"Update all fields of an existing {resource_name}.",
            tags=tags
        ),
        partial_update=extend_schema(
            summary=f"Partially update {resource_name}",
            description=f"Update specific fields of an existing {resource_name}.",
            tags=tags
        ),
        destroy=extend_schema(
            summary=f"Delete {resource_name}",
            description=f"Delete an existing {resource_name}.",
            tags=tags
        ),
    )


class BaseReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Base ViewSet for read-only operations with consistent configuration.
    
    Provides the same standard configuration as BaseModelViewSet but only
    allows list and retrieve operations.
    """
    
    permission_classes = [ConditionalAuthentication]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    ordering = ['-created_at']