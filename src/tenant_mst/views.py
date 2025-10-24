from django.views import generic
from django.urls import  reverse
from .models import Tenant
from .form import TenantEditForm
from config.common import Common
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from config.base import ManagerOverMixin
from django.http import Http404


class TenantEditView(LoginRequiredMixin, ManagerOverMixin, generic.UpdateView):
    '''
    ログイン中のユーザーに紐づくテナント情報を編集する画面
    '''
    model = Tenant
    template_name = 'tenant_mst/edit.html'
    form_class = TenantEditForm
    context_object_name = 'tenant'

    def get_object(self, queryset=None):
        try:
            tenant = self.request.user.tenant
            if tenant is None or getattr(tenant, 'is_deleted', False):
                raise Http404('このテナントは既に削除されています。')
            return tenant
        except Tenant.DoesNotExist:
            raise Http404('このテナントは既に削除されています。')

    def get_success_url(self):
        messages.success(self.request, 'テナント情報を更新しました')
        return reverse('tenant_mst:edit')

    def form_valid(self, form):
        Common.save_data(selv=self, form=form, is_update=True)
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)
