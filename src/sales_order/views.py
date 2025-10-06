from django.forms import inlineformset_factory
from django.views import generic
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from .models import SalesOrder, SalesOrderDetail
from partner_mst.models import Partner
from product_mst.models import Product
from .form import SalesOrderForm, SalesOrderDetailForm, SalesOrderDetailFormSet
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView
from .utils import fill_formset
from django.db import transaction

DATA_COLUMNS = [
    'sales_order_no', 'partner', 'sales_order_date', 'remarks',
    'line_no', 'product', 'quantity', 'unit', 'master_unit_price', 'billing_unit_price',
    'is_tax_exempt', 'tax_rate', 'rounding_method'
] + Common.COMMON_DATA_COLUMNS


# -----------------------------
# SalesOrder CRUD (一覧)
# -----------------------------

class SalesOrderListView(generic.ListView):
    '''
    受注一覧画面
    - 検索条件（キーワード / 受注日）に対応
    - ページネーション対応
    '''
    model = SalesOrder
    template_name = 'sales_order/list.html'
    context_object_name = 'sales_orders'
    paginate_by = 20

    def get_queryset(self):
        queryset = SalesOrder.objects.filter(
            is_deleted=False, tenant=self.request.user.tenant
        ).select_related('partner')

        # 検索フォームの入力値を取得
        sales_order_no = self.request.GET.get('search_sales_order_no')
        status_code = self.request.GET.get('search_status_code')
        partner = self.request.GET.get('search_partner')

        # フィルタ適用
        if sales_order_no:
            queryset = queryset.filter(Q(sales_order_no__icontains=sales_order_no))
        if status_code:
            queryset = queryset.filter(status_code=status_code)
        if partner:
            queryset = queryset.filter(partner=partner)

        # クエリセット返却
        return queryset.order_by('sales_order_date', 'sales_order_no')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_sales_order_no'] = self.request.GET.get('search_sales_order_no') or ''
        context['search_status_code'] = self.request.GET.get('search_status_code') or ''
        context['search_partner'] = self.request.GET.get('search_partner') or ''
        context['status_choices'] = SalesOrder.STATUS_CHOICES
        context['partners'] = Partner.objects.filter(
            is_deleted=False, tenant=self.request.user.tenant
        ).order_by('id')
        context = Common.set_pagination(context, self.request.GET.urlencode())
        return context


# -----------------------------
# SalesOrder CRUD
# -----------------------------
class SalesOrderCreateView(generic.CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales_order/edit.html'
    success_url = reverse_lazy('sales_order:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = False
        formset = SalesOrderDetailFormSet(self.request.POST or None)
        context['formset'] = fill_formset(formset)
        context['form_action'] = reverse('sales_order:create')
        context['modal_title'] = '受注新規登録'
        return context

    def form_valid(self, form):
        form.instance.create_user = self.request.user
        form.instance.update_user = self.request.user
        form.instance.tenant = self.request.user.tenant
        sales_order_message(self.request, '登録', form.instance.sales_order_no)
        return super().form_valid(form)


class SalesOrderUpdateView(generic.UpdateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales_order/edit.html'
    success_url = reverse_lazy('sales_order:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        form.instance.update_user = self.request.user
        form.instance.tenant = self.request.user.tenant
        response = super().form_valid(form)
        sales_order_message(self.request, '更新', self.object.sales_order_no)
        return response


class SalesOrderDeleteView(generic.View):
    '''
    受注削除（論理削除）
    '''
    def post(self, request, *args, **kwargs):
        obj = SalesOrder.objects.get(pk=kwargs['pk'])
        obj.is_deleted = True
        obj.update_user = request.user
        obj.save()
        sales_order_message(request, '削除', obj.sales_order_no)
        return HttpResponseRedirect(reverse_lazy('sales_order:list'))


# -----------------------------
# SalesOrder CRUD (モーダル)
# -----------------------------
class SalesOrderCreateModalView(SalesOrderCreateView):
    template_name = 'sales_order/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        formset = fill_formset(get_sales_order_detail_formset())

        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'formset': formset,
                'form_action': reverse('sales_order:create'),
                'modal_title': '受注新規登録',
                'is_update': False,
            },
            request,
        )
        return JsonResponse({'success': True, 'html': html})

    # ----------------------------------------------------
    # POST（登録処理）
    # ----------------------------------------------------
    def post(self, request, *args, **kwargs):
        self.object = None
        form = SalesOrderForm(request.POST, prefix='header', user=request.user)
        formset = SalesOrderDetailFormSet(request.POST, prefix='details')

        # バリデーション
        if not (form.is_valid() and formset.is_valid()):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                html = render_to_string(
                    self.template_name,
                    {
                        'form': form,
                        'formset': formset,
                        'form_action': reverse('sales_order:create'),
                        'modal_title': '受注新規登録',
                        'is_update': False,
                    },
                    request,
                )
                return JsonResponse({'success': False, 'html': html})
            return super().form_invalid(form)

        # ヘッダ保存
        self.object = form.save(commit=False)
        self.object.create_user = request.user
        self.object.update_user = request.user
        self.object.tenant = request.user.tenant
        self.object.save()

        # 明細保存
        n = 1
        for f in formset.forms:
            if not f.cleaned_data:
                continue
            if f.cleaned_data.get('DELETE'):
                continue
            if not f.cleaned_data.get('product'):
                continue

            d = f.save(commit=False)
            d.sales_order = self.object
            d.tenant = request.user.tenant

            # 商品マスタ単価をコピー
            if d.product_id and not d.master_unit_price:
                d.master_unit_price = d.product.unit_price

            d.line_no = n
            n += 1
            d.save()

        sales_order_message(self.request, '登録', self.object.sales_order_no)
        return JsonResponse({'success': True})


class SalesOrderUpdateModalView(SalesOrderUpdateView):
    template_name = 'sales_order/form.html'

    # ----------------------------------------------------
    # GET（モーダル表示）
    # ----------------------------------------------------
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # prefix を統一（POST と同じ）
        form = SalesOrderForm(instance=self.object, prefix='header')
        formset = get_sales_order_detail_formset(instance=self.object)

        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'formset': formset,
                'form_action': reverse('sales_order:update', kwargs={'pk': self.object.pk}),
                'modal_title': f'受注更新: {self.object.sales_order_no}',
                'is_update': True,
            },
            request,
        )
        return JsonResponse({'success': True, 'html': html})

    # ----------------------------------------------------
    # POST（更新処理）
    # ----------------------------------------------------
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        form = SalesOrderForm(request.POST, instance=self.object, prefix='header')
        formset = SalesOrderDetailFormSet(request.POST, instance=self.object, prefix='details')

        # バリデーション
        if not (form.is_valid() and formset.is_valid()):
            import pprint
            print("---- [DEBUG] form.errors ----")
            pprint.pprint(form.errors)

            print("---- [DEBUG] form.non_field_errors ----")
            pprint.pprint(form.non_field_errors())

            print("---- [DEBUG] formset.non_form_errors ----")
            pprint.pprint(formset.non_form_errors())

            print("---- [DEBUG] formset.errors ----")
            for i, e in enumerate(formset.errors):
                print(f"  formset[{i}]: {e}")

            # optional: 明細データも確認
            for i, f in enumerate(formset.forms):
                print(f"  [{i}] cleaned_data (raw): {getattr(f, 'cleaned_data', None)}")

            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                obj = getattr(self, 'object', None)
                modal_title = f'受注更新: {obj.sales_order_no}' if obj else '受注更新'
                html = render_to_string(
                    self.template_name,
                    {
                        'form': form,
                        'formset': formset,
                        'form_action': reverse(
                            'sales_order:update',
                            kwargs={'pk': obj.pk} if obj else {}
                        ),
                        'modal_title': modal_title,
                    },
                    self.request
                )
                return JsonResponse({'success': False, 'html': html})
            return super().form_invalid(form)

        with transaction.atomic():
            # --- ヘッダ保存 ---

            self.object = form.save(commit=False)
            self.object.update_user = request.user
            self.object.tenant = request.user.tenant
            self.object.save()

            # --- 明細全削除 ---
            SalesOrderDetail.objects.filter(sales_order=self.object).delete()

            # --- 明細再登録 ---
            line_no = 1
            for f in formset.forms:
                if not f.cleaned_data:
                    continue
                if not f.cleaned_data.get('product'):
                    continue

                d = f.save(commit=False)
                d.sales_order = self.object
                d.tenant = request.user.tenant
                d.line_no = line_no

                # 単価未設定なら商品マスタからコピー
                if d.product_id and not d.master_unit_price:
                    d.master_unit_price = d.product.unit_price

                d.save()
                line_no += 1

        sales_order_message(request, '更新', self.object.sales_order_no)
        return JsonResponse({'success': True})


class ProductInfoView(generic.View):
    def get(self, request, *args, **kwargs):
        product_id = request.GET.get('product_id')
        try:
            product = Product.objects.get(pk=product_id, tenant=request.user.tenant)
            return JsonResponse({
                'unit': product.unit,
                'unit_price': product.unit_price,
            })
        except Product.DoesNotExist:
            return JsonResponse({'error': '商品が見つかりません'}, status=404)
        
class PartnerInfoView(generic.View):
    def get(self, request, *args, **kwargs):
        partner_id = request.GET.get('partner_id')
        try:
            partner = Partner.objects.get(pk=partner_id, tenant=request.user.tenant)
            return JsonResponse({
                'postal_code': partner.postal_code,
                'state': partner.state,
                'city': partner.city,
                'address': partner.address,
                'address': partner.address2,
                'contact_name': partner.contact_name,
                'tel_number': partner.tel_number,
                'email': partner.email,
            })
        except Partner.DoesNotExist:
            return JsonResponse({'error': '取引先が見つかりません'}, status=404)

# -----------------------------
# Export / Import
# -----------------------------
class ExportExcel(ExcelExportBaseView):
    model_class = SalesOrderDetail
    filename_prefix = 'sales_order'
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('sales_order', 'product', 'sales_order__partner') \
                 .filter(
                     is_deleted=False,
                     sales_order__in=search_order_data(
                         request=request,
                         query_set=SalesOrder.objects.all()
                     )
                 ) \
                 .order_by('sales_order__sales_order_no', 'line_no')

    def row(self, detail):
        return get_order_detail_row(detail.sales_order, detail)


class ExportCSV(CSVExportBaseView):
    model_class = SalesOrderDetail
    filename_prefix = 'sales_order'
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('sales_order', 'product', 'sales_order__partner') \
                 .filter(
                     is_deleted=False,
                     sales_order__in=search_order_data(
                         request=request,
                         query_set=SalesOrder.objects.all()
                     )
                 ) \
                 .order_by('sales_order__sales_order_no', 'line_no')
                 

    def row(self, detail):
        # 明細1件を1行に整形
        return [Common.format_for_csv(v) for v in get_order_detail_row(detail.sales_order, detail)]


class ImportCSV(CSVImportBaseView):
    expected_headers = DATA_COLUMNS
    model_class = SalesOrder
    unique_field = 'sales_order_no'

    def validate_row(self, row, idx, existing, request):
        pass
        

# -----------------------------
# 共通関数
# -----------------------------
def get_order_detail_row(sales_order, detail):
    return [
        sales_order.sales_order_no,
        sales_order.partner.partner_name if sales_order.partner else '',
        sales_order.sales_order_date,
        sales_order.remarks,
        detail.line_no if detail else '',
        detail.product.product_name if detail and detail.product else '',
        detail.quantity if detail else '',
        detail.unit if detail else '',
        detail.billing_unit_price if detail else '',
        '1' if (detail and detail.is_tax_exempt) else '0',
        detail.tax_rate if detail else '',
        detail.rounding_method if detail else '',
    ] + Common.get_common_columns(rec=sales_order)


def search_order_data(request, query_set):
    keyword = request.GET.get('search_sales_order_no') or ''
    if keyword:
        query_set = query_set.filter(
            Q(order_no__icontains=keyword) |
            Q(partner__partner_name__icontains=keyword)
        )
    return query_set


def sales_order_message(request, action, sales_order_no):
    messages.success(request, f'受注「{sales_order_no}」を{action}しました。')

# 動的にextraを決める関数
def get_sales_order_detail_formset(instance=None, data=None):
    count = instance.details.count() if instance else 0

    if count < 10:
        extra = 10 - count  # 常に10行表示
    else:
        extra = 1  # 現行数 +1

    DynamicFormSet = inlineformset_factory(
        SalesOrder,
        SalesOrderDetail,
        form=SalesOrderDetailForm,
        extra=extra,
        can_delete=True
    )

    return DynamicFormSet(data=data, instance=instance)