from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, ApplicationLogViewSet

router = DefaultRouter()
router.register(r'accounts', AccountViewSet)
router.register(r'logs', ApplicationLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
