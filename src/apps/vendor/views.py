from django_filters import rest_framework as django_filters
from apps.base.base_viewset import BaseModelViewSet, create_standard_schema_view
from .models import Vendor
from .serializers import VendorSerializer


class VendorFilter(django_filters.FilterSet):
    contact_numbers = django_filters.CharFilter(
        field_name="contact_numbers__number", lookup_expr="icontains"
    )

    class Meta:
        model = Vendor
        fields = {
            "name": ["exact", "icontains"],
            "email": ["exact", "icontains"],
            "address": ["exact", "icontains"],
            "remarks": ["exact", "icontains"],
            "city": ["exact", "icontains"],
            "is_active": ["exact"],
        }


@create_standard_schema_view(
    "vendor", 
    "Vendor management with contact information", 
    ["Vendors"]
)
class VendorViewSet(BaseModelViewSet):
    """
    ViewSet for managing vendors/suppliers.
    
    Provides CRUD operations for vendors including:
    - Listing all vendors with pagination and filtering
    - Creating new vendors with contact numbers
    - Retrieving, updating, and deleting specific vendors
    - Filtering by name, email, address, city, contact number, and active status
    - Ordering by various fields
    """
    queryset = Vendor.objects.all().prefetch_related("contact_numbers")
    serializer_class = VendorSerializer
    filterset_class = VendorFilter
    ordering_fields = ["name", "email", "address", "city", "created_at", "is_active"]