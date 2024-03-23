from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Count

from core.models import Post, User, HashTag
from ..serializers import AugmentedPostPreviewSerializer, UserProfileSerializer, HashtagSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from ..utils import is_valid_utc_timestamp, get_page_response, sort_posts_by_rating
from django.core.paginator import Paginator
from django.db.models import TextField
from django.db.models.functions import Length

TextField.register_lookup(Length, 'length')
TextField.register_lookup(TrigramSimilarity, 'similarity')

      
class SearchTopView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  
  def get(self, request, *args, **kwargs):
    query = request.query_params.get('q', None)
    timestamp_str = request.query_params.get('timestamp', None)
    if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
      return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
    timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
    page = request.query_params.get('page', 1)
    
    empty_response = get_page_response(Paginator([], 1).page(1), request)
    
    if query is None or len(query) == 0:
      return Response(empty_response, status=status.HTTP_200_OK)
    # Search post by post content
    filtered_posts = Post.objects.filter(Q(content__icontains=query) | Q(author__name__icontains=query) | Q(author__username__icontains=query)).filter(created_at__lte=timestamp)
    filtered_posts = sort_posts_by_rating(filtered_posts)
    paginator = Paginator(filtered_posts, 20)
    page = paginator.page(page)
    response_body = get_page_response(page, request, AugmentedPostPreviewSerializer)
    
    return Response(response_body, status=status.HTTP_200_OK)
  

class SearchLatestView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  
  def get(self, request, *args, **kwargs):
    query = request.query_params.get('q', None)
    timestamp_str = request.query_params.get('timestamp', None)
    if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
      return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
    timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
    page = request.query_params.get('page', 1)
    
    empty_response = get_page_response(Paginator([], 1).page(1), request)
    
    if query is None or len(query) == 0:
      return Response(empty_response, status=status.HTTP_200_OK)
    # Search post by post content
    filtered_posts = Post.objects.filter(Q(content__icontains=query) | Q(author__name__icontains=query) | Q(author__username__icontains=query)).filter(created_at__lte=timestamp)
    paginator = Paginator(filtered_posts, 20)
    page = paginator.page(page)
    response_body = get_page_response(page, request, AugmentedPostPreviewSerializer)
    return Response(response_body, status=status.HTTP_200_OK)
  

class SearchPeopleView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  
  def get(self, request, *args, **kwargs):
    query = request.query_params.get('q', None)
    timestamp_str = request.query_params.get('timestamp', None)
    if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
      return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
    timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
    page = request.query_params.get('page', 1)
    
    empty_response = get_page_response(Paginator([], 1).page(1), request)
    
    if query is None or len(query) == 0:
      return Response(empty_response, status=status.HTTP_200_OK)
    
    # Search user by name and username
    filtered_users = User.objects.filter(is_staff=False).filter(
      Q(username__icontains=query) | Q(name__icontains=query)
    ).filter(created_at__lte=timestamp)
    
    paginator = Paginator(filtered_users, 20)
    page = paginator.page(page)
    response_body = get_page_response(page, request, UserProfileSerializer)
    return Response(response_body, status=status.HTTP_200_OK)
  

class SearchMediaView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  
  def get(self, request, *args, **kwargs):
    query = request.query_params.get('q', None)
    timestamp_str = request.query_params.get('timestamp', None)
    if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
      return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
    timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
    page = request.query_params.get('page', 1)
    
    empty_response = get_page_response(Paginator([], 1).page(1), request)
    
    if query is None or len(query) == 0:
      return Response(empty_response, status=status.HTTP_200_OK)
    
    # Search post by post content
    filtered_posts = Post.objects.filter(Q(content__icontains=query) | Q(author__name__icontains=query) | Q(author__username__icontains=query)).filter(created_at__lte=timestamp)
    filtered_media = []
    
    for post in filtered_posts:
      images = post.images.all()
      for image in images:
        filtered_media.append(request.build_absolute_uri(image.image.url))
        if len(filtered_media) == 20:
          break
      if len(filtered_media) == 20:
        break
      
    paginator = Paginator(filtered_media, 20)
    page = paginator.page(page)
    response_body = get_page_response(page, request)
    
    return Response(response_body, status=status.HTTP_200_OK)
  
      
class SearchHashtagView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  
  def get(self, request, *args, **kwargs):
    query = request.query_params.get('q', None)
    
    # Search hashtag by name
    filtered_hashtags = HashTag.objects.annotate(
      popularity=Count('posts'),
    ).filter(name__startswith=query).order_by('-popularity')

    hash_tags = HashtagSerializer(filtered_hashtags, many=True).data
    return Response(hash_tags, status=status.HTTP_200_OK)