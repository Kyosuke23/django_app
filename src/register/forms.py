from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import CustomUser
from django import forms


class SignUpForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = (
            'username',
            'email',
            'tel_number',
            'gender',
            'privilege',
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
        self.fields['username'].widget.attrs['placeholder'] = '例）山田 太郎'
        self.fields['email'].widget.attrs['placeholder'] = '例）xxx@test.com'
        self.fields['tel_number'].widget.attrs['placeholder'] = '例）09012345678'
        # 不要なパスワードフィールドを削除
        if 'password1' in self.fields:
            del self.fields['password1']
        if 'password2' in self.fields:
            del self.fields['password2']
            
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # 自分以外に同じ username があればエラー
        qs = CustomUser.objects.exclude(pk=self.instance.pk).filter(username=username)
        if qs.exists():
            raise forms.ValidationError('このユーザー名は既に使用されています。')
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
