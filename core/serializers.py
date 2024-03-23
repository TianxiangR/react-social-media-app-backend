from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Post, User, PostImage, PostLike, Bookmark, Notification, HashTag, Log
from typing import *
import re
from .utils import is_hashtag

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'name', 'date_of_birth', 'created_at', 'profile_image']
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            name=validated_data['name'],
            date_of_birth=validated_data['date_of_birth'],
            profile_image=validated_data['profile_image']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=256)
    password = serializers.CharField(max_length=256)
    

class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'date_of_birth', 'created_at', 'profile_image']
        
class UserProfileSerializer(serializers.ModelSerializer):
    followers = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'date_of_birth', 'created_at', 'profile_image', 'bio', 'location', 'followers', 'following', 'website', 'header_photo', 'is_following']
        
    def get_followers(self, obj) -> int:
        return obj.followers.count()
    
    def get_following(self, obj) -> int:
        return obj.following.count()
    
    def get_is_following(self, obj) -> bool:
        return obj.followers.filter(follower=self.context['request'].user).exists()


class PublicUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    username = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=50)
    profile_image = serializers.ImageField()
        

class PublicQueryUserSerializer(serializers.Serializer):
    found = serializers.SerializerMethodField()
    
    def validate(self, data):
        data = super().validate(data)
        if 'email' not in data:
            raise serializers.ValidationError({'email': 'This field is required'})
        return data
    
    def get_found(self, obj):
        return User.objects.filter(email=obj.email).exists()


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'author', 'content', 'created_at', 'reply_parent', 'repost_parent']
    
    def create(self, validated_data):
        post = super().create(validated_data)
        
        # extract hashtags from content
        content = validated_data['content']
        seen = set()
        words = content.split()
        
        for word in words:
            if is_hashtag(word):
                tag_name = word[1:]
                if tag_name not in seen:
                    tag, _ = HashTag.objects.get_or_create(name=tag_name)
                    tag.posts.add(post)
                    seen.add(tag_name)
                    tag.save()
                    
        
        return post
    
    def update(self, instance, validated_data):
        instance.content = validated_data.get('content', instance.content)
        new_tags = set()
        content = validated_data['content']
        words = content.split()
        for word in words:
            if is_hashtag(word):
                tag_name = word[1:]
                new_tags.add(tag_name)
                tag, _ = HashTag.objects.get_or_create(name=tag_name)
                tag.posts.add(instance)
                tag.save()
        
        for tag in instance.hashtags.all():
            if tag.name not in new_tags:
                tag.posts.remove(instance)
                tag.save()
            
        
    
class PostPreviewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    author = UserProfileSerializer()
    content = serializers.CharField()
    created_at = serializers.DateTimeField()
    images = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    repost_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    view_count = serializers.SerializerMethodField()
    bookmark_count = serializers.SerializerMethodField()
    bookmarked = serializers.SerializerMethodField()
    reposted = serializers.SerializerMethodField()
    
    def get_images(self, obj) -> List[str]:
        images = PostImage.objects.filter(post=obj)
        request = self.context['request']
        return [request.build_absolute_uri(image.image.url) for image in images]
    
    def get_liked(self, obj) -> bool:
        return obj.likes.filter(user=self.context['request'].user.id).exists()

    def get_reply_count(self, obj) -> int:
        return obj.replies.count()
    
    def get_repost_count(self, obj) -> int:
        return obj.reposts.count()
    
    def get_like_count(self, obj) -> int:
        return obj.likes.count()
    
    def get_view_count(self, obj) -> int:
        return obj.visits.count()
    
    def get_bookmarked(self, obj) -> bool:
        return obj.bookmarks.filter(user=self.context['request'].user.id).exists()
    
    def get_bookmark_count(self, obj) -> int:
        return obj.bookmarks.count()
    
    def get_reposted(self, obj) -> bool:
        return obj.reposts.filter(author=self.context['request'].user.id).exists()
    
class AugmentedPostPreviewSerializer(PostPreviewSerializer):
    repost_parent = PostPreviewSerializer()
    reply_parent = PostPreviewSerializer()
    
class PostLikeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLike
        fields = '__all__'
        

class PostDetailSerializer(AugmentedPostPreviewSerializer):
    reply_parent = serializers.SerializerMethodField()
    
    def get_reply_parent(self, obj):
        if obj.reply_parent:
            return PostDetailSerializer(obj.reply_parent, context=self.context).data
        return None
    
class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = '__all__'


class PostLikeSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    post = AugmentedPostPreviewSerializer()
    user = UserProfileSerializer()


class NotificationModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        
class NotificationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    type = serializers.CharField()
    data = serializers.SerializerMethodField()
    read = serializers.BooleanField()
    
    def get_data(self, obj):
        if obj.type == 'like':
            serializer = PostLikeSerializer(obj.like, context=self.context)
            return serializer.data
        elif obj.type == 'reply':
            post = obj.reply
            serializer = AugmentedPostPreviewSerializer(post, context=self.context)
            return serializer.data
        elif obj.type == 'repost':
            post = obj.repost
            serializer = AugmentedPostPreviewSerializer(post, context=self.context)
            return serializer.data
        elif obj.type == 'follow':
            follow = obj.follow
            serializer = UserProfileSerializer(follow.follower, context=self.context)
            return serializer.data
        else:
            return None

class HashtagSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=1000)
    related_post_count = serializers.SerializerMethodField()
    
    def get_related_post_count(self, obj):
        return obj.posts.count()


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = '__all__'
    