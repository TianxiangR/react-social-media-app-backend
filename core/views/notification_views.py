from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from core.models import PostImage, Post, User, PostImage, Bookmark, Notification
from ..serializers import NotificationModelSerializer, NotificationSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from ..utils import is_valid_utc_timestamp, get_page_response
from django.core.paginator import Paginator

class NotificationListView(GenericAPIView):
  permission_classes = [IsAuthenticated]
  authentication_classes = [JWTAuthentication]
  serializer_class = NotificationModelSerializer
  
  def get(self, request):
    prefetch = request.query_params.get('prefetch', 'false')
    
    if prefetch == 'true':
      unread_count = Notification.objects.filter(recipient=request.user, read=False).count()
      return Response({
        "count": unread_count
      }, status=status.HTTP_200_OK)
    
    page = request.query_params.get('page', 1)
    timestamp_str = request.query_params.get('timestamp', None)
    if timestamp_str is not None and not is_valid_utc_timestamp(timestamp_str):
      return Response({'error': 'Invalid timestamp'}, status=status.HTTP_400_BAD_REQUEST)
    timestamp = timezone.now() if timestamp_str is None else datetime.utcfromtimestamp(float(timestamp_str))
    notifications = Notification.objects.filter(recipient=request.user).filter(created_at__lte=timestamp).order_by('-created_at')
    paginator = Paginator(notifications, 20)
    page = paginator.page(page)
    response = get_page_response(page, request, NotificationSerializer)
    return Response(response, status=status.HTTP_200_OK)
  
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
  

# class NotificationPrefetch(GenericAPIView):
#   permission_classes = [IsAuthenticated]
#   authentication_classes = [JWTAuthentication]
#   serializer_class = NotificationModelSerializer
  
#   def get(self, request):
#     unread_count = Notification.objects.filter(recipient=request.user, is_seen=False).count()
#     return Response({
#       "count": unread_count
#       }, status=status.HTTP_200_OK)