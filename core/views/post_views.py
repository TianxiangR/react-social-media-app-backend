from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from core.models import PostImage, Post
from ..serializers import PostSerializer, PostPreviewSerializer, PostLikeSerializer, PostDetailSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


class PostView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = PostSerializer
  
  def post(self, request):
      data = request.POST
      images = request.FILES.getlist('images')

      data = dict(data)
      
      if data.get('content') is not None and len(data.get('content')) != 0:
        data['content'] = data['content'][0]
      
      data['author'] = request.user.id
      
      serializer = self.serializer_class(data=data)
      serializer.is_valid(raise_exception=True)
      post = serializer.save()
      
      for image in images:
          post_image = PostImage.objects.create(post=post, image=image)
      
      return Response(serializer.data, status=status.HTTP_201_CREATED)
  
  def get(self, request):
      posts = request.user.posts.all()
      serializer = PostPreviewSerializer(posts, many=True, context={'request': request})
      return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class PostDetailView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  lookup_url_kwarg = 'postId'
  queryset = Post.objects.all()
  
  def get(self, request, postId):
      post = self.get_object()
      serializer = PostDetailSerializer(post, context={'request': request})
      return Response(serializer.data, status=status.HTTP_200_OK)
    
  def delete(self, request, postId):
      post = self.get_object()
      
      if post.author != request.user:
          return Response(status=status.HTTP_403_FORBIDDEN)
      
      post.delete()
      return Response(status=status.HTTP_204_NO_CONTENT)
    

class PostLikeView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  lookup_url_kwarg = 'postId'
  queryset = Post.objects.all()
  
  def post(self, request, *args, **kwargs):
      post = self.get_object()
      like = PostLikeSerializer(data={'post': post.id, 'user': request.user.id})
      like.is_valid(raise_exception=True)
      like.save()
      return Response(status=status.HTTP_201_CREATED)
    
  def delete(self, request, *args, **kwargs):
      post = self.get_object()
      like = post.likes.filter(user=request.user)
      if like.exists():
          like.delete()
          return Response(status=status.HTTP_204_NO_CONTENT)
      
      return Response(status=status.HTTP_404_NOT_FOUND)


class PostReplyView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = PostSerializer
  lookup_url_kwarg = 'postId'
  
  def post(self, request, postId):
      parent_post = get_object_or_404(Post, id=postId)
      print(parent_post)
    
      data = request.POST
      images = request.FILES.getlist('images')

      data = dict(data)
      
      if data.get('content') is not None and len(data.get('content')) != 0:
        data['content'] = data['content'][0]
      
      data['author'] = request.user.id
      
      serializer = self.serializer_class(data=data)
      serializer.is_valid(raise_exception=True)
      post = serializer.save()
      
      for image in images:
          post_image = PostImage.objects.create(post=post, image=image)
          
      post.reply_parent = parent_post
      post.save()
      
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    
      