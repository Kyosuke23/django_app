from django.urls import path
from . import views

app_name = 'register'

urlpatterns = [
    path('', views.RegisterUserView.as_view(), name='register_user'),
]
