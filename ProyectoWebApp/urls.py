from django.urls import path
from ProyectoWebApp import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('', views.home, name='index'),
    path('home/', views.index_demo, name='home'),
    path('robots.txt', RedirectView.as_view(url='/static/ProyectoWebApp/robots.txt', permanent=True)),
    path('sitemap.xml', RedirectView.as_view(url='/static/ProyectoWebApp/sitemap.xml', permanent=True)),
    
      
]

urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)