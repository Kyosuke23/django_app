from django.shortcuts import redirect
from decimal import Decimal
from django.views import generic
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from .models import SalesOrder, SalesOrderDetail
from partner_mst.models import Partner
from product_mst.models import Product
from .form import SalesOrderForm, SalesOrderDetailFormSet
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView
from .services import *
from django.db import transaction
from .constants import *
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponseForbidden, Http404
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

DATA_COLUMNS = [
    'sales_order_no', 'partner', 'sales_order_date', 'remarks',
    'line_no', 'product', 'quantity', 'unit', 'master_unit_price', 'billing_unit_price',
    'is_tax_exempt', 'tax_rate', 'rounding_method'
] + Common.COMMON_DATA_COLUMNS


# -----------------------------
# 一覧表示
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
        context['status_choices'] = STATUS_CHOICES
        context = Common.set_pagination(context, self.request.GET.urlencode())
        return context


# -----------------------------
# 削除処理
# -----------------------------
class SalesOrderDeleteView(generic.View):
    '''
    受注削除（物理削除）
    '''
    def post(self, request, *args, **kwargs):
        obj = SalesOrder.objects.get(pk=kwargs['pk'])
        obj.delete()
        sales_order_message(request, '削除', obj.sales_order_no)
        return JsonResponse({'success': True})


# -----------------------------
# 登録処理
# -----------------------------
class SalesOrderCreateView(generic.CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales_order/form.html'
    success_url = reverse_lazy('sales_order:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = None
        form = SalesOrderForm(prefix='header', user=request.user)
        formset = fill_formset(get_sales_order_detail_formset())        
        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'formset': formset,
                'form_action': reverse('sales_order:create'),
                'modal_title': '受注新規登録',
                'is_update': False,
                'is_submittable': True,
            },
            request,
        )
        return JsonResponse({'success': True, 'html': html})

    # ----------------------------------------------------
    # POST（登録処理）
    # ----------------------------------------------------
    def post(self, request, *args, **kwargs):
        form = SalesOrderForm(request.POST, prefix='header')
        formset = SalesOrderDetailFormSet(request.POST, prefix='details')
        action_type = request.POST.get('action_type')

        # ▼ バリデーション
        if not (form.is_valid() and formset.is_valid()):
            html = render_to_string(
                self.template_name,
                {
                    'form': form,
                    'formset': formset,
                    'form_action': reverse('sales_order:create'),
                    'modal_title': '受注登録',
                    'is_update': False,
                },
                request,
            )
            return JsonResponse({'success': False, 'html': html})

        order = save_details(form=form, formset=formset, user=request.user, action_type=action_type)
        sales_order_message(request, '登録', order.sales_order_no)
        return JsonResponse({'success': True})

# -----------------------------
# 更新処理
# -----------------------------
class SalesOrderUpdateView(generic.UpdateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales_order/form.html'
    success_url = reverse_lazy('sales_order:list')

    # ----------------------------------------------------
    # GET（モーダル表示）
    # ----------------------------------------------------
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = SalesOrderForm(instance=self.object, prefix='header', user=request.user)
        formset = get_sales_order_detail_formset(instance=self.object)
        status_code = getattr(self.object, 'status_code', None)
        create_user = getattr(self.object, 'create_user', None)
        
        # ボタン操作可否判定
        is_submittable = get_submittable(user=request.user, form=form)
        
        # フィールドの一括制御（自分で作成した仮保存データ以外は編集不可）
        if not (status_code == STATUS_CODE_DRAFT and create_user == request.user):
            for field in form.fields.values():
                field.widget.attrs['disabled'] = True
            for f in formset.forms:
                for field in f.fields.values():
                    field.widget.attrs['disabled'] = True
                    
        # フィールド個別の操作制御
        form = apply_field_permissions(form=form, user=request.user)

        html = render_to_string(
            self.template_name,
            {
                'form': form,
                'formset': formset,
                'form_action': reverse('sales_order:update', kwargs={'pk': self.object.pk}),
                'modal_title': f'受注更新: {self.object.sales_order_no}',
                'is_update': True,
                'is_submittable': is_submittable, 
            },
            request,
        )
        return JsonResponse({'success': True, 'html': html})

    # ----------------------------------------------------
    # POST（更新処理）
    # ----------------------------------------------------
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action_type = request.POST.get('action_type')
        
        #  顧客による承認 / 却下
        if action_type in [STATUS_CODE_CONFIRMED, STATUS_CODE_REJECTED_OUT]:
            # 保存処理
            self.object.status_code = action_type
            self.object.save(update_fields=['status_code'])
            return redirect('sales_order:public_thanks')
        
        form = SalesOrderForm(request.POST, instance=self.object, prefix='header', action_type=action_type, user=request.user)
        formset = SalesOrderDetailFormSet(request.POST, instance=self.object, prefix='details')
        user = request.user
        
        # 再作成時は登録値を引き継いで受注ステータスを仮保存に戻す
        if action_type == STATUS_CODE_RETAKE:
            # 保存処理
            self.object.status_code = STATUS_CODE_DRAFT
            self.object.update_user = request.user
            self.object.save(update_fields=['status_code', 'update_user'])

            # 最新の状態を再描画
            form = SalesOrderForm(instance=self.object, prefix='header', user=request.user)
            formset = get_sales_order_detail_formset(instance=self.object)
            html = render_to_string(
                self.template_name,
                {
                    'form': form,
                    'formset': formset,
                    'form_action': reverse('sales_order:update', kwargs={'pk': self.object.pk}),
                    'modal_title': f'受注更新: {self.object.sales_order_no}',
                    'is_update': True,
                    'is_submittable': get_submittable(user=user, form=form),
                },
                request,
            )
            # モーダルを再描画
            return JsonResponse({'success': True, 'html': html})
        
        if action_type == STATUS_CODE_APPROVED:
            with transaction.atomic():
                # self.object.status_code = STATUS_CODE_APPROVED
                self.object.manager_comment = request.POST.get('header-manager_comment')
                self.object.update_user = user
                self.object.save(update_fields=['status_code', 'manager_comment', 'update_user'])

                partner = getattr(self.object, 'partner', None)
                if partner and partner.email:
                    try:
                        signer = TimestampSigner()
                        token = signer.sign_object({
                            'sales_order_id': self.object.id,
                            'partner_email': partner.email,
                        })
                        url = request.build_absolute_uri(reverse('sales_order:public_detail', kwargs={'token': token}))
                        print(url)
                        self.object.subject = f"【承認通知】受注番号 {self.object.sales_order_no}"
                        context = {
                            'partner': partner,
                            'order': self.object,
                            'url': url,
                            'now': timezone.now(),
                        }
                        message = render_to_string('sales_order/mails/mail_approved.txt', context)

                        # send_mail(
                        #     subject,
                        #     message.strip(),
                        #     getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
                        #     [partner.email],
                        #     fail_silently=False,
                        # )
                    except Exception as e:
                        sales_order_message(request, '承認', self.object.sales_order_no)
                        return JsonResponse({'success': False})

                sales_order_message(request, '承認', self.object.sales_order_no)
                return JsonResponse({'success': True})

        # 仮保存 or 提出時以外は受注ステータスの更新のみとする
        if action_type not in [STATUS_CODE_DRAFT, STATUS_CODE_SUBMITTED]:
            self.object.status_code = action_type
            self.object.update_user = request.user
            self.object.save(update_fields=['status_code', 'update_user'])
            sales_order_message(request, '更新', self.object.sales_order_no)
            return JsonResponse({'success': True})

        # バリデーション
        if not (form.is_valid() and formset.is_valid()):
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

        order = save_details(form=form, formset=formset, user=request.user, action_type=action_type)
        sales_order_message(request, '更新', order.sales_order_no)
        return JsonResponse({'success': True})
    
# -----------------------------
# 顧客回答後の画面表示
# -----------------------------
class SalesOrderPublicThanksView(generic.View):
    '''
    顧客回答後の完了画面
    '''
    template_name = "sales_order/public_thanks.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

# -----------------------------
# 商品情報の取得処理
# -----------------------------
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
        
# -----------------------------
# 取引先情報の取得処理
# -----------------------------
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
                'address2': partner.address2,
                'contact_name': partner.contact_name,
                'tel_number': partner.tel_number,
                'email': partner.email,
            })
        except Partner.DoesNotExist:
            return JsonResponse({'error': '取引先が見つかりません'}, status=404)

# -----------------------------
# 顧客向け回答画面表示
# -----------------------------   
class SalesOrderPublicDetailView(generic.View):
    '''
    顧客向けの公開受注詳細画面
    '''
    template_name = 'sales_order/public_detail.html'
    max_age_seconds = 60 * 60 * 24 * 3  # 3日間有効

    def get(self, request, token, *args, **kwargs):
        signer = TimestampSigner()

        # ------------------------------------------------------------
        # トークン検証
        # ------------------------------------------------------------
        try:
            data = signer.unsign_object(token, max_age=self.max_age_seconds)
            order_id = data.get('sales_order_id')
            partner_email = data.get('partner_email')
        except SignatureExpired:
            return HttpResponseForbidden("リンクの有効期限が切れています。")
        except BadSignature:
            return HttpResponseForbidden("リンクが不正または改ざんされています。")
        except Exception:
            return HttpResponseForbidden("リンクが無効です。")

        # ------------------------------------------------------------
        # 対象受注データの取得
        # ------------------------------------------------------------
        order = SalesOrder.objects.select_related('partner').filter(pk=order_id).first()
        if not order:
            raise Http404("受注データが見つかりません。")
        
        details = (SalesOrderDetail.objects.filter(sales_order=order).select_related('product').order_by('line_no'))

        # ------------------------------------------------------------
        # アクセス認可チェック（メールアドレス照合）
        # ------------------------------------------------------------
        if not order.partner or order.partner.email.lower() != partner_email.lower():
            return HttpResponseForbidden("アクセス権限がありません。")

        # ------------------------------------------------------------
        # 明細・金額集計
        # ------------------------------------------------------------
        # details = order.details.all() 
        subtotal = Decimal('0')
        tax_total = Decimal('0')

        for d in details:
            qty = d.quantity or Decimal('0')
            unit_price = d.master_unit_price or Decimal('0')
            d.amount_d = qty * unit_price

            subtotal += d.amount_d

            if getattr(d, 'tax_exempt', False):
                tax = Decimal('0')
            else:
                tax_rate = getattr(d, 'tax_rate', Decimal('0')) or Decimal('0')
                tax = d.amount_d * tax_rate
            tax_total += tax

        total = subtotal + tax_total

        # ------------------------------------------------------------
        # アクセスログ更新（任意）
        # ------------------------------------------------------------
        if hasattr(order, "public_accessed_at") and not order.public_accessed_at:
            order.public_accessed_at = timezone.now()
            order.save(update_fields=["public_accessed_at"])

        # ------------------------------------------------------------
        # コンテキストをテンプレートに渡す
        # ------------------------------------------------------------
        context = {
            "order": order,
            "details": details,
            "subtotal": subtotal,
            "tax_total": tax_total,
            "total": total,
            "is_public": True,
        }

        return render(request, self.template_name, context)

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
