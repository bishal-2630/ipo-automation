from .models import Account, ApplicationLog, FCMToken, BankAccount
from .serializers import AccountSerializer, ApplicationLogSerializer, FCMTokenSerializer, BankAccountSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .tasks import run_all_accounts_task


class FCMTokenViewSet(viewsets.ModelViewSet):
    serializer_class = FCMTokenSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = FCMToken.objects.all()

    def create(self, request, *args, **kwargs):
        token = request.data.get('token')
        device_id = request.data.get('device_id')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        fcm_token_obj, created = FCMToken.objects.update_or_create(
            token=token,
            defaults={
                'user': request.user,
                'device_id': device_id
            }
        )
        serializer = self.get_serializer(fcm_token_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class BankAccountViewSet(viewsets.ModelViewSet):
    serializer_class = BankAccountSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BankAccount.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ApplicationLogViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationLogSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return logs for accounts owned by the logged-in user
        return ApplicationLog.objects.filter(account__owner=self.request.user).order_by('-timestamp')

    @action(detail=False, methods=['post'], url_path='mark-as-read')
    def mark_as_read(self, request):
        unreads = self.get_queryset().filter(is_read=False)
        unreads.update(is_read=True)
        return Response({'status': 'marked as read'})


class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        if not username or not password:
            return Response({'error': 'Please provide username and password'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class ManualTriggerView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        run_all_accounts_task.delay()
        return Response({"status": "Automation triggered for all active accounts"}, status=status.HTTP_200_OK)
class HealthView(APIView):
    def get(self, request):
        import os
        from cryptography.fernet import Fernet
        from django.conf import settings
        
        key = os.environ.get("ENCRYPTION_KEY", "").strip()
        key_valid = False
        error_msg = None
        try:
            if key:
                Fernet(key.encode())
                key_valid = True
        except Exception as e:
            error_msg = str(e)
            
        index_path = os.path.join(settings.BASE_DIR, 'frontend', 'index.html')
        index_exists = os.path.exists(index_path)
            
        return Response({
            "status": "online",
            "version": "v3.17-final",
            "encryption_key_length": len(key),
            "encryption_key_valid": key_valid,
            "encryption_error": error_msg,
            "branch": "website-ipo",
            "base_dir": str(settings.BASE_DIR),
            "index_html_exists": index_exists,
            "index_path": index_path
        })

def home_view(request):
    from django.shortcuts import render
    from django.http import HttpResponse
    import os
    from django.conf import settings
    
    index_path = os.path.join(settings.BASE_DIR, 'frontend', 'index.html')
    if not os.path.exists(index_path):
        return HttpResponse(f"Error: index.html not found at {index_path}. Static files might not be collected or build might have failed.", status=500)
    
    return render(request, 'index.html')
