from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, ApplicationLogViewSet, RegisterView, LoginView


router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'logs', ApplicationLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
]
