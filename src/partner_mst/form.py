from django import forms
from .models import Partner

class PartnerForm(forms.ModelForm):
    '''
    取引先マスタ用フォーム
    '''
    class Meta:
        model = Partner
        fields = [
            'partner_name',
            'partner_name_kana',
            'partner_type',
            'contact_name',
            'email',
            'tel_number',
            'postal_code',
            'state',
            'city',
            'address',
            'address2',
        ]
        widgets = {
            'partner_name': forms.TextInput(attrs={'class': 'form-control'}),
            'partner_name_kana': forms.TextInput(attrs={'class': 'form-control'}),
            'partner_type': forms.Select(attrs={'class': 'form-control'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tel_number': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'address2': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        # views.pyのget_form()後のバリデーション（同一テナント内での重複チェック）
        cleaned_data = super().clean()
        tenant = self.initial.get('tenant') or getattr(self.instance, 'tenant', None)
        partner_name = cleaned_data.get('partner_name')
        email = cleaned_data.get('email')
        
        # 同一テナント内で同じ取引先・メールアドレスの組み合わせを禁止
        if tenant and partner_name and email:
            qs = Partner.objects.filter(tenant=tenant, partner_name=partner_name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('partner_name', '同じ取引先名称とメールアドレスの組み合わせが既に登録されています。')
                self.add_error('email', '同じ取引先名称とメールアドレスの組み合わせが既に登録されています。')
        return cleaned_data