from django.contrib.auth.forms import PasswordChangeForm
from .models import CustomUser, UserGroup
from tenant_mst.models import Tenant
from django import forms
from .constants import  PRIVILEGE_CHOICES, EMPLOYMENT_STATUS_CHOICES, GENDER_CHOICES

class UserSearchForm(forms.Form):
    """ユーザーマスタ検索フォーム"""
    search_keyword = forms.CharField(
        required=False,
        max_length=255,
        label='キーワード検索',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'キーワードを入力してください',
            }
        )
    )

    search_username = forms.CharField(
        required=False,
        max_length=100,
        label='ユーザー名',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-sm'}
        )
    )

    search_email = forms.CharField(
        required=False,
        label='メールアドレス',
        widget=forms.TextInput(
            attrs={'class': 'form-control form-control-sm'}
        )
    )

    search_gender = forms.ChoiceField(
        required=False,
        label='性別',
        choices=[('', 'すべて')] + list(GENDER_CHOICES),
        widget=forms.Select(
            attrs={'class': 'form-select form-select-sm'}
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

    search_employment_status = forms.ChoiceField(
        required=False,
        label='雇用状態',
        choices=[('', 'すべて')] + list(EMPLOYMENT_STATUS_CHOICES),
        widget=forms.Select(
            attrs={'class': 'form-select form-select-sm'}
        )
    )

    search_privilege = forms.ChoiceField(
        required=False,
        label='権限',
        choices=[('', 'すべて')] + list(PRIVILEGE_CHOICES),
        widget=forms.Select(
            attrs={'class': 'form-select form-select-sm'}
        )
    )

    search_user_group = forms.ModelChoiceField(
        required=False,
        label='所属グループ',
        queryset=UserGroup.objects.filter(is_deleted=False).order_by('group_name'),
        widget=forms.Select(
            attrs={'class': 'form-select form-select-sm'}
        )
    )

    sort = forms.ChoiceField(
        required=False,
        label='並び替え',
        choices=[
            ('', '並び替え'),
            ('username_kana', 'ユーザー名（カナ）：昇順 ▲'),
            ('-username_kana', 'ユーザー名（カナ）：降順 ▼'),
            ('email', 'メールアドレス：昇順 ▲'),
            ('-email', 'メールアドレス：降順 ▼'),
        ],
        widget=forms.Select(
            attrs={'class': 'form-select form-select-sm', 'id': 'form-select'}
        )
    )

    # 並び替え
    SORT_GROUPS = {
        'ユーザー名（カナ）': [
            ('username_kana', 'ユーザー名（カナ）：昇順 ▲'),
            ('-username_kana', 'ユーザー名（カナ）：降順 ▼'),
        ],
        'メールアドレス': [
            ('email', 'メールアドレス：昇順  ▲'),
            ('-email', 'メールアドレス：降順 ▼'),
        ],
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # optgroup構造を設定
        choices = [('', '並び替え')]
        for group_label, options in self.SORT_GROUPS.items():
            # optgroup構造は (group_label, [ (value, label), ... ]) の形で渡す必要あり
            choices.append((group_label, [(val, lbl) for val, lbl in options]))
        self.fields['sort'].choices = choices

        # 各フィールド共通属性
        for name, field in self.fields.items():
            if name != 'search_keyword':
                field.widget.attrs.setdefault('class', 'form-control form-control-sm')


from django import forms
from register.models import CustomUser, UserGroup


class SignUpForm(forms.ModelForm):
    """ユーザー登録・編集フォーム"""

    groups_custom = forms.ModelMultipleChoiceField(
        queryset=UserGroup.objects.filter(is_deleted=False).order_by('group_name'),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select select2',
        }),
        label='所属グループ',
        help_text='ユーザーが所属するグループを選択してください。（複数選択可）'
    )

    class Meta:
        model = CustomUser
        fields = (
            'username',
            'username_kana',
            'email',
            'tel_number',
            'gender',
            'employment_status',
            'privilege',
            'groups_custom',
        )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        is_update = kwargs.pop('is_update', False)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.is_update = is_update

        # 所属グループをテナントごとに絞り込み
        if request is not None and hasattr(request, 'user'):
            tenant = getattr(request.user, 'tenant', None)
            if tenant:
                self.fields['groups_custom'].queryset = UserGroup.objects.filter(tenant=tenant, is_deleted=False).order_by('group_name')

        # privilege選択肢を自分より強い権限を除外
        if self.user and hasattr(self.user, 'privilege'):
            user_priv = int(self.user.privilege)
            self.fields['privilege'].choices = [
                c for c in self.fields['privilege'].choices
                if c[0] == '' or int(c[0]) >= user_priv
            ]

        # 全項目共通のclassを付与
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        # エラーフィールドに警告色を付与
        for error in self.errors:
            self.fields[error].widget.attrs['class'] = (
                f"{self.fields[error].widget.attrs['class']} is-invalid"
            )

        # プレースホルダの設定
        self.fields['username'].widget.attrs['placeholder'] = '例）山田 太郎'
        self.fields['username_kana'].widget.attrs['placeholder'] = '例）ヤマダ タロウ'
        self.fields['email'].widget.attrs['placeholder'] = '例）info@test.com'
        self.fields['tel_number'].widget.attrs['placeholder'] = '例）090-1234-5678'

        # 不要なパスワードフィールドを削除
        if 'password1' in self.fields:
            del self.fields['password1']
        if 'password2' in self.fields:
            del self.fields['password2']

        # 更新時は一部フィールドを任意に設定
        if is_update:
            for field_name, field in self.fields.items():
                if field_name not in ['employment_status', 'privilege', 'groups_custom']:
                    field.required = False

    def clean(self):
        cleaned_data = super().clean()

        if getattr(self, 'is_update', False):
            # モデル側の blank=False チェックを回避
            if not cleaned_data.get('username'):
                cleaned_data['username'] = self.instance.username or 'DUMMY_USERNAME'

            if not cleaned_data.get('email'):
                cleaned_data['email'] = self.instance.email or 'dummy@example.com'

            # 不要な必須エラーを削除
            removable_fields = ['username', 'email']
            for field in removable_fields:
                if field in self.errors:
                    self.errors.pop(field)
        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')

        # 更新時は空入力を許可
        if getattr(self, 'is_update', False) and not username:
            return username

        return username


class ChangePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 全項目共通のclassを付与
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        # エラーフィールドに警告色を付与
        for error in self.errors:
            self.fields[error].widget.attrs['class']= f'{self.fields[error].widget.attrs['class']} is-invalid'


class UserGroupForm(forms.ModelForm):
    selected_group = forms.ModelChoiceField(
        queryset=UserGroup.objects.none(),
        required=False,
        label='既存グループ',
        widget=forms.Select(attrs={
            'id': 'groupId',
            'class': 'form-select form-select-sm'
        })
    )

    class Meta:
        model = UserGroup
        fields = ['group_name']
        widgets = {
            'group_name': forms.TextInput(attrs={
                'id': 'groupName',
                'class': 'form-select select2',
                'multiple': 'multiple',
                'placeholder': 'ユーザーグループ名を入力',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['selected_group'].queryset = UserGroup.objects.filter(is_deleted=False).order_by('group_name')


class InitialUserForm(forms.Form):
    '''
    システム管理者が初期ユーザーを招待するフォーム
    '''
    company_name = forms.CharField(label='企業名', max_length=255)
    username = forms.CharField(label='氏名', max_length=100)
    email = forms.EmailField(label='メールアドレス', max_length=254)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('このメールアドレスは既に登録されています。')

        return email

class TenantRegisterForm(forms.ModelForm):
    '''
    テナント情報登録フォーム
    '''
    class Meta:
        model = Tenant
        fields = ['tenant_name', 'representative_name', 'email', 'tel_number',
                  'postal_code', 'state', 'city', 'address', 'address2']
