from .forms import SignUpForm
from register.models import CustomUser
from django.views import generic
from django.urls import reverse_lazy
from django.contrib import messages

class RegisterUserView(generic.FormView):
    class Meta:
        model = CustomUser
    template_name = 'register/index.html'
    form_class = SignUpForm

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    
    def get_success_url(self):
        messages.success(self.request, '登録が完了しました')
        return reverse_lazy('dashboard:top')