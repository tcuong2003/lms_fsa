from django.urls import path
from django.contrib.auth import views as auth_views
from . import views  # Import your views from the main app

app_name = 'main'

urlpatterns = [
    # Your other URL patterns
    path('', views.home, name='home'),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]

