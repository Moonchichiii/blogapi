from django.urls import path
from .views import ProfileList, ProfileDetail, CurrentUserProfile

urlpatterns = [
    path('profiles/', ProfileList.as_view(), name='profile_list'),
    path('profiles/<int:user_id>/', ProfileDetail.as_view(), name='profile_detail'),
    path('profile/', CurrentUserProfile.as_view(), name='current_user_profile'),
]