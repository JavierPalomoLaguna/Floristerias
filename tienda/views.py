from django.shortcuts import get_object_or_404, render
from .models import CategoriaProducto, Productos
from django.http import HttpResponse
import csv
from django.views.decorators.csrf import csrf_exempt

def tienda(request):
    productos = Productos.objects.filter(disponibilidad=True)
    categorias = CategoriaProducto.objects.all()
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'meta_title': 'Tiendas Online para Comercios - Desarrollo Ecommerce | Código Vivo Studio',
        'meta_description': 'Creamos tiendas online profesionales para comercios. Catálogo de productos, pasarelas de pago y gestión de pedidos.',
    }
    
    return render(request, 'tienda/tienda.html', context)

def productos_por_categoria(request, categoria_id):
    categoria = get_object_or_404(CategoriaProducto, id=categoria_id)
    productos = Productos.objects.filter(categoria=categoria, disponibilidad=True)
    return render(request, 'tienda/categoria.html', {
        'productos': productos,
        'categoria': categoria
    })

def detalle_producto(request, producto_id):
    producto = get_object_or_404(Productos, id=producto_id)
    fotos_extra = producto.fotos_extra.all()
    categoria = producto.categoria
    return render(request, 'tienda/productos.html', {
        'producto': producto,
        'fotos_extra': fotos_extra,
        'categoria': categoria
    })

def checkout(request):
    carro = request.session.get("carro", {})
    for item in carro.values():
        item["total"] = item["precio"] * item["cantidad"]

    context = {
        'carro': carro,
        'productos_total_carro': sum(item["cantidad"] for item in carro.values()),
        'importe_total_carro': sum(item["precio"] * item["cantidad"] for item in carro.values())
    }

    return render(request, 'carro/checkout.html', context)

def exportar_csv(request):
    categorias = CategoriaProducto.objects.all()
    productos = Productos.objects.all()

    # Si hay filtros aplicados (GET o POST), filtramos
    fecha_desde = request.POST.get("fecha_desde") or request.GET.get("fecha_desde")
    fecha_hasta = request.POST.get("fecha_hasta") or request.GET.get("fecha_hasta")
    categoria_id = request.POST.get("categoria") or request.GET.get("categoria")

    if fecha_desde:
        productos = productos.filter(created__gte=fecha_desde)
    if fecha_hasta:
        productos = productos.filter(created__lte=fecha_hasta)
    if categoria_id and categoria_id != "todos":
        productos = productos.filter(categoria_id=categoria_id)

    # Si es POST con selección de productos → generar CSV
    if request.method == "POST" and "seleccionados" in request.POST:
        seleccionados = request.POST.getlist("seleccionados")
        productos = productos.filter(id__in=seleccionados)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="productos.csv"'

        writer = csv.writer(response)
        writer.writerow(["Nombre", "Precio", "Stock", "Disponibilidad", "Categoría", "Fecha creación"])

        for p in productos:
            writer.writerow([
                p.nombre,
                p.precio_total,
                p.stock,
                "Sí" if p.disponibilidad else "No",
                p.categoria.nombre if p.categoria else "",
                p.created.strftime("%Y-%m-%d %H:%M")
            ])
        return response

    return render(request, "admin/exportar_csv.html", {
        "categorias": categorias,
        "productos": productos,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "categoria_id": categoria_id,
    })


    