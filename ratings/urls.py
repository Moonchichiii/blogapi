from django.urls import path
from .views import CreateOrUpdateRatingView, GetUserRatingView

urlpatterns = [
    path("rate/", CreateOrUpdateRatingView.as_view(), name="create-update-rating"),
    path("rate/<int:post_id>/", GetUserRatingView.as_view(), name="get-user-rating"),
]
