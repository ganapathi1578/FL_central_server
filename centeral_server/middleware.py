# your_app/middleware.py

from django.utils import timezone

class ForceAsiaKolkataTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.activate('Asia/Kolkata')
        response = self.get_response(request)
        timezone.deactivate()
        return response