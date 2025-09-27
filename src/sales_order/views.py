from django.views import generic
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from .models import SalesOrder, SalesOrderDetail
from partner_mst.models import Partner
from product_mst.models import Product
from .form import SalesOrderForm
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView
from .form import SalesOrderForm, SalesOrderDetailFormSet

DATA_COLUMNS = [
    'sales_order_no', 'partner', 'sales_order_date', 'delivery_date', 'remarks',
    'line_no', 'product', 'quantity', 'unit', 'unit_price',
    'tax_exempt', 'tax_rate', 'rounding_mode'
] + Common.COMMON_DATA_COLUMNS


# -----------------------------
# SalesOrder CRUD (一覧)
# -----------------------------

class SalesOrderListView(generic.ListView):
    """
    受注一覧画面
    - 検索条件（キーワード / 受注日）に対応
    - ページネーション対応
    """
    model = SalesOrder
    template_name = "sales_order/list.html"
    context_object_name = "sales_orders"
    paginate_by = 20

    def get_queryset(self):
        queryset = SalesOrder.objects.filter(
            is_deleted=False, tenant=self.request.user.tenant
        ).select_related("partner")

        search = self.request.GET.get("search")
        sales_order_date = self.request.GET.get("sales_order_date")

        if search:
            queryset = queryset.filter(
                Q(order_no__icontains=search) |
                Q(partner__partner_name__icontains=search)
            )

        if sales_order_date:
            queryset = queryset.filter(sales_order_date=sales_order_date)

        return queryset.order_by("sales_order_date", "sales_order_no")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("search") or ""
        context["sales_order_date"] = self.request.GET.get("sales_order_date") or ""
        context['partners'] = Partner.objects.filter(is_deleted=False, tenant=self.request.user.tenant).order_by('id')
        context = Common.set_pagination(context, self.request.GET.urlencode())
        return context


# -----------------------------
# SalesOrder CRUD (通常遷移)
# -----------------------------

class SalesOrderCreateView(generic.CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = "sales_order/edit.html"
    success_url = reverse_lazy("sales_order:list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = False
        if self.request.method == "POST":
            formset = SalesOrderDetailFormSet(self.request.POST)
        else:
            formset = SalesOrderDetailFormSet()

        # 明細が10件未満なら補充
        current_forms = len(formset.forms)
        if current_forms < 10:
            for i in range(10 - current_forms):
                formset.forms.append(formset.empty_form)

        context["formset"] = formset
        context["form_action"] = reverse("sales_order:create")
        context["modal_title"] = "受注新規登録"
        return context

    def form_valid(self, form):
        form.instance.create_user = self.request.user
        form.instance.update_user = self.request.user
        form.instance.tenant = self.request.user.tenant
        sales_order_message(self.request, "登録", form.instance.sales_order_no)
        return super().form_valid(form)


class SalesOrderUpdateView(generic.UpdateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = "sales_order/edit.html"
    success_url = reverse_lazy("sales_order:list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_update"] = True
        return context

    def form_valid(self, form):
        form.instance.update_user = self.request.user
        form.instance.tenant = self.request.user.tenant
        response = super().form_valid(form)
        sales_order_message(self.request, "更新", self.object.sales_order_no)
        return response


class SalesOrderDeleteView(generic.View):
    """
    受注削除（論理削除）
    """
    def post(self, request, *args, **kwargs):
        obj = SalesOrder.objects.get(pk=kwargs["pk"])
        obj.is_deleted = True
        obj.update_user = request.user
        obj.save()
        sales_order_message(request, "削除", obj.sales_order_no)
        return HttpResponseRedirect(reverse_lazy("sales_order:list"))


# -----------------------------
# SalesOrder CRUD (モーダル)
# -----------------------------

class SalesOrderCreateModalView(SalesOrderCreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = "sales_order/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = None
        context = self.get_context_data()
        html = render_to_string(self.template_name, context, request)
        return JsonResponse({"success": True, "html": html})

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.create_user = self.request.user
        self.object.update_user = self.request.user
        self.object.tenant = self.request.user.tenant
        self.object.save()

        formset = SalesOrderDetailFormSet(self.request.POST, instance=self.object)
        if formset.is_valid():
            formset.save()

        sales_order_message(self.request, "登録", self.object.sales_order_no)

        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        return super().form_valid(form)

    def form_invalid(self, form):
        formset = SalesOrderDetailFormSet(self.request.POST)
        # form_invalid時も補充
        if len(formset.forms) < 10:
            for i in range(10 - len(formset.forms)):
                formset.forms.append(formset.empty_form)
        context = self.get_context_data(form=form, formset=formset)
        html = render_to_string(self.template_name, context, self.request)
        return JsonResponse({"success": False, "html": html, "is_update": False})


class SalesOrderUpdateModalView(SalesOrderUpdateView):
    template_name = "sales_order/form.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = SalesOrderDetailFormSet(instance=self.object)

        # 明細が10件未満なら補充
        if len(formset.forms) < 10:
            for i in range(10 - len(formset.forms)):
                formset.forms.append(formset.empty_form)

        html = render_to_string(
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "form_action": reverse(
                    "sales_order:update", kwargs={"pk": self.object.pk}
                ),
                "modal_title": f"受注更新: {self.object.sales_order_no}",
                "is_update": True,
            },
            request,
        )
        return JsonResponse({"success": True, "html": html})

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.update_user = self.request.user
        self.object.tenant = self.request.user.tenant
        self.object.save()

        total_forms = int(self.request.POST.get("details-TOTAL_FORMS", 0))

        for i in range(total_forms):
            pk = self.request.POST.get(f"details-{i}-id")  # 既存行なら pk が入る
            product = self.request.POST.get(f"details-{i}-product")
            delete_flag = self.request.POST.get(f"details-{i}-DELETE")

            if delete_flag and pk:  # チェックあり & 既存行 → 物理削除
                SalesOrderDetail.objects.filter(pk=pk, sales_order=self.object).delete()
                continue

            if not product:  # 商品が空 → スキップ
                continue

            if pk:  # 既存行の更新
                detail = SalesOrderDetail.objects.get(pk=pk, sales_order=self.object)
                detail.product_id = product
                detail.quantity = self.request.POST.get(f"details-{i}-quantity") or 0
                detail.unit = self.request.POST.get(f"details-{i}-unit") or ""
                detail.unit_price = self.request.POST.get(f"details-{i}-unit_price") or 0
                detail.tax_rate = self.request.POST.get(f"details-{i}-tax_rate") or 10
                detail.is_tax_exempt = bool(self.request.POST.get(f"details-{i}-is_tax_exempt"))
                detail.rounding_method = self.request.POST.get(f"details-{i}-rounding_method") or "ROUND_DOWN"
                detail.update_user = self.request.user
                detail.save()
            else:  # 新規行の追加
                SalesOrderDetail.objects.create(
                    sales_order=self.object,
                    line_no=i,
                    product_id=product,
                    quantity=self.request.POST.get(f"details-{i}-quantity") or 0,
                    unit=self.request.POST.get(f"details-{i}-unit") or "",
                    unit_price=self.request.POST.get(f"details-{i}-unit_price") or 0,
                    tax_rate=self.request.POST.get(f"details-{i}-tax_rate") or 10,
                    is_tax_exempt=bool(self.request.POST.get(f"details-{i}-is_tax_exempt")),
                    rounding_method=self.request.POST.get(f"details-{i}-rounding_method") or "ROUND_DOWN",
                    tenant=self.request.user.tenant,
                    create_user=self.request.user,
                    update_user=self.request.user,
                )

        sales_order_message(self.request, "更新", self.object.sales_order_no)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        return super().form_valid(form)

    def form_invalid(self, form):
        formset = SalesOrderDetailFormSet(self.request.POST, instance=getattr(self, "object", None))
        if len(formset.forms) < 10:
            for i in range(10 - len(formset.forms)):
                formset.forms.append(formset.empty_form)

        obj = getattr(self, "object", None)
        modal_title = f"受注更新: {obj.sales_order_no}" if obj else "受注更新"
        html = render_to_string(
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "form_action": reverse(
                    "sales_order:update",
                    kwargs={"pk": obj.pk} if obj else {},
                ),
                "modal_title": modal_title,
            },
            self.request,
        )
        return JsonResponse({"success": False, "html": html})


class ExportExcel(ExcelExportBaseView):
    """
    SalesOrder + SalesOrderDetail のExcel出力
    """
    model_class = SalesOrder
    filename_prefix = 'sales_order'
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return search_order_data(request=request, query_set=qs)

    def row(self, rec):
        """受注1件につき明細行を展開"""
        rows = []
        details = rec.details.filter(is_deleted=False)
        if not details.exists():
            # 明細が無い場合でもヘッダだけ出す
            rows.append(get_order_detail_row(rec, None))
        else:
            for detail in details:
                rows.append(get_order_detail_row(rec, detail))
        return rows

# -----------------------------
# Export / Import
# -----------------------------

class ExportCSV(CSVExportBaseView):
    """
    SalesOrder + SalesOrderDetail のCSV出力
    """
    model_class = SalesOrder
    filename_prefix = 'sales_order'
    headers = DATA_COLUMNS

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return search_order_data(request=request, query_set=qs)

    def row(self, rec):
        rows = []
        details = rec.details.filter(is_deleted=False)
        if not details.exists():
            rows.append(get_order_detail_row(rec, None))
        else:
            for detail in details:
                rows.append(get_order_detail_row(rec, detail))
        return rows


class ImportCSV(CSVImportBaseView):
    """
    SalesOrder + SalesOrderDetail のCSVインポート
    """
    expected_headers = DATA_COLUMNS
    model_class = SalesOrder
    unique_field = 'sales_order_no'

    def validate_row(self, row, idx, existing, request):
        """1行ごとのバリデーション処理"""
        sales_order_no = row.get('sales_order_no')
        if not sales_order_no:
            return None, f'{idx}行目: sales_order_no が空です'

        # partner
        partner_name = row.get('partner')
        partner = None
        if partner_name:
            try:
                partner = Partner.objects.get(partner_name=partner_name, tenant=request.user.tenant)
            except Partner.DoesNotExist:
                return None, f'{idx}行目: partner "{partner_name}" が存在しません'

        # 日付
        sales_order_date, err = Common.parse_date(row.get('sales_order_date'), 'sales_order_date', idx)
        if err: return None, err
        delivery_date, err = Common.parse_date(row.get('delivery_date'), 'delivery_date', idx)
        if err: return None, err

        # product
        product_name = row.get('product')
        product = None
        if product_name:
            try:
                product = Product.objects.get(product_nm=product_name, tenant=request.user.tenant)
            except Product.DoesNotExist:
                return None, f'{idx}行目: product "{product_name}" が存在しません'

        # 数値変換
        try:
            quantity = int(row.get('quantity') or 0)
            unit_price = int(row.get('unit_price') or 0)
        except ValueError:
            return None, f'{idx}行目: 数値変換エラー(quantity/unit_price)'

        # SalesOrder オブジェクト
        sales_order, _ = SalesOrder.objects.get_or_create(
            sales_order_no=sales_order_no,
            tenant=request.user.tenant,
            defaults={
                'partner': partner,
                'sales_order_date': sales_order_date,
                'delivery_date': delivery_date,
                'remarks': row.get('remarks') or '',
                'create_user': request.user,
                'update_user': request.user,
            }
        )

        # SalesOrderDetail オブジェクト
        detail = SalesOrderDetail(
            sales_order=sales_order,
            line_no=row.get('line_no') or 1,
            product=product,
            quantity=quantity,
            unit=row.get('unit') or '',
            unit_price=unit_price,
            tax_exempt=row.get('tax_exempt') == '1',
            tax_rate=row.get('tax_rate') or 10,
            rounding_mode=row.get('rounding_mode') or 'ROUND_DOWN',
            create_user=request.user,
            update_user=request.user,
            tenant=request.user.tenant,
        )

        return detail, None


# -----------------------------
# 共通関数
# -----------------------------

def get_order_detail_row(sales_order, detail):
    """受注ヘッダ + 明細を1行化"""
    return [
        sales_order.sales_order_no,
        sales_order.partner.partner_name if sales_order.partner else '',
        sales_order.sales_order_date,
        sales_order.delivery_date,
        sales_order.remarks,
        detail.line_no if detail else '',
        detail.product.product_nm if detail and detail.product else '',
        detail.quantity if detail else '',
        detail.unit if detail else '',
        detail.unit_price if detail else '',
        '1' if (detail and detail.tax_exempt) else '0',
        detail.tax_rate if detail else '',
        detail.rounding_mode if detail else '',
    ] + Common.get_common_columns(rec=sales_order)


def search_order_data(request, query_set):
    """共通検索処理: 受注番号・取引先名"""
    keyword = request.GET.get('search') or ''
    if keyword:
        query_set = query_set.filter(
            Q(order_no__icontains=keyword) |
            Q(partner__partner_name__icontains=keyword)
        )
    return query_set

# -----------------------------
# 共通メッセージ関数
# -----------------------------

def sales_order_message(request, action, sales_order_no):
    messages.success(request, f"受注「{sales_order_no}」を{action}しました。")
