from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class Alergeno(models.Model):
    ALERGENOS_CHOICES = [
        ('gluten', 'Gluten'),
        ('crustaceos', 'Crustáceos'),
        ('huevos', 'Huevos'),
        ('pescado', 'Pescado'),
        ('cacahuetes', 'Cacahuetes'),
        ('soja', 'Soja'),
        ('lacteos', 'Lácteos'),
        ('frutos_cascara', 'Frutos de Cáscara'),
        ('apio', 'Apio'),
        ('mostaza', 'Mostaza'),
        ('sesamo', 'Sésamo'),
        ('sulfitos', 'Sulfitos'),
        ('altramuces', 'Altramuces'),
        ('moluscos', 'Moluscos'),
    ]
    
    codigo = models.CharField(max_length=20, choices=ALERGENOS_CHOICES, unique=True)
    nombre = models.CharField(max_length=50)
    
    class Meta:
        verbose_name = 'alérgeno'
        verbose_name_plural = 'alérgenos'
    
    def __str__(self):
        return self.nombre

class Servicio(models.Model):
    # Choices para categorías
    CATEGORIAS_CHOICES = [
        ('entrantes_picoteo', 'Entrantes y Picoteo'),
        ('primeros', 'Primeros Platos'),
        ('segundos', 'Segundos Platos'),
        ('postres', 'Postres'),
        ('bebidas', 'Bebidas'),
        ('reservas', 'Reservas'),
        ('localizacion', 'Localización'),
        ('contacto', 'Contacto'),
    ]

    titulo = models.CharField(max_length=50)
    contenido = models.TextField(max_length=500)
    imagen = models.ImageField(upload_to='servicios')
    categoria = models.CharField(max_length=20, choices=CATEGORIAS_CHOICES)
    precio = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    alergenos = models.ManyToManyField(Alergeno, blank=True)  # Ahora está en el lugar correcto
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'servicio'
        verbose_name_plural = 'servicios'
        ordering = ['categoria', 'titulo']
    
    def __str__(self):
        return f"{self.titulo} - {self.get_categoria_display()}"

    def get_alergenos_html(self):
        """Devuelve HTML con iconos de FontAwesome y colores para cada alérgeno"""
        alergenos_data = {
            'gluten': {'icon': 'fa-bread-slice', 'color': '#8B4513', 'title': 'Contiene gluten'},
            'crustaceos': {'icon': 'fa-shrimp', 'color': '#FF6B6B', 'title': 'Crustáceos'},
            'huevos': {'icon': 'fa-egg', 'color': '#FFD700', 'title': 'Huevos'},
            'pescado': {'icon': 'fa-fish', 'color': '#4682B4', 'title': 'Pescado'},
            'cacahuetes': {'icon': 'fa-seedling', 'color': '#8B7355', 'title': 'Cacahuetes'},
            'soja': {'icon': 'fa-leaf', 'color': '#32CD32', 'title': 'Soja'},
            'lacteos': {'icon': 'fa-cheese', 'color': '#F0E68C', 'title': 'Lácteos'},
            'frutos_cascara': {'icon': 'fa-tree', 'color': '#A0522D', 'title': 'Frutos de cáscara'},
            'apio': {'icon': 'fa-carrot', 'color': '#90EE90', 'title': 'Apio'},
            'mostaza': {'icon': 'fa-mortar-pestle', 'color': '#FFD700', 'title': 'Mostaza'},
            'sesamo': {'icon': 'fa-seedling', 'color': '#F4A460', 'title': 'Sésamo'},
            'sulfitos': {'icon': 'fa-flask', 'color': '#9370DB', 'title': 'Sulfitos'},
            'altramuces': {'icon': 'fa-seedling', 'color': '#8A2BE2', 'title': 'Altramuces'},
            'moluscos': {'icon': 'fa-shell', 'color': '#FFB6C1', 'title': 'Moluscos'},
        }
        
        html_icons = []
        for alergeno_rel in self.alergenos.all():
            alergeno = alergeno_rel.codigo
            if alergeno in alergenos_data:
                data = alergenos_data[alergeno]
                html_icons.append(
                    f'<i class="fas {data["icon"]}" style="color: {data["color"]}; font-size: 1.2rem; margin: 0 2px;" title="{data["title"]}"></i>'
                )
        
        return ' '.join(html_icons) if html_icons else '<span class="text-muted">Sin alérgenos destacados</span>'
    
class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]
    
    nombre = models.CharField(max_length=100, verbose_name='Nombre completo')
    telefono = models.CharField(max_length=15, verbose_name='Teléfono')
    email = models.EmailField(verbose_name='Correo electrónico')
    fecha = models.DateField(verbose_name='Fecha de la reserva')
    hora = models.TimeField(verbose_name='Hora de la reserva')
    numero_personas = models.PositiveIntegerField(verbose_name='Número de personas')
    comentarios = models.TextField(max_length=500, blank=True, verbose_name='Comentarios adicionales')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated = models.DateTimeField(auto_now=True, verbose_name='Última actualización')
    
    class Meta:
        verbose_name = 'reserva'
        verbose_name_plural = 'reservas'
        ordering = ['fecha', 'hora']
    
    def __str__(self):
        return f"Reserva de {self.nombre} - {self.fecha} {self.hora} ({self.numero_personas} personas)"