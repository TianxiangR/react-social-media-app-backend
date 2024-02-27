from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from core.models import Post, User, PostImage
from ..serializers import AugmentedPostPreviewSerializer, UserProfileSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from ..utils import is_valid_utc_timestamp, get_page_response, sort_posts_by_rating
from django.core.paginator import Paginator


class SearchAPIView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  
  def get(self, request, *args, **kwargs):
    query = request.query_params.get('q', None)
    query_type = request.query_params.get('type', None)
    timestamp_str = request.query_params.get('timestamp', None)
    if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
      return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
    timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
    page = request.query_params.get('page', 1)
    
    empty_response = get_page_response(Paginator([], 1).page(1), request)
    
    if query_type == None:
      return Response({
        "error": "Query type not provided"
      }, status=status.HTTP_400_BAD_REQUEST)
    
    if query_type == 'top':
      if query is None or len(query) == 0:
        return Response(empty_response, status=status.HTTP_200_OK)
      # Search post by post content
      filtered_posts = Post.objects.filter(Q(content__icontains=query) | Q(author__name__icontains=query)).filter(created_at__lte=timestamp)
      filtered_posts = sort_posts_by_rating(filtered_posts)
      paginator = Paginator(filtered_posts, 20)
      page = paginator.page(page)
      response_body = get_page_response(page, request, AugmentedPostPreviewSerializer)
      
      return Response(response_body, status=status.HTTP_200_OK)
    
    elif query_type == 'latest':
      if query is None or len(query) == 0:
        return Response(empty_response, status=status.HTTP_200_OK)
      # Search post by post content
      filtered_posts = Post.objects.filter(Q(content__icontains=query) | Q(author__name__icontains=query)).filter(created_at__lte=timestamp)
      paginator = Paginator(filtered_posts, 20)
      page = paginator.page(page)
      response_body = get_page_response(page, request, AugmentedPostPreviewSerializer)
      return Response(response_body, status=status.HTTP_200_OK)
    
    elif query_type == 'people':
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
      
    elif query_type == 'media':
      if query is None or len(query) == 0:
        return Response(empty_response, status=status.HTTP_200_OK)
      
      # Search post by post content
      filtered_posts = Post.objects.filter(content__icontains=query).filter(created_at__lte=timestamp)
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
      
    else:
      return Response({
        "error": "Invalid query type"
      }, status=status.HTTP_400_BAD_REQUEST)
      
      
    