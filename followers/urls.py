from django.urls import path
from .views import FollowUnfollowView

urlpatterns = [
    path('follow/', FollowUnfollowView.as_view(), name='follow-unfollow'),
]
