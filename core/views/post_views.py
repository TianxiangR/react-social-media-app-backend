from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from core.models import PostImage, Post, User, PostImage, Bookmark, Notification
from ..serializers import PostSerializer, PostPreviewSerializer, PostLikeModelSerializer, PostDetailSerializer, AugmentedPostPreviewSerializer, BookmarkSerializer, NotificationModelSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q


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
        PostImage.objects.create(post=post, image=image)
        
      serializer = AugmentedPostPreviewSerializer(post, context={'request': request})
      
      return Response(serializer.data, status=status.HTTP_201_CREATED)
  
  def get(self, request):
      posts = Post.objects.filter(Q(author__followers__follower=request.user) | Q(author=request.user)).order_by('-created_at')
      serializer = AugmentedPostPreviewSerializer(posts, many=True, context={'request': request})
      return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class UserPostsView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = AugmentedPostPreviewSerializer
  lookup_url_kwarg = 'username'
  
  def get(self, request, username):
      author = get_object_or_404(User, username=username)
      posts = Post.objects.filter(author=author)
      serializer = self.serializer_class(posts, many=True, context={'request': request})
      return Response(serializer.data, status=status.HTTP_200_OK)
    

class UserLikedPostsView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = PostPreviewSerializer
  lookup_url_kwarg = 'username'
  
  def get(self, request, username):
      author = get_object_or_404(User, username=username)
      likes = author.likes.all().order_by('-created_at')
      posts = [like.post for like in likes]
      serializer = self.serializer_class(posts, many=True, context={'request': request})
      return Response(serializer.data, status=status.HTTP_200_OK)
    

class UserMediaView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = PostPreviewSerializer
  lookup_url_kwarg = 'username'
  
  def get(self, request, username):
      author = get_object_or_404(User, username=username)
      post_images = PostImage.objects.filter(post__author=author)
      images = [request.build_absolute_uri(image.image.url) for image in reversed(post_images)]
      
      response = {
        'images': images
      }
      
      return Response(response, status=status.HTTP_200_OK)
    
    
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
      like = PostLikeModelSerializer(data={'post': post.id, 'user': request.user.id})
      like.is_valid(raise_exception=True)
      like.save()
      
      if post.author.id != request.user.id:
        notification = {
          'recipient': post.author.id,
          'type': 'like',
          'like': like.data['id'],
        }
        
        noti_serializer = NotificationModelSerializer(data=notification)
        noti_serializer.is_valid(raise_exception=True)
        noti_serializer.save()
      
      serializer = AugmentedPostPreviewSerializer(post, context={'request': request})
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    
  def delete(self, request, *args, **kwargs):
      post = self.get_object()
      like = post.likes.filter(user=request.user)
      if like.exists():
          like.delete()
          serializer = AugmentedPostPreviewSerializer(post, context={'request': request})
          return Response(serializer.data, status=status.HTTP_200_OK)
      
      return Response(status=status.HTTP_404_NOT_FOUND)
    

class PostBookmarkView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  lookup_url_kwarg = 'postId'
  queryset = Post.objects.all()
  
  def post(self, request, *args, **kwargs):
      post = self.get_object()
      
      if Bookmark.objects.filter(user=request.user, post=post).exists():
          return Response({'message': 'Post already bookmarked'}, status=status.HTTP_400_BAD_REQUEST)
              
      serializer = BookmarkSerializer(data={'user': request.user.id, 'post': post.id})
      serializer.is_valid(raise_exception=True)
      serializer.save()
      
      serializer = AugmentedPostPreviewSerializer(post, context={'request': request})
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    
  def delete(self, request, *args, **kwargs):
      post = self.get_object()
      if not Bookmark.objects.filter(user=request.user, post=post).exists():
          return Response({'message': 'Post not bookmarked'}, status=status.HTTP_400_BAD_REQUEST)
        
      bookmark = Bookmark.objects.filter(user=request.user, post=post).first()
      bookmark.delete()
      
      serializer = AugmentedPostPreviewSerializer(post, context={'request': request})
      return Response(serializer.data, status=status.HTTP_200_OK)
    
class BookmarkListView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  
  def get(self, request):
      bookmarks = Bookmark.objects.filter(user=request.user).order_by('-created_at')
      serializer = AugmentedPostPreviewSerializer([bookmark.post for bookmark in bookmarks], many=True, context={'request': request})
      return Response(serializer.data, status=status.HTTP_200_OK)


class PostReplyView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = PostSerializer
  lookup_url_kwarg = 'postId'
  
  def post(self, request, postId):
      parent_post = get_object_or_404(Post, id=postId)
    
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
          PostImage.objects.create(post=post, image=image)
          
      post.reply_parent = parent_post
      post.save()
      
      if parent_post.author != request.user:
        notification = {
          'recipient': parent_post.author.id,
          'type': 'reply',
          'reply': post.id,
        }
        
        noti_serializer = NotificationModelSerializer(data=notification)
        noti_serializer.is_valid(raise_exception=True)
        noti_serializer.save()
      
      serializer = AugmentedPostPreviewSerializer(post, context={'request': request})
      
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class PostRepostView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = PostSerializer
  lookup_url_kwarg = 'postId'
  
  def post(self, request, postId):
      parent_post = get_object_or_404(Post, id=postId)
    
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
        PostImage.objects.create(post=post, image=image)
          
      post.repost_parent = parent_post
      post.save()
      
      if parent_post.author != request.user:
        notification = {
          'recipient': parent_post.author.id,
          'type': 'repost',
          'repost': post.id,
        }
        
        noti_serializer = NotificationModelSerializer(data=notification)
        noti_serializer.is_valid(raise_exception=True)
        noti_serializer.save()
      
      
      serializer = AugmentedPostPreviewSerializer(post, context={'request': request})
      
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    
      