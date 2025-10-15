from django.views import generic
from django.urls import  reverse
from .models import Tenant
from .form import TenantEditForm
from config.common import Common
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages


class TenantEditView(generic.UpdateView):
    '''
    ログイン中のユーザーに紐づくテナント情報を編集する画面
    '''
    model = Tenant
    template_name = 'tenant_mst/edit.html'
    form_class = TenantEditForm
    context_object_name = 'tenant'

    def get_object(self, queryset=None):
        return self.request.user.tenant

    def get_success_url(self):
        messages.success(self.request, 'テナント情報を更新しました')
        return reverse('tenant_mst:edit')

    def form_valid(self, form):
        Common.save_data(selv=self, form=form, is_update=True)
        return super().form_valid(form)
    
    def form_invalid(self, form):
        pass
