from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Post, User, PostImage, PostLike, Bookmark, Notification
from typing import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'name', 'date_of_birth', 'created_at', 'profile_image']
    
    def create(self, validated_data):
        print(validated_data)
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
        print(data)
        if 'email' not in data:
            raise serializers.ValidationError({'email': 'This field is required'})
        return data
    
    def get_found(self, obj):
        return User.objects.filter(email=obj.email).exists()


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'author', 'content', 'created_at', 'reply_parent', 'repost_parent']
        

class PostPreviewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    author = UserProfileSerializer()
    content = serializers.CharField()
    created_at = serializers.DateTimeField()
    images = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    repost_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    view_count = serializers.SerializerMethodField()
    bookmarked = serializers.SerializerMethodField()
    
    def get_images(self, obj) -> List[str]:
        images = PostImage.objects.filter(post=obj)
        request = self.context['request']
        return [request.build_absolute_uri(image.image.url) for image in images]
    
    def get_liked(self, obj) -> bool:
        return obj.likes.filter(user=self.context['request'].user.id).exists()

    def get_comment_count(self, obj) -> int:
        return obj.replies.count()
    
    def get_repost_count(self, obj) -> int:
        return obj.reposts.count()
    
    def get_like_count(self, obj) -> int:
        return obj.likes.count()
    
    def get_view_count(self, obj) -> int:
        return 0
    
    def get_bookmarked(self, obj) -> bool:
        return obj.bookmarks.filter(user=self.context['request'].user.id).exists()
    
class AugmentedPostPreviewSerializer(PostPreviewSerializer):
    repost_parent = PostPreviewSerializer()
    reply_parent = PostPreviewSerializer()
    
    
class PostLikeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLike
        fields = '__all__'
        

class PostDetailSerializer(AugmentedPostPreviewSerializer):
    replies = serializers.SerializerMethodField()
    
    def get_replies(self, obj):
        replies = obj.replies.all()
        serializer = PostPreviewSerializer(replies, many=True, context=self.context)
        return serializer.data
    
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
