from django.urls import path
from .views import auth_views, user_views, post_views
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
]