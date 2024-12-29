from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.views import generic
from django.urls import reverse_lazy

class Login(LoginView):
    fields = '__all__'
    template_name = 'login/login.html'

    def get_success_url(self):
        return reverse_lazy('dashboard:top')

class Logout(LogoutView):
    template_name = 'login/login.html'
