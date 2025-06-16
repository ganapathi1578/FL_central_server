from django.db import models
from django.utils import timezone
import string, random

def generate_new_id():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not HouseTunnel.objects.filter(house_id=code).exists():
            return code

class HouseTunnel(models.Model):
    house_id   = models.CharField(max_length=32, unique=True, default=generate_new_id)
    secret_key = models.CharField(max_length=64)            # a hashed token
    connected  = models.BooleanField(default=False)
    last_seen  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"House {self.house_id} - {'Connected' if self.connected else 'Disconnected'}"



class RegistrationToken(models.Model):
    token      = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False) 

    def is_valid(self): 
        return self.expires_at > timezone.now()

    def __str__(self):
        return f"Token: {self.token} (Expires: {self.expires_at})"  