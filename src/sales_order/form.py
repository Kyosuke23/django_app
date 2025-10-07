from django import forms
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import SalesOrder, SalesOrderDetail
from .constants import STATUS_CODE_DRAFT

User = get_user_model()


class SalesOrderForm(forms.ModelForm):
    '''
    受注ヘッダ用フォーム
    - partner, remarks, rounding_method に加え
    - 提出時に参照可能なユーザー・グループを指定できる
    '''
    reference_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='参照ユーザー'
    )
    reference_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='参照グループ'
    )

    class Meta:
        model = SalesOrder
        fields = [
            'delivery_date',
            'partner',
            'remarks',
            'rounding_method',
            'reference_users',
            'reference_groups',
        ]
        widgets = {
            'partner': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rounding_method': forms.Select(attrs={'class': 'form-select'}),
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        self.action_type = kwargs.pop('action_type', None)
        super().__init__(*args, **kwargs)

        if user is not None:
            # --- partner をテナント内に限定 ---
            self.fields['partner'].queryset = (
                self.fields['partner'].queryset.filter(tenant=user.tenant)
            )

            # --- reference_users: 同じテナント所属 & 管理者以上のユーザーを候補に ---
            queryset = User.objects.filter(
                tenant=user.tenant,
                privilege__lte=1
            ).order_by('username')
            
            # 仮保存データのみ自分を除去
            status_code = getattr(self.instance, 'status_code', None)
            if status_code == STATUS_CODE_DRAFT:
                queryset = queryset.exclude(id=user.id)
            self.fields['reference_users'].queryset = queryset

            # --- reference_groups: テナント紐づきグループがある場合 ---
            if hasattr(user, 'tenant') and hasattr(user.tenant, 'groups'):
                self.fields['reference_groups'].queryset = (
                    user.tenant.groups.all().order_by('name')
                )
            else:
                # テナントとグループが未連携なら全グループから選択
                self.fields['reference_groups'].queryset = Group.objects.all().order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        partner = cleaned_data.get('partner')

        # ステータスが仮作成以外かつ取引先未選択
        if self.action_type != STATUS_CODE_DRAFT and not partner:
            self.add_error('partner', '取引先を選択してください。')

        return cleaned_data


class SalesOrderDetailForm(forms.ModelForm):
    '''
    受注明細用フォーム
    '''
    class Meta:
        model = SalesOrderDetail
        fields = [
            'product',
            'quantity',
            'billing_unit_price',
            'is_tax_exempt',
            'tax_rate',
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control text-end'}),
            'billing_unit_price': forms.NumberInput(attrs={'class': 'form-control text-end'}),
            'is_tax_exempt': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tax_rate': forms.Select(attrs={'class': 'form-select'}),
        }


class BaseSalesOrderDetailFormSet(BaseInlineFormSet):
    def clean(self):
        cleaned_data = super().clean()
        seen = {}
        dup = set()

        for i, row in enumerate(self.forms):
            if not hasattr(row, 'cleaned_data'):
                continue
            data = row.cleaned_data
            if not data or data.get('DELETE'):
                continue

            product = data.get('product')

            # 商品・単価・数量の相関チェック
            if not product:
                if row.cleaned_data.get('quantity') or row.cleaned_data.get('unit_price'):
                    row.add_error('product', '商品を選択してください。')
                continue

            # 同一商品チェック
            if product in seen:
                dup.add(product)
                error_msg = f'同一商品が複数行に登録されています（{product.product_name}）。'
                row.add_error('product', error_msg)
                seen[product].add_error('product', error_msg)
            else:
                seen[product] = row

        return cleaned_data

    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        # 空行を許可
        if not any([
            form.data.get(f"{self.prefix}-{i}-product"),
            form.data.get(f"{self.prefix}-{i}-quantity"),
            form.data.get(f"{self.prefix}-{i}-billing_unit_price"),
        ]):
            form.empty_permitted = True
        return form


SalesOrderDetailFormSet = inlineformset_factory(
    SalesOrder, SalesOrderDetail,
    form=SalesOrderDetailForm,
    formset=BaseSalesOrderDetailFormSet,
    extra=1, can_delete=True,
)
