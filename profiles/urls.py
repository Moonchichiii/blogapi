from django.urls import path
from .views import UpdateProfileView

urlpatterns = [
    path('update-profile/', UpdateProfileView.as_view(), name='update_profile'),
]
