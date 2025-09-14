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