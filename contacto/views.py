from django.shortcuts import render
from django.core.mail import send_mail
from .forms import FormularioContacto
from .models import MensajeContacto
from django.conf import settings

def contacto(request):
    mensaje_exito = None

    if request.method == "POST":
        formulario = FormularioContacto(request.POST)
        if formulario.is_valid():
            nombre = formulario.cleaned_data["name"]
            email = formulario.cleaned_data["email"]
            contenido = formulario.cleaned_data["contenido"]

            # Guardar en la base de datos
            MensajeContacto.objects.create(
                nombre=nombre,
                email=email,
                contenido=contenido
            )

            # Enviar correo
            send_mail(
                subject="Nuevo mensaje de contacto",
                message=f"Nombre: {nombre}\nEmail: {email}\nContenido:\n{contenido}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=['jpalomolaguna@gmail.com'],
                fail_silently=False,
            )

            mensaje_exito = "Mensaje enviado correctamente."
            formulario = FormularioContacto()
    else:
        formulario = FormularioContacto()

    context = {
        "formulario": formulario,
        "mensaje_exito": mensaje_exito,
        'meta_title': 'Contacta con Nuestros Desarrolladores Web | Código Vivo Studio',
        'meta_description': 'Solicita presupuesto para tu proyecto web. Desarrollo personalizado para restaurantes, comercios y empresas.',
    }
    
    return render(request, "contacto/contacto.html", context)