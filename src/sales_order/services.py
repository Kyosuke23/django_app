from .constants import *
from .form import  SalesOrderDetailForm
from .models import SalesOrder, SalesOrderDetail
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.forms import inlineformset_factory

def fill_formset(formset, min_forms=10):
    '''FormSetを指定数まで補充する'''
    while len(formset.forms) < min_forms:
        formset.forms.append(formset.empty_form)
    return formset

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
    ]

def search_order_data(request, query_set):
    keyword = request.GET.get('search_sales_order_no') or ''
    if keyword:
        query_set = query_set.filter(
            Q(sales_order_no__icontains=keyword) |
            Q(partner__partner_name__icontains=keyword)
        )
    return query_set

def sales_order_message(request, action, sales_order_no):
    '''CRUD後のメッセージ表示'''
    messages.success(request, f'受注「{sales_order_no}」を{action}しました。')

def get_sales_order_detail_formset(instance=None, data=None):
    '''受注明細行の初期表示行数を算出'''
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

def get_submittable(user, form):
    '''ログインユーザーと受注ステータスから、ボタン操作可否を判定する'''
    # ログインユーザー
    login_user = user
    
    # 受注データ情報
    instance = getattr(form, 'instance', None)
    status_code = getattr(instance, 'status_code', None)  # 受注ステータス
    create_user = instance.create_user  # 作成者（担当者）
    reference_users_manager = getattr(instance, 'reference_users', None)
    reference_users = reference_users_manager.all() if reference_users_manager else []  # 参照ユーザー
    
    # 新規作成：作成者未設定は新規作成とし、可
    if not create_user:
        return True
    # 仮作成 = 担当者のみ可
    if status_code == STATUS_CODE_DRAFT:
        return create_user == login_user
    # 見積書：提出済 = 承認依頼先の人のみ可
    if status_code == STATUS_CODE_QUOTATION_SUBMITTED:
        return login_user in reference_users
    # 見積書：社内却下 = 担当者のみ可
    if status_code == STATUS_CODE_QUOTATION_REJECTED_IN:
        return create_user == login_user
    # 見積書：顧客却下 = 担当者のみ可
    if status_code == STATUS_CODE_QUOTATION_REJECTED_OUT:
        return create_user == login_user
    # 見積書：顧客承諾 = 担当者のみ可
    if status_code == STATUS_CODE_QUOTATION_CONFIRMED:
        return create_user == login_user
    # 注文書：提出済 = 承認依頼先の人のみ可
    if status_code == STATUS_CODE_ORDER_SUBMITTED:
        return login_user in reference_users
    # 注文書：社内却下 = 担当者のみ可
    if status_code == STATUS_CODE_ORDER_REJECTED_IN:
        return create_user == login_user
    # 注文書：顧客却下 = 担当者のみ可
    if status_code == STATUS_CODE_ORDER_REJECTED_OUT:
        return create_user == login_user
    # キャンセル：担当者のみ可
    if status_code == STATUS_CODE_CANCELED:
        return create_user == login_user
    return False

def save_details(form, formset, user, action_type):
    '''登録・更新時の共通処理'''
    with transaction.atomic():
        order = form.save(commit=False)
        order.status_code = action_type
        order.quotation_manager_comment = form.data.get('header-quotation_manager_comment', '').strip()
        order.quotation_customer_comment = form.data.get('header-quotation_customer_comment', '').strip()
        order.order_manager_comment = form.data.get('header-order_manager_comment', '').strip()
        order.order_customer_comment = form.data.get('header-order_customer_comment', '').strip()
        order.update_user = user
        order.tenant = user.tenant
        if not order.pk:
            order.create_user = user
        order.save()
        form.save_m2m()  # 参照ユーザー・グループの保存

        SalesOrderDetail.objects.filter(sales_order=order).delete()
        for i, f in enumerate(formset.forms, 1):
            if f.cleaned_data and f.cleaned_data.get('product'):
                detail = f.save(commit=False)
                detail.sales_order = order
                detail.tenant = user.tenant
                detail.line_no = i
                if not detail.master_unit_price and detail.product:
                    detail.master_unit_price = detail.product.unit_price
                detail.save()
    return order

def apply_field_permissions(form, user):
    '''
    備考・承認者コメント・顧客コメントの編集権限をステータスとユーザーで制御
    '''
    status = form.instance.status_code

    # まず全て無効化
    for field_name in ['remarks', 'quotation_manager_comment', 'quotation_customer_comment', 'order_manager_comment', 'order_customer_comment']:
        if field_name in form.fields:
            form.fields[field_name].widget.attrs['readonly'] = True
            
    # 新規作成 = 備考の編集可
    if not form.instance.create_user:
        form.fields['remarks'].widget.attrs.pop('readonly', None)
        
    # 仮保存 = 作成者のみ備考の編集可
    if status == STATUS_CODE_DRAFT and form.instance.create_user == user:
        form.fields['remarks'].widget.attrs.pop('readonly', None)

    # 見積書：提出済 = 承認権限者のみ見積書コメント（承認者）の編集可
    if status == STATUS_CODE_QUOTATION_SUBMITTED and user in form.instance.reference_users.all():
        form.fields['quotation_manager_comment'].widget.attrs.pop('readonly', None)
        
    # 注文書：提出済 = 承認権限者のみ注文書コメント（承認者）の編集可
    if status == STATUS_CODE_ORDER_SUBMITTED and user in form.instance.reference_users.all():
        form.fields['order_manager_comment'].widget.attrs.pop('readonly', None)
        
    # 見積書：顧客承諾済 = 担当者のみ納入日と納入場所の編集可
    if status == STATUS_CODE_QUOTATION_CONFIRMED and form.instance.create_user == user:
        form.fields['delivery_due_date'].widget.attrs.pop('readonly', None)
        form.fields['delivery_place'].widget.attrs.pop('readonly', None)
        
    return form