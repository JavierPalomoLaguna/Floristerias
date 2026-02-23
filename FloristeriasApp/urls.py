from django.urls import path
from FloristeriasApp import views  # ← CAMBIAR AQUÍ
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('', views.home, name='index'),
    path('home/', lambda request: redirect('/', permanent=True)),
    path('politica-privacidad/', views.politica_privacidad, name='politica_privacidad'),
    path('aviso-legal/', views.aviso_legal, name='aviso_legal'),
]

# Esto solo en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)