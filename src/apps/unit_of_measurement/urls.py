from django.urls import path, include
from .views import router

urlpatterns = [
    path('unit-of-measurement/', include(router.urls)),
]
