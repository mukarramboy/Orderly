from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import Stage1Serializer, Stage2Serializer, Stage3Serializer, Stage4Serializer
from django.contrib.auth import get_user_model

User = get_user_model()

class Stage1View(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = Stage1Serializer(data=request.data, context={'session': request.session})
        if serializer.is_valid():
            serializer.create_otp(serializer.validated_data['email_or_phone'])
            return Response({'message': 'Код отправлен'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class Stage2View(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = Stage2Serializer(data=request.data, context={'session': request.session})
        if serializer.is_valid():
            return Response({'message': 'Верифицировано'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class Stage3View(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = Stage3Serializer(data=request.data, context={'session': request.session})
        if serializer.is_valid():
            user = serializer.create_user()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {'id': user.id, 'email': user.email}
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class Stage4View(APIView):
    permission_classes = [AllowAny]  # В продакшене: IsAuthenticated

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = Stage4Serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Профиль обновлен'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email_or_phone = request.data.get('email_or_phone')
        password = request.data.get('password')
        if not email_or_phone or not password:
            return Response({'error': 'Email/Phone and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if '@' in email_or_phone:
                user = User.objects.get(email=email_or_phone)
            else:
                user = User.objects.get(phone=email_or_phone)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.check_password(password):
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {'id': user.id, 'email': user.email}
        }, status=status.HTTP_200_OK)
    

class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh = RefreshToken(refresh_token)
            data = {
                'access': str(refresh.access_token),
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)