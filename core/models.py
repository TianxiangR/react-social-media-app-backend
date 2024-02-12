from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinLengthValidator
import uuid

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
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    

class Post(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    reply_parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    repost_parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='reposts')

    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.content[:20]


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
    
    class Meta:
        unique_together = ['post', 'user']
        
    def __str__(self):
        return f'{self.user} likes {self.post}'
    
class Bookmark(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    
    class Meta:
        unique_together = ['post', 'user']
        
    def __str__(self):
        return f'{self.user} bookmarked {self.post}'