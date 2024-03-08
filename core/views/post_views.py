from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from core.models import PostImage, Post, User, PostImage, Bookmark, Notification
from ..serializers import PostSerializer, PostPreviewSerializer, PostLikeModelSerializer, \
  PostDetailSerializer, AugmentedPostPreviewSerializer, BookmarkSerializer, \
  NotificationModelSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q
from ..utils import add_visit_record, get_page_response, is_valid_utc_timestamp, sort_posts_by_rating
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime

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
      timestamp_str = request.query_params.get('timestamp', None)
      if timestamp_str is not None and not is_valid_utc_timestamp(float(timestamp_str)):
        return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
      timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
      page = request.query_params.get('page', 1)
      posts = Post.objects.order_by('-created_at').filter((Q(author__followers__follower=request.user) | Q(author=request.user)) & Q(created_at__lte=timestamp)).distinct()
      paginator = Paginator(posts, 20)
      current_page = paginator.get_page(page)
      response = get_page_response(current_page, request, AugmentedPostPreviewSerializer)
      return Response(response, status=status.HTTP_200_OK)
    
    
class UserPostsView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = AugmentedPostPreviewSerializer
  lookup_url_kwarg = 'username'
  
  def get(self, request, username):
      author = get_object_or_404(User, username=username)
      timestamp_str = request.query_params.get('timestamp', None)
      if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
        return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
      timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
      page = request.query_params.get('page', 1)
      posts = Post.objects.filter(author=author).filter(created_at__lte=timestamp).order_by('-created_at')
      paginator = Paginator(posts, 20)
      current_page = paginator.get_page(page)
      response = get_page_response(current_page, request, self.serializer_class)
      return Response(response, status=status.HTTP_200_OK)
    

class UserLikedPostsView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = AugmentedPostPreviewSerializer
  lookup_url_kwarg = 'username'
  
  def get(self, request, username):
      author = get_object_or_404(User, username=username)
      likes = author.likes.all().order_by('-created_at')
      posts = [like.post for like in likes]
      timestamp_str = request.query_params.get('timestamp', None)
      if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
        return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
      timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
      page = request.query_params.get('page', 1)
      filtered_posts = list(filter(lambda post: post.created_at <= timestamp, posts))
      paginator = Paginator(filtered_posts, 20)
      current_page = paginator.get_page(page)
      response = get_page_response(current_page, request, self.serializer_class)
      return Response(response, status=status.HTTP_200_OK)
    

class UserMediaView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = PostPreviewSerializer
  lookup_url_kwarg = 'username'
  
  def get(self, request, username):
      author = get_object_or_404(User, username=username)
      timestamp_str = request.query_params.get('timestamp', None)
      if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
        return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
      timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
      page = request.query_params.get('page', 1)
      post_images = PostImage.objects.filter(post__author=author).filter(post__created_at__lte=timestamp).order_by('-post__created_at')
      paginator = Paginator(post_images, 30)
      current_page = paginator.get_page(page)
      images = [request.build_absolute_uri(image.image.url) for image in current_page.object_list]
      
      response = {
        'count': paginator.count,
        'next': current_page.next_page_number() if current_page.has_next() else None,
        'previous': current_page.previous_page_number() if current_page.has_previous() else None,
        'results': images,
        'total_pages': paginator.num_pages,
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
      add_visit_record(request.user, post)
      return Response(serializer.data, status=status.HTTP_200_OK)
    
  def delete(self, request, postId):
      post = self.get_object()
      
      if post.author != request.user:
          return Response(status=status.HTTP_403_FORBIDDEN)
      
      post.delete()
      return Response(status=status.HTTP_204_NO_CONTENT)
    
class PostReplyListView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  lookup_url_kwarg = 'postId'
  queryset = Post.objects.all()
  serializer_class = AugmentedPostPreviewSerializer
  
  def get(self, request, postId):
      post = self.get_object()
      page = request.query_params.get('page', 1)
      timestamp_str = request.query_params.get('timestamp', None)
      if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
        return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
      timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
      replies = post.replies.all().filter(created_at__lte=timestamp)
      reply_list = list(replies)
      reply_list_len = len(reply_list)
      
      for i in range(reply_list_len):
        reply = reply_list[i]
        next_reply = reply.replies.all().filter(created_at__lte=timestamp).order_by('-created_at').first()
        while next_reply:
          reply_list.append(next_reply)
          next_reply = next_reply.replies.all().filter(created_at__lte=timestamp).order_by('-created_at').first()
      reply_list.sort(key=lambda reply: reply.created_at, reverse=True)
      paginator = Paginator(reply_list, 20)
      current_page = paginator.get_page(page)
      response = get_page_response(current_page, request, self.serializer_class)
      return Response(response, status=status.HTTP_200_OK)
    
  def post(self, request, postId):
    parent_post = get_object_or_404(Post, id=postId)
  
    data = request.POST
    images = request.FILES.getlist('images')

    data = dict(data)
    
    if data.get('content') is not None and len(data.get('content')) != 0:
      data['content'] = data['content'][0]
    
    data['author'] = request.user.id
    
    serializer = PostSerializer(data=data)
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
    add_visit_record(request.user, parent_post)
    serializer = AugmentedPostPreviewSerializer(post, context={'request': request})
    
    return Response(serializer.data, status=status.HTTP_201_CREATED)
    

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
      add_visit_record(request.user, post)
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
      add_visit_record(request.user, post)
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
      page = request.query_params.get('page', 1)
      timestamp_str = request.query_params.get('timestamp', None)
      if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
        return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
      timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
      bookmarks = Bookmark.objects.filter(user=request.user).filter(post__created_at__lte=timestamp).order_by('-post__created_at')
      posts = [bookmark.post for bookmark in bookmarks]
      paginator = Paginator(posts, 20)
      response = get_page_response(paginator.get_page(page), request, AugmentedPostPreviewSerializer)
      return Response(response, status=status.HTTP_200_OK)

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
      
      add_visit_record(request.user, parent_post)
      serializer = AugmentedPostPreviewSerializer(post, context={'request': request})
      
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
class TopRatedPostListView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  
  def get(self, request):
      timestamp_str = request.query_params.get('timestamp', None)
      if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
        return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
      timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
      page = request.query_params.get('page', 1)
      posts = Post.objects.filter(created_at__lte=timestamp)
      posts = sort_posts_by_rating(posts)
      paginator = Paginator(posts, 20)
      response = get_page_response(paginator.page(page), request, AugmentedPostPreviewSerializer)
      return Response(response, status=status.HTTP_200_OK)
    

class FollowingPostListView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  
  def get(self, request):
      timestamp_str = request.query_params.get('timestamp', None)
      if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
        return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
      timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
      page = request.query_params.get('page', 1)
      posts = Post.objects.filter((Q(author__followers__follower=request.user) | Q(author=request.user)) & Q(created_at__lte=timestamp)).distinct()
      paginator = Paginator(posts, 20)
      response = get_page_response(paginator.page(page), request, AugmentedPostPreviewSerializer)
      return Response(response, status=status.HTTP_200_OK)
      