import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SECRET_KEY = 'django-insecure-3nl+%03ac=dfw!^0!dypa2%-93mm^y$d0iv0hp%h&%km503s&z'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_bootstrap5',
    'bootstrap_modal_forms',
    'widget_tweaks',
    'rest_framework',
    'django.contrib.humanize', 
    'register.apps.RegisterConfig',
    'login.apps.LoginConfig',
    'dashboard.apps.DashboardConfig',
    'demo_app.apps.DemoappConfig',
    'product_mst.apps.ProductMstConfig',
    'tenant_mst.apps.TenantMstConfig',
    'partner_mst.apps.PartnerMstConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'demo_app.middleware.auth.AuthMiddleware',
    'register.middleware.auth.AuthMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.const_str',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

# テンプレート上で数値をカンマ区切りする位置（intcomma）
NUMBER_GROUPING = 3

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = 'login:login'

AUTH_USER_MODEL = 'register.CustomUser'

# メッセージストレージ
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'