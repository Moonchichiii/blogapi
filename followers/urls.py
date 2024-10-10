from django.urls import path
from .views import FollowerListView, FollowUnfollowView



urlpatterns = [
    path('follow/', FollowUnfollowView.as_view(), name='follow-unfollow'),
    path('<int:user_id>/', FollowerListView.as_view(), name='follower-list'),
]
