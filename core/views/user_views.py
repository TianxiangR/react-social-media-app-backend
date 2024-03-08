from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from ..serializers import CurrentUserSerializer, UserProfileSerializer, NotificationModelSerializer
from django.utils import timezone
from datetime import datetime
from ..utils import is_valid_utc_timestamp, get_page_response
from ..models import User, Follow
from django.db.models import Q
from django.core.paginator import Paginator

class CurrentUser(GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = UserProfileSerializer
  
    def get(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = UserProfileSerializer
  lookjup_url_kwarg = 'username'
  
  def get(self, request, username):    
    user = get_object_or_404(User, username=username)
    serializer = self.get_serializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)
    
  
  def patch(self, request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
      return Response({'error': 'You are not forbidden to edit this user'}, status=status.HTTP_403_UNAUTHORIZED)
    
    form_data = request.POST
    files = request.FILES
    resquest_data = dict()
    
    for key, value in form_data.items():
      resquest_data[key] = value
    
    for key, value in files.items():
      resquest_data[key] = value
    
    serializer = self.get_serializer(user, data=resquest_data, partial=True)
    
    if not serializer.is_valid():
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    serializer.save()
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
  
class UserFollowView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  lookup_url_kwarg = 'username'
  
  def post(self, request, username):
    user = get_object_or_404(User, username=username)
    if user == request.user:
      return Response({'error': 'You cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
    follow = Follow.objects.filter(follower=request.user, following=user).first()
    if follow is not None:
      return Response({'error': 'You are already following this user'}, status=status.HTTP_400_BAD_REQUEST)
    follow = Follow(follower=request.user, following=user)
    follow.save()
      
    noti_serializer = NotificationModelSerializer(data={
      'recipient': user.id,
      'type': 'follow',
      'follow': follow.id,
    })
    
    noti_serializer.is_valid(raise_exception=True)
    noti_serializer.save()
    
    serializer = UserProfileSerializer(user, context={'request': request})
    
    return Response(serializer.data, status=status.HTTP_200_OK)
  
  def delete(self, request, username):
    user = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(follower=request.user, following=user).first()
    if follow is None:
      return Response({'error': 'You are not following this user'}, status=status.HTTP_400_BAD_REQUEST)
    follow.delete()
    
    serializer = UserProfileSerializer(user, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
  
class UserFollowerListView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  lookup_url_kwarg = 'username'
  
  def get(self, request, username):
    user = get_object_or_404(User, username=username)
    page = request.query_params.get('page', 1)
    timestamp_str = request.query_params.get('timestamp', None)
    if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
      return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
    timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
    follows = Follow.objects.filter(following=user, created_at__lt=timestamp).order_by('-created_at')
    followers = [follow.follower for follow in follows]
    paginator = Paginator(followers, 20)
    current_page = paginator.get_page(page)
    response = get_page_response(current_page, request, UserProfileSerializer)
    return Response(response, status=status.HTTP_200_OK)
  

class UserFollowingListView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  lookup_url_kwarg = 'username'
  
  def get(self, request, username):
    user = get_object_or_404(User, username=username)
    page = request.query_params.get('page', 1)
    timestamp_str = request.query_params.get('timestamp', None)
    if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
      return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
    timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
    follows = Follow.objects.filter(follower=user, created_at__lt=timestamp).order_by('-created_at')
    following = [follow.following for follow in follows]
    paginator = Paginator(following, 20)
    current_page = paginator.get_page(page)
    response = get_page_response(current_page, request, UserProfileSerializer)
    return Response(response, status=status.HTTP_200_OK)
    
    
    

    