from django.db import models
from tienda.models import Productos
from clientes.models import Cliente
from decimal import Decimal
from django.utils import timezone


# Create your models here.

class ConfiguracionEnvio(models.Model):
    umbral_envio_gratis = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=300.00,
        verbose_name="Umbral para envío gratis (€)"
    )
    costo_envio_estandar = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=5.95,
        verbose_name="Costo envío estándar (€)"
    )
    activo = models.BooleanField(default=True, verbose_name="Configuración activa")
    
    class Meta:
        verbose_name = 'configuración de envío'
        verbose_name_plural = 'configuraciones de envío'
    
    def __str__(self):
        return f"Envío: {self.costo_envio_estandar}€ / Gratis desde {self.umbral_envio_gratis}€"
    
    def save(self, *args, **kwargs):
        # Solo permitir una configuración activa
        if self.activo:
            ConfiguracionEnvio.objects.exclude(pk=self.pk).update(activo=False)
        super().save(*args, **kwargs)

class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    pagado = models.BooleanField(default=False)
    metodo_pago = models.CharField(max_length=20, choices=[('tarjeta', 'Tarjeta'), ('bizum', 'Bizum')])
    enviado = models.BooleanField(default=False, verbose_name="Pedido enviado")
    fecha_envio = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de envío")
    gastos_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Gastos de envío")
    envio_gratis = models.BooleanField(default=False, verbose_name="Envío gratis")

    # Campos adicionales para trazabilidad Redsys
    codigo_autorizacion = models.CharField(max_length=10, blank=True, null=True)
    fecha_pago = models.DateField(blank=True, null=True)
    hora_pago = models.TimeField(blank=True, null=True)
    pais_tarjeta = models.CharField(max_length=5, blank=True, null=True)
    identificador_comercio = models.CharField(max_length=20, blank=True, null=True)
    
    # ✅ NUEVO: CAMPOS PARA TRACKING DE ERRORES
    codigo_respuesta = models.CharField(max_length=10, blank=True, null=True, verbose_name="Código Respuesta Redsys")
    descripcion_error = models.CharField(max_length=100, blank=True, null=True, verbose_name="Descripción Error")
    fecha_intento = models.DateTimeField(blank=True, null=True, verbose_name="Fecha Intento Pago")

    # ✅ NUEVOS CAMPOS PARA FLORISTERÍA
    destinatario_nombre = models.CharField(max_length=200, blank=True, default='')
    destinatario_direccion = models.TextField(blank=True, default='')
    destinatario_cp = models.CharField(max_length=10, blank=True, default='')
    destinatario_localidad = models.CharField(max_length=100, blank=True, default='')
    destinatario_provincia = models.CharField(max_length=100, blank=True, default='')
    destinatario_telefono = models.CharField(max_length=20, blank=True, default='')
    mensaje_dedicatoria = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'pedido'
        verbose_name_plural = 'pedidos'

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.nombre}"

    # ✅ CORREGIDO: Total INCLUYENDO gastos de envío
    @property
    def total(self):
        """Calcula el total INCLUYENDO gastos de envío"""
        total_productos = sum(
            Decimal(str(linea.producto.precio)) * linea.cantidad 
            for linea in self.lineapedido_set.all()
        )
        return total_productos + Decimal(str(self.gastos_envio))

    # ✅ NUEVAS PROPIEDADES PARA IVA
    @property
    def base_imponible(self):
        """Base imponible sin IVA"""
        base = Decimal('0.00')
        for linea in self.lineapedido_set.all():
            precio_con_iva = Decimal(str(linea.producto.precio))
            precio_sin_iva = precio_con_iva / Decimal('1.21')
            base += precio_sin_iva * linea.cantidad
        
        # Gastos de envío sin IVA
        if self.gastos_envio > 0:
            gastos_sin_iva = Decimal(str(self.gastos_envio)) / Decimal('1.21')
            base += gastos_sin_iva
        
        return base

    @property
    def iva_total(self):
        """Total de IVA"""
        iva = Decimal('0.00')
        for linea in self.lineapedido_set.all():
            precio_con_iva = Decimal(str(linea.producto.precio))
            precio_sin_iva = precio_con_iva / Decimal('1.21')
            iva_linea = (precio_con_iva - precio_sin_iva) * linea.cantidad
            iva += iva_linea
        
        # IVA de gastos de envío
        if self.gastos_envio > 0:
            gastos_con_iva = Decimal(str(self.gastos_envio))
            gastos_sin_iva = gastos_con_iva / Decimal('1.21')
            iva += gastos_con_iva - gastos_sin_iva
        
        return iva

    @property
    def gastos_envio_sin_iva(self):
        """Gastos de envío sin IVA"""
        if self.gastos_envio > 0:
            return Decimal(str(self.gastos_envio)) / Decimal('1.21')
        return Decimal('0.00')

    @property
    def iva_envio(self):
        """IVA de los gastos de envío"""
        if self.gastos_envio > 0:
            gastos_con_iva = Decimal(str(self.gastos_envio))
            return gastos_con_iva - (gastos_con_iva / Decimal('1.21'))
        return Decimal('0.00')
    
    
class LineaPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    producto = models.ForeignKey(Productos, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'línea de pedido'
        verbose_name_plural = 'líneas de pedido'

    @property
    def subtotal(self):
        return self.producto.precio * self.cantidad

    # ✅ NUEVAS PROPIEDADES PARA IVA
    @property
    def precio_sin_iva(self):
        """Precio unitario sin IVA"""
        precio_con_iva = Decimal(str(self.producto.precio))
        return precio_con_iva / Decimal('1.21')

    @property
    def iva(self):
        """IVA unitario"""
        precio_con_iva = Decimal(str(self.producto.precio))
        precio_sin_iva = precio_con_iva / Decimal('1.21')
        return precio_con_iva - precio_sin_iva

    @property
    def total_sin_iva(self):
        """Total de la línea sin IVA"""
        return self.precio_sin_iva * self.cantidad

    @property
    def total_iva(self):
        """Total IVA de la línea"""
        return self.iva * self.cantidad

    @property
    def total_con_iva(self):
        """Total de la línea con IVA"""
        return Decimal(str(self.producto.precio)) * self.cantidad
    

class Devolucion(models.Model):
    ESTADOS_DEVOLUCION = [
        ('solicitada', 'Solicitada'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('completada', 'Completada'),
    ]
    
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='devoluciones')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_DEVOLUCION, default='solicitada')
    motivo = models.TextField(blank=True)
    notas_internas = models.TextField(blank=True)
    
    # Campos financieros CON IVA
    base_imponible_devolucion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    iva_devolucion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    importe_total_devolucion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gastos_envio_devolucion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'devolución'
        verbose_name_plural = 'devoluciones'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Devolución #{self.id} - Pedido #{self.pedido.id}"
    
    def procesar_devolucion(self):
        """Procesa la devolución: actualiza stock y calcula importes CON IVA"""
        if self.estado != 'aprobada':
            return False
        
        try:
            base_imponible = Decimal('0.00')
            iva_total = Decimal('0.00')
            total_devolucion = Decimal('0.00')
            
            # Procesar cada línea de devolución
            for linea_devolucion in self.lineas.all():
                # Incrementar stock del producto
                producto = linea_devolucion.linea_pedido_original.producto
                producto.stock += linea_devolucion.cantidad_devuelta
                producto.save()
                
                # Calcular importes CON IVA
                precio_con_iva = Decimal(str(linea_devolucion.precio_unitario_devolucion))
                precio_sin_iva = precio_con_iva / Decimal('1.21')
                iva_linea = precio_con_iva - precio_sin_iva
                
                base_imponible += precio_sin_iva * linea_devolucion.cantidad_devuelta
                iva_total += iva_linea * linea_devolucion.cantidad_devuelta
                total_devolucion += precio_con_iva * linea_devolucion.cantidad_devuelta
                
                print(f"✅ Stock incrementado: {producto.nombre} +{linea_devolucion.cantidad_devuelta} unidades")
            
            # Calcular gastos de envío proporcionales CON IVA
            if self.es_devolucion_total():
                gastos_envio_con_iva = self.pedido.gastos_envio
                gastos_envio_sin_iva = gastos_envio_con_iva / Decimal('1.21')
                iva_envio = gastos_envio_con_iva - gastos_envio_sin_iva
                
                self.gastos_envio_devolucion = gastos_envio_con_iva
                base_imponible += gastos_envio_sin_iva
                iva_total += iva_envio
            else:
                # Gastos de envío proporcionales al porcentaje devuelto
                porcentaje_devolucion = total_devolucion / self.pedido.total
                gastos_envio_con_iva = self.pedido.gastos_envio * porcentaje_devolucion
                gastos_envio_sin_iva = gastos_envio_con_iva / Decimal('1.21')
                iva_envio = gastos_envio_con_iva - gastos_envio_sin_iva
                
                self.gastos_envio_devolucion = gastos_envio_con_iva
                base_imponible += gastos_envio_sin_iva
                iva_total += iva_envio
            
            # Guardar importes finales
            self.base_imponible_devolucion = base_imponible
            self.iva_devolucion = iva_total
            self.importe_total_devolucion = total_devolucion + self.gastos_envio_devolucion
            self.estado = 'completada'
            self.fecha_procesamiento = timezone.now()
            self.save()
            
            print(f"✅ Devolución #{self.id} procesada.")
            print(f"   Base imponible: {self.base_imponible_devolucion:.2f}€")
            print(f"   IVA: {self.iva_devolucion:.2f}€")
            print(f"   Total: {self.importe_total_devolucion:.2f}€")
            return True
            
        except Exception as e:
            print(f"❌ Error procesando devolución: {e}")
            return False
    
    def es_devolucion_total(self):
        """Verifica si es una devolución total del pedido"""
        total_lineas_pedido = sum(linea.cantidad for linea in self.pedido.lineapedido_set.all())
        total_devuelto = sum(linea.cantidad_devuelta for linea in self.lineas.all())
        return total_devuelto >= total_lineas_pedido
    
    def get_productos_devueltos(self):
        """Lista de productos devueltos"""
        return [
            {
                'producto': linea.linea_pedido_original.producto,
                'cantidad': linea.cantidad_devuelta,
                'precio_sin_iva': (Decimal(str(linea.precio_unitario_devolucion)) / Decimal('1.21')).quantize(Decimal('0.01')),
                'iva': (Decimal(str(linea.precio_unitario_devolucion)) - (Decimal(str(linea.precio_unitario_devolucion)) / Decimal('1.21'))).quantize(Decimal('0.01')),
                'precio_con_iva': linea.precio_unitario_devolucion,
                'importe_total': linea.importe_devolucion,
                'razon': linea.get_razon_display()
            }
            for linea in self.lineas.all()
        ]
    def calcular_importes(self):
        """Calcula automáticamente los importes de la devolución INCLUYENDO gastos de envío"""
        from decimal import Decimal
        total_base = Decimal('0.00')
        total_iva = Decimal('0.00')

        print(f"🚨 DEBUG: calcular_importes() EJECUTADO para devolución #{self.id}")
        
        # Calcular importes de los productos devueltos
        for linea in self.lineas.all():
            precio_con_iva = Decimal(str(linea.precio_unitario_devolucion))
            precio_sin_iva = precio_con_iva / Decimal('1.21')
            iva_linea = precio_con_iva - precio_sin_iva
            
            base_linea = precio_sin_iva * Decimal(str(linea.cantidad_devuelta))
            iva_linea_total = iva_linea * Decimal(str(linea.cantidad_devuelta))
            
            total_base += base_linea
            total_iva += iva_linea_total
        
        print(f"DEBUG: Base productos: {total_base}, IVA productos: {total_iva}")
        
        # ✅ AÑADIR GASTOS DE ENVÍO SI EXISTEN
        if self.gastos_envio_devolucion and self.gastos_envio_devolucion > 0:
            gastos_con_iva = Decimal(str(self.gastos_envio_devolucion))
            gastos_sin_iva = gastos_con_iva / Decimal('1.21')
            iva_gastos = gastos_con_iva - gastos_sin_iva
            
            total_base += gastos_sin_iva
            total_iva += iva_gastos
            print(f"DEBUG: Gastos envío: {gastos_con_iva} (base: {gastos_sin_iva}, IVA: {iva_gastos})")
        
        total_final = total_base + total_iva
        print(f"DEBUG: Total final: {total_final}")
        
        # Actualizar los campos
        self.base_imponible_devolucion = total_base
        self.iva_devolucion = total_iva
        self.importe_total_devolucion = total_final
        self.save()
            # Propiedades para acceder fácilmente a los importes
    @property
    def total_con_iva(self):
        return self.importe_total_devolucion
    
    @property
    def total_sin_iva(self):
        return self.base_imponible_devolucion

class LineaDevolucion(models.Model):
    devolucion = models.ForeignKey(Devolucion, on_delete=models.CASCADE, related_name='lineas')
    linea_pedido_original = models.ForeignKey(LineaPedido, on_delete=models.CASCADE)
    cantidad_devuelta = models.PositiveIntegerField()
    precio_unitario_devolucion = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Razones de devolución
    RAZONES = [
        ('defectuoso', 'Producto defectuoso'),
        ('no_satisfaccion', 'No satisface expectativas'),
        ('error_envio', 'Error en el envío'),
        ('cambio_talla', 'Cambio de talla'),
        ('otro', 'Otro motivo'),
    ]
    razon = models.CharField(max_length=20, choices=RAZONES, default='no_satisfaccion')
    
    @property
    def importe_devolucion(self):
        return self.precio_unitario_devolucion * self.cantidad_devuelta
    
    @property
    def precio_sin_iva(self):
        return Decimal(str(self.precio_unitario_devolucion)) / Decimal('1.21')
    
    @property
    def iva_unitario(self):
        return Decimal(str(self.precio_unitario_devolucion)) - self.precio_sin_iva
    
    @property
    def total_sin_iva(self):
        return self.precio_sin_iva * self.cantidad_devuelta
    
    @property
    def total_iva(self):
        return self.iva_unitario * self.cantidad_devuelta

    class Meta:
        verbose_name = 'línea de devolución'
        verbose_name_plural = 'líneas de devolución'