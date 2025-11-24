from django.shortcuts import render, redirect
from django.shortcuts import render, redirect
from servicios.models import Servicio, Reserva
from django.contrib import messages
from datetime import date

def servicios(request):
    # Obtener todos los servicios ordenados por categoría y título
    servicios = Servicio.objects.all()
    
    # Agrupar servicios por categoría
    servicios_por_categoria = {}
    for servicio in servicios:
        categoria = servicio.get_categoria_display()  # Nombre legible de la categoría
        if categoria not in servicios_por_categoria:
            servicios_por_categoria[categoria] = []
        servicios_por_categoria[categoria].append(servicio)
    
    # Ordenar las categorías según el orden deseado
    orden_categorias = [
        'Entrantes y Picoteo',
        'Primeros Platos', 
        'Segundos Platos',
        'Postres',
        'Bebidas',
        'Reservas',
        'Localización',
        'Contacto'
    ]
    
    # Crear lista ordenada de categorías con sus servicios
    categorias_ordenadas = []
    for categoria_nombre in orden_categorias:
        if categoria_nombre in servicios_por_categoria:
            categorias_ordenadas.append({
                'nombre': categoria_nombre,
                'servicios': servicios_por_categoria[categoria_nombre],
                'slug': categoria_nombre.lower().replace(' ', '_').replace('ó', 'o')
            })
    
    context = {
        'categorias_ordenadas': categorias_ordenadas,
        'today': date.today().isoformat(),
        'meta_title': 'Carta del Restaurante - La Trastienda',
        'meta_description': 'Descubre nuestra carta con entrantes, primeros, segundos, postres y bebidas. Reserva tu mesa online.',
    }
    return render(request, "servicios/servicios.html", context)


def procesar_reserva(request):
    if request.method == 'POST':
        # Procesar datos del formulario manualmente
        nombre = request.POST.get('nombre')
        telefono = request.POST.get('telefono')
        email = request.POST.get('email')
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')
        numero_personas = request.POST.get('numero_personas')
        comentarios = request.POST.get('comentarios', '')
        
        # Validaciones básicas
        if not all([nombre, telefono, email, fecha, hora, numero_personas]):
            messages.error(request, 'Por favor, completa todos los campos obligatorios.')
            return redirect('servicios')
        
        try:
            # Crear reserva
            reserva = Reserva.objects.create(
                nombre=nombre,
                telefono=telefono,
                email=email,
                fecha=fecha,
                hora=hora,
                numero_personas=numero_personas,
                comentarios=comentarios,
                estado='pendiente'
            )
            
            messages.success(
                request, 
                f'¡Reserva enviada correctamente! Te confirmaremos por teléfono o email. '
                f'Reserva para {reserva.numero_personas} personas el {reserva.fecha} a las {reserva.hora}.'
            )
        except Exception as e:
            messages.error(request, 'Error al procesar la reserva. Por favor, inténtalo de nuevo.')
        
        return redirect('servicios')
    
    return redirect('servicios')