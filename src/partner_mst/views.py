from django.views import generic
from django.urls import reverse_lazy, reverse
from .models import Partner
from .form import PartnerForm
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.shortcuts import redirect
from sales_order.models import SalesOrder
from django.db.models.deletion import ProtectedError

# CSV/Excel の共通出力カラム定義
DATA_COLUMNS = [
    'partner_name', 'contact_name',
    'email', 'tel_number', 'postal_code', 'state',
    'city', 'address', 'address2'
] + Common.COMMON_DATA_COLUMNS

FILENAME_PREFIX = 'partner_mst'

# -----------------------------
# Partner CRUD
# -----------------------------

class PartnerListView(generic.ListView):
    model = Partner
    template_name = 'partner_mst/list.html'
    context_object_name = 'partners'
    paginate_by = 20

    def get_queryset(self):
        query_set = Partner.objects.filter(is_deleted=False, tenant=self.request.user.tenant)
        query_set = filter_data(request=self.request, query_set=query_set)
        return query_set.order_by('partner_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_keyword'] = self.request.GET.get('search_keyword') or ''
        context = Common.set_pagination(context, self.request.GET.urlencode())
        return context


class PartnerCreateView(generic.CreateView):
    '''
    取引先登録
    - GET: 部分テンプレートを返す（Ajax）
    - POST: Ajaxで登録処理
    '''
    model = Partner
    form_class = PartnerForm
    template_name = 'partner_mst/form.html'

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'form_action': reverse('partner_mst:create'),
                'modal_title': '取引先新規登録',
            },
            request
        )
        return JsonResponse({'success': True, 'html': html})

    def form_valid(self, form):
        Common.save_data(selv=self, form=form, is_update=False)
        partner_message(self.request, '登録', self.object.partner_name)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(
                self.template_name,
                {
                    'form': form,
                    'form_action': reverse('partner_mst:create'),
                    'modal_title': '取引先新規登録',
                },
                self.request
            )
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


class PartnerUpdateView(generic.UpdateView):
    '''
    取引先更新
    - GET: 部分テンプレートを返す（Ajax）
    - POST: Ajaxで更新処理
    '''
    model = Partner
    form_class = PartnerForm
    template_name = 'partner_mst/form.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'form_action': reverse('partner_mst:update', kwargs={'pk': self.object.pk}),
                'modal_title': f'取引先更新: {self.object.partner_name}',
            },
            request
        )
        return JsonResponse({'success': True, 'html': html})

    def form_valid(self, form):
        Common.save_data(selv=self, form=form, is_update=True)
        partner_message(self.request, '更新', self.object.partner_name)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            obj = getattr(self, 'object', None)
            modal_title = f'取引先更新: {obj.partner_name}' if obj else '取引先更新'
            html = render_to_string(
                self.template_name,
                {
                    'form': form,
                    'form_action': reverse(
                        'partner_mst:update',
                        kwargs={'pk': obj.pk} if obj else {}
                    ),
                    'modal_title': modal_title,
                },
                self.request
            )
            return JsonResponse({'success': False, 'html': html})
        return super().form_invalid(form)


class PartnerDeleteView(generic.View):
    model = Partner
    template_name = 'partner_mst/confirm_delete.html'
    success_url = reverse_lazy('partner_mst:list')

    def post(self, request, *args, **kwargs):
        obj = Partner.objects.get(pk=kwargs['pk'])
        obj.is_deleted = True
        obj.update_user = request.user
        obj.save()
        partner_message(request, '削除', obj.partner_name)
        return HttpResponseRedirect(reverse_lazy('partner_mst:list'))


class PartnerBulkDeleteView(generic.View):
    ''' 一括削除処理 '''
    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('ids')
        if ids:
            try:
                Partner.objects.filter(id__in=ids).delete()
                return JsonResponse({'message': f'{len(ids)}件削除しました'})
            except ProtectedError as e:
                # 削除できなかった取引先を抽出（SalesOrderDetail → Partnerを辿る）
                protected_partners = set()
                for obj in e.protected_objects:
                    if isinstance(obj, SalesOrder):
                        protected_partners.add(obj.partner)

                details = ', '.join(
                    f"{p.partner_name}" for p in protected_partners
                )
                return JsonResponse({
                    'error': '使用中の取引先は削除できません',
                    'details': details or str
                }, status=400)
        else:
            messages.warning(request, '削除対象が選択されていません')
        return redirect('partner_mst:list')

# -----------------------------
# Export / Import
# -----------------------------

class ExportExcel(ExcelExportBaseView):
    model_class = Partner
    filename_prefix = FILENAME_PREFIX
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return filter_data(request=request, query_set=qs)

    def row(self, rec):
        return get_row(rec)


class ExportCSV(CSVExportBaseView):
    model_class = Partner
    filename_prefix = FILENAME_PREFIX
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return filter_data(request=request, query_set=qs)

    def row(self, rec):
        return get_row(rec)


class ImportCSV(CSVImportBaseView):
    expected_headers = DATA_COLUMNS
    model_class = Partner
    unique_field = FILENAME_PREFIX

    def validate_row(self, row, idx, existing, request):
        partner_name = row.get('partner_name')
        if not partner_name:
            return None, f'{idx}行目: partner_name が空です'
        if partner_name in existing:
            return None, f'{idx}行目: partner_name "{partner_name}" は既に存在します'

        obj = Partner(
            partner_name=partner_name,
            contact_name=row.get('contact_name'),
            email=row.get('email'),
            tel_number=row.get('tel_number'),
            postal_code=row.get('postal_code'),
            state=row.get('state'),
            city=row.get('city'),
            address=row.get('address'),
            address2=row.get('address2'),
            create_user=request.user,
            update_user=request.user,
            tenant=request.user.tenant
        )
        return obj, None


# -----------------------------
# 共通関数
# -----------------------------

def get_row(rec):
    return [
        rec.partner_name,
        rec.contact_name,
        rec.email,
        rec.tel_number,
        rec.postal_code,
        rec.state,
        rec.city,
        rec.address,
        rec.address2
    ] + Common.get_common_columns(rec=rec)


def filter_data(request, query_set):
    keyword = request.GET.get('search_keyword') or ''
    if keyword:
        query_set = query_set.filter(
            Q(partner_name__icontains=keyword) |
            Q(contact_name__icontains=keyword) |
            Q(email__icontains=keyword)
        )
    return query_set


def partner_message(request, action, partner_name):
    messages.success(request, f'取引先「{partner_name}」を{action}しました。')
