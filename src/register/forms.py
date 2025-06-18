from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import CustomUser
from django import forms


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
            'city',
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
        self.fields['username'].widget.attrs['placeholder'] = '半角数字または記号'
        self.fields['last_name'].widget.attrs['placeholder'] = '例）山田'
        self.fields['first_name'].widget.attrs['placeholder'] = '例）太郎'
        self.fields['email'].widget.attrs['placeholder'] = '例）xxx@test.com'
        self.fields['tel_number'].widget.attrs['placeholder'] = '例）09012345678'
        self.fields['postal_cd'].widget.attrs['placeholder'] = '例）1300012	'
        self.fields['address'].widget.attrs['placeholder'] = '住所（市区町村・町名・番地）'
        self.fields['address2'].widget.attrs['placeholder'] = '住所2（建物名）'

class EditForm(forms.ModelForm):
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
            'city',
            'address',
            'address2',
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
        self.fields['username'].widget.attrs['placeholder'] = '半角数字または記号'
        self.fields['last_name'].widget.attrs['placeholder'] = '例）山田'
        self.fields['first_name'].widget.attrs['placeholder'] = '例）太郎'
        self.fields['email'].widget.attrs['placeholder'] = '例）xxx@test.com'
        self.fields['tel_number'].widget.attrs['placeholder'] = '例）09012345678'
        self.fields['postal_cd'].widget.attrs['placeholder'] = '例）1300012	'
        self.fields['address'].widget.attrs['placeholder'] = '住所（市区町村・町名・番地）'
        self.fields['address2'].widget.attrs['placeholder'] = '住所2（建物名）'


class ChangePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 全項目共通のclassを付与
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        # エラーフィールドに警告色を付与
        for error in self.errors:
            self.fields[error].widget.attrs['class']= f'{self.fields[error].widget.attrs['class']} is-invalid'
