from django.urls import path
from .views import ProfileList, ProfileView, UpdateProfileView, CurrentUserProfileView

urlpatterns = [
    path('profiles/', ProfileList.as_view(), name='profile_list'),
    path('profiles/<int:user_id>/', ProfileView.as_view(), name='profile_view'),
    path('update-profile/', UpdateProfileView.as_view(), name='update_profile'),
    path('my-profile/', CurrentUserProfileView.as_view(), name='my_profile'),
]
