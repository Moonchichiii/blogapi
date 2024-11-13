from django.urls import path
from .views import CreateOrUpdateRatingView, GetPostRatingView

urlpatterns = [
    path("ratings/", CreateOrUpdateRatingView.as_view(), name="create-update-rating"),
    path("ratings/<int:post_id>/", GetPostRatingView.as_view(), name="get-post-rating"),
]