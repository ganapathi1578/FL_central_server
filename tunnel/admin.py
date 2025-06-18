from django.contrib import admin
from .models import RegistrationToken,  HouseTunnel, User

@admin.register(RegistrationToken)
class RegistrationTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "expires_at")
    readonly_fields = ("token",)

    def save_model(self, request, obj, form, change):
        if not change:
            # obj is new → generate a random token
            import secrets
            obj.token = secrets.token_urlsafe(32)
        super().save_model(request, obj, form, change)

@admin.register(HouseTunnel)
class HouseTunnelAdmin(admin.ModelAdmin):
    list_display = ("house_id", "connected", "last_seen")
    readonly_fields = ("house_id", "last_seen")
    fields = ("house_id", "secret_key", "connected", "last_seen")

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('userid', 'email', 'password')