from django import forms
from .models import Product, ProductCategory

class ProductSearchForm(forms.Form):
    '''
    商品マスタ管理画面：検索フォーム
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
        queryset=ProductCategory.objects.none(),
        empty_label='すべて',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    search_unit = forms.CharField(
        required=False,
        max_length=20,
        label='単位',
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )

    search_unit_price_min = forms.DecimalField(
        required=False,
        label='単価（下限）',
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': '円'}),
        min_value=0
    )

    search_unit_price_max = forms.DecimalField(
        required=False,
        label='単価（上限）',
        max_digits=12,
        decimal_places=2,
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
        user = kwargs.pop('user', None)
        self.tenant = getattr(user, 'tenant', None)
        super().__init__(*args, **kwargs)

        # optgroup構造を設定
        choices = [('', '並び替え')]
        for group_label, options in self.SORT_GROUPS.items():
            # optgroup構造は (group_label, [ (value, label), ... ]) の形で渡す必要あり
            choices.append((group_label, [(val, lbl) for val, lbl in options]))
        self.fields['sort'].choices = choices

        # 検索フォームの商品カテゴリへのフィルタ設定
        if user and hasattr(user, 'tenant'):
            self.fields['search_category'].queryset = ProductCategory.objects.filter(tenant=user.tenant, is_deleted=False).order_by('product_category_name')
        else:
            # 匿名やテスト時などは空クエリセット
            self.fields['search_category'].queryset = ProductCategory.objects.none()

        # 各フィールド共通属性
        for name, field in self.fields.items():
            if name != 'search_keyword':
                field.widget.attrs.setdefault('class', 'form-control form-control-sm')


class ProductForm(forms.ModelForm):
    '''
    商品マスタ管理画面：登録・更新フォーム
    '''
    unit_price = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control text-end'}),
        label='単価'
    )

    class Meta:
        model = Product
        fields = ['product_name', 'product_category', 'description', 'unit_price', 'unit']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'product_category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.tenant = getattr(user, 'tenant', None)
        super().__init__(*args, **kwargs)

        if user is not None:
            # 商品カテゴリをテナント内に限定
            self.fields['product_category'].queryset = (self.fields['product_category'].queryset.filter(tenant=user.tenant, is_deleted=False))

        self.fields['unit'].required = False

    def clean(self):
        # views.pyのget_form()後のバリデーション（同一テナント内での重複チェック）
        cleaned_data = super().clean()
        tenant = self.initial.get('tenant') or getattr(self.instance, 'tenant', None)
        product_name = cleaned_data.get('product_name')

        # 同一テナント内で同じ商品名の組み合わせを禁止
        if tenant and product_name:
            qs = Product.objects.filter(tenant=tenant, product_name=product_name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('product_name', '同じ商品名が既に登録されています。')
        return cleaned_data

class ProductCategoryForm(forms.ModelForm):
    '''
    商品マスタ管理画面：商品カテゴリ管理フォーム
    '''
    selected_category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.none(),
        required=False,
        label='既存カテゴリ',
        widget=forms.Select(attrs={
            'id': 'categoryId',
            'class': 'form-select form-select-sm'
        })
    )

    class Meta:
        model = ProductCategory
        fields = ['product_category_name']
        widgets = {
            'product_category_name': forms.TextInput(attrs={
                'id': 'categoryName',
                'class': 'form-control form-control-sm',
                'placeholder': 'カテゴリ名を入力',
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.tenant = getattr(user, 'tenant', None)
        super().__init__(*args, **kwargs)
        self.fields['selected_category'].queryset = ProductCategory.objects.filter(tenant=user.tenant, is_deleted=False).order_by('product_category_name')

        # 削除アクション時は必須チェックを無効化
        action = self.data.get('action') or self.initial.get('action')
        if action == 'delete':
            self.fields['product_category_name'].required = False