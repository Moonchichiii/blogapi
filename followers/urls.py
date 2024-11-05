from django.urls import path
from .views import FollowerDetailView, PopularFollowersView

urlpatterns = [
    path('follow/', FollowerDetailView.as_view(), name='follow-unfollow'),
    path('<int:user_id>/', FollowerDetailView.as_view(), name='follower_detail'),
    path('<int:user_id>/popular-followers/', PopularFollowersView.as_view(), name='popular_followers'),
]
