# setup_site.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyectoFloristerias.settings')  # ← CAMBIAR AQUÍ
django.setup()

from django.conf import settings
from django.contrib.sites.models import Site

def setup_site():
    print("🌐 Configurando Site de Django...")
    
    site, created = Site.objects.get_or_create(id=1)
    
    if settings.ENV == 'production':
        site.domain = 'tudominio.com'  # Cambiar por tu dominio
        site.name = 'Floristería Online'
        print("🚀 Configurando para PRODUCCIÓN")
    else:
        site.domain = 'localhost:8000'
        site.name = 'Floristería - Desarrollo' 
        print("💻 Configurando para DESARROLLO")
    
    site.save()
    
    print(f"✅ Site configurado:")
    print(f"   ID: {site.id}")
    print(f"   Dominio: {site.domain}")
    print(f"   Nombre: {site.name}")
    print(f"   Entorno: {settings.ENV}")

if __name__ == "__main__":
    setup_site()