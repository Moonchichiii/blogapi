from django.urls import path
from .views import ProfileList, ProfileView, UpdateProfileView

urlpatterns = [
    path('profiles/', ProfileList.as_view(), name='profile_list'),
    path('profile/<int:user__id>/', ProfileView.as_view(), name='profile_view'),
    path('update-profile/', UpdateProfileView.as_view(), name='update_profile'),
]
