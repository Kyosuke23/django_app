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
        super().clean()
        seen = set(); dup = set()
        for f in self.forms:
            if not hasattr(f, 'cleaned_data'):
                continue
            if f.cleaned_data.get('DELETE'):
                continue
            p = f.cleaned_data.get('product')
            if not p:
                continue
            if p in seen: dup.add(p)
            seen.add(p)
        if dup:
            names = ', '.join([p.product_name for p in dup])
            raise forms.ValidationError(f'同一商品が複数行に登録されています: {names}')

SalesOrderDetailFormSet = inlineformset_factory(
    SalesOrder, SalesOrderDetail,
    form=SalesOrderDetailForm,
    formset=BaseSalesOrderDetailFormSet,
    extra=1, can_delete=True,
)