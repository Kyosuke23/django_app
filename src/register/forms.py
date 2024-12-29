from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class SignUpForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'birthday',
            'gender',
            'tel_number',
            'postal_cd',
            'state',
            'address',
            'address2',
            'privilege',
            'password1',
            'password2',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 全項目共通のclassを付与
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        # エラーフィールドに警告色を付与
        for error in self.errors:
            self.fields[error].widget.attrs['class']= f'{self.fields[error].widget.attrs['class']} is-invalid'
        # プレースホルダの設定
        self.fields['username'].widget.attrs['placeholder'] = 'ユーザー名'
        self.fields['last_name'].widget.attrs['placeholder'] = '姓'
        self.fields['first_name'].widget.attrs['placeholder'] = '名'
        self.fields['email'].widget.attrs['placeholder'] = 'xxx@example.com'
        self.fields['birthday'].widget.attrs['placeholder'] = 'yyyy-MM-dd'
        self.fields['tel_number'].widget.attrs['placeholder'] = '111-2222-3333'
        self.fields['postal_cd'].widget.attrs['placeholder'] = '111-2222'
        self.fields['address'].widget.attrs['placeholder'] = '住所（市町村・町名・番地）'
        self.fields['address2'].widget.attrs['placeholder'] = '住所2（建物名）'
