from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from ..serializers import CurrentUserSerializer

from core.models import User

class CurrentUser(GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = CurrentUserSerializer
  
    def get(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
      
  
class PublicQueryUser(GenericAPIView):  
  def get(self, request):
    if 'email' in request.query_params:
      found = User.objects.filter(email=request.query_params['email']).exists()
      return Response({'found': found}, status=status.HTTP_200_OK)
    
    if 'username' in request.query_params:
      found = User.objects.filter(username=request.query_params['username']).exists()
      return Response({'found': found}, status=status.HTTP_200_OK)
    
    return Response({'error': 'No email or username provided'}, status=status.HTTP_400_BAD_REQUEST)

    