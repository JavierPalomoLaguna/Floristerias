import os
from decouple import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'd^czxedced*yn8mz7-nhrf7w234!d#&sn5unmoz!_4x^lv+$o+'

ENV = config('DJANGO_ENV', default='local')

SITE_ID = 1

if ENV == 'production':
    DEBUG = False
    ALLOWED_HOSTS = ['codigovivostudio.cloud', 'www.codigovivostudio.cloud', '72.61.94.146']
    CSRF_TRUSTED_ORIGINS = ['https://codigovivostudio.cloud', 'https://www.codigovivostudio.cloud']
    
    # Configuración automática del Site para producción
    try:
        from django.contrib.sites.models import Site
        site = Site.objects.get(id=1)
        site.domain = 'codigovivostudio.cloud'
        site.name = 'Código Vivo Studio'
        site.save()
    except:
        pass  # Se creará con el comando de setup
    
else:
    DEBUG = True
    ALLOWED_HOSTS = [
        'localhost',
        '127.0.0.1',
        '.ngrok-free.dev',
        'codigovivostudio.cloud',
        'www.codigovivostudio.cloud',
        '.localhost',
        '0.0.0.0',
        'testserver',
    ]
    CSRF_TRUSTED_ORIGINS = [
        'https://*.ngrok-free.dev',
        'https://codigovivostudio.cloud',
        'https://www.codigovivostudio.cloud',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]
    
    # Configuración automática del Site para desarrollo
    try:
        from django.contrib.sites.models import Site
        site = Site.objects.get(id=1)
        site.domain = 'localhost:8000'
        site.name = 'Código Vivo Studio - Desarrollo'
        site.save()
    except:
        pass  # Se creará con el comando de setup

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',      
    'django.contrib.sitemaps',   
    'ProyectoWebApp',
    'servicios',
    'blog',
    'contacto',
    'tienda',
    'carro',
    'clientes',
    'ventas.apps.VentasConfig',
    'crispy_forms',
    'crispy_bootstrap4',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'proyectoweb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'proyectoweb', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'carro.context_processor.importe_total_carro',
                'carro.context_processor.productos_total_carro',
                'carro.context_processor.gastos_envio_carro',
                'carro.context_processor.total_con_envio_carro',
                'carro.context_processor.envio_gratis_info',
                'clientes.context_processors.cliente_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'proyectoweb.wsgi.application'

# Base de datos PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-eu'
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

if ENV == 'production':
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
    ]
else:
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
        os.path.join(BASE_DIR, 'ProyectoWebApp/static'),
    ]

# Archivos multimedia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'jpalomolaguna@gmail.com'
EMAIL_HOST_PASSWORD = config('EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
CRISPY_TEMPLATE_PACK = "bootstrap4"

SESSION_COOKIE_AGE = 1209600  # 2 semanas
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

GASTOS_ENVIO = 5.95
UMBRAL_ENVIO_GRATIS = 300.00