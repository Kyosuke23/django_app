from django import forms
from .models import Product, ProductCategory

class ProductSearchForm(forms.Form):
    '''
    商品マスタ検索フォーム
    '''
    # 基本検索
    search_keyword = forms.CharField(
        required=False,
        max_length=255,
        label='キーワード検索',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'キーワードを入力',
            }
        )
    )

    # 詳細検索
    search_product_name = forms.CharField(
        required=False,
        max_length=100,
        label='商品名称',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )

    search_category = forms.ModelChoiceField(
        required=False,
        label='商品カテゴリ',
        queryset=ProductCategory.objects.all(),
        empty_label='すべて',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    search_unit = forms.CharField(
        required=False,
        max_length=20,
        label='単位',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )

    min_price = forms.DecimalField(
        required=False,
        label='単価（下限）',
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': '円'}),
        min_value=0
    )

    max_price = forms.DecimalField(
        required=False,
        label='単価（上限）',
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': '円'}),
        min_value=0
    )

    # 並び替え
    SORT_GROUPS = {
        '商品名称': [
            ('product_name', '商品名称：昇順 ▲'),
            ('-product_name', '商品名称：降順 ▼'),
        ],
        '商品カテゴリ': [
            ('product_category__product_category_name', '商品カテゴリ：昇順 ▲'),
            ('-product_category__product_category_name', '商品カテゴリ：降順 ▼'),
        ],
        '単価': [
            ('unit_price', '単価：昇順 ▲'),
            ('-unit_price', '単価：降順 ▼'),
        ],
    }

    sort = forms.ChoiceField(
        required=False,
        label='並び替え',
        choices=[],
        widget=forms.Select(attrs={
            'id': 'form-select',
            'class': 'form-select form-select-sm',
        })
    )

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


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'product_category', 'description', 'unit_price', 'unit']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'product_category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control text-end'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user is not None:
            # 商品カテゴリをテナント内に限定
            self.fields['categories'].queryset = (self.fields['categories'].queryset.filter(tenant=user.tenant))
