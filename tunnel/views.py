import hashlib, uuid, json
from django.utils import timezone
from rest_framework.permissions import AllowAny
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse, HttpResponseRedirect
from rest_framework.decorators import api_view
from .models import HouseTunnel, RegistrationToken
from .utils import send_and_wait
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import RegistrationToken
import secrets
import base64


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

"""
async def proxy_to_home(request, house_id, path):
    print("entered view proxy")
    # 1) Find the connected tunnel record
    tunnel = await sync_to_async(
        HouseTunnel.objects.filter(house_id=house_id, connected=True).first
    )()
    if not tunnel:
        return JsonResponse({'error': 'home offline'}, status=503)

    # 2) Prepare headers for the proxied request
    headers = dict(request.headers)
    # forward cookies from browser to home server
    if request.COOKIES:
        headers['Cookie'] = "; ".join(f"{k}={v}" for k, v in request.COOKIES.items())

    # 3) Build the proxy frame
    frame = {
        'action':  'proxy_request',
        'id':      str(uuid.uuid4()),
        'method':  request.method,
        'path':    path,
        'headers': headers,
        'body':    request.body.decode('utf-8', 'ignore'),
    }

    # 4) Send over WebSocket and await the home server’s response
    response = await send_and_wait(house_id, frame)
    status       = response.get('status', 200)
    resp_headers = response.get('headers', {})
    content_type = resp_headers.get('Content-Type', '')
    raw_body     = response.get('body', b'')

    # 5) Handle HTTP redirects (3xx)
    if 300 <= status < 400 and 'Location' in resp_headers:
        loc = resp_headers['Location']
        # rewrite to proxy path
        if loc.startswith('/'):
            loc = f"/homes/{house_id}{loc}"
        redirect = HttpResponseRedirect(loc)
        # relay Set-Cookie if present
        if 'Set-Cookie' in resp_headers:
            redirect['Set-Cookie'] = resp_headers['Set-Cookie']
        return redirect

    # 6) Handle HTML content
    if 'text/html' in content_type:
        # decode bytes → str
        body_str = raw_body.decode('utf-8', 'ignore') if isinstance(raw_body, (bytes, bytearray)) else raw_body
        soup = BeautifulSoup(body_str, 'html.parser')
        prefix = f"/homes/{house_id}"

        # rewrite all relevant tags
        for tag in soup.find_all(["a", "form", "script", "link"]):
            if tag.name == "form" and tag.has_attr("action"):
                attr = "action"
            elif tag.has_attr("href"):
                attr = "href"
            elif tag.has_attr("src"):
                attr = "src"
            else:
                continue

            val = tag[attr]
            if val.startswith("/"):
                tag[attr] = prefix + val

        new_body = str(soup).encode('utf-8')
        resp = HttpResponse(new_body, status=status, content_type=content_type)

    else:
        # 7) Handle JSON/error responses
        if content_type.startswith("application/json") or status >= 400:
            body_bytes = raw_body if isinstance(raw_body, (bytes, bytearray)) else raw_body.encode('utf-8')
            resp = HttpResponse(
                body_bytes,
                status=status,
                content_type=content_type or "application/json"
            )
        # 8) Binary/media: stream directly
        else:
            body_bytes = raw_body if isinstance(raw_body, (bytes, bytearray)) else raw_body.encode('utf-8')
            resp = StreamingHttpResponse(body_bytes, status=status)
            # copy through other headers (but not Set-Cookie or Content-Length)
            for k, v in resp_headers.items():
                if k.lower() not in ('set-cookie', 'content-length'):
                    resp[k] = v

    # 9) Finally, relay any Set-Cookie
    if 'Set-Cookie' in resp_headers:
        resp['Set-Cookie'] = resp_headers['Set-Cookie']

    return resp
"""
async def proxy_to_home(request, house_id, path):
    print("entered view proxy")

    # 1) Find the connected tunnel record
    tunnel = await sync_to_async(
        HouseTunnel.objects.filter(house_id=house_id, connected=True).first
    )()
    if not tunnel:
        return JsonResponse({'error': 'home offline'}, status=503)

    # 2) Prepare headers for the proxied request
    headers = dict(request.headers)
    if request.COOKIES:
        headers['Cookie'] = "; ".join(f"{k}={v}" for k, v in request.COOKIES.items())
    if 'Range' in request.headers:
        headers['Range'] = request.headers['Range']

    # 3) Build the proxy request frame
    frame = {
        'action':  'proxy_request',
        'id':      str(uuid.uuid4()),
        'method':  request.method,
        'path':    path,
        'headers': headers,
        'body':    request.body.decode('utf-8', 'ignore'),
    }

    # 4) Send to the home server and await response
    response = await send_and_wait(house_id, frame)
    status       = response.get('status', 200)
    resp_headers = response.get('headers', {})
    is_base64    = response.get('is_base64', False)
    raw_body     = response.get('body', b'')

    # 5) Handle HTTP redirects (3xx)
    if 300 <= status < 400 and 'Location' in resp_headers:
        loc = resp_headers['Location']
        if loc.startswith('/'):
            loc = f"/homes/{house_id}{loc}"
        redirect = HttpResponseRedirect(loc)
        if 'Set-Cookie' in resp_headers:
            redirect['Set-Cookie'] = resp_headers['Set-Cookie']
        return redirect

    # 6) Decode the body
    if is_base64:
        body_bytes = base64.b64decode(raw_body)
    else:
        body_bytes = raw_body.encode('utf-8') if isinstance(raw_body, str) else raw_body

    # 7) Return appropriate response type
    content_type = resp_headers.get('Content-Type', '')

    # JSON or plain text: buffer fully
    if content_type.startswith('application/json') or content_type.startswith('text/'):
        return HttpResponse(
            body_bytes,
            status=status,
            content_type=content_type or 'application/json'
        )

    # Binary/media content: stream
    resp = StreamingHttpResponse(body_bytes, status=status, content_type=content_type)
    for k, v in resp_headers.items():
        if k.lower() == 'set-cookie':
            resp[k] = v
    return resp




@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_registration_token(request):
    ttl = int(request.data.get("ttl", 10))
    token = secrets.token_urlsafe(32)
    expires = timezone.now() + timedelta(minutes=ttl)
    RegistrationToken.objects.create(token=token, expires_at=expires)
    return Response({"token": token, "expires_at": expires})