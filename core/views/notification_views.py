from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from core.models import PostImage, Post, User, PostImage, Bookmark, Notification
from ..serializers import NotificationModelSerializer, NotificationSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q

class NotificationListView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = NotificationModelSerializer
  
  def get(self, request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
  
  def patch(self, request):
    notifications = Notification.objects.filter(recipient=request.user)
    for notification in notifications:
      notification.is_seen = True
      notification.save()
    return Response({'message': 'All notifications marked as seen'}, status=status.HTTP_200_OK)
    
  def delete(self, request):
    notifications = Notification.objects.filter(recipient=request.user)
    notifications.delete()
    return Response({'message': 'All notifications deleted'}, status=status.HTTP_200_OK)
  
class NotificationView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = NotificationModelSerializer
  
  def patch(self, request, notificationId):
    notification = get_object_or_404(Notification, id=notificationId)
    if notification.recipient != request.user:
      return Response({'error': 'You are not authorized to mark this notification as seen'}, status=status.HTTP_403_FORBIDDEN)
    notification.read = True
    notification.save()
    serializer = NotificationSerializer(notification, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)