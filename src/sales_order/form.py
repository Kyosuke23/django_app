from django import forms
from django.forms import inlineformset_factory
from .models import SalesOrder, SalesOrderDetail


class SalesOrderForm(forms.ModelForm):
    """
    受注ヘッダ用フォーム
    """
    class Meta:
        model = SalesOrder
        fields = ['sales_order_no', 'sales_order_date', 'partner', 'remarks', 'rounding_method',]
        widgets = {
            'sales_order_no': forms.TextInput(attrs={'class': 'form-control'}),
            'sales_order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'partner': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rounding_method': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["partner"].queryset = (
                # テナントに紐づく取引先だけに絞る
                self.fields["partner"].queryset.filter(tenant=user.tenant)
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
            'unit',
            'unit_price',
            'amount',
            'is_tax_exempt',
            'tax_rate',
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control text-end'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control text-end'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control text-end'}),
            'is_tax_exempt': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control text-end', 'step': '0.01'}),
        }


# 受注明細の inline formset（新規で10行表示）
SalesOrderDetailFormSet = inlineformset_factory(
    SalesOrder,
    SalesOrderDetail,
    form=SalesOrderDetailForm,
    extra=10,      # 新規登録時に空行を10行用意
    can_delete=True
)
