from .models import Post, User, VisitRecord, PostLike
from datetime import datetime
from django.core.paginator import Paginator, Page
from rest_framework.serializers import Serializer
from rest_framework.request import Request
from typing import Optional

def is_valid_utc_timestamp(timestamp: float | int | str):
    try:
        # Attempt to create a datetime object from the timestamp
        datetime.utcfromtimestamp(float(timestamp))
        return True  # No error, so the timestamp is valid
    except Exception:
        return False  # ValueError indicates an invalid timestamp

def add_visit_record(visitor, post):
  now = datetime.now()
  last_visit = VisitRecord.objects.filter(visitor=visitor, post=post).order_by('-created_at').first()
  if last_visit:
    duration = now - last_visit.created_at
    if duration.days > 0:
      VisitRecord.objects.create(visitor=visitor, post=post)
  else:
    VisitRecord.objects.create(visitor=visitor, post=post)
    
    
def get_page_response(page: Page, request: Request, serializer_class: Optional[Serializer] = None):
  data = None
  if serializer_class is None:
    data = page.object_list
  else:
    data = serializer_class(page.object_list, many=True, context={'request': request}).data
  return {
    'count': page.paginator.count,
    'total_pages': page.paginator.num_pages,
    'next': page.next_page_number() if page.has_next() else None,
    'previous': page.previous_page_number() if page.has_previous() else None,
    'results': data
  }
  