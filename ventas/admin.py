from django.contrib import admin
from django.utils import timezone
from django.urls import reverse, path
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from .models import Pedido, LineaPedido, ConfiguracionEnvio, Devolucion, LineaDevolucion
import csv
from datetime import datetime
from .utils import enviar_email_pedido_confirmado
from django.db.models import Q

class LineaPedidoInline(admin.TabularInline):
    model = LineaPedido
    extra = 0
    readonly_fields = ('producto', 'cantidad', 'subtotal')
    can_delete = False

@admin.register(ConfiguracionEnvio)
class ConfiguracionEnvioAdmin(admin.ModelAdmin):
    list_display = ('umbral_envio_gratis', 'costo_envio_estandar', 'activo')
    list_editable = ('activo',)
    
    def has_add_permission(self, request):
        if ConfiguracionEnvio.objects.exists():
            return False
        return True

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'cliente_clickable', 
        'fecha', 
        'pagado', 
        'metodo_pago',
        'enviado',
        'gastos_envio',  
        'envio_gratis',  
        'get_factura_link',
        'codigo_autorizacion', 
        'codigo_respuesta',      
        'descripcion_error',     
        'fecha_pago', 
        'hora_pago', 
        'get_total'
    )
    list_filter = (
        'pagado',
        'enviado',
        'envio_gratis',  
        'metodo_pago',
        ('fecha', admin.DateFieldListFilter),
        ('fecha_pago', admin.DateFieldListFilter),
        'pais_tarjeta',
    )
    search_fields = (
        'cliente__nombre', 
        'id', 
        'codigo_autorizacion',
        'codigo_respuesta',      
        'descripcion_error'      
    )
    readonly_fields = ('fecha_envio',)
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    inlines = [LineaPedidoInline]
    
    # ✅ PAGINACIÓN - 10 elementos por página
    list_per_page = 10
    
    # ✅ ACCIONES INCLUYENDO EXPORTAR CSV Y REENVIAR EMAIL
    actions = ['marcar_como_enviado', 'exportar_csv', 'reenviar_email_confirmacion']
    
    def exportar_csv(self, request, queryset):
        """Exporta los pedidos seleccionados a CSV"""
        
        # Si no hay selección, exporta TODOS los pedidos
        if not queryset:
            queryset = Pedido.objects.all()
        
        # Crear respuesta HTTP con archivo CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="pedidos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # ✅ CABECERAS COMPLETAS (cliente + pedido + productos)
        headers = [
            # Información del pedido
            'ID Pedido', 'Fecha Pedido', 'Método Pago', 'Pagado', 'Enviado',
            'Gastos Envío', 'Envío Gratis', 'Base Imponible', 'IVA Total', 'Total',
            
            # Información del cliente
            'Cliente ID', 'Nombre Cliente', 'Apellidos', 'Email', 'Teléfono', 'CIF/DNI',
            'Dirección', 'Localidad', 'Provincia', 'Código Postal',
            
            # Información de pago (si existe)
            'Código Autorización', 'Fecha Pago', 'Hora Pago', 'País Tarjeta',
            'Código Respuesta', 'Descripción Error'
        ]
        
        writer.writerow(headers)
        
        # ✅ DATOS DE CADA PEDIDO
        for pedido in queryset:
            row = [
                # Información del pedido
                pedido.id,
                pedido.fecha.strftime("%d/%m/%Y %H:%M"),
                pedido.get_metodo_pago_display(),
                'Sí' if pedido.pagado else 'No',
                'Sí' if pedido.enviado else 'No',
                f"{pedido.gastos_envio:.2f}€",
                'Sí' if pedido.envio_gratis else 'No',
                f"{pedido.base_imponible:.2f}€",
                f"{pedido.iva_total:.2f}€",
                f"{pedido.total:.2f}€",
                
                # Información del cliente
                pedido.cliente.id,
                pedido.cliente.nombre,
                pedido.cliente.apellidos,
                pedido.cliente.email,
                pedido.cliente.telefono or '',
                pedido.cliente.cif or '',
                f"{pedido.cliente.calle} {pedido.cliente.numero_calle}",
                pedido.cliente.localidad,
                pedido.cliente.provincia,
                pedido.cliente.codigo_postal,
                
                # Información de pago
                pedido.codigo_autorizacion or '',
                pedido.fecha_pago.strftime("%d/%m/%Y") if pedido.fecha_pago else '',
                pedido.hora_pago.strftime("%H:%M") if pedido.hora_pago else '',
                pedido.pais_tarjeta or '',
                pedido.codigo_respuesta or '',
                pedido.descripcion_error or ''
            ]
            
            writer.writerow(row)
        
        return response
    
    exportar_csv.short_description = "📊 Exportar pedidos seleccionados a CSV"
    
    def reenviar_email_confirmacion(self, request, queryset):
        """Reenvía email de confirmación con factura"""
        for pedido in queryset:
            if pedido.pagado:  # Solo enviar si está pagado
                try:
                    enviar_email_pedido_confirmado(pedido)
                    self.message_user(request, f"✅ Email reenviado para pedido {pedido.id}")
                except Exception as e:
                    self.message_user(request, f"❌ Error enviando email para pedido {pedido.id}: {e}", level=messages.ERROR)
            else:
                self.message_user(request, f"⚠️ Pedido {pedido.id} no está pagado", level=messages.WARNING)
    
    reenviar_email_confirmacion.short_description = "📧 Reenviar email de confirmación"
    
    # ✅ CLIENTE CLICKABLE
    def cliente_clickable(self, obj):
        url = reverse('admin:ventas_pedido_detalle', args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, obj.cliente.nombre)
    cliente_clickable.short_description = 'Cliente'
    cliente_clickable.admin_order_field = 'cliente__nombre'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('pedido/<int:pedido_id>/detalle/', 
                 self.admin_site.admin_view(self.pedido_detalle_view),
                 name='ventas_pedido_detalle'),
        ]
        return custom_urls + urls
    
    # ✅ VISTA DETALLE PEDIDO
    def pedido_detalle_view(self, request, pedido_id):
        try:
            pedido = Pedido.objects.get(id=pedido_id)
            lineas_pedido = LineaPedido.objects.filter(pedido=pedido)
            cliente = pedido.cliente
            
            context = {
                'pedido': pedido,
                'cliente': cliente,
                'lineas_pedido': lineas_pedido,
                'opts': self.model._meta,
                'title': f'Detalles del Pedido {pedido.id}',
            }
            return render(request, 'admin/ventas/pedido_detalle.html', context)
            
        except Pedido.DoesNotExist:
            self.message_user(request, "Pedido no encontrado", level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:ventas_pedido_changelist'))
    
    def marcar_como_enviado(self, request, queryset):
        updated = queryset.update(enviado=True, fecha_envio=timezone.now())
        self.message_user(request, f"{updated} pedido(s) marcado(s) como enviado(s)")
    marcar_como_enviado.short_description = "Marcar pedidos seleccionados como enviados"
    
    def get_factura_link(self, obj):
        if obj.pagado:
            return format_html('<a href="{}" target="_blank">📄 Ver Factura {}</a>', 
                             reverse('ver_factura', args=[obj.id]), obj.id)
        return "❌ Pendiente pago"
    get_factura_link.short_description = 'Factura'
    get_factura_link.allow_tags = True
    
    def get_total(self, obj):
        return f"{obj.total:.2f} €" if obj.total else "0.00 €"
    get_total.short_description = 'Total'

    
@admin.register(LineaPedido)
class LineaPedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'producto', 'cantidad', 'subtotal')
    search_fields = ('pedido__id', 'producto__nombre')
    readonly_fields = ('subtotal',)

# ✅ MEJORADO: LineaDevolucionInline con mejor visualización
class LineaDevolucionInline(admin.TabularInline):
    model = LineaDevolucion
    extra = 0
    fields = ['get_nombre_producto', 'cantidad_devuelta', 'precio_unitario_devolucion', 'razon']
    readonly_fields = ['get_nombre_producto', 'precio_unitario_devolucion', 'linea_pedido_original']
    can_delete = False  # ✅ Quita el checkbox "¿Eliminar?"
    
    # ✅ Quita "Agregar Línea de devolución adicional" COMPLETAMENTE
    def has_add_permission(self, request, obj=None):
        # Nunca permitir añadir líneas manualmente
        return False
    
    def get_nombre_producto(self, obj):
        return obj.linea_pedido_original.producto.nombre
    get_nombre_producto.short_description = 'Producto'

@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'pedido', 'cliente_info', 'fecha_solicitud', 'estado', 
        'importe_total_devolucion', 'acciones_devolucion'
    ]
    list_filter = ['estado', 'fecha_solicitud']
    search_fields = ['pedido__id', 'pedido__cliente__nombre']
    readonly_fields = ['fecha_solicitud', 'fecha_procesamiento', 'base_imponible_devolucion', 'iva_devolucion', 'importe_total_devolucion', 'pedido_info']
    inlines = [LineaDevolucionInline]
    actions = ['aprobar_devoluciones', 'rechazar_devoluciones', 'procesar_devoluciones']
    
    # ✅ AGREGAR BOTÓN "CREAR DEVOLUCIÓN" ENCIMA DE LA LISTA
    change_list_template = 'admin/ventas/devolucion_change_list.html'
    
    fieldsets = (
        ('Información General', {
            'fields': ('pedido_info', 'estado', 'motivo', 'notas_internas')
        }),
        ('Fechas', {
            'fields': ('fecha_solicitud', 'fecha_procesamiento')
        }),
        ('Importes de Devolución', {
            'fields': ('base_imponible_devolucion', 'iva_devolucion', 'importe_total_devolucion', 'gastos_envio_devolucion')
        }),
    )
    
    def cliente_info(self, obj):
        return obj.pedido.cliente.nombre
    cliente_info.short_description = 'Cliente'
    
    # ✅ NUEVO: Mostrar pedido como texto simple sin widget ForeignKey
    def pedido_info(self, obj):
        return f"Pedido {obj.pedido.id} - {obj.pedido.cliente.nombre}"
    pedido_info.short_description = 'Pedido'
    
    def acciones_devolucion(self, obj):
        """Solo información de estado en la lista"""
        if obj.estado == 'solicitada':
            return "⏳ Solicitada"
        elif obj.estado == 'aprobada':
            return "✅ Aprobada - Pendiente de completar"
        elif obj.estado == 'rechazada':
            return "❌ Rechazada"
        elif obj.estado == 'procesada':
            return "🔄 En proceso"
        elif obj.estado == 'completada':
            return "🏁 Completada"
        return "-"
    acciones_devolucion.short_description = 'Acciones'
        
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('devolucion/<int:devolucion_id>/procesar/', 
                self.admin_site.admin_view(self.procesar_devolucion_view),
                name='ventas_devolucion_process'),
            # ✅ NUEVA URL PARA BUSCAR PEDIDOS Y CREAR DEVOLUCIÓN
            path('crear-devolucion/', 
                self.admin_site.admin_view(self.crear_devolucion_view),
                name='ventas_devolucion_crear'),
            path('crear-devolucion-pedido/<int:pedido_id>/', 
                self.admin_site.admin_view(self.crear_devolucion_pedido_view),
                name='ventas_devolucion_crear_pedido'),            
        ]
        return custom_urls + urls
    
    # ✅ VISTA PARA BUSCAR PEDIDOS (ESTE MÉTODO FALTABA)
    def crear_devolucion_view(self, request):
        query = request.GET.get('q', '')
        pedidos = Pedido.objects.none()
        
        if query:
            # Buscar por número de pedido, nombre de cliente o email
            pedidos = Pedido.objects.filter(
                Q(id__icontains=query) |
                Q(cliente__nombre__icontains=query) |
                Q(cliente__apellidos__icontains=query) |
                Q(cliente__email__icontains=query)
            ).select_related('cliente').prefetch_related('lineapedido_set')[:50]  # Límite de 50 resultados
        
        context = {
            'title': 'Buscar Pedido para Devolución',
            'pedidos': pedidos,
            'query': query,
            'opts': self.model._meta,
        }
        return render(request, 'admin/ventas/buscar_pedido_devolucion.html', context)
    
    # ✅ VISTA PARA CREAR DEVOLUCIÓN DE UN PEDIDO ESPECÍFICO
    def crear_devolucion_pedido_view(self, request, pedido_id):
        try:
            pedido = Pedido.objects.get(id=pedido_id)
            lineas_pedido = LineaPedido.objects.filter(pedido=pedido)
            
            if request.method == 'POST':
                # Procesar el formulario de devolución
                motivo = request.POST.get('motivo', '')
                notas_internas = request.POST.get('notas_internas', '')                
                
                # ✅ VALIDAR QUE HAY AL MENOS UN PRODUCTO SELECCIONADO
                productos_seleccionados = False
                lineas_con_devolucion = []
                
                for linea in lineas_pedido:
                    cantidad_key = f'cantidad_{linea.id}'
                    cantidad_devuelta = request.POST.get(cantidad_key, '0')
                    
                    if cantidad_devuelta and int(cantidad_devuelta) > 0:
                        productos_seleccionados = True
                        lineas_con_devolucion.append((linea, int(cantidad_devuelta)))
                
                # ✅ SI NO HAY PRODUCTOS SELECCIONADOS, MOSTRAR ERROR
                if not productos_seleccionados:
                    messages.error(request, '❌ Debes seleccionar al menos un producto para devolver')
                    context = {
                        'title': f'Crear Devolución - Pedido {pedido.id}',
                        'pedido': pedido,
                        'lineas_pedido': lineas_pedido,
                        'opts': self.model._meta,
                    }
                    return render(request, 'admin/ventas/crear_devolucion_pedido.html', context)
                
                # ✅ LÓGICA PARA DETERMINAR SI DEVOLVER GASTOS DE ENVÍO
                from decimal import Decimal
                devolver_gastos_envio = False
                gastos_envio_a_devolver = Decimal('0.00')
                
                # Verificar si el usuario marcó explícitamente devolver gastos de envío
                if request.POST.get('devolver_gastos_envio'):
                    # 1. Si es una devolución TOTAL (todos los productos), devolver gastos de envío completos
                    total_productos_pedido = sum(linea.cantidad for linea in lineas_pedido)
                    total_productos_devueltos = sum(cantidad for _, cantidad in lineas_con_devolucion)
                    
                    if total_productos_devueltos >= total_productos_pedido:
                        # Devolución total - devolver gastos de envío completos
                        gastos_envio_a_devolver = pedido.gastos_envio
                        devolver_gastos_envio = True
                        print(f"✅ Devolución TOTAL - Gastos de envío a devolver: {gastos_envio_a_devolver}€")
                    else:
                        # Devolución parcial - el admin decide si devolver gastos proporcionales
                        # Por defecto, no devolvemos gastos en parciales
                        gastos_envio_a_devolver = Decimal('0.00')
                        devolver_gastos_envio = False
                        print("ℹ️ Devolución PARCIAL - No se devuelven gastos de envío por defecto")
                
                # ✅ CREAR LA DEVOLUCIÓN SOLO SI HAY PRODUCTOS SELECCIONADOS
                devolucion = Devolucion.objects.create(
                    pedido=pedido,
                    estado='solicitada',
                    motivo=motivo,
                    notas_internas=notas_internas,
                    fecha_solicitud=timezone.now(),
                    # ✅ AÑADIR GASTOS DE ENVÍO SI SE SOLICITA
                    gastos_envio_devolucion=gastos_envio_a_devolver
                )
                
                # Procesar las líneas de devolución
                for linea, cantidad_devuelta in lineas_con_devolucion:
                    LineaDevolucion.objects.create(
                        devolucion=devolucion,
                        linea_pedido_original=linea,
                        cantidad_devuelta=cantidad_devuelta,
                        precio_unitario_devolucion=linea.producto.precio,
                       
                    )
                
                # ✅ CALCULAR IMPORTES AUTOMÁTICAMENTE
                devolucion.calcular_importes()
                
                # Mensaje informativo sobre gastos de envío
                mensaje_gastos = ""
                if devolver_gastos_envio:
                    mensaje_gastos = f" (incluyendo {gastos_envio_a_devolver}€ de gastos de envío)"
                else:
                    mensaje_gastos = " (sin gastos de envío)"
                
                messages.success(request, f'✅ Devolución {devolucion.id} creada exitosamente para el pedido {pedido.id}{mensaje_gastos}')
                return HttpResponseRedirect(reverse('admin:ventas_devolucion_change', args=[devolucion.id]))
            
            context = {
                'title': f'Crear Devolución - Pedido {pedido.id}',
                'pedido': pedido,
                'lineas_pedido': lineas_pedido,
                'opts': self.model._meta,
            }
            return render(request, 'admin/ventas/crear_devolucion_pedido.html', context)
            
        except Pedido.DoesNotExist:
            messages.error(request, 'Pedido no encontrado')
            return HttpResponseRedirect(reverse('admin:ventas_devolucion_crear'))

    # ✅ MÉTODO PROCESAR DEVOLUCIÓN
    def procesar_devolucion_view(self, request, devolucion_id):
        try:
            devolucion = Devolucion.objects.get(id=devolucion_id)
            if devolucion.estado == 'aprobada':
                # Aquí iría la lógica para procesar la devolución
                # Por ahora solo cambiamos el estado
                devolucion.estado = 'procesada'
                devolucion.fecha_procesamiento = timezone.now()
                devolucion.save()
                self.message_user(request, f"✅ Devolución {devolucion.id} procesada exitosamente")
            else:
                self.message_user(request, "La devolución debe estar aprobada para procesarse", level=messages.ERROR)
        except Devolucion.DoesNotExist:
            self.message_user(request, "Devolución no encontrada", level=messages.ERROR)
        
        return HttpResponseRedirect(reverse('admin:ventas_devolucion_changelist'))
    def save_model(self, request, obj, form, change):
        """Se ejecuta cuando se guarda una devolución desde el admin"""
        
        # Verificar si el estado está cambiando a "completada"
        estado_cambiando_a_completada = False
        if change and 'estado' in form.changed_data and obj.estado == 'completada':
            estado_cambiando_a_completada = True
            print(f"🔔 DEBUG: Estado cambiando a 'completada' para devolución {obj.id}")
        
        # Guardar primero el objeto
        super().save_model(request, obj, form, change)
        
        # ✅ LÓGICA CUANDO EL ESTADO CAMBIA A "COMPLETADA"
        if estado_cambiando_a_completada:
            try:
                # VERIFICAR que tiene líneas de devolución
                if not obj.lineas.exists():
                    self.message_user(request, "❌ La devolución no tiene productos para devolver", level=messages.ERROR)
                    return

                print(f"🔔 DEBUG: Ejecutando lógica de devolución completada para #{obj.id}")

                # 1. ACTUALIZAR STOCK
                stock_actualizado = []
                for linea in obj.lineas.all():
                    producto = linea.linea_pedido_original.producto
                    stock_anterior = producto.stock
                    producto.stock += linea.cantidad_devuelta
                    producto.save()
                    
                    stock_actualizado.append({
                        'producto': producto.nombre,
                        'cantidad': linea.cantidad_devuelta,
                        'stock_anterior': stock_anterior,
                        'stock_nuevo': producto.stock
                    })
                    
                    print(f"✅ Stock incrementado: {producto.nombre} +{linea.cantidad_devuelta} unidades (de {stock_anterior} a {producto.stock})")

                # 2. CALCULAR IMPORTES (por si acaso)
                obj.calcular_importes()
                print(f"✅ Importes calculados: {obj.importe_total_devolucion}€")

                # 3. GENERAR FACTURA NEGATIVA (CONTRAFACTURA)
                from .utils import generar_factura_pdf
                pdf_content = generar_factura_pdf(
                    pedido=obj.pedido, 
                    devolucion=obj
                )
                print(f"✅ Factura negativa generada para devolución {obj.id}")

                # 4. ENVIAR EMAIL CON LA FACTURA NEGATIVA
                try:
                    self.enviar_email_devolucion_completada(obj, pdf_content)
                    email_enviado = True
                    print(f"✅ Email enviado a {obj.pedido.cliente.email}")
                    self.message_user(request, f"✅ Devolución {obj.id} COMPLETADA - Stock actualizado y email enviado")
                except Exception as e:
                    email_enviado = False
                    print(f"⚠️ Error enviando email: {e}")
                    self.message_user(request, f"✅ Devolución {obj.id} COMPLETADA - Stock actualizado (email no enviado: {e})", level=messages.WARNING)

                # 5. ACTUALIZAR FECHA DE PROCESAMIENTO
                obj.fecha_procesamiento = timezone.now()
                obj.save()
                
            except Exception as e:
                print(f"❌ Error completando devolución {obj.id}: {e}")
                self.message_user(request, f"❌ Error completando devolución: {e}", level=messages.ERROR)
        
        # ✅ RECALCULAR IMPORTES SI SE MODIFICAN LOS GASTOS DE ENVÍO
        elif 'gastos_envio_devolucion' in form.changed_data:
            print(f"DEBUG: Gastos de envío cambiados, recalculando importes...")
            obj.calcular_importes()
        
    def completar_devolucion_view(self, request, devolucion_id):
        try:
            devolucion = Devolucion.objects.get(id=devolucion_id)
            print(f"🔔 DEBUG: Devolución encontrada - estado: {devolucion.estado}")
            
            # VERIFICACIÓN MEJORADA del estado
            if devolucion.estado != 'aprobada':
                self.message_user(request, "❌ Solo se pueden completar devoluciones aprobadas", level=messages.ERROR)
                print(f"❌ DEBUG: Devolución no está aprobada, estado actual: {devolucion.estado}")
                return HttpResponseRedirect(reverse('admin:ventas_devolucion_change', args=[devolucion_id]))
            
            # VERIFICAR que tiene líneas de devolución
            if not devolucion.lineas.exists():
                print(f"❌ DEBUG: Devolución no tiene líneas")
                self.message_user(request, "❌ La devolución no tiene productos para devolver", level=messages.ERROR)
                return HttpResponseRedirect(reverse('admin:ventas_devolucion_change', args=[devolucion_id]))

            # 1. ACTUALIZAR STOCK - CON MEJOR MANEJO DE ERRORES
            stock_actualizado = []
            try:
                for linea in devolucion.lineas.all():
                    producto = linea.linea_pedido_original.producto
                    stock_anterior = producto.stock
                    producto.stock += linea.cantidad_devuelta
                    producto.save()
                    
                    stock_actualizado.append({
                        'producto': producto.nombre,
                        'cantidad': linea.cantidad_devuelta,
                        'stock_anterior': stock_anterior,
                        'stock_nuevo': producto.stock
                    })
                    
                    print(f"✅ Stock incrementado: {producto.nombre} +{linea.cantidad_devuelta} unidades (de {stock_anterior} a {producto.stock})")
                    
            except Exception as e:
                self.message_user(request, f"❌ Error crítico actualizando stock: {e}", level=messages.ERROR)
                return HttpResponseRedirect(reverse('admin:ventas_devolucion_change', args=[devolucion_id]))

            # 2. CALCULAR IMPORTES
            try:
                devolucion.calcular_importes()
                print(f"✅ Importes calculados: {devolucion.importe_total_devolucion}€")
            except Exception as e:
                self.message_user(request, f"⚠️ Devolución completada pero error calculando importes: {e}", level=messages.WARNING)

            # 3. GENERAR FACTURA NEGATIVA (CONTRAFACTURA)
            try:
                from .utils import generar_factura_pdf
                pdf_content = generar_factura_pdf(
                    pedido=devolucion.pedido, 
                    devolucion=devolucion
                )
                print(f"✅ Factura negativa generada para devolución {devolucion.id}")
            except Exception as e:
                self.message_user(request, f"❌ Error generando factura negativa: {e}", level=messages.ERROR)
                return HttpResponseRedirect(reverse('admin:ventas_devolucion_change', args=[devolucion_id]))

            # 4. ENVIAR EMAIL CON LA FACTURA NEGATIVA - CORREGIDO
            email_enviado = False
            try:
                # Pasar el pdf_content al método de email
                self.enviar_email_devolucion_completada(devolucion, pdf_content)
                email_enviado = True
                print(f"✅ Email enviado a {devolucion.pedido.cliente.email}")
            except Exception as e:
                self.message_user(request, f"⚠️ Devolución completada pero error enviando email: {e}", level=messages.WARNING)
                email_enviado = False

            # 5. CAMBIAR ESTADO (SOLO si todo lo anterior fue exitoso)
            try:
                devolucion.estado = 'completada'
                devolucion.fecha_procesamiento = timezone.now()
                devolucion.save()
                
                # Mensaje final según resultado
                if email_enviado:
                    self.message_user(request, f"✅ Devolución {devolucion.id} COMPLETADA - Stock actualizado y email enviado")
                else:
                    self.message_user(request, f"✅ Devolución {devolucion.id} COMPLETADA - Stock actualizado (email no enviado)")
                    
            except Exception as e:
                self.message_user(request, f"❌ Error finalizando devolución: {e}", level=messages.ERROR)
                
        except Devolucion.DoesNotExist:
            self.message_user(request, "❌ Devolución no encontrada", level=messages.ERROR)
        
        return HttpResponseRedirect(reverse('admin:ventas_devolucion_change', args=[devolucion_id]))


    # ✅ AÑADE ESTE MÉTODO NUEVO A LA CLASE DevolucionAdmin
    def enviar_email_devolucion_completada(self, devolucion, pdf_content):
        """Envía email de confirmación de devolución con factura negativa adjunta"""
        try:
            print(f"🔔 DEBUG: enviar_email_devolucion_completada ejecutado para devolución {devolucion.id}")
            
            from django.core.mail import EmailMessage
            from django.conf import settings
            
            # Asunto del email
            asunto = f'✅ Devolución Completada - Pedido {devolucion.pedido.id} - LA TRASTIENDA S.L.'
            print(f"🔔 DEBUG: Asunto: {asunto}")
            print(f"🔔 DEBUG: Destinatario: {devolucion.pedido.cliente.email}")
            
            # Cuerpo del email
            mensaje = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h2 style="color: #2c3e50;">Devolución Completada - Pedido {devolucion.pedido.id}</h2>
                
                <p>Hola {devolucion.pedido.cliente.nombre},</p>
                
                <p>Tu devolución para el pedido <strong>{devolucion.pedido.id}</strong> ha sido procesada exitosamente.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3 style="color: #2c3e50; margin-top: 0;">📦 Resumen de la Devolución</h3>
                    <p><strong>Número de Devolución:</strong> DEV-{devolucion.id}</p>
                    <p><strong>Fecha de Procesamiento:</strong> {timezone.now().strftime('%d/%m/%Y %H:%M')}</p>
                    <p><strong>Importe a Devolver:</strong> -{devolucion.importe_total_devolucion:.2f}€</p>
                    <p><strong>Motivo:</strong> {devolucion.motivo}</p>
                </div>
                
                <p>📎 Adjuntamos la factura de devolución (contrafactura) en formato PDF.</p>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #e8f5e8; border-radius: 5px;">
                    <h4 style="color: #27ae60; margin-top: 0;">💳 Información del Reembolso</h4>
                    <p>El importe será reembolsado utilizando el mismo método de pago utilizado en la compra original.</p>
                    <p>El proceso de reembolso puede tardar entre 3-5 días hábiles en reflejarse en tu cuenta.</p>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #e3f2fd; border-radius: 5px;">
                    <h4 style="color: #1976d2; margin-top: 0;">📞 ¿Necesitas ayuda?</h4>
                    <p>Si tienes alguna pregunta sobre tu devolución, contáctanos:</p>
                    <p>📧 Email: contabilidad@latrastienda.es<br>
                    📞 Teléfono: 666666666</p>
                </div>
                
                <p style="margin-top: 20px; color: #7f8c8d;">¡Gracias por confiar en nosotros!</p>
                <p><strong>El equipo de LA TRASTIENDA S.L.</strong></p>
            </body>
            </html>
            """
            
            # Crear el email
            email = EmailMessage(
                subject=asunto,
                body=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[devolucion.pedido.cliente.email],
                reply_to=['contabilidad@latrastienda.es'],
            )
            
            # Configurar como HTML
            email.content_subtype = "html"
            
            # Adjuntar PDF de la factura negativa
            print(f"🔔 DEBUG: Adjuntando PDF de {len(pdf_content)} bytes")
            email.attach(
                filename=f"factura_devolucion_{devolucion.id}.pdf",
                content=pdf_content,
                mimetype="application/pdf"
            )
            
            # Enviar email
            print(f"🔔 DEBUG: Enviando email...")
            email.send(fail_silently=False)
            
            print(f"✅ Email de devolución enviado a {devolucion.pedido.cliente.email} para devolución {devolucion.id}")
            return True
            
        except Exception as e:
            print(f"❌ ERROR CRÍTICO enviando email de devolución {devolucion.id}: {e}")
            import traceback
            print(f"❌ TRACEBACK: {traceback.format_exc()}")
            raise e

  
            
    def aprobar_devoluciones(self, request, queryset):
        for devolucion in queryset:
            if devolucion.estado == 'solicitada':
                devolucion.estado = 'aprobada'
                devolucion.save()
                devolucion.calcular_importes()
                self.message_user(request, f"✅ Devolución {devolucion.id} aprobada")
    aprobar_devoluciones.short_description = "✅ Aprobar devoluciones seleccionadas"
    
    def rechazar_devoluciones(self, request, queryset):
        for devolucion in queryset:
            if devolucion.estado == 'solicitada':
                devolucion.estado = 'rechazada'
                devolucion.save()
                self.message_user(request, f"❌ Devolución {devolucion.id} rechazada")
    rechazar_devoluciones.short_description = "❌ Rechazar devoluciones seleccionadas"
    
    def procesar_devoluciones(self, request, queryset):
        for devolucion in queryset:
            if devolucion.estado == 'aprobada':
                # Lógica simplificada por ahora
                devolucion.estado = 'procesada'
                devolucion.fecha_procesamiento = timezone.now()
                devolucion.save()
                self.message_user(request, f"✅ Devolución {devolucion.id} procesada")
            else:
                self.message_user(request, f"⚠️ Devolución {devolucion.id} no está aprobada", level=messages.WARNING)
    procesar_devoluciones.short_description = "🔄 Procesar devoluciones"