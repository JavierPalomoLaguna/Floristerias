from .models import Cliente

def cliente_context(request):
    """
    Context processor que usa sesión persistente para clientes
    No se ve afectado por login/logout de admin
    """
    cliente = None
    
    # Usar una clave de sesión específica que NO sea afectada por login de admin
    cliente_session_key = 'cliente_persistent_id'
    cliente_id = request.session.get(cliente_session_key)
    
    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            # Si el cliente no existe, limpiar la sesión
            if cliente_session_key in request.session:
                del request.session[cliente_session_key]
                request.session.modified = True
    
    return {'cliente': cliente}