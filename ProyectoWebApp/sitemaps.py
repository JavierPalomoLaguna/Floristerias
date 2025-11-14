from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return [
            'index',           
            'home',            
            'password_reset',  
            'servicios',       
            'tienda',          
            'contacto',        
            'blog',            
        ]

    def location(self, item):
        return reverse(item)