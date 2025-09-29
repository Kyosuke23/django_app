"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('demo_app/', include('demo_app.urls')),
    path('product_mst/', include('product_mst.urls')),
    path('partner_mst/', include('partner_mst.urls')),
    path('sales_order/', include('sales_order.urls')),
    path('login/', include('login.urls')),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', include('dashboard.urls')),
    path('register/', include('register.urls')),
    path('', RedirectView.as_view(url='/login/')),
]
