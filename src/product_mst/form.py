from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_cd', 'product_nm', 'product_category', 'description', 'price', 'start_date', 'end_date']
        widgets = {
            'product_cd': forms.TextInput(attrs={'class': 'form-control'}),
            'product_nm': forms.TextInput(attrs={'class': 'form-control'}),
            'product_category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control text-end'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
