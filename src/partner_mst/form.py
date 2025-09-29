from django import forms
from .models import Partner

class PartnerForm(forms.ModelForm):
    """
    取引先マスタ用フォーム
    """
    class Meta:
        model = Partner
        # 入力対象のフィールドを列挙（必要に応じて調整してください）
        fields = [
            "partner_name",
            "email",
            "tel_number",
            "postal_code",
            "state",
            "city",
            "address",
            "address2",
        ]
        widgets = {
            "partner_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "tel_number": forms.TextInput(attrs={"class": "form-control"}),
            "postal_code": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "address2": forms.TextInput(attrs={"class": "form-control"}),
        }
