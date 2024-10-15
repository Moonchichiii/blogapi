from django.urls import path
from .views import FollowerListView, FollowerDetailView

urlpatterns = [
    path('followers/<int:user_id>/', FollowerListView.as_view(), name='follower-list'),
    path('follow/', FollowerDetailView.as_view(), name='follow-unfollow'),
    path('popular-followers/<int:user_id>/', FollowerListView.as_view(), name='popular-followers'),
]