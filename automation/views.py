from rest_framework import viewsets
from .models import Account, ApplicationLog
from .serializers import AccountSerializer, ApplicationLogSerializer

from rest_framework.decorators import action
from rest_framework.response import Response
from .tasks import apply_ipo_task

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        account = self.get_object()
        apply_ipo_task.delay(account.id)
        return Response({'status': 'Automation task triggered'})

    @action(detail=False, methods=['post'])
    def apply_all(self, request):
        from .tasks import run_all_accounts_task
        run_all_accounts_task.delay()
        return Response({'status': 'Automation task triggered for all active accounts'})

class ApplicationLogViewSet(viewsets.ModelViewSet):
    queryset = ApplicationLog.objects.all().order_by('-timestamp')
    serializer_class = ApplicationLogSerializer
