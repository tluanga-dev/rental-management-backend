from django.urls import path
from .views import IDManagerHealthCheckView

app_name = 'id_manager'

urlpatterns = [
    path('health/', IDManagerHealthCheckView.as_view(), name='health-check'),
]