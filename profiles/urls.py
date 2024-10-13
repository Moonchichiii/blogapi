from django.urls import path
from .views import ProfileList, ProfileDetail, CurrentUserProfileView

urlpatterns = [
    path('profiles/', ProfileList.as_view(), name='profile_list'),
    path('profiles/<int:user_id>/', ProfileDetail.as_view(), name='profile_detail'),
    path('profile/', CurrentUserProfileView.as_view(), name='current_user_profile'),
    
]
