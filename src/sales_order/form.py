from django import forms
from django.forms import inlineformset_factory
from .models import SalesOrder, SalesOrderDetail
from django.forms.models import BaseInlineFormSet


class SalesOrderForm(forms.ModelForm):
    '''
    受注ヘッダ用フォーム
    '''
    class Meta:
        model = SalesOrder
        fields = [
            'partner',
            'remarks',
            'rounding_method',
        ]
        widgets = {
            'partner': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rounding_method': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['partner'].queryset = (
                # テナントに紐づく取引先だけに絞る
                self.fields['partner'].queryset.filter(tenant=user.tenant)
            )

class SalesOrderDetailForm(forms.ModelForm):
    '''
    受注明細用フォーム
    '''
    class Meta:
        model = SalesOrderDetail
        fields = [
            'product',
            'quantity',
            'billing_unit_price',
            'is_tax_exempt',
            'tax_rate',
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control text-end'}),
            'billing_unit_price': forms.NumberInput(attrs={'class': 'form-control text-end'}),
            'is_tax_exempt': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tax_rate': forms.Select(attrs={'class': 'form-select'}),
        }

class BaseSalesOrderDetailFormSet(BaseInlineFormSet):
    def clean(self):
        cleaned_data = super().clean()
        seen = {}
        dup = set()

        for i, row in enumerate(self.forms):
            if not hasattr(row, 'cleaned_data'):
                continue
            data = row.cleaned_data
            if not data or data.get('DELETE'):
                continue

            product = data.get('product')
            if not product:
                continue

            # 同一商品を検出
            if product in seen:
                dup.add(product)
                # エラーメッセージ
                error_msg = f'同一商品が複数行に登録されています（{product.product_name}）。'
                # 2行目以降にもエラーを表示
                row.add_error('product', error_msg)
                # 最初の行にもエラーを表示（ユーザーが気づきやすいように）
                seen[product].add_error('product', error_msg)
            else:
                seen[product] = row

        return cleaned_data

SalesOrderDetailFormSet = inlineformset_factory(
    SalesOrder, SalesOrderDetail,
    form=SalesOrderDetailForm,
    formset=BaseSalesOrderDetailFormSet,
    extra=1, can_delete=True,
)