from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import IdManager
from datetime import datetime


class IDManagerHealthCheckView(APIView):
    """
    Health check endpoint for ID Manager service.
    
    Returns the operational status of the ID Manager including:
    - Service availability
    - Database connectivity
    - ID generation capability
    - Performance metrics
    """
    permission_classes = [AllowAny]  # Allow public access for monitoring
    
    def get(self, request, *args, **kwargs):
        """
        GET /api/id-manager/health/
        
        Returns health status of the ID Manager service.
        """
        try:
            # Perform health check
            health_status = IdManager.health_check()
            
            # Add current timestamp
            health_status['checked_at'] = datetime.now().isoformat()
            
            # Determine HTTP status code
            http_status = status.HTTP_200_OK if health_status['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
            
            return Response(health_status, status=http_status)
            
        except Exception as e:
            # Catastrophic failure
            return Response({
                'status': 'critical',
                'message': f'Health check failed: {str(e)}',
                'error_type': type(e).__name__,
                'checked_at': datetime.now().isoformat()
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)