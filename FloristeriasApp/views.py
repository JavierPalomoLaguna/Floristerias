from django.shortcuts import render
from django.db.models import Subquery, OuterRef
from tienda.models import Productos, CategoriaProducto


# Create your views here.
def home(request):
    categorias = CategoriaProducto.objects.all()[:6]  # Limita a 6 categorías
    productos_por_categoria = []

    for categoria in categorias:
        producto = Productos.objects.filter(categoria=categoria, disponibilidad=True).first()
        if producto:
            productos_por_categoria.append(producto)

    return render(request, 'FloristeriasApp/home.html', {  # ← CAMBIAR AQUÍ
        'productos_por_categoria': productos_por_categoria
    })


def politica_cookies(request):
    context = {
        'title': 'Política de Cookies',
        'meta_description': 'Política de cookies de la floristería.'
    }
    return render(request, 'FloristeriasApp/politica_cookies.html', context)  # ← CAMBIAR AQUÍ

def politica_privacidad(request):
    context = {
        'title': 'Política de Privacidad',
        'meta_description': 'Política de privacidad de la floristería. Información sobre protección de datos personales.'
    }
    return render(request, 'FloristeriasApp/politica_privacidad.html', context)  # ← CAMBIAR AQUÍ

def aviso_legal(request):
    context = {
        'title': 'Aviso Legal',
        'meta_description': 'Aviso legal de la floristería. Condiciones de uso del sitio web y información legal.'
    }
    return render(request, 'FloristeriasApp/aviso_legal.html', context)  # ← CAMBIAR AQUÍ