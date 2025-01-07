from django.urls import path
from . import views
from .views import Login, Logout 

app_name = 'login'

urlpatterns = [
    path('', views.Login.as_view(), name='login'),
]