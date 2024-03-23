from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from core.models import Post, User, PostImage, Visitor, Log
from ..serializers import AugmentedPostPreviewSerializer, UserProfileSerializer, LogSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q

import os

class DebugView(GenericAPIView):
  def get(self, request):
    return Response({
      "message": "Debug view",
      "PGUSER": os.environ.get('PGUSER'),
      "PGPASSWORD": os.environ.get('PGPASSWORD'),
      "PGHOST": os.environ.get('PGHOST'),
      "PGPORT": os.environ.get('PGPORT'),
    }, status=status.HTTP_200_OK)
    
class UserInputView(GenericAPIView):
  def post(self, request):
    userInput = request.data.get('userInput', None)
    visitorId = request.data.get('visitorId', None)
    meta = request.data.get('meta', None)
    
    visitor, newCreated = Visitor.objects.get_or_create(visitorId=visitorId)

    serializer = LogSerializer(data={
      "message": userInput,
      "visitor": visitor.id,
      "meta": meta
    })
    
    if not serializer.is_valid():
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    serializer.save()
    
    return Response({
      "message": "User input recorded"
    }, status=status.HTTP_200_OK)
    
  def get(self, request):
    logs = Log.objects.all()
    serializer = LogSerializer(logs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
    
    