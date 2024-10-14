from django.urls import path
from .views import CommentList, CommentDetail

urlpatterns = [
    path("posts/<int:post_id>/comments/", CommentList.as_view(), name="comment-list"),
    path("comments/<int:pk>/", CommentDetail.as_view(), name="comment-detail"),
]
