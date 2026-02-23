from .models import Cliente

def cliente_context(request):
    """
    Context processor que usa sesión persistente para clientes
    No se ve afectado por login/logout de admin
    """
    cliente = None
    cliente_id = request.session.get('cliente_persistent_id')
    
    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            if 'cliente_persistent_id' in request.session:
                del request.session['cliente_persistent_id']
                request.session.modified = True
    
    return {'cliente': cliente}