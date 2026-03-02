from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, ApplicationLogViewSet, RegisterView, LoginView, FCMTokenViewSet, ManualTriggerView, BankAccountViewSet, HealthView

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'logs', ApplicationLogViewSet, basename='applicationlog')
router.register(r'fcm-tokens', FCMTokenViewSet, basename='fcm-token')
router.register(r'bank-accounts', BankAccountViewSet, basename='bankaccount')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('run-all/', ManualTriggerView.as_view(), name='run-all'),
    path('health/', HealthView.as_view(), name='health'),
]
