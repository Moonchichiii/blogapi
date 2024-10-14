from django.urls import path
from .views import CreateProfileTagView

urlpatterns = [
    path("create/", CreateProfileTagView.as_view(), name="create-profile-tag"),
]
