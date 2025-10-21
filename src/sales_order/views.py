from django.shortcuts import redirect
from django.views import generic
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import SalesOrder, SalesOrderDetail, ApprovalToken
from partner_mst.models import Partner
from product_mst.models import Product
from register.models import CustomUser, UserGroup
from .form import SalesOrderSearchForm, SalesOrderForm, SalesOrderDetailFormSet
from config.common import Common
from config.base import CSVExportBaseView, CSVImportBaseView, ExcelExportBaseView, PrivilegeRequiredMixin
from .services import *
from django.db import transaction
from .constants import *
from django.utils.dateparse import parse_date
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
from django.contrib.auth.mixins import LoginRequiredMixin
import tempfile
import io, csv


# 出力カラム定義
HEADER_MAP = {
    '受注番号': 'sales_order_no',
    '取引先': 'partner',
    '受注日': 'sales_order_date',
    '受注担当者': 'assignee',
    '納入予定日': 'delivery_due_date',
    '納入場所': 'delivery_place',
    '備考': 'remarks',
    '見積書_承認者コメント': 'quotation_manager_comment',
    '見積書_顧客コメント': 'quotation_customer_comment',
    '注文書_承認者コメント': 'order_manager_comment',
    '注文書_顧客コメント': 'order_customer_comment',
    '端数処理方法': 'rounding_method',
    '行番号': 'line_no',
    '商品': 'product',
    '数量': 'quantity',
    '原単価': 'master_unit_price',
    '請求単価': 'billing_unit_price',
    '課税対象外': 'is_tax_exempt',
    '税率': 'tax_rate',
    '参照ユーザー': 'reference_users',
    '参照グループ': 'reference_groups',
}

# 出力ファイル名定義
FILENAME_PREFIX = 'sales_order'

#--------------------------
# 一覧表示
#--------------------------
class SalesOrderListView(generic.ListView):
    model = SalesOrder
    template_name = 'sales_order/list.html'
    context_object_name = 'sales_orders'
    paginate_by = settings.DEFAULT_PAGE_SIZE

    def get_queryset(self):
        req = self.request
        form = SalesOrderSearchForm(req.GET or None)

        # 基本フィルタ：対象テナントかつ削除フラグFalse
        queryset = SalesOrder.objects.filter(
            is_deleted=False
            , tenant=req.user.tenant
        ).select_related('partner')

        # 権限フィルタ：担当者が自分、または参照可能（ユーザーまたはグループ単位）
        queryset = queryset.filter(
            Q(assignee=req.user)
            | (
                (
                    Q(reference_users=req.user)
                    | Q(reference_groups__in=req.user.groups_custom.all())
                )
                & ~Q(status_code='DRAFT')
            )
        )

        # 検索フォームが有効な場合のみフィルタ
        if form.is_valid():
            queryset = filter_data(form.cleaned_data, queryset).distinct()

            # 並び替え処理
            sort = form.cleaned_data.get('sort')
            queryset = set_table_sort(queryset, sort)
        else:
            queryset = queryset.order_by('-sales_order_date')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = SalesOrderSearchForm(self.request.GET or None)
        context['form'] = form
        context['partners'] = Partner.objects.filter(is_deleted=False, tenant=self.request.user.tenant)
        context = Common.set_pagination(context, self.request.GET.urlencode())
        return context


#--------------------------
# 削除処理
#--------------------------
class SalesOrderDeleteView(generic.View):
    '''
    受注削除（物理削除）
    '''
    def post(self, request, *args, **kwargs):
        obj = SalesOrder.objects.get(pk=kwargs['pk'])
        obj.delete()
        sales_order_message(request, '削除', obj.sales_order_no)
        return JsonResponse({'success': True})


#--------------------------
# 登録処理
#--------------------------
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

    #-------------------------------------------------
    # POST（登録処理）
    #-------------------------------------------------
    def post(self, request, *args, **kwargs):
        form = SalesOrderForm(request.POST, prefix='header')
        formset = SalesOrderDetailFormSet(request.POST, prefix='details')
        action_type = request.POST.get('action_type')

        # バリデーション
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

#--------------------------
# 更新処理
#--------------------------
class SalesOrderUpdateView(generic.UpdateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'sales_order/form.html'
    success_url = reverse_lazy('sales_order:list')

    #-------------------------------------------------
    # GET（モーダル表示）
    #-------------------------------------------------
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = SalesOrderForm(instance=self.object, prefix='header', user=request.user)
        formset = get_sales_order_detail_formset(instance=self.object)
        status_code = getattr(self.object, 'status_code', None)
        assignee = getattr(self.object, 'assignee', None)

        # ボタン操作可否判定
        is_submittable = get_submittable(user=request.user, form=form)

        # フィールドの一括制御（自分で作成した仮保存データ以外は編集不可）
        if not (status_code == STATUS_CODE_DRAFT and assignee == request.user):
            for field in form.fields.values():
                widget_type = field.widget.__class__.__name__
                if widget_type in ['Select', 'SelectMultiple', 'CheckboxInput', 'RadioSelect']:
                    field.widget.attrs['disabled'] = True
                else:
                    field.widget.attrs['readonly'] = True
            for f in formset.forms:
                for field in f.fields.values():
                    widget_type = field.widget.__class__.__name__
                    if widget_type in ['Select', 'SelectMultiple', 'CheckboxInput', 'RadioSelect']:
                        field.widget.attrs['disabled'] = True
                    else:
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

    #-------------------------------------------------
    # POST（更新処理）
    #-------------------------------------------------
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

                    # 古いトークンを無効化
                    ApprovalToken.objects.filter(
                        sales_order=self.object,
                        partner_email=partner.email
                    ).update(used=True, used_at=timezone.now())

                    # 新しいトークンを登録
                    ApprovalToken.objects.create(
                        token=token,
                        sales_order=self.object,
                        partner_email=partner.email
                    )

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

                    # 古いトークンを無効化
                    ApprovalToken.objects.filter(
                        sales_order=self.object,
                        partner_email=partner.email
                    ).update(used=True, used_at=timezone.now())

                    # 新しいトークンを登録
                    ApprovalToken.objects.create(
                        token=token,
                        sales_order=self.object,
                        partner_email=partner.email
                    )

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
        顧客による見積書回答後の処理
        '''
        # 古いトークンを無効化
        ApprovalToken.objects.filter(
            token=request.POST.get('token')
        ).update(used=True, used_at=timezone.now())

        # データの更新
        action_type = request.POST.get('action_type')
        self.object.status_code = action_type
        self.object.quotation_customer_comment = request.POST.get('quotation_customer_comment', '').strip()
        self.object.save(update_fields=['status_code', 'quotation_customer_comment'])
        return redirect('sales_order:public_thanks')

    def handle_customer_reply_order(self, request):
        '''
        顧客による注文書回答後の処理
        '''
        # 古いトークンを無効化
        ApprovalToken.objects.filter(
            token=request.POST.get('token')
        ).update(used=True, used_at=timezone.now())

        # データの更新
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

        # 古いトークンを無効化
        ApprovalToken.objects.filter(
            sales_order=self.object,
            partner_email=partner.email
        ).update(used=True, used_at=timezone.now())

        # 新しいトークンを登録
        ApprovalToken.objects.create(
            token=token,
            sales_order=self.object,
            partner_email=partner.email
        )

        context = {
            'partner': partner,
            'order': self.object,
            'url': url,
            'now': timezone.now(),
        }
        message = render_to_string(template, context)
        print(f"[MAIL DEBUG]\n{message}\n{url}")  # TODO: logger.infoに変更予定

#--------------------------
# 顧客回答後の画面表示
#--------------------------
class SalesOrderPublicThanksView(generic.View):
    '''
    顧客回答後の完了画面
    '''
    template_name = "sales_order/public_thanks.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

#--------------------------
# 商品情報の取得処理
#--------------------------
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

#--------------------------
# 取引先情報の取得処理
#--------------------------
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

#--------------------------
# 見積書確認画面
#--------------------------
class SalesOrderPublicConfirmView(generic.View):
    '''
    見積書確認画面
    '''
    template_name = 'sales_order/public_confirm.html'
    max_age_seconds = 60 * 60 * 24 * 3  # 3日間有効

    def get(self, request, token, *args, **kwargs):
        signer = TimestampSigner()

        #---------------------------------------------------------
        # トークン検証
        #---------------------------------------------------------
        try:
            data = signer.unsign_object(token, max_age=self.max_age_seconds)
            order_id = data.get('sales_order_id')
            partner_email = data.get('partner_email')
        except SignatureExpired:
            return HttpResponseForbidden('リンクの有効期限が切れています。')
        except BadSignature:
            return HttpResponseForbidden('リンクが不正または改ざんされています。')
        except Exception:
            return HttpResponseForbidden('リンクが無効です。')

        # トークン存在＆未使用チェック
        token_obj = ApprovalToken.objects.filter(token=token).first()
        if not token_obj or token_obj.used:
            return HttpResponseForbidden('このリンクはすでに使用されています。')

        #---------------------------------------------------------
        # 対象受注データの取得
        #---------------------------------------------------------
        order = SalesOrder.objects.select_related('partner').filter(pk=order_id).first()
        if not order:
            raise Http404('受注データが見つかりません。')

        #---------------------------------------------------------
        # アクセス認可チェック（メールアドレス照合）
        #---------------------------------------------------------
        if not order.partner or order.partner.email.lower() != partner_email.lower():
            return HttpResponseForbidden('アクセス権限がありません。')

        #---------------------------------------------------------
        # アクセスログ更新（任意）
        #---------------------------------------------------------
        if hasattr(order, 'public_accessed_at') and not order.public_accessed_at:
            order.public_accessed_at = timezone.now()
            order.save(update_fields=['public_accessed_at'])

        #---------------------------------------------------------
        # コンテキストをテンプレートに渡す
        #---------------------------------------------------------
        context = {'order_id': order.pk, 'signed_token': token}

        return render(request, self.template_name, context)

#--------------------------
# 注文書確認画面
#--------------------------
class SalesOrderPublicContractView(generic.View):
    '''
    注文書確認画面
    '''
    template_name = 'sales_order/public_contract.html'
    max_age_seconds = 60 * 60 * 24 * 3  # 3日間有効

    def get(self, request, token, *args, **kwargs):
        signer = TimestampSigner()

        #---------------------------------------------------------
        # トークン検証
        #---------------------------------------------------------
        try:
            data = signer.unsign_object(token, max_age=self.max_age_seconds)
            order_id = data.get('sales_order_id')
            partner_email = data.get('partner_email')
        except SignatureExpired:
            return HttpResponseForbidden('リンクの有効期限が切れています。')
        except BadSignature:
            return HttpResponseForbidden('リンクが不正または改ざんされています。')
        except Exception:
            return HttpResponseForbidden('リンクが無効です。')

        # トークン存在＆未使用チェック
        token_obj = ApprovalToken.objects.filter(token=token).first()
        if not token_obj or token_obj.used:
            return HttpResponseForbidden('このリンクはすでに使用されています。')

        #---------------------------------------------------------
        # 対象受注データの取得
        #---------------------------------------------------------
        order = SalesOrder.objects.select_related('partner').filter(pk=order_id).first()
        if not order:
            raise Http404('受注データが見つかりません。')

        #---------------------------------------------------------
        # アクセス認可チェック（メールアドレス照合）
        #---------------------------------------------------------
        if not order.partner or order.partner.email.lower() != partner_email.lower():
            return HttpResponseForbidden('アクセス権限がありません。')

        #---------------------------------------------------------
        # アクセスログ更新（任意）
        #---------------------------------------------------------
        if hasattr(order, 'public_accessed_at') and not order.public_accessed_at:
            order.public_accessed_at = timezone.now()
            order.save(update_fields=['public_accessed_at'])

        #---------------------------------------------------------
        # コンテキストをテンプレートに渡す
        #---------------------------------------------------------
        context = {'order_id': order.pk, 'signed_token': token}

        return render(request, self.template_name, context)

#--------------------------
# Export / Import
#--------------------------
class ExportExcel(ExcelExportBaseView):
    model_class = SalesOrderDetail
    filename_prefix = 'sales_order'
    headers = HEADER_MAP

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
        return get_row(detail.sales_order, detail)


class ExportCSV(CSVExportBaseView):
    model_class = SalesOrderDetail
    filename_prefix = FILENAME_PREFIX
    headers = list(HEADER_MAP.keys())

    def get_queryset(self, request):
        req = self.request
        form = SalesOrderSearchForm(req.GET or None)

        # クエリセットを初期化（削除フラグ：False, 所属テナント限定）
        orders = SalesOrder.objects.filter(
            is_deleted=False,
            tenant=req.user.tenant
        ).select_related('partner')

        # フォームが有効なら検索条件を反映
        if form.is_valid():
            orders = filter_data(cleaned_data=form.cleaned_data, queryset=orders)

        # 並び替え
        sort = form.cleaned_data.get('sort') if form.is_valid() else ''
        orders = set_table_sort(queryset=orders, sort=sort)

        # 明細データ粒度で取得
        details = SalesOrderDetail.objects.filter(
            is_deleted=False,
            tenant=req.user.tenant,
            sales_order__in=orders
        ).select_related('sales_order', 'product')

        return details

    def row(self, detail):
        return get_row(header=detail.sales_order, detail=detail)


class ImportCSV(LoginRequiredMixin, CSVImportBaseView):
    '''
    受注データ（ヘッダ＋明細）CSVインポート
    ExportCSVの出力フォーマットに対応
    '''
    expected_headers = list(HEADER_MAP.keys())
    model_class = SalesOrderDetail
    HEADER_MAP = HEADER_MAP
    unique_field = None  # 重複チェックは受注明細行単位で実施

    def post(self, request, *args, **kwargs):
        '''
        unique_fieldがNoneの場合はexistingを空セットで初期化
        '''
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'error': 'ファイルが選択されていません'}, status=400)

        # Baseのpost()と同じ流れを維持
        decoded_file = io.TextIOWrapper(file.file, encoding='utf-8')
        reader = csv.DictReader(decoded_file)
        headers = reader.fieldnames

        # ヘッダチェック
        if headers != self.expected_headers:
            return JsonResponse({'error': 'CSVヘッダが一致しません。'}, status=400)

        existing = set()  # unique_fieldがNoneなので空集合にする

        # 通常のvalidate_row呼び出し
        objects = []
        errors = []
        for idx, row in enumerate(reader, start=2):
            obj, err = self.validate_row(row, idx, existing, request)
            if err:
                errors.append(err)
            elif obj:
                objects.append(obj)

        if errors:
            return JsonResponse({'error': '\n'.join(errors)}, status=400)

        self.model_class.objects.bulk_create(objects)
        return JsonResponse({'success': f'{len(objects)}件を登録しました。'})

    @transaction.atomic
    def validate_row(self, row, idx, existing, request):
        data = row.copy()
        tenant = request.user.tenant
        # ------------------------------------------------------
        # 受注担当者の解決
        # ------------------------------------------------------
        assignee = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'assignee'))
        try:
            cuser = CustomUser.objects.get(tenant=tenant, username=assignee)
        except CustomUser.DoesNotExist:
            return None, f'{idx}行目: ユーザー「{assignee}」が存在しません。'

        # ------------------------------------------------------
        # 取引先の解決
        # ------------------------------------------------------
        partner_name = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'partner'))
        try:
            partner = Partner.objects.get(tenant=tenant, partner_name=partner_name)
        except Partner.DoesNotExist:
            return None, f'{idx}行目: 取引先「{partner_name}」が存在しません。'

        # ------------------------------------------------------
        # 受注ヘッダ生成または再利用
        # ------------------------------------------------------
        sales_order_no = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'sales_order_no'))
        sales_order_date = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'sales_order_date'))
        delivery_due_date = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'delivery_due_date'))
        delivery_place = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'delivery_place'))
        quotation_manager_comment = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'quotation_manager_comment'))
        quotation_customer_comment = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'quotation_customer_comment'))
        order_manager_comment = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'order_manager_comment'))
        order_customer_comment = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'order_customer_comment'))
        remarks = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'remarks'))
        rounding_method = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'rounding_method'))
        header_data = {
            'tenant': tenant,
            'partner': partner,
            'sales_order_no': sales_order_no,
            'assignee': cuser,
            'sales_order_date': parse_date(sales_order_date),
            'delivery_place': delivery_place,
            'delivery_due_date': parse_date(delivery_due_date),
            'quotation_manager_comment': quotation_manager_comment or '',
            'quotation_customer_comment': quotation_customer_comment or '',
            'order_manager_comment': order_manager_comment or '',
            'order_customer_comment': order_customer_comment or '',
            'remarks': remarks or '',
            'rounding_method': get_rounding_code(label=rounding_method),
        }

        header_obj, created = SalesOrder.objects.get_or_create(
            tenant=tenant,
            sales_order_no=sales_order_no,
            defaults={
                **header_data,
                'create_user': request.user,
                'update_user': request.user,
            }
        )

        if not created:
            # 既存の受注を更新
            for k, v in header_data.items():
                setattr(header_obj, k, v)
            header_obj.update_user = request.user
            header_obj.save()

        # ------------------------------------------------------
        # 参照ユーザー / グループ設定
        # ------------------------------------------------------
        ref_users_text = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'reference_users'))
        ref_groups_text = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'reference_groups'))
        if ref_users_text:
            user_names = [name.strip() for name in ref_users_text.split(',') if name.strip()]
            users = CustomUser.objects.filter(username__in=user_names, is_deleted=False)
            header_obj.reference_users.set(users)

        if ref_groups_text:
            group_names = [name.strip() for name in ref_groups_text.split(',') if name.strip()]
            groups = UserGroup.objects.filter(group_name__in=group_names)
            header_obj.reference_groups.set(groups)

        # ------------------------------------------------------
        # 商品（Product）の解決
        # ------------------------------------------------------
        product_name = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'product'))
        try:
            product = Product.objects.get(tenant=tenant, product_name=product_name)
        except Product.DoesNotExist:
            return None, f'{idx}行目: 商品「{product_name}」が存在しません。'

        # ------------------------------------------------------
        # SalesOrderDetail（明細）の作成
        # ------------------------------------------------------
        line_no = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'line_no'))
        quantity = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'quantity'))
        master_unit_price = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'master_unit_price'))
        billing_unit_price = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'billing_unit_price'))
        is_tax_exempt = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'is_tax_exempt'))
        tax_rate = data.get(next(k for k, v in self.HEADER_MAP.items() if v == 'tax_rate'))
        detail = SalesOrderDetail(
            sales_order=header_obj,
            line_no=line_no or 0,
            product=product,
            quantity=quantity or 0,
            master_unit_price=master_unit_price or 0,
            billing_unit_price=billing_unit_price or 0,
            is_tax_exempt=(is_tax_exempt in ['非課税', 'True', '1']),
            tax_rate=tax_rate or 0,
            tenant=tenant,
            create_user=request.user,
            update_user=request.user,
        )

        return detail, None


class OrderSheetPdfView(generic.DetailView):
    '''
    注文書の発行処理
    '''
    model = SalesOrder
    template_name = 'sales_order/pdf/order_sheet.html'
    context_object_name = 'order'

    #----------------------------------------
    # GET処理
    #----------------------------------------
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_pdf()

    #----------------------------------------
    # POST処理
    #----------------------------------------
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_pdf()


    #----------------------------------------
    # PDF生成処理
    #----------------------------------------
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

        filename = f'注文書_{self.object.sales_order_no}.pdf'
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

    #----------------------------------------
    # GET処理
    #----------------------------------------
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_pdf()

    #----------------------------------------
    # POST処理
    #----------------------------------------
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_pdf()


    #----------------------------------------
    # PDF生成処理
    #----------------------------------------
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


def filter_data(cleaned_data, queryset):
    '''検索条件反映'''
    keyword = cleaned_data.get('search_keyword', '').strip()
    if keyword:
        queryset = queryset.filter(
            Q(sales_order_no__icontains=keyword)
            | Q(partner__partner_name__icontains=keyword)
            | Q(delivery_place__icontains=keyword)
            | Q(status_code__icontains=keyword)
        )

    # 個別フィールド
    if cleaned_data.get('search_sales_order_no'):
        queryset = queryset.filter(sales_order_no__icontains=cleaned_data['search_sales_order_no'])

    if cleaned_data.get('search_partner'):
        queryset = queryset.filter(partner=cleaned_data['search_partner'])

    if cleaned_data.get('search_status_code'):
        queryset = queryset.filter(status_code=cleaned_data['search_status_code'])

    if cleaned_data.get('search_sales_order_date'):
        queryset = queryset.filter(sales_order_date=cleaned_data['search_sales_order_date'])

    if cleaned_data.get('search_delivery_due_date'):
        queryset = queryset.filter(delivery_due_date=cleaned_data['search_delivery_due_date'])

    if cleaned_data.get('search_delivery_place'):
        queryset = queryset.filter(delivery_place__icontains=cleaned_data['search_delivery_place'])

    return queryset


def set_table_sort(queryset, sort):
    '''並び替え処理'''
    valid_sorts = [
        'sales_order_no', '-sales_order_no',
        'sales_order_date', '-sales_order_date',
        'delivery_due_date', '-delivery_due_date',
        'total_amount', '-total_amount'
    ]
    if sort in valid_sorts:
        return queryset.order_by(sort)
    return queryset.order_by('-sales_order_date')