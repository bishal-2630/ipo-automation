from rest_framework import viewsets
from .models import Account, ApplicationLog
from .serializers import AccountSerializer, ApplicationLogSerializer

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

class ApplicationLogViewSet(viewsets.ModelViewSet):
    queryset = ApplicationLog.objects.all().order_by('-timestamp')
    serializer_class = ApplicationLogSerializer
