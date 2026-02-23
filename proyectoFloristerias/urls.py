"""proyectoFloristerias URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls import include, path
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from FloristeriasApp.sitemaps import StaticViewSitemap  # ← CAMBIAR AQUÍ
from django.views.generic import RedirectView  
from django.conf import settings  
from django.conf.urls.static import static 
from FloristeriasApp import views  # ← CAMBIAR AQUÍ


sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('FloristeriasApp.urls')),  # ← CAMBIAR AQUÍ
    path('contacto/', include('contacto.urls')),
    path('tienda/', include('tienda.urls')),
    path('carro/', include('carro.urls')),
    path('clientes/', include('clientes.urls')),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('ventas/', include('ventas.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', RedirectView.as_view(url='/static/FloristeriasApp/robots.txt', permanent=True)),  # ← CAMBIAR AQUÍ
    path('politica-cookies/', views.politica_cookies, name='politica_cookies'),
]