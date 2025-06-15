from django.urls import path, re_path
from .views import register_or_get_id, proxy_to_home
from .views import create_registration_token



urlpatterns = [
    path('api/register_or_get_id/', register_or_get_id),
    path("api/admin/create_registration_token/", create_registration_token, name="create_registration_token"),
]