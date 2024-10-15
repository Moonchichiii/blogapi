from django.urls import path
from .views import CommentList, CommentDetail, ModerateComment

urlpatterns = [
    path("posts/<int:post_id>/comments/", CommentList.as_view(), name="comment-list"),
    path("comments/<int:pk>/", CommentDetail.as_view(), name="comment-detail"),
    path("comments/<int:pk>/moderate/", ModerateComment.as_view(), name="comment-moderate"),
]