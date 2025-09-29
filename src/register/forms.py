from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import CustomUser
from django import forms


class SignUpForm(UserCreationForm):
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

class EditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = (
            'username',
            'email',
            'tel_number',
            'gender',
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
        self.fields['username'].widget.attrs['placeholder'] = '半角例）山田 太郎数字または記号'
        self.fields['email'].widget.attrs['placeholder'] = '例）xxx@test.com'
        self.fields['tel_number'].widget.attrs['placeholder'] = '例）09012345678'


class ChangePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 全項目共通のclassを付与
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        # エラーフィールドに警告色を付与
        for error in self.errors:
            self.fields[error].widget.attrs['class']= f'{self.fields[error].widget.attrs['class']} is-invalid'
