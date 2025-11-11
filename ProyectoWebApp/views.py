from django.shortcuts import render
from django.db.models import Subquery, OuterRef
from tienda.models import Productos, CategoriaProducto


# Create your views here.

def index_demo(request):
    return render(request, 'ProyectoWebApp/home.html')

def home(request):
    categorias = CategoriaProducto.objects.all()[:5]  # Limita a 5 categorías
    productos_por_categoria = []

    for categoria in categorias:
        producto = Productos.objects.filter(categoria=categoria, disponibilidad=True).first()
        if producto:
            productos_por_categoria.append(producto)

    return render(request, 'ProyectoWebApp/index.html', {
        'productos_por_categoria': productos_por_categoria
    })


