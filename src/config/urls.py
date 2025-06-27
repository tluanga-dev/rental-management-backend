"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from apps.core.public_views import public_health_check, api_info, item_count_status
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


def health_check(request):
    return JsonResponse({"status": "healthy", "service": "rental_backend"})


urlpatterns = [
    # Health check endpoints
    path("", public_health_check, name="health_check"),
    path("api/", api_info, name="api_index"),
    path("api/item-count/", item_count_status, name="item_count_status"),
    
    # Admin interface
    path("admin/", admin.site.urls),
    
    # OpenAPI Schema and Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    
    # Authentication endpoints
    path("api/auth/", include("apps.core.auth_urls")),
    
    # API endpoints (protected by JWT)
    path("api/", include("apps.unit_of_measurement.urls")),          # /api/unit-of-measurement/
    path("api/", include("apps.warehouse.urls")),                    # /api/warehouses/
    path("api/customers/", include("apps.customer.urls")),           # /api/customers/
    path("api/", include("apps.item_packaging.urls")),               # /api/packaging/
    path("api/vendors/", include("apps.vendor.urls")),               # /api/vendors/
    path("api/items/", include("apps.item_category.urls")),          # /api/items/categories/, /api/items/subcategories/
    path("api/inventory/", include("apps.inventory_item.urls")),     # /api/inventory/
    path("api/purchases/", include("apps.purchase.urls")),          # /api/purchases/
    path("api/id-manager/", include("apps.id_manager.urls")),       # /api/id-manager/
]