from django.contrib import admin
from django.urls import path, include
from two_factor.urls import urlpatterns as tf_urls
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(tf_urls)),
    path("api/accounts/", include("accounts.urls")),
    path("api/", include("profiles.urls")),
    path("api/", include("posts.urls")),
    path("api/", include("comments.urls")),
    path("api/", include("ratings.urls")),
    path("api/", include("tags.urls")),
    path("api/followers/", include("followers.urls")),
    path("api/", include("notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
