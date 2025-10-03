from django import forms
from .models import Product

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
