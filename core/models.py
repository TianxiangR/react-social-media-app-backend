from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinLengthValidator
import uuid
import datetime

# Create your models here.
class User(AbstractUser):
    id  = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    username = models.CharField(max_length=20, validators=[MinLengthValidator(4)], unique=True)
    password = models.CharField(max_length=256)
    email = models.EmailField(unique=True, max_length=256)
    name = models.CharField(max_length=50, blank=False)
    date_of_birth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=50, blank=True, null=True)
    header_photo = models.ImageField(upload_to='header_photos/', blank=True, null=True)
    website = models.URLField(max_length=100, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def __str__(self):
        return self.username
    

class Post(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reply_parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    repost_parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='reposts')

    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.content[:20].replace('\n', ' ')


class PostImage(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='post_images/', blank=False, null=False)
    
    def __str__(self):
        return str(self.image)
    
    
class PostLike(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'user']
        ordering = ['-created_at']
        
    def __str__(self):
        return f'{self.user} likes {self.post}'
    
class Bookmark(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'user']
        ordering = ['-created_at']
        
    def __str__(self):
        return f'{self.user} bookmarked {self.post}'
    

class Follow(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['follower', 'following'], name='unique_followers')
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        return f'{self.follower} follows {self.following}'
    
class Notification(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=[
        ('like', 'like'),
        ('reply', 'reply'),
        ('follow', 'follow'),
        ('repost', 'repost')
    ])
    like = models.ForeignKey(PostLike, on_delete=models.CASCADE, related_name='notification', null=True, blank=True)
    reply = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reply_notification', null=True, blank=True)
    repost = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='repost_notification', null=True, blank=True)
    follow = models.ForeignKey(Follow, on_delete=models.CASCADE, related_name='notification', null=True, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    class Meta:
        constraints = [
            models.CheckConstraint(check=(models.Q(type='like') & models.Q(like__isnull=False)) | (models.Q(type='reply') & models.Q(reply__isnull=False)) | (models.Q(type='repost') & models.Q(repost__isnull=False)) | (models.Q(type='follow') & models.Q(follow__isnull=False)), name='notification_type_check') 
        ]
        ordering = ['-created_at']
        

class VisitRecord(models.Model):
    visitor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='visits')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='visits')
    created_at = models.DateTimeField(auto_now_add=True)
