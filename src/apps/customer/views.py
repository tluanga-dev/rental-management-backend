from django_filters import rest_framework as django_filters
from apps.base.base_viewset import BaseModelViewSet, create_standard_schema_view
from .models import Customer
from .serializers import CustomerSerializer


class CustomerFilter(django_filters.FilterSet):
    contact_number = django_filters.CharFilter(
        field_name="contact_numbers__number", lookup_expr="icontains"
    )

    class Meta:
        model = Customer
        fields = {
            "name": ["exact", "icontains"],
            "email": ["exact", "icontains"],
            "address": ["exact", "icontains"],
            "remarks": ["exact", "icontains"],
            "city": ["exact", "icontains"],
            "is_active": ["exact"],
        }


@create_standard_schema_view(
    "customer", 
    "Customer management with contact information", 
    ["Customers"]
)
class CustomerViewSet(BaseModelViewSet):
    """
    ViewSet for managing customers.
    
    Provides CRUD operations for customers including:
    - Listing all customers with pagination and filtering
    - Creating new customers with contact numbers
    - Retrieving, updating, and deleting specific customers
    - Filtering by name, email, address, city, contact number, and active status
    - Ordering by various fields
    """
    queryset = Customer.objects.all().prefetch_related("contact_numbers")
    serializer_class = CustomerSerializer
    filterset_class = CustomerFilter
    ordering_fields = ["name", "email", "address", "city", "created_at", "is_active"]