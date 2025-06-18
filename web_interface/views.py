from django.shortcuts import render, redirect
from tunnel.models import RegistrationToken, User, HouseTunnel
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils import timezone
import secrets

def home(request):
    """
    Render the home page of the home management software.
    """
    return render(request, 'home.html')

def login_view(request):
    """
    Render the login page.
    """
    if request.method == 'POST':
        userid = request.POST.get('userid')
        password = request.POST.get('password')
        try:
            user = User.objects.get(userid=userid)
            if user.check_password(password):
                request.session['user_id'] = user.id
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid password!')
        except User.DoesNotExist:
            messages.error(request, 'User ID does not exist!')
    return render(request, 'login.html')

def register_view(request):
    """
    Render the registration page.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        userid = request.POST.get('userid')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'register.html')
        if User.objects.filter(userid=userid).exists():
            messages.error(request, 'User ID already exists!')
            return render(request, 'register.html')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return render(request, 'register.html')
        user = User(email=email, userid=userid)
        user.set_password(password)
        user.save()
        messages.success(request, 'Registration successful! Please login.')
        return redirect('login')
    return render(request, 'register.html')



def dashboard(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = User.objects.get(id=user_id)
    tokens = RegistrationToken.objects.filter(user=user)
    housetunnels = HouseTunnel.objects.filter(user=user)
    if request.method == 'POST':
        if 'create_token' in request.POST:
            ttl = int(request.POST.get('ttl', 10))
            token = secrets.token_urlsafe(32)
            expires = timezone.now() + timedelta(minutes=ttl)
            RegistrationToken.objects.create(token=token, expires_at=expires, user=user)
            messages.success(request, f'New registration token generated. It will expire in {ttl} minutes.')
            return redirect('dashboard')
    return render(request, 'dashboard.html', {
        'user': user,
        'tokens': tokens,
        'housetunnels': housetunnels,
    })
