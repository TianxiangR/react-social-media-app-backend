from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import User
from core.serializers import UserSerializer, UserLoginSerializer

class UserLogin(TokenObtainPairView):
    serializer_class = UserLoginSerializer
    queryset = User.objects.all()
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        print(request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(User, email=request.data['email'])
        if user:
            return Response({'message': 'User logged in successfully'}, status=status.HTTP_200_OK)
        return Response({'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

class UserCreate(TokenObtainPairView):
    serializer_class = UserSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        refresh = RefreshToken.for_user(serializer.instance)
        return Response({
          'refresh': str(refresh),
          'access': str(refresh.access_token),
          }, status=status.HTTP_201_CREATED)