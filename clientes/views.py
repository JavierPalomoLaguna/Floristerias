from django.shortcuts import render, redirect, get_object_or_404
from .forms import ClienteForm, LoginForm, ClienteEdicionForm
from .models import Cliente
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse


def registro_cliente(request):
    if request.user.is_authenticated:
        cliente = Cliente.objects.filter(usuario=request.user).first()
        form = ClienteForm(instance=cliente)
    else:
        form = ClienteForm()

    if request.method == 'POST':
        if request.user.is_authenticated:
            form = ClienteForm(request.POST, instance=cliente)
        else:
            form = ClienteForm(request.POST)

        if form.is_valid():
            cif = form.cleaned_data['cif']
            email = form.cleaned_data['email']  # ✅ Usamos email
            password = form.cleaned_data['password1']

            if Cliente.objects.filter(cif=cif).exists():
                form.add_error('cif', 'Ya existe un cliente con este CIF.')
                return render(request, 'clientes/clientes.html', {'form': form})

            # ✅ Verificamos si existe el email
            if Cliente.objects.filter(email=email).exists():
                form.add_error('email', 'Ya existe un cliente con este email.')
                return render(request, 'clientes/clientes.html', {'form': form})

            # ✅ Guardar Cliente con email como usuario
            nuevo_cliente = form.save(commit=False)
            nuevo_cliente.usuario = email  # ✅ El usuario es el email
            nuevo_cliente.password = make_password(password)
            nuevo_cliente.save()

            # Activar sesión del cliente
            request.session['cliente_persistent_id'] = nuevo_cliente.id

            messages.success(request, "Registro completado con éxito.")
            return redirect('checkout')

    return render(request, 'clientes/clientes.html', {'form': form})

def tramitar_pedido(request):
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            email = login_form.cleaned_data['email']  # ✅ Cambiado de usuario a email
            password = login_form.cleaned_data['password']

            try:
                # ✅ Buscamos por usuario (que ahora es el email)
                cliente = Cliente.objects.get(usuario=email)
                if check_password(password, cliente.password):
                    request.session['cliente_persistent_id'] = cliente.id
                    messages.success(request, f"Bienvenido {cliente.nombre}")
                    return redirect('checkout')
                else:
                    messages.error(request, "Contraseña incorrecta.")
            except Cliente.DoesNotExist:
                messages.error(request, "Email no encontrado.")
    else:
        login_form = LoginForm()

    return render(request, 'clientes/tramitar_pedido.html', {
        'login_form': login_form
    })

def pedido_confirmado(request):
    return render(request, 'clientes/pedido_confirmado.html')


def solicitar_reset(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')  # o podrías pedir el email en lugar del usuario
        try:
            cliente = Cliente.objects.get(usuario=usuario)
            token = cliente.generar_token()
            reset_link = request.build_absolute_uri(f"/clientes/reset/{token}/")

            # Enviar email con el enlace
            send_mail(
                subject="Recuperación de contraseña",
                message=(
                    f"Hola {cliente.usuario},\n\n"
                    f"Has solicitado restablecer tu contraseña.\n"
                    f"Pulsa en este enlace para crear una nueva:\n{reset_link}\n\n"
                    f"Si no fuiste tú, ignora este mensaje."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[cliente.email],
                fail_silently=False,
            )

            messages.success(request, "Te hemos enviado un enlace a tu correo.")
            return redirect('solicitar_reset')  # redirige a la misma vista o a donde prefieras
        except Cliente.DoesNotExist:
            messages.error(request, "No existe un cliente con ese usuario.")

    return render(request, 'clientes/solicitar_reset.html')

def reset_password(request, token):
    try:
        cliente = Cliente.objects.get(reset_token=token)
        if cliente.reset_token_expiration < timezone.now():
            messages.error(request, "El enlace ha caducado.")
            return redirect('solicitar_reset')
    except Cliente.DoesNotExist:
        messages.error(request, "Token inválido.")
        return redirect('solicitar_reset')

    if request.method == 'POST':
        nueva_password = request.POST.get('password1')

        # Validación: no permitir repetir la misma contraseña
        if check_password(nueva_password, cliente.password):
            messages.error(request, "La nueva contraseña no puede ser igual a la anterior.")
            return render(request, 'clientes/reset_password.html', {'token': token})

        # Guardar nueva contraseña
        cliente.password = make_password(nueva_password)
        cliente.reset_token = None
        cliente.reset_token_expiration = None
        cliente.save()

        messages.success(request, "Tu contraseña ha sido restablecida con éxito.")
        return redirect('tienda')

    return render(request, 'clientes/reset_password.html', {'token': token})

def logout_cliente(request):
    # Solo eliminar la sesión del cliente, no toda la sesión
    if 'cliente_persistent_id' in request.session:
        del request.session['cliente_persistent_id']
    return redirect('tienda')

def zona_cliente(request):
    cliente_id = request.session.get('cliente_persistent_id')
    if not cliente_id:
        return redirect('tramitar_pedido')

    cliente = Cliente.objects.get(id=cliente_id)
    return render(request, 'clientes/zona/index_cliente.html', {'cliente': cliente})

def confirmar_pedido(request):
    cliente_id = request.session.get('cliente_persistent_id')
    if not cliente_id:
        return redirect('tramitar_pedido')  # por si alguien accede sin estar logueado

    return render(request, 'clientes/confirmar_pedido.html')

def editar_datos_cliente(request):
    cliente_id = request.session.get('cliente_persistent_id')
    if not cliente_id:
        return redirect('tramitar_pedido')

    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        form = ClienteEdicionForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Tus datos han sido actualizados correctamente.")
            return redirect('zona_cliente')
    else:
        form = ClienteEdicionForm(instance=cliente)

    return render(request, 'clientes/zona/editar_datos_cliente.html', {'form': form, 'cliente': cliente})


def historial_pedidos(request):
    cliente_id = request.session.get('cliente_persistent_id')
    if not cliente_id:
        return redirect('tramitar_pedido')

    # Obtener el cliente
    cliente = Cliente.objects.get(id=cliente_id)
    
    # Obtener solo pedidos PAGADOS del cliente, ordenados por fecha descendente
    from ventas.models import Pedido
    pedidos = Pedido.objects.filter(
        cliente=cliente, 
        pagado=True
    ).order_by('-fecha')
    
    return render(request, 'clientes/zona/historial_pedidos.html', {
        'cliente': cliente,
        'pedidos': pedidos
    })

def detalle_pedido(request, pedido_id):
    cliente_id = request.session.get('cliente_persistent_id')
    if not cliente_id:
        return redirect('tramitar_pedido')

    # Verificar que el pedido pertenece al cliente
    from ventas.models import Pedido, LineaPedido
    try:
        pedido = Pedido.objects.get(id=pedido_id, cliente_id=cliente_id, pagado=True)
    except Pedido.DoesNotExist:
        messages.error(request, "Pedido no encontrado")
        return redirect('historial_pedidos')

    # Obtener las líneas del pedido
    lineas_pedido = LineaPedido.objects.filter(pedido=pedido)
    
    return render(request, 'clientes/zona/detalle_pedido.html', {
        'pedido': pedido,
        'lineas_pedido': lineas_pedido
    })

def localidades_por_provincia(request):
    provincia = request.GET.get('provincia')
    localidades = []

    if provincia:
        localidades = Cliente.objects.filter(provincia=provincia).order_by('localidad').values_list('localidad', flat=True).distinct()

    return JsonResponse({'localidades': list(localidades)})