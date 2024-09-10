from django.urls import path
from .views import CreateUpdateRating

urlpatterns = [
    path('rate/', CreateUpdateRating.as_view(), name='create-update-rating'),
]