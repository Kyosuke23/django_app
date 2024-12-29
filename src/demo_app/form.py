from django import forms
from .models.item_mst import Item
from django.contrib.auth.validators import ASCIIUsernameValidator


class ItemCreationForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = (
            'item_cd',
            'item_nm',
            'category',
            'description',
            'price',
        )

    def __init__(self, *args, **kwargs):
        # フォームの初期化
        super().__init__(*args, **kwargs)
        # 全項目共通のclassを付与
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        # エラーフィールドに警告色を付与
        for error in self.errors:
            self.fields[error].widget.attrs['class']= f'{self.fields[error].widget.attrs['class']} is-invalid'

class AjaxTestForm(forms.Form):
    input = forms.CharField(label='入力してください')
    input2 = forms.CharField(label='半角英数字と記号のみ', required=False, validators=[ASCIIUsernameValidator()])