from .models import SalesOrderDetail
from product_mst.models import Product

def fill_formset(formset, min_forms=10):
    '''
    FormSetを指定数まで補充する
    '''
    while len(formset.forms) < min_forms:
        formset.forms.append(formset.empty_form)
    return formset


def save_order_details(request, sales_order):
    '''
    POSTデータから受注明細を保存する
    - 商品が空の行はスキップ
    - DELETE チェックがある行は物理削除
    '''
    total_forms = int(request.POST.get('details-TOTAL_FORMS', 0))

    for i in range(total_forms):
        pk = request.POST.get(f'details-{i}-id')
        product = request.POST.get(f'details-{i}-product')
        delete_flag = request.POST.get(f'details-{i}-DELETE')

        if delete_flag and pk:
            SalesOrderDetail.objects.filter(pk=pk, sales_order=sales_order).delete()
            continue

        if not product:
            continue
        
        product_obj = Product.objects.get(pk=product, tenant=request.user.tenant)
        master_price = product_obj.unit_price
        master_unit = product_obj.unit

        if pk:  # 既存行の更新
            detail = SalesOrderDetail.objects.get(pk=pk, sales_order=sales_order)
            detail.product_id = product
            detail.quantity = request.POST.get(f'details-{i}-quantity') or 0
            detail.billing_unit_price = request.POST.get(f'details-{i}-billing_unit_price') or 0
            detail.tax_rate = request.POST.get(f'details-{i}-tax_rate') or 10
            detail.is_tax_exempt = bool(request.POST.get(f'details-{i}-is_tax_exempt'))
            detail.rounding_method = request.POST.get(f'details-{i}-rounding_method') or 'floor'
            detail.update_user = request.user
            detail.save()
        else:  # 新規作成
            SalesOrderDetail.objects.create(
                sales_order = sales_order,
                line_no = i,
                product_id = product,
                quantity = request.POST.get(f'details-{i}-quantity') or 0,
                unit = master_unit,
                master_unit = master_price,
                billing_unit_price = request.POST.get(f'details-{i}-billing_unit_price') or 0,
                tax_rate = request.POST.get(f'details-{i}-tax_rate') or 10,
                is_tax_exempt = bool(request.POST.get(f'details-{i}-is_tax_exempt')),
                rounding_method = request.POST.get(f'details-{i}-rounding_method') or 'floor',
                tenant = request.user.tenant,
                create_user = request.user,
                update_user = request.user,
            )
