from .models import Cliente

def cliente_context(request):
    """
    Context processor separado que NO se ve afectado por login de admin
    """
    # SIEMPRE procesar cliente, independientemente del usuario admin
    cliente = None
    cliente_id = request.session.get('cliente_id')
    
    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            # Si el cliente no existe, limpiar la sesión
            if 'cliente_id' in request.session:
                del request.session['cliente_id']
                request.session.modified = True
    
    return {'cliente': cliente}