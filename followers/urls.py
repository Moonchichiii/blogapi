from django.urls import path
from .views import FollowerDetailView

urlpatterns = [
    path('follow/', FollowerDetailView.as_view(), name='follow-unfollow'),
]
