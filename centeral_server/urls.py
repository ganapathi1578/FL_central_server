from django.contrib import admin
from django.urls import path, include
from tunnel.views import proxy_to_home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("tunnel/", include("tunnel.urls")),   # REST endpoints
    # proxy endpoint:
    path("homes/<str:house_id>/<path:path>",proxy_to_home),
]
