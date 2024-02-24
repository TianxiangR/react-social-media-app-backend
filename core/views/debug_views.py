from rest_framework.generics import get_object_or_404, GenericAPIView
from rest_framework.response import Response
from rest_framework import status

from core.models import Post, User, PostImage
from ..serializers import AugmentedPostPreviewSerializer, UserProfileSerializer
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