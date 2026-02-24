from django.shortcuts import render, redirect
from django.conf import settings
from tienda.models import Productos
from clientes.models import Cliente
from .models import Pedido, LineaPedido, ConfiguracionEnvio
import base64, hashlib, hmac, json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .utils import generar_factura_pdf, enviar_email_pedido_confirmado
from datetime import datetime
from Crypto.Cipher import DES3
import hmac
import hashlib
import base64

# ✅ DATOS DE PRUEBA REDSYS (AGREGADOS AL PRINCIPIO)
clave = "sq7HjrUOBfKmC576ILgskD5srU870gJ7"
merchant_code = "999008881"
terminal = "049"

# ✅ AGREGAR ESTA FUNCIÓN SI NO EXISTE
def create_signature(clave, encoded_params, order):
    key = base64.b64decode(clave)
    order_bytes = order.encode('utf-8').ljust(8, b'\x00')[:8]
    cipher = DES3.new(key, DES3.MODE_ECB)
    key_3des = cipher.encrypt(order_bytes)
    signature = hmac.new(key_3des, encoded_params.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(signature).decode('utf-8')
# ✅ FIN DE LA FUNCIÓN

def confirmar_pedido(request):
    carro = request.session.get('carro', {})
    cliente_id = request.session.get('cliente_persistent_id')

    if request.method == 'POST' and carro and cliente_id:
        metodo_pago = request.POST.get('metodo_pago')
        cliente = Cliente.objects.get(id=cliente_id)

        # ✅ OBTENER CONFIGURACIÓN DE ENVÍO
        try:
            config_envio = ConfiguracionEnvio.objects.get(activo=True)
            umbral = float(config_envio.umbral_envio_gratis)
            costo_envio = float(config_envio.costo_envio_estandar)
        except ConfiguracionEnvio.DoesNotExist:
            print("❌ DEBUG: No se encontró configuración activa: ConfiguracionEnvio matching query does not exist.")
            umbral = 300.00
            costo_envio = 5.95

        # Calcular importe total del carrito
        importe_total = sum(item["precio"] * item["cantidad"] for item in carro.values())
        
        # ✅ CALCULAR GASTOS DE ENVÍO
        if importe_total >= umbral:
            gastos_envio = 0
            envio_gratis = True
        else:
            gastos_envio = costo_envio
            envio_gratis = False

        # ✅ VERIFICAR STOCK ANTES DE CREAR PEDIDO
        productos_sin_stock = []
        for key, item in carro.items():
            producto = Productos.objects.get(id=item['producto_id'])
            if producto.stock < item['cantidad']:
                productos_sin_stock.append(f"{producto.nombre} (stock: {producto.stock}, pedido: {item['cantidad']})")
        
        if productos_sin_stock:
            error_message = f'Stock insuficiente para: {", ".join(productos_sin_stock)}'
            print(f"❌ {error_message}")
            importe_total = sum(item["precio"] * item["cantidad"] for item in carro.values())
            return render(request, 'carro/checkout.html', {
                'carro': carro,
                'importe_total_carro': importe_total,
                'error_stock': error_message
            })

        # ✅ CAPTURAR DATOS DE ENVÍO Y DEDICATORIA
        usar_direccion_cliente = request.POST.get('usar_direccion_cliente', '1') == '1'
        
        print(f"🔍 DEBUG: usar_direccion_cliente = {usar_direccion_cliente}")
        
        if usar_direccion_cliente:
            # Usar dirección del cliente
            destinatario_nombre = f"{cliente.nombre} {cliente.apellidos}"
            destinatario_direccion = f"{cliente.calle} {cliente.numero_calle}"
            if cliente.portal or cliente.escalera or cliente.piso or cliente.puerta:
                partes = []
                if cliente.portal:
                    partes.append(f"Portal {cliente.portal}")
                if cliente.escalera:
                    partes.append(f"Esc. {cliente.escalera}")
                if cliente.piso:
                    partes.append(f"{cliente.piso}º")
                if cliente.puerta:
                    partes.append(cliente.puerta)
                destinatario_direccion += ", " + " ".join(partes)
            destinatario_cp = cliente.codigo_postal or ''
            destinatario_localidad = cliente.localidad or ''
            destinatario_provincia = cliente.provincia or ''
            destinatario_telefono = cliente.telefono or ''
        else:
            # Usar nueva dirección proporcionada
            destinatario_nombre = request.POST.get('destinatario_nombre', '')
            destinatario_calle = request.POST.get('destinatario_calle', '')
            destinatario_portal = request.POST.get('destinatario_portal', '')
            destinatario_piso = request.POST.get('destinatario_piso', '')
            
            destinatario_direccion = destinatario_calle
            if destinatario_portal or destinatario_piso:
                partes = []
                if destinatario_portal:
                    partes.append(f"Portal {destinatario_portal}")
                if destinatario_piso:
                    partes.append(destinatario_piso)
                destinatario_direccion += ", " + " ".join(partes)
            
            destinatario_cp = request.POST.get('destinatario_cp', '')
            destinatario_localidad = request.POST.get('destinatario_localidad', '')
            destinatario_provincia = request.POST.get('destinatario_provincia', '')
            destinatario_telefono = request.POST.get('destinatario_telefono', '')
        
        # Capturar tarjeta de dedicatoria
        mensaje_dedicatoria = request.POST.get('mensaje_dedicatoria', '')
        
        print(f"✅ DEBUG: Destinatario: {destinatario_nombre}")
        print(f"✅ DEBUG: Dirección: {destinatario_direccion}")
        print(f"✅ DEBUG: Dedicatoria: {mensaje_dedicatoria[:50]}...")

        # ✅ CREAR PEDIDO CON DATOS DE ENVÍO
        pedido = Pedido.objects.create(
            cliente=cliente,
            metodo_pago=metodo_pago,
            pagado=False,
            gastos_envio=gastos_envio,  
            envio_gratis=envio_gratis,
            # ✅ NUEVOS CAMPOS
            destinatario_nombre=destinatario_nombre,
            destinatario_direccion=destinatario_direccion,
            destinatario_cp=destinatario_cp,
            destinatario_localidad=destinatario_localidad,
            destinatario_provincia=destinatario_provincia,
            destinatario_telefono=destinatario_telefono,
            mensaje_dedicatoria=mensaje_dedicatoria
        )

        print(f"✅ Pedido #{pedido.id} creado con datos de envío")

        # Crear líneas de pedido
        for key, item in carro.items():
            producto = Productos.objects.get(id=item['producto_id'])
            LineaPedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=item['cantidad']
            )

        # Limpiar el carrito
        del request.session['carro']
        request.session.modified = True

        # Guardar el ID del pedido en sesión para usarlo en pago_redsys
        request.session['pedido_id'] = pedido.id

        # Redirigir al TPV si el método es tarjeta o bizum
        if metodo_pago in ['tarjeta', 'bizum']:
            return redirect('pago_redsys')
        else:
            return render(request, 'ventas/confirmar_pedido.html', {'metodo_pago': metodo_pago})

    return redirect('checkout')

@csrf_exempt
def notificacion_redsys(request):
    if request.method == 'GET':
        return HttpResponse("OK - URL accesible", status=200)
    
    if request.method != 'POST':
        return HttpResponse(status=405)

    # ✅ AHORA USA LA VARIABLE 'clave' DEFINIDA AL PRINCIPIO
    firma_recibida = request.POST.get('Ds_Signature')
    parametros_codificados = request.POST.get('Ds_MerchantParameters')
    
    print("🔔 NOTIFICACIÓN RECIBIDA DE REDSYS")
    print("Firma recibida:", firma_recibida)
    print("Params codificados:", parametros_codificados)

    if not firma_recibida or not parametros_codificados:
        print("❌ Faltan parámetros en la notificación")
        return HttpResponse(status=400)

    try:
        # Decodificar parámetros
        datos_json = base64.b64decode(parametros_codificados).decode()
        datos = json.loads(datos_json)
        print("📊 Datos recibidos:", datos)
        
        # Decodificar los valores URL-encoded
        from urllib.parse import unquote
        
        decoded_datos = {}
        for key, value in datos.items():
            if isinstance(value, str):
                decoded_datos[key] = unquote(value)
            else:
                decoded_datos[key] = value
        
        print("📊 Datos decodificados:", decoded_datos)
        
        # Calcular firma
        order = decoded_datos.get('Ds_Order', '')
        firma_calculada = create_signature(clave, parametros_codificados, order)
        
        # Normalizar firmas para comparación
        def normalizar_firma(firma):
            return firma.replace('-', '+').replace('_', '/')
        
        firma_recibida_normalizada = normalizar_firma(firma_recibida)
        firma_calculada_normalizada = normalizar_firma(firma_calculada)
        
        print("🔐 Firma recibida:", firma_recibida)
        print("🔐 Firma recibida (normalizada):", firma_recibida_normalizada)
        print("🔐 Firma calculada:", firma_calculada)
        print("🔐 Firma calculada (normalizada):", firma_calculada_normalizada)

    except Exception as e:
        print(f"❌ Error procesando datos: {e}")
        return HttpResponse(status=400)

    # Validar firma (usando versiones normalizadas)
    if firma_recibida_normalizada != firma_calculada_normalizada:
        print("❌ Firma no válida")
        print("❌ Diferencia en firmas:")
        print(f"   Recibida:  {firma_recibida_normalizada}")
        print(f"   Calculada: {firma_calculada_normalizada}")
        return HttpResponse(status=403)

    # Extraer datos relevantes (usando los decodificados)
    codigo_pedido = decoded_datos.get('Ds_Order')
    respuesta = decoded_datos.get('Ds_Response')
    
    print(f"📦 Pedido: {codigo_pedido}, Respuesta: {respuesta}")

    # Si la respuesta es menor a 100, el pago fue exitoso
    if codigo_pedido and respuesta and int(respuesta) < 100:
        try:
            pedido = Pedido.objects.get(id=int(codigo_pedido))
            pedido.pagado = True
            pedido.codigo_autorizacion = decoded_datos.get('Ds_AuthorisationCode')

            # Parsear fecha y hora
            fecha_str = decoded_datos.get('Ds_Date')
            hora_str = decoded_datos.get('Ds_Hour')

            print(f"📅 Fecha cruda: {fecha_str}")
            print(f"⏰ Hora cruda: {hora_str}")

            if fecha_str:
                try:
                    pedido.fecha_pago = datetime.strptime(fecha_str, "%d/%m/%Y").date()
                    print(f"✅ Fecha parseada: {pedido.fecha_pago}")
                except Exception as e:
                    print(f"⚠️ Error parseando fecha '{fecha_str}': {e}")

            if hora_str:
                try:
                    pedido.hora_pago = datetime.strptime(hora_str, "%H:%M").time()
                    print(f"✅ Hora parseada: {pedido.hora_pago}")
                except Exception as e:
                    print(f"⚠️ Error parseando hora '{hora_str}': {e}")

            # ✅ ACTUALIZAR STOCK DE PRODUCTOS
            lineas_pedido = LineaPedido.objects.filter(pedido=pedido)
            for linea in lineas_pedido:
                producto = linea.producto
                if producto.stock >= linea.cantidad:
                    producto.stock -= linea.cantidad
                    producto.save()
                    print(f"✅ Stock actualizado: {producto.nombre} -{linea.cantidad} unidades (stock restante: {producto.stock})")
                else:
                    print(f"❌ ERROR: Stock insuficiente para {producto.nombre} (stock: {producto.stock}, pedido: {linea.cantidad})")

            pedido.pais_tarjeta = decoded_datos.get('Ds_Card_Country')
            pedido.identificador_comercio = decoded_datos.get('Ds_MerchantCode', '')
            pedido.save()
            
            print(f"✅ Pedido {codigo_pedido} marcado como PAGADO y stock actualizado")
            print(f"✅ Código autorización: {pedido.codigo_autorizacion}")
            print(f"✅ País tarjeta: {pedido.pais_tarjeta}")
            print(f"✅ ID Comercio: {pedido.identificador_comercio}")
            
            # ✅ NUEVO: ENVIAR EMAIL DE CONFIRMACIÓN CON FACTURA
            try:
                enviar_email_pedido_confirmado(pedido)
                print(f"✅ Email de confirmación enviado a {pedido.cliente.email}")
            except Exception as e:
                print(f"⚠️ Error enviando email: {e}")
            
        except Pedido.DoesNotExist:
            print(f"❌ Pedido {codigo_pedido} no encontrado")
            return HttpResponse(status=404)
        except Exception as e:
            print(f"❌ Error guardando pedido: {e}")
            return HttpResponse(status=500)

    # ✅ MEJORADO: MANEJO DE PAGOS RECHAZADOS CON GUARDADO DE ERRORES
    else:
        print(f"❌ Pago rechazado para pedido {codigo_pedido}. Respuesta: {respuesta}")
        
        try:
            pedido = Pedido.objects.get(id=int(codigo_pedido))
            
            # ✅ GUARDAR INFORMACIÓN DEL ERROR EN LOS NUEVOS CAMPOS
            pedido.codigo_respuesta = respuesta
            pedido.fecha_intento = datetime.now()
            
            # Mapear códigos de error comunes de Redsys
            codigos_error = {
                '0184': 'Tarjeta denegada',
                '0180': 'Tarjeta caducada', 
                '0101': 'Tarjeta inválida',
                '0102': 'Tarjeta con restricciones',
                '0181': 'Tarjeta en lista negra',
                '0185': 'Cuenta no operativa',
                '0188': 'Error en la autenticación',
                '0190': 'Denegación sin especificar motivo',
                '0191': 'Fecha de caducidad errónea',
                '0192': 'Intento de fraude',
                '0196': 'Error genérico',
                '0202': 'Tarjeta en excepción',
                '0904': 'Comercio no autorizado',
                '0909': 'Error de sistema',
                '0912': 'Emisor no disponible',
                '0913': 'Transacción duplicada',
                '0944': 'Sesión CADUCADA',
                '0950': 'Operación de devolución no permitida',
                '9912': 'Emisor no disponible',
                '9913': 'Error en la confirmación',
                '9914': 'Confirmación "KO"',
                '9915': 'Aplicación ocupada',
                '9928': 'Anulación de autorización en diferido',
                '9929': 'Anulación de autorización en diferido',
                '9997': 'Procesando otra transacción',
                '9998': 'Operación en proceso de autenticación',
                '9999': 'Operación que ha sido redirigida al emisor'
            }
            
            pedido.descripcion_error = codigos_error.get(respuesta, f'Error desconocido: {respuesta}')
            pedido.save()
            
            print(f"📝 Pedido {codigo_pedido} - Error guardado: {pedido.descripcion_error}")
            
        except Pedido.DoesNotExist:
            print(f"❌ Pedido {codigo_pedido} no encontrado")
        except Exception as e:
            print(f"❌ Error guardando información de error: {e}")

    return HttpResponse("OK", status=200)


@csrf_exempt
def pago_redsys(request):
    pedido_id = request.session.get('pedido_id')

    if not pedido_id:
        return redirect('checkout')

    try:
        pedido = Pedido.objects.get(id=pedido_id)
    except Pedido.DoesNotExist:
        return redirect('checkout')

    # Calcular importe total en céntimos (INCLUYENDO GASTOS DE ENVÍO)
    lineas = LineaPedido.objects.filter(pedido=pedido)
    total_euros = sum(float(lp.producto.precio) * lp.cantidad for lp in lineas)
    total_euros += float(pedido.gastos_envio)  # INCLUIR GASTOS DE ENVÍO
    total_centimos = int(total_euros * 100)

    
    if settings.ENV == 'production':
        base_url = 'https://www.codigovivostudio.cloud'
    else:
        base_url = 'https://uncascaded-arturo-delightsomely.ngrok-free.dev'

    merchant_params = {
        "Ds_Merchant_Amount": str(total_centimos),
        "Ds_Merchant_Order": f"{pedido.id}{datetime.now().strftime('%H%M%S')}",
        "Ds_Merchant_MerchantCode": merchant_code,
        "Ds_Merchant_Currency": "978",
        "Ds_Merchant_TransactionType": "0",
        "Ds_Merchant_Terminal": terminal,
        "Ds_Merchant_MerchantURL": f"{base_url}/ventas/notificacion/",
        "Ds_Merchant_UrlOK": f"{base_url}/ventas/exito/",
        "Ds_Merchant_UrlKO": f"{base_url}/ventas/error/",
        "Ds_Merchant_ConsumerLanguage": "001"
    }
    
    encoded_params = base64.b64encode(json.dumps(merchant_params).encode()).decode()
    signature = create_signature(clave, encoded_params, merchant_params["Ds_Merchant_Order"])
    
    return render(request, 'ventas/pago_redsys.html', {
        'encoded_params': encoded_params,
        'signature': signature
    })


def exito_pago(request):
    pedido_id = request.session.get('pedido_id')
    metodo_pago = None
    
    if pedido_id:
        try:
            pedido = Pedido.objects.get(id=pedido_id)
            metodo_pago = pedido.metodo_pago
            # Limpiar sesión
            if 'pedido_id' in request.session:
                del request.session['pedido_id']
        except Pedido.DoesNotExist:
            pass
    
    return render(request, 'ventas/exito_pago.html', {
        'metodo_pago': metodo_pago
    })

def error_pago(request):
    pedido_id = request.session.get('pedido_id')
    
    # Opcional: marcar el pedido como fallido
    if pedido_id:
        try:
            pedido = Pedido.objects.get(id=pedido_id)
            # Puedes agregar un campo para tracking de errores
        except Pedido.DoesNotExist:
            pass
            
    return render(request, 'ventas/error_pago.html')


def ver_factura(request, pedido_id):
    """View para ver y descargar la factura PDF"""
    try:
        pedido = Pedido.objects.get(id=pedido_id)
        
        # Generar PDF
        pdf = generar_factura_pdf(pedido)
        
        # Crear respuesta HTTP con el PDF
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="factura_{pedido.id}.pdf"'
        
        return response
        
    except Pedido.DoesNotExist:
        return HttpResponse("Pedido no encontrado", status=404)
    except Exception as e:
        return HttpResponse(f"Error generando factura: {str(e)}", status=500)