from django.contrib import admin
from django.urls import path, include, re_path
from tunnel.views import proxy_to_home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("tunnel/", include("tunnel.urls")),   # REST endpoints
    # proxy endpoint:
    re_path(r'^homes/(?P<house_id>[A-Z0-9]{6})/(?P<path>.*)$', proxy_to_home),
    
]
