from django.contrib import admin
from .models import Servicio, Alergeno, Reserva


class AlergenoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo')
    list_filter = ('codigo',)

class ServicioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'precio', 'created', 'updated')
    list_filter = ('categoria', 'created', 'updated', 'alergenos')
    search_fields = ('titulo', 'contenido')
    readonly_fields = ('created', 'updated')
    filter_horizontal = ('alergenos',)  # Selector múltiple más amigable
    
    fieldsets = (
        ('Información básica', {
            'fields': ('titulo', 'contenido', 'categoria', 'precio')
        }),
        ('Imagen y alérgenos', {
            'fields': ('imagen', 'alergenos')
        }),
        ('Metadatos', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )


class ReservaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'fecha', 'hora', 'numero_personas', 'estado', 'created')
    list_filter = ('estado', 'fecha', 'created')
    search_fields = ('nombre', 'telefono', 'email')
    readonly_fields = ('created', 'updated')
    list_editable = ('estado',)
    
    fieldsets = (
        ('Información de la reserva', {
            'fields': ('nombre', 'telefono', 'email', 'fecha', 'hora', 'numero_personas', 'comentarios')
        }),
        ('Estado y seguimiento', {
            'fields': ('estado', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )


admin.site.register(Servicio, ServicioAdmin)
admin.site.register(Alergeno, AlergenoAdmin)
admin.site.register(Reserva, ReservaAdmin)
