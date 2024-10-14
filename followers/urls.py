from django.urls import path
from .views import FollowerListView, FollowUnfollowView, PopularFollowersView

urlpatterns = [
    path("follow/", FollowUnfollowView.as_view(), name="follow-unfollow"),
    path("<int:user_id>/", FollowerListView.as_view(), name="follower-list"),
    path(
        "<int:user_id>/popular-followers/",
        PopularFollowersView.as_view(),
        name="popular_followers",
    ),
]
