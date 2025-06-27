"""
Public views that don't require authentication.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone


@api_view(['GET'])
@permission_classes([AllowAny])
def public_health_check(request):
    """Public health check endpoint."""
    return Response({
        'status': 'healthy',
        'service': 'rental_backend',
        'message': 'API is running and accessible'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def item_count_status(request):
    """Public endpoint to get current item count status."""
    # Get cached data from the periodic task
    cached_data = cache.get('system_item_count')
    
    if cached_data:
        return Response({
            'status': 'success',
            'data': cached_data,
            'message': 'Item count data from periodic task'
        })
    else:
        # If no cached data, provide basic info
        return Response({
            'status': 'no_data',
            'message': 'No recent item count data available. Periodic task may not be running.',
            'timestamp': timezone.now().isoformat()
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """Public API information endpoint."""
    base_url = request.build_absolute_uri('/').rstrip('/')
    
    return Response({
        'api_info': {
            'title': 'Rental Backend API',
            'version': '1.0.0',
            'description': 'REST API for rental management system with JWT authentication',
            'base_url': base_url,
            'authentication': {
                'type': 'JWT Bearer Token',
                'endpoints': {
                    'login': f'{base_url}/api/auth/login/',
                    'register': f'{base_url}/api/auth/register/',
                    'refresh': f'{base_url}/api/auth/refresh/',
                    'verify': f'{base_url}/api/auth/verify/',
                }
            },
            'documentation': {
                'health_check': f'{base_url}/',
                'admin_panel': f'{base_url}/admin/',
                'item_count_status': f'{base_url}/api/item-count/',
            }
        }
    })
