from django.urls import path
from .views import auth_views, user_views, post_views, search_views, notification_views, debug_views
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    path('login/', TokenObtainPairView.as_view()),
    path('signup/', auth_views.UserCreate.as_view()),
    path('get-current-user/', user_views.CurrentUser.as_view()),
    path('public-query-user/', user_views.PublicQueryUser.as_view()),
    path('posts/', post_views.PostView.as_view()),
    path('posts/<uuid:postId>/', post_views.PostDetailView.as_view()),
    path('posts/<uuid:postId>/likes/', post_views.PostLikeView.as_view()),
    path('posts/<uuid:postId>/replies/', post_views.PostReplyView.as_view()),
    path('posts/<uuid:postId>/reposts/', post_views.PostRepostView.as_view()),
    path('posts/<uuid:postId>/bookmarks/', post_views.PostBookmarkView.as_view()),
    path('users/<str:username>/posts/', post_views.UserPostsView.as_view()),
    path('users/<str:username>/', user_views.UserView.as_view()),
    path('users/<str:username>/likes/', post_views.UserLikedPostsView.as_view()),
    path('users/<str:username>/media/', post_views.UserMediaView.as_view()),
    path('users/<str:username>/follow/', user_views.UserFollowView.as_view()),
    path('search/', search_views.SearchAPIView.as_view()),
    path('notifications/', notification_views.NotificationView.as_view()),
    path('bookmarks/', post_views.BookmarkListView.as_view()),
    path('debug/', debug_views.DebugView.as_view()),
]