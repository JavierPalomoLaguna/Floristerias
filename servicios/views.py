from django.shortcuts import render
from servicios.models import Servicio

def servicios(request):
    servicios = Servicio.objects.all()
    
    context = {
        'servicios': servicios,
        'meta_title': 'Desarrollo Web para Restaurantes y Comercios - Código Vivo Studio',
        'meta_description': 'Soluciones web personalizadas para restaurantes y comercios. Tiendas online, sistemas de reservas y automatización empresarial.',
    }
    return render(request, "servicios/servicios.html", context)