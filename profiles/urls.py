from django.urls import path
from .views import ProfileListView, ProfileDetailView

urlpatterns = [
    path('profiles/', ProfileListView.as_view(), name='profile_list'),
    path('profiles/<int:user_id>/', ProfileDetailView.as_view(), name='profile_detail'),
]
