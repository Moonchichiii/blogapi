from django.urls import path
from .views import PostList, PostDetail, ApprovePost, DisapprovePost

urlpatterns = [
    path('posts/', PostList.as_view(), name='post-list'),
    path('posts/<int:pk>/', PostDetail.as_view(), name='post-detail'),
    path('posts/<int:pk>/approve/', ApprovePost.as_view(), name='approve-post'),
    path('posts/<int:pk>/disapprove/', DisapprovePost.as_view(), name='disapprove-post'),
]
