import hashlib, uuid, json
from django.utils import timezone
from rest_framework.permissions import AllowAny
from django.http import JsonResponse, StreamingHttpResponse
from rest_framework.decorators import api_view
from .models import HouseTunnel, RegistrationToken
from .utils import send_and_wait
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def register_or_get_id(request):
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)


    try:
        data = json.loads(request.body)
        token = data.get("token")
    except Exception:
        return JsonResponse({"error":"invalid JSON"}, status=400)

    rt = RegistrationToken.objects.filter(
        token=token, expires_at__gt=timezone.now()
    ).first()

    if not rt.is_valid:
        return JsonResponse({"error":"invalid or expired registration token"}, status=403)
    
    # check if token is already used
    if not rt or rt.is_used:
        return JsonResponse({"error": "invalid or expired registration token"}, status=403)
    
    # Marking as used
    rt.is_used = True
    rt.save()
    key = hashlib.sha256(token.encode()).hexdigest()
    tunnel, created = HouseTunnel.objects.get_or_create(secret_key=key)

    return JsonResponse({
        "house_id":   tunnel.house_id,
        "secret_key": tunnel.secret_key
    })


async def proxy_to_home(request, house_id, path):
    # 1) Look up the tunnel
    tunnel = await HouseTunnel.objects.filter(house_id=house_id, connected=True).afirst()
    if not tunnel:
        return JsonResponse({'error': 'home offline'}, status=503)

    # 2) Build the frame
    frame = {
        'action': 'proxy_request',
        'id': str(uuid.uuid4()),
        'method': request.method,
        'path': path,
        'headers': dict(request.headers),
        'body': (await request.body).decode('utf-8', 'ignore'),
    }

    # 3) Send and wait (your send_and_wait util)
    from .utils import send_and_wait
    response = await send_and_wait(house_id, frame)

    # 4) Return streaming response
    return StreamingHttpResponse(
        response['body'],
        status=response['status'],
        headers=response['headers']
    )

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import RegistrationToken
import secrets

@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_registration_token(request):
    ttl = int(request.data.get("ttl", 10))
    token = secrets.token_urlsafe(32)
    expires = timezone.now() + timedelta(minutes=ttl)
    RegistrationToken.objects.create(token=token, expires_at=expires)
    return Response({"token": token, "expires_at": expires})