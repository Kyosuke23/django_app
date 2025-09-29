from django import forms
from tenant_mst.models import Tenant

class TenantEditForm(forms.ModelForm):
    '''
    テナント情報編集フォーム
    '''
    class Meta:
        model = Tenant
        fields = [
            'tenant_name',
            'postal_cd',
            'state',
            'city',
            'address',
            'address2',
        ]
        widgets = {
            'tenant_name': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_cd': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'address2': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'tenant_name': 'テナント名',
            'postal_cd': '郵便番号',
            'state': '都道府県',
            'city': '市区町村',
            'address': '住所',
            'address2': '住所2',
        }
