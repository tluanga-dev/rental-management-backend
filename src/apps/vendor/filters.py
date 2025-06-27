import django_filters
from .models import Vendor


class VendorFilter(django_filters.FilterSet):
    contact_number = django_filters.CharFilter(
        field_name="contact_numbers__number", lookup_expr="icontains"
    )

    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )

    name_contains = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains"
    )

    updated_at = django_filters.DateTimeFilter(
        field_name="updated_at", lookup_expr="exact"
    )

    class Meta:
        model = Vendor
        fields = {
            "name": ["exact", "icontains"],
            "email": ["exact", "icontains"],
            "city": ["exact", "icontains"],
            "is_active": ["exact"],
            "created_at": ["exact", "lt", "gt"],
            "updated_at": ["exact", "lt", "gt"],
        }
