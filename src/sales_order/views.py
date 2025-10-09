from django.shortcuts import redirect
from django.views import generic
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import SalesOrder, SalesOrderDetail
from partner_mst.models import Partner
from product_mst.models import Product
from .form import SalesOrderForm, SalesOrderDetailFormSet
from config.common import Common
from config.base import CSVExportBaseView, ExcelExportBaseView
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
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from weasyprint import HTML
import tempfile


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
        
        # フィールド個別の操作制御
        form = apply_field_permissions(form=form, user=request.user)
     
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
                field.widget.attrs['readonly'] = True
            for f in formset.forms:
                for field in f.fields.values():
                    field.widget.attrs['readonly'] = True
                    
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
        
        # アクション別ハンドラをディスパッチ
        handler_map = {
            ACTION_CODE_OUTPUT_QUOTATION_IN: self.handle_output_quotation_in,
            ACTION_CODE_OUTPUT_QUOTATION_OUT: self.handle_output_quotation_out,
            ACTION_CODE_OUTPUT_ORDER_IN: self.handle_output_order_in,
            ACTION_CODE_OUTPUT_ORDER_OUT: self.handle_output_order_out,
            STATUS_CODE_QUOTATION_RETAKE: self.handle_quotation_retake,
            STATUS_CODE_ORDER_RETAKE: self.handle_order_retake,
            STATUS_CODE_DRAFT: self.handle_default,
            STATUS_CODE_QUOTATION_SUBMITTED: self.handle_default,
            STATUS_CODE_QUOTATION_APPROVED: self.handle_quotation_approved,
            STATUS_CODE_QUOTATION_REJECTED_IN: self.handle_quotation_rejected_in,
            STATUS_CODE_QUOTATION_CONFIRMED: self.handle_customer_reply_quotation,
            STATUS_CODE_QUOTATION_REJECTED_OUT: self.handle_customer_reply_quotation,
            STATUS_CODE_ORDER_SUBMITTED: self.handle_order_submitted,
            STATUS_CODE_ORDER_APPROVED: self.handle_order_approved,
            STATUS_CODE_ORDER_CONFIRMED: self.handle_customer_reply_order,
            STATUS_CODE_ORDER_REJECTED_IN: self.handle_order_rejected_in,
            STATUS_CODE_ORDER_REJECTED_OUT: self.handle_customer_reply_order,
        }

        handler = handler_map.get(action_type, self.handle_default)
        return handler(request)
        
    # ============================================================
    # 個別ハンドラ群
    # ============================================================
    def handle_quotation_retake(self, request):
        '''
        見積書再作成
        - ステータスを仮保存に戻して再描画
        '''
        # データ更新
        self.object.status_code = STATUS_CODE_DRAFT
        self.object.update_user = request.user
        self.object.save(update_fields=['status_code', 'update_user'])
        
        # モーダルを再描画
        return self.render_form(request)
    
    def handle_order_retake(self, request):
        '''
        注文書再作成
        - ステータスを見積書：顧客承認済みに戻して再描画
        '''
        # データ更新
        self.object.status_code = STATUS_CODE_QUOTATION_CONFIRMED
        self.object.update_user = request.user
        self.object.save(update_fields=['status_code', 'update_user'])
        
        # モーダルを再描画
        return self.render_form(request)

    def handle_quotation_approved(self, request):
        '''
        見積承認（社内）
        - 承認者コメントを保存し、顧客にメール通知
        - 次は顧客による承認
        '''
        with transaction.atomic():
            # データ更新
            self.object.status_code = STATUS_CODE_QUOTATION_APPROVED
            self.object.quotation_manager_comment = request.POST.get('header-quotation_manager_comment', '').strip()
            self.object.update_user = request.user
            self.object.save(update_fields=['status_code', 'quotation_manager_comment', 'update_user'])

            partner = getattr(self.object, 'partner', None)
            if partner and partner.email:
                try:
                    signer = TimestampSigner()
                    token = signer.sign_object({
                        'sales_order_id': self.object.id,
                        'partner_email': partner.email,
                    })
                    url = request.build_absolute_uri(reverse('sales_order:public_confirm', kwargs={'token': token}))
                    self.object.subject = f"【見積書確認依頼】受注番号 {self.object.sales_order_no}"
                    context = {
                        'partner': partner,
                        'order': self.object,
                        'url': url,
                        'now': timezone.now(),
                    }
                    message = render_to_string('sales_order/mails/mail_approved.txt', context)
                    print(message)
                    print(url)

                    # send_mail(
                    #     subject,
                    #     message.strip(),
                    #     getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
                    #     [partner.email],
                    #     fail_silently=False,
                    # )
                except Exception as e:
                    # 処理後メッセージ
                    sales_order_message(request, '承認', self.object.sales_order_no)
                    
                    # モーダルを閉じて一覧画面へ
                    return JsonResponse({'success': False})

        # 処理後メッセージ
        sales_order_message(request, '承認', self.object.sales_order_no)
        
        # モーダルを閉じて一覧画面へ
        return JsonResponse({'success': True})

    def handle_quotation_rejected_in(self, request):
        '''
        見積却下（社内）
        - 承認者コメントを保存し、ステータス更新
        '''
        with transaction.atomic():
            # データ更新
            self.object.status_code = STATUS_CODE_QUOTATION_REJECTED_IN
            self.object.quotation_manager_comment = request.POST.get('header-quotation_manager_comment', '').strip()
            self.object.update_user = request.user
            self.object.save(update_fields=['status_code', 'quotation_manager_comment', 'update_user'])

        # 処理後メッセージ
        sales_order_message(request, '却下', self.object.sales_order_no)
        
        # モーダルを閉じて一覧画面へ
        return JsonResponse({'success': True})

    def handle_order_submitted(self, request):
        '''
        注文書提出
        - 次は承認者による承認
        '''
        self.object.status_code = STATUS_CODE_ORDER_SUBMITTED
        self.object.delivery_due_date = request.POST.get('header-delivery_due_date')
        self.object.delivery_place = request.POST.get('header-delivery_place', '').strip()
        self.object.update_user = request.user
        self.object.save(update_fields=['status_code', 'delivery_due_date', 'delivery_place', 'update_user'])
        sales_order_message(request, '更新', self.object.sales_order_no)
        return JsonResponse({'success': True})

    def handle_order_approved(self, request):
        '''
        注文書承認
        - 顧客にメール通知
        - 次は顧客による正式承認待ち
        '''
        with transaction.atomic():
            self.object.status_code = STATUS_CODE_ORDER_APPROVED
            self.object.order_manager_comment = request.POST.get('header-order_manager_comment', '').strip()
            self.object.update_user = request.user
            self.object.save(update_fields=['status_code', 'order_manager_comment', 'update_user'])

            partner = getattr(self.object, 'partner', None)
            if partner and partner.email:
                try:
                    signer = TimestampSigner()
                    token = signer.sign_object({
                        'sales_order_id': self.object.id,
                        'partner_email': partner.email,
                    })
                    url = request.build_absolute_uri(reverse('sales_order:public_contract', kwargs={'token': token}))
                    self.object.subject = f"【発注書確認依頼】受注番号 {self.object.sales_order_no}"
                    context = { 
                        'partner': partner,
                        'order': self.object,
                        'url': url,
                        'now': timezone.now(),
                    }
                    message = render_to_string('sales_order/mails/order_approved.txt', context)
                    print(message)
                    print(url)
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

    def handle_output_quotation_in(self, request):
        '''
        見積書確認（社内）
        - 社内からの帳票発行
        - 納入予定日・納入場所の更新のみ許可
        '''
        if getattr(self.object, 'create_user', None) == request.user:
            self.object.delivery_due_date = request.POST.get('header-delivery_due_date')
            self.object.delivery_place = request.POST.get('header-delivery_place', '').strip()
            self.object.update_user = request.user
            self.object.save(update_fields=['delivery_due_date', 'delivery_place', 'update_user'])
        return JsonResponse({'success': True})
    

    def handle_output_quotation_out(self, request):
        '''
        見積書確認（顧客）
        - 顧客による帳票発行
        - サーバサイドでは特に何もしない
        '''
        return JsonResponse({'success': True})

    def handle_output_order_in(self, request):
        '''
        注文書確認（社内）
        - 社内からの帳票発行
        - 納入予定日・納入場所の更新のみ許可
        '''

        if getattr(self.object, 'create_user', None) == request.user:
            self.object.delivery_due_date = request.POST.get('header-delivery_due_date')
            self.object.delivery_place = request.POST.get('header-delivery_place', '').strip()
            self.object.update_user = request.user
            self.object.save(update_fields=['delivery_due_date', 'delivery_place', 'update_user'])
        return JsonResponse({'success': True})

    def handle_output_order_out(self, request):
        '''
        注文書確認（顧客）
        - 顧客による帳票発行
        - サーバサイドでは特に何もしない
        '''
        return JsonResponse({'success': True})
    
    def handle_order_rejected_in(self, request):
        '''
        注文書却下（社内）
        - 承認者コメントを保存し、ステータス更新
        '''
        with transaction.atomic():
            # データ更新
            self.object.status_code = STATUS_CODE_ORDER_REJECTED_IN
            self.object.order_manager_comment = request.POST.get('header-order_manager_comment', '').strip()
            self.object.update_user = request.user
            self.object.save(update_fields=['status_code', 'order_manager_comment', 'update_user'])

        # 処理後メッセージ
        sales_order_message(request, '却下', self.object.sales_order_no)
        
        # モーダルを閉じて一覧画面へ
        return JsonResponse({'success': True})

    def handle_customer_reply_quotation(self, request):
        '''
        顧客による見積書回答後ののページ表示
        '''
        action_type = request.POST.get('action_type')
        self.object.status_code = action_type
        self.object.quotation_customer_comment = request.POST.get('quotation_customer_comment', '').strip()
        self.object.save(update_fields=['status_code', 'quotation_customer_comment'])
        return redirect('sales_order:public_thanks')
    
    def handle_customer_reply_order(self, request):
        '''
        顧客による注文書回答後ののページ表示
        '''
        action_type = request.POST.get('action_type')
        self.object.status_code = action_type
        self.object.order_customer_comment = request.POST.get('order_customer_comment', '').strip()
        self.object.save(update_fields=['status_code', 'order_customer_comment'])
        return redirect('sales_order:public_thanks')

    def handle_default(self, request):
        '''
        仮保存・見積書提出
        '''
        action_type = request.POST.get('action_type')
        form = SalesOrderForm(request.POST, instance=self.object, prefix='header', action_type=action_type, user=request.user)
        formset = SalesOrderDetailFormSet(request.POST, instance=self.object, prefix='details')
        is_submittable = get_submittable(user=request.user, form=form)
        form = apply_field_permissions(form=form, user=request.user)

        # バリデーション
        if not (form.is_valid() and formset.is_valid()):
            html = render_to_string(
                self.template_name,
                {
                    'form': form,
                    'formset': formset,
                    'form_action': reverse('sales_order:update', kwargs={'pk': self.object.pk}),
                    'is_update': True,
                    'is_submittable': is_submittable,
                    'modal_title': f'受注更新: {self.object.sales_order_no}',
                },
                request,
            )
            return JsonResponse({'success': False, 'html': html})

        order = save_details(form=form, formset=formset, user=request.user, action_type=action_type)
        sales_order_message(request, '更新', order.sales_order_no)
        return JsonResponse({'success': True})

    # ============================================================
    # 共通ユーティリティ
    # ============================================================

    def disable_fields(self, form, formset):
        '''フォームとフォームセットの全フィールドを非活性化'''
        for field in form.fields.values():
            field.widget.attrs['readonly'] = True
        for f in formset.forms:
            for field in f.fields.values():
                field.widget.attrs['readonly'] = True

    def render_form(self, request):
        '''最新状態のフォーム再描画'''
        # フォームの情報を取得
        form = SalesOrderForm(instance=self.object, prefix='header', user=request.user)
        formset = get_sales_order_detail_formset(instance=self.object)
        
        # ボタン操作の活性制御
        is_submittable = get_submittable(user=request.user, form=form)
        
        # コメント欄の活性制御
        form.fields['quotation_manager_comment'].widget.attrs['readonly'] = True
        form.fields['order_manager_comment'].widget.attrs['readonly'] = True
        form.fields['quotation_customer_comment'].widget.attrs['readonly'] = True
        form.fields['order_customer_comment'].widget.attrs['readonly'] = True
        
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

    def send_approval_mail(self, request, partner, template, route):
        '''承認通知メール送信'''
        signer = TimestampSigner()
        token = signer.sign_object({
            'sales_order_id': self.object.id,
            'partner_email': partner.email,
        })
        url = request.build_absolute_uri(reverse(route, kwargs={'token': token}))
        print('=====================')
        print(url)
        print('=====================')
        context = {
            'partner': partner,
            'order': self.object,
            'url': url,
            'now': timezone.now(),
        }
        message = render_to_string(template, context)
        print(f"[MAIL DEBUG]\n{message}\n{url}")  # TODO: logger.infoに変更予定
    
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
# 見積書確認画面
# -----------------------------   
class SalesOrderPublicConfirmView(generic.View):
    '''
    見積書確認画面
    '''
    template_name = 'sales_order/public_confirm.html'
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
        
        # ------------------------------------------------------------
        # アクセス認可チェック（メールアドレス照合）
        # ------------------------------------------------------------
        if not order.partner or order.partner.email.lower() != partner_email.lower():
            return HttpResponseForbidden("アクセス権限がありません。")
        
        # ------------------------------------------------------------
        # アクセスログ更新（任意）
        # ------------------------------------------------------------
        if hasattr(order, "public_accessed_at") and not order.public_accessed_at:
            order.public_accessed_at = timezone.now()
            order.save(update_fields=["public_accessed_at"])

        # ------------------------------------------------------------
        # コンテキストをテンプレートに渡す
        # ------------------------------------------------------------
        context = {'order_id': order.pk,}
        
        return render(request, self.template_name, context)

# -----------------------------
# 注文書確認画面
# -----------------------------   
class SalesOrderPublicContractView(generic.View):
    '''
    注文書確認画面
    '''
    template_name = 'sales_order/public_contract.html'
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
        
        # ------------------------------------------------------------
        # アクセス認可チェック（メールアドレス照合）
        # ------------------------------------------------------------
        if not order.partner or order.partner.email.lower() != partner_email.lower():
            return HttpResponseForbidden("アクセス権限がありません。")
        
        # ------------------------------------------------------------
        # アクセスログ更新（任意）
        # ------------------------------------------------------------
        if hasattr(order, "public_accessed_at") and not order.public_accessed_at:
            order.public_accessed_at = timezone.now()
            order.save(update_fields=["public_accessed_at"])

        # ------------------------------------------------------------
        # コンテキストをテンプレートに渡す
        # ------------------------------------------------------------
        context = {'order_id': order.pk,}
        
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

class OrderSheetPdfView(generic.DetailView):
    '''
    注文書の発行処理
    '''
    model = SalesOrder
    template_name = 'sales_order/pdf/order_sheet.html'
    context_object_name = 'order'

    # -------------------------------------------
    # GET処理
    # -------------------------------------------
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_pdf()

    # -------------------------------------------
    # POST処理
    # -------------------------------------------    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_pdf()


    # -------------------------------------------
    # PDF生成処理
    # -------------------------------------------
    def render_pdf(self):
        context = {
            'order': self.object,
            'details': self.object.details.all(),
            'partner': self.object.partner,
            # 'company_name': self.request.user.tenant.tenant_name,
            'title': f"注文書（{self.object.sales_order_no}）",
        }

        html_string = render_to_string(self.template_name, context)
        html = HTML(string=html_string, base_url=self.request.build_absolute_uri('/'))

        with tempfile.NamedTemporaryFile(delete=True) as output:
            html.write_pdf(target=output.name)
            output.seek(0)
            pdf_data = output.read()

        filename = f"注文書_{self.object.sales_order_no}.pdf"
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    
class QuatationSheetPdfView(generic.DetailView):
    '''
    見積書の発行処理
    '''
    model = SalesOrder
    template_name = 'sales_order/pdf/quotation_sheet.html'
    context_object_name = 'order'

    # -------------------------------------------
    # GET処理
    # -------------------------------------------
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_pdf()

    # -------------------------------------------
    # POST処理
    # -------------------------------------------    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_pdf()


    # -------------------------------------------
    # PDF生成処理
    # -------------------------------------------
    def render_pdf(self):
        context = {
            'order': self.object,
            'details': self.object.details.all(),
            'partner': self.object.partner,
            # 'company_name': self.request.user.tenant.tenant_name,
            'title': f"見積書（{self.object.sales_order_no}）",
        }

        html_string = render_to_string(self.template_name, context)
        html = HTML(string=html_string, base_url=self.request.build_absolute_uri('/'))

        with tempfile.NamedTemporaryFile(delete=True) as output:
            html.write_pdf(target=output.name)
            output.seek(0)
            pdf_data = output.read()

        filename = f"見積書_{self.object.sales_order_no}.pdf"
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response