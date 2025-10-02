from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'product_category', 'description', 'price']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'product_category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control text-end'}),
        }
