import django_filters
from ..models.item_mst import Item
from django import forms

class ItemFilter(django_filters.FilterSet):
    item_cd = django_filters.CharFilter(
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    item_nm = django_filters.CharFilter(
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    category = django_filters.CharFilter(
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    price_min = django_filters.NumberFilter(
        field_name='price', lookup_expr='gte',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '最小価格'})
    )
    price_max = django_filters.NumberFilter(
        field_name='price', lookup_expr='lte',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '最大価格'})
    )

    class Meta:
        model = Item
        fields = ['item_cd', 'item_nm', 'category', 'price_min', 'price_max']