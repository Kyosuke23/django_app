from django import forms
from .models import Partner

class PartnerSearchForm(forms.Form):
    '''
    取引先マスタ検索フォーム
    '''
    search_keyword = forms.CharField(
        required=False,
        max_length=255,
        label='キーワード検索',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'キーワードを入力'
            }
        )
    )

    search_partner_name = forms.CharField(
        required=False,
        max_length=100,
        label='取引先名称',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-sm'}
        )
    )

    search_partner_type = forms.ChoiceField(
        required=False,
        label='取引先区分',
        choices=[('', 'すべて')] + list(Partner.PARTNER_TYPE_CHOICES),
        widget=forms.Select(
            attrs={'class': 'form-select form-select-sm'}
        )
    )

    search_contact_name = forms.CharField(
        required=False,
        max_length=50,
        label='担当者名',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-sm'}
        )
    )

    search_email = forms.CharField(
        required=False,
        max_length=254,
        label='メールアドレス',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-sm'}
        )
    )

    search_tel_number = forms.CharField(
        required=False,
        max_length=20,
        label='電話番号',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-sm'}
        )
    )

    search_address = forms.CharField(
        required=False,
        max_length=255,
        label='住所',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-sm'}
        )
    )

    # 並び替え（optgroup対応）
    SORT_GROUPS = {
        '取引先名称（カナ）': [
            ('partner_name_kana', '取引先名称（カナ）：昇順 ▲'),
            ('-partner_name_kana', '取引先名称（カナ）：降順 ▼'),
        ],
        'メールアドレス': [
            ('email', 'メールアドレス ▲'),
            ('-email', 'メールアドレス ▼'),
        ],
    }

    sort = forms.ChoiceField(
        required=False,
        label='並び替え',
        choices=[],
        widget=forms.Select(
            attrs={'class': 'form-select form-select-sm', 'id': 'form-select'}
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = [('', '並び替え')]
        for group_label, options in self.SORT_GROUPS.items():
            choices.append((group_label, [(val, lbl) for val, lbl in options]))
        self.fields['sort'].choices = choices

        # 共通のフィールド属性設定
        for name, field in self.fields.items():
            if name != 'search_keyword':
                field.widget.attrs.setdefault('class', 'form-control form-control-sm')

class PartnerForm(forms.ModelForm):
    '''
    取引先マスタ登録・更新フォーム
    '''
    class Meta:
        model = Partner
        required_css_class = 'required'
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
            'partner_type': forms.Select(attrs={'class': 'form-control',}),
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
        email = cleaned_data.get('email')
        self.fields['partner_type'].required = True

        # 同一テナント内で同じメールアドレスを禁止
        if tenant and email:
            qs = Partner.objects.filter(tenant=tenant, email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('email', '同じメールアドレスが既に登録されています。')
        return cleaned_data