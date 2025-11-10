from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from decimal import Decimal
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone 
from reportlab.lib.enums import TA_CENTER 

def generar_factura_pdf(pedido, devolucion=None):
    """Genera un PDF de factura para un pedido o contrafactura para devolución"""
    
    # Determinar si es factura normal o contrafactura
    es_devolucion = devolucion is not None
    titulo_documento = "FACTURA DE DEVOLUCIÓN" if es_devolucion else "FACTURA"
    numero_documento = f"DEV-{devolucion.id}" if es_devolucion else f"{pedido.id}"
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    
    # Crear documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    estilo_normal = styles['Normal']
    
    # Contenido del PDF
    story = []
    
    # Título con número de documento
    story.append(Paragraph(f"{titulo_documento} Nº {numero_documento}", estilo_titulo))
    story.append(Spacer(1, 10))
    
    # Información de LA TRASTIENDA S.L.
    info_empresa = [
        ["EMITIDO POR:", "CLIENTE:"],
        ["LA TRASTIENDA S.L.", f"{pedido.cliente.nombre} {pedido.cliente.apellidos}"],
        ["Avenida de Asturias 14, 28000 Madrid", f"{pedido.cliente.calle} {pedido.cliente.numero_calle}"],
        ["CIF: B00000000", f"{pedido.cliente.localidad}, {pedido.cliente.provincia}"],
        ["Teléfono: 666666666", f"Portal: {pedido.cliente.portal}" if pedido.cliente.portal else ""],
        ["Email: contabilidad@latrastienda.es", f"Escalera: {pedido.cliente.escalera}" if pedido.cliente.escalera else ""],
        ["", f"Piso: {pedido.cliente.piso}, Puerta: {pedido.cliente.puerta}"],
        ["", f"Código Postal: {pedido.cliente.codigo_postal}"],
        ["", f"Teléfono: {pedido.cliente.telefono or 'No proporcionado'}"],
        ["", f"Email: {pedido.cliente.email}"],
        ["", f"CIF: {pedido.cliente.cif or 'No proporcionado'}"],
    ]
    
    tabla_info = Table(info_empresa, colWidths=[doc.width/2.0]*2)
    tabla_info.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    story.append(tabla_info)
    story.append(Spacer(1, 20))
    
    # Detalles del documento
    detalles_documento = [
        ["Nº Documento:", f"{numero_documento}"],
        ["Fecha de emisión:", timezone.now().strftime("%d/%m/%Y")],
        ["Pedido original:", f"{pedido.id}"],
    ]
    
    if es_devolucion:
        detalles_documento.insert(1, ["Devolución:", f"#{devolucion.id}"])
        detalles_documento.append(["Motivo:", f"{devolucion.motivo}"])
    
    tabla_detalles = Table(detalles_documento, colWidths=[doc.width/3.0]*2)
    tabla_detalles.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    
    story.append(tabla_detalles)
    story.append(Spacer(1, 20))
    
    # Productos - ✅ AHORA CON IVA SEPARADO
    encabezados = ['Producto', 'Cantidad', 'Precio sin IVA', 'IVA 21%', 'Total con IVA']
    datos_productos = [encabezados]
    
    # Calcular totales
    base_imponible_total = Decimal('0.00')
    iva_total = Decimal('0.00')
    total_general = Decimal('0.00')
    
    if es_devolucion:
        # PRODUCTOS DEVUELTOS (mostrar como negativo)
        for linea in devolucion.lineas.all():
            # Precio con IVA (usar el precio de la devolución)
            precio_con_iva = Decimal(str(linea.precio_unitario_devolucion))
            
            # Calcular precio sin IVA (21%)
            precio_sin_iva = precio_con_iva / Decimal('1.21')
            iva_linea = precio_con_iva - precio_sin_iva
            
            # Totales por línea (en negativo para devoluciones)
            total_linea_sin_iva = precio_sin_iva * linea.cantidad_devuelta
            total_iva_linea = iva_linea * linea.cantidad_devuelta
            total_linea_con_iva = precio_con_iva * linea.cantidad_devuelta
            
            # Restar del total (por ser devolución)
            base_imponible_total -= total_linea_sin_iva
            iva_total -= total_iva_linea
            total_general -= total_linea_con_iva
            
            datos_productos.append([
                f"DEVOLUCIÓN - {linea.linea_pedido_original.producto.nombre}",
                f"-{linea.cantidad_devuelta}",
                f"-{precio_sin_iva:.2f} €",
                f"-{iva_linea:.2f} €",
                f"-{precio_con_iva:.2f} €"
            ])
        
        # ✅ GASTOS DE ENVÍO PARA DEVOLUCIONES (si aplica)
        if devolucion.gastos_envio_devolucion and devolucion.gastos_envio_devolucion > 0:
            gastos_envio_decimal = Decimal(str(devolucion.gastos_envio_devolucion))
            
            # Calcular gastos de envío sin IVA (21%)
            gastos_sin_iva = gastos_envio_decimal / Decimal('1.21')
            iva_envio = gastos_envio_decimal - gastos_sin_iva
            
            datos_productos.append([
                "DEVOLUCIÓN - Gastos de envío",
                "1",
                f"-{gastos_sin_iva:.2f} €",
                f"-{iva_envio:.2f} €",
                f"-{gastos_envio_decimal:.2f} €"
            ])
            
            base_imponible_total -= gastos_sin_iva
            iva_total -= iva_envio
            total_general -= gastos_envio_decimal
            
    else:
        # PRODUCTOS COMPRADOS (factura normal)
        for linea in pedido.lineapedido_set.all():
            # Precio con IVA (el que se muestra en la tienda)
            precio_con_iva = Decimal(str(linea.producto.precio))
            
            # Calcular precio sin IVA (21%)
            precio_sin_iva = precio_con_iva / Decimal('1.21')
            iva_linea = precio_con_iva - precio_sin_iva
            
            # Totales por línea
            total_linea_sin_iva = precio_sin_iva * linea.cantidad
            total_iva_linea = iva_linea * linea.cantidad
            total_linea_con_iva = precio_con_iva * linea.cantidad
            
            datos_productos.append([
                linea.producto.nombre,
                str(linea.cantidad),
                f"{precio_sin_iva:.2f} €",
                f"{iva_linea:.2f} €",
                f"{precio_con_iva:.2f} €"
            ])
            
            base_imponible_total += total_linea_sin_iva
            iva_total += total_iva_linea
            total_general += total_linea_con_iva
        
        # Gastos de envío para facturas normales
        gastos_envio_decimal = Decimal(str(pedido.gastos_envio))
        
        if gastos_envio_decimal > 0:
            # Calcular gastos de envío sin IVA (21%)
            gastos_sin_iva = gastos_envio_decimal / Decimal('1.21')
            iva_envio = gastos_envio_decimal - gastos_sin_iva
            
            datos_productos.append([
                "Gastos de envío",
                "1",
                f"{gastos_sin_iva:.2f} €",
                f"{iva_envio:.2f} €",
                f"{gastos_envio_decimal:.2f} €"
            ])
            
            base_imponible_total += gastos_sin_iva
            iva_total += iva_envio
            total_general += gastos_envio_decimal
        elif pedido.envio_gratis:
            datos_productos.append([
                "Gastos de envío (Gratis)",
                "1",
                "0.00 €",
                "0.00 €",
                "0.00 €"
            ])
    
    # Tabla de productos
    tabla_productos = Table(datos_productos, colWidths=[doc.width*0.35, doc.width*0.1, doc.width*0.15, doc.width*0.15, doc.width*0.15])
    tabla_productos.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    
    story.append(tabla_productos)
    story.append(Spacer(1, 20))
    
    # Totales
    if es_devolucion:
        # Para devoluciones, mostrar totales en negativo
        totales = [
            ["BASE IMPONIBLE:", f"-{abs(base_imponible_total):.2f} €"],
            ["IVA (21%):", f"-{abs(iva_total):.2f} €"],
            ["TOTAL A DEVOLVER:", f"-{abs(total_general):.2f} €"],
        ]
    else:
        # Para facturas normales
        total_final = Decimal(str(pedido.total))
        totales = [
            ["BASE IMPONIBLE:", f"{base_imponible_total:.2f} €"],
            ["IVA (21%):", f"{iva_total:.2f} €"],
            ["TOTAL:", f"{total_final:.2f} €"],
        ]
    
    tabla_totales = Table(totales, colWidths=[doc.width*0.7, doc.width*0.3])
    tabla_totales.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('LINEABOVE', (0,2), (-1,2), 1, colors.black),
    ]))
    
    story.append(tabla_totales)
    
    # Pie de página
    story.append(Spacer(1, 30))
    if es_devolucion:
        story.append(Paragraph("Devolución procesada - LA TRASTIENDA S.L.", styles['Normal']))
    else:
        story.append(Paragraph("Gracias por su compra - LA TRASTIENDA S.L.", styles['Normal']))
    
    # Generar PDF
    doc.build(story)
    
    # Obtener contenido del PDF
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf

def enviar_email_pedido_confirmado(pedido):
    """Envía email de confirmación con factura PDF adjunta"""
    
    try:
        # Generar la factura PDF
        pdf_content = generar_factura_pdf(pedido)
        
        # Asunto del email
        asunto = f'✅ Confirmación de Pedido #{pedido.id} - LA TRASTIENDA S.L.'
        
        # Cuerpo del email
        mensaje = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 style="color: #2c3e50;">¡Gracias por tu compra, {pedido.cliente.nombre}!</h2>
            
            <p>Tu pedido <strong>#{pedido.id}</strong> ha sido confirmado exitosamente.</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <h3 style="color: #2c3e50; margin-top: 0;">📦 Resumen del Pedido</h3>
                <p><strong>Fecha:</strong> {pedido.fecha.strftime('%d/%m/%Y %H:%M')}</p>
                <p><strong>Método de pago:</strong> {pedido.get_metodo_pago_display()}</p>
                <p><strong>Total:</strong> {pedido.total:.2f}€</p>
                <p><strong>Estado:</strong> {"✅ Pagado" if pedido.pagado else "⏳ Pendiente de pago"}</p>
            </div>
            
            <p>📎 Adjuntamos tu factura en formato PDF.</p>
            
            <div style="margin-top: 20px; padding: 15px; background-color: #e8f5e8; border-radius: 5px;">
                <h4 style="color: #27ae60; margin-top: 0;">📞 ¿Necesitas ayuda?</h4>
                <p>Si tienes alguna pregunta sobre tu pedido, contáctanos:</p>
                <p>📧 Email: contabilidad@latrastienda.es<br>
                   📞 Teléfono: 666666666</p>
            </div>
            
            <p style="margin-top: 20px; color: #7f8c8d;">¡Esperamos que disfrutes de tus productos!</p>
            <p><strong>El equipo de LA TRASTIENDA S.L.</strong></p>
        </body>
        </html>
        """
        
        # Crear el email
        email = EmailMessage(
            subject=asunto,
            body=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[pedido.cliente.email],
            reply_to=['contabilidad@latrastienda.es'],
        )
        
        # Configurar como HTML
        email.content_subtype = "html"
        
        # Adjuntar PDF
        email.attach(
            filename=f"factura_{pedido.id}.pdf",
            content=pdf_content,
            mimetype="application/pdf"
        )
        
        # Enviar email
        email.send(fail_silently=False)
        
        print(f"✅ Email enviado a {pedido.cliente.email} para pedido #{pedido.id}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando email para pedido #{pedido.id}: {e}")
        return False