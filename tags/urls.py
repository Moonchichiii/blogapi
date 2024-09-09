from django.urls import path
from .views import CreateProfileTag

urlpatterns = [
    path('create-tag/', CreateProfileTag.as_view(), name='create-profile-tag'),
]
