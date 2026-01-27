from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return [
            'index',                    # Página principal
            'servicios',                # App servicios (restaurante)
            'tienda',                   # App tienda
            'contacto',                 # App contacto
            'blog',                     # App blog
            'politica_privacidad',      # Política de privacidad
            'aviso_legal',              # Aviso legal
            'politica_cookies',         # Política de cookies
            'password_reset',           # Recuperar contraseña
        ]

    def location(self, item):
        return reverse(item)