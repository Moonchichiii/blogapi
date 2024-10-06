from django.urls import path
from .views import CreateOrUpdateRatingView

urlpatterns = [
    path('rate/', CreateOrUpdateRatingView.as_view(), name='create-update-rating'),
]