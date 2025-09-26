from django import forms
from .models import SalesOrder, SalesOrderDetail


class SalesOrderForm(forms.ModelForm):
    """
    受注ヘッダ用フォーム
    """
    class Meta:
        model = SalesOrder
        fields = ['order_no', 'order_date', 'partner', 'remarks']
        widgets = {
            'order_no': forms.TextInput(attrs={'class': 'form-control'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'partner': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SalesOrderDetailForm(forms.ModelForm):
    """
    受注明細用フォーム
    """
    class Meta:
        model = SalesOrderDetail
        fields = [
            'product',
            'quantity',
            'unit',
            'unit_price',
            'is_tax_exempt',
            'tax_rate',
            'rounding_method',
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control text-end'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control text-end'}),
            'is_tax_exempt': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control text-end', 'step': '0.01'}),
            'rounding_method': forms.Select(attrs={'class': 'form-select'}),
        }
