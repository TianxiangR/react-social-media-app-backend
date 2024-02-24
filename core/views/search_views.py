from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from core.models import Post, User, PostImage
from ..serializers import AugmentedPostPreviewSerializer, UserProfileSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q


class SearchAPIView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  
  def get(self, request, *args, **kwargs):
    query = request.query_params.get('q', None)
    query_type = request.query_params.get('type', None)
    
    if query_type == None:
      return Response({
        "error": "Query type not provided"
      }, status=status.HTTP_400_BAD_REQUEST)
    
    if query_type == 'top':
      if query is None or len(query) == 0:
        return Response({
          "users": [],
          "posts": [],
        }, status=status.HTTP_200_OK)
      
      # Search user by name and username
      filtered_users = User.objects.filter(is_staff=False).filter(
        Q(username__icontains=query) | Q(name__icontains=query)
      )[:3]
      
      # Search post by post content
      filtered_posts = Post.objects.filter(content__icontains=query)[:20]
      
      user_serializer = UserProfileSerializer(filtered_users, many=True, context={'request': request})
      post_serializer = AugmentedPostPreviewSerializer(filtered_posts, many=True, context={'request': request})
      
      return Response({
        "users": user_serializer.data,
        "posts": post_serializer.data
      }, status=status.HTTP_200_OK)
    
    elif query_type == 'latest':
      if query is None or len(query) == 0:
        return Response({
          "posts": [],
        }, status=status.HTTP_200_OK)
      
      # Search post by post content
      filtered_posts = Post.objects.filter(content__icontains=query)[:20]
      post_serializer = AugmentedPostPreviewSerializer(filtered_posts, many=True, context={'request': request})
      return Response({
        "posts": post_serializer.data
      }, status=status.HTTP_200_OK)
    
    elif query_type == 'people':
      if query is None or len(query) == 0:
        return Response({
          "users": []
        }, status=status.HTTP_200_OK)
      
      # Search user by name and username
      filtered_users = User.objects.filter(is_staff=False).filter(
        Q(username__icontains=query) | Q(name__icontains=query)
      )[:20]
      
      user_serializer = UserProfileSerializer(filtered_users, many=True, context={'request': request})
      return Response({
        "users": user_serializer.data
      }, status=status.HTTP_200_OK)
      
    elif query_type == 'media':
      if query is None or len(query) == 0:
        return Response({
          "media": []
        }, status=status.HTTP_200_OK)
      
      # Search post by post content
      filtered_posts = Post.objects.filter(content__icontains=query)
      filtered_media = []
      
      for post in filtered_posts:
        images = post.images.all()
        for image in images:
          filtered_media.append(request.build_absolute_uri(image.image.url))
          if len(filtered_media) == 20:
            break
        if len(filtered_media) == 20:
          break
      
      return Response({
        "media": filtered_media
      }, status=status.HTTP_200_OK)
      
    else:
      return Response({
        "error": "Invalid query type"
      }, status=status.HTTP_400_BAD_REQUEST)
      
      
    