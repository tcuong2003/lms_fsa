from django.urls import path
from . import views

app_name = 'home'
urlpatterns = [
    path('', views.get_home, name='get_home'),
   
]
