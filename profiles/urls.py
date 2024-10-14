from django.urls import path
from .views import ProfileList, ProfileDetailView

urlpatterns = [
    path("profiles/", ProfileList.as_view(), name="profile_list"),
    path("profiles/<int:user_id>/", ProfileDetailView.as_view(), name="profile_detail"),
]
