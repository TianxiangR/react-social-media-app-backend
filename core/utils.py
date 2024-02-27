from .models import Post, User, VisitRecord, PostLike
from datetime import datetime
from django.core.paginator import Paginator, Page
from rest_framework.serializers import Serializer
from rest_framework.request import Request
from typing import Optional
import math

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


def sigmoid(x):
    return 2000 / (1 + math.exp(-0.005 * x)) - 1000


def sort_posts_by_rating(posts):
    post_meta = []
    
    max_like_score = 0
    max_view_score = 0
    max_bookmark_score = 0
    max_comment_score = 0
    max_repost_score = 0
    i = 0
    for post in posts:
      likes = post.likes.count()
      views = post.visits.count()
      bookmarks = post.bookmarks.count()
      comments = post.replies.count()
      reposts = post.reposts.count()
      time_score = len(posts) - i
      likes_score = sigmoid(likes)
      views_score = sigmoid(views)
      bookmarks_score = sigmoid(bookmarks)
      comments_score = sigmoid(comments)
      reposts_score = sigmoid(reposts)
      
      max_like_score = max(max_like_score, likes_score)
      max_view_score = max(max_view_score, views_score)
      max_bookmark_score = max(max_bookmark_score, bookmarks_score)
      max_comment_score = max(max_comment_score, comments_score)
      max_repost_score = max(max_repost_score, reposts_score)
      
      post_meta.append({
        'post': post,
        'like_score': likes_score,
        'view_score': views_score,
        'bookmark_score': bookmarks_score,
        'comment_score': comments_score,
        'repost_score': reposts_score,
        'time_score': time_score
      })
      i += 1
      
    # normalize the scores
    for meta in post_meta:
      meta['like_score'] = meta['like_score'] / max_like_score if max_like_score > 0 else 0
      meta['view_score'] = meta['view_score'] / max_view_score if max_view_score > 0 else 0
      meta['bookmark_score'] = meta['bookmark_score'] / max_bookmark_score if max_bookmark_score > 0 else 0
      meta['comment_score'] = meta['comment_score'] / max_comment_score if max_comment_score > 0 else 0
      meta['repost_score'] = meta['repost_score'] / max_repost_score if max_repost_score > 0 else 0
      meta['time_score'] = meta['time_score'] / len(posts) if len(posts) > 0 else 0
      
    sorted_post_meta = sorted(post_meta, key=lambda x: x['like_score'] * 0.1 + x['view_score'] * 0.1 + x['bookmark_score'] * 0.1 + x['comment_score'] * 0.1 + x['repost_score'] * 0.1 + x['time_score'] * 0.5, reverse=True)
    
    return [meta['post'] for meta in sorted_post_meta]
      
      