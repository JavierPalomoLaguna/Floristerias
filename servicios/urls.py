from django.urls import path
from . import views
from .views import procesar_reserva


urlpatterns = [
    path('', views.servicios, name='servicios'),
    path('reservar/', procesar_reserva, name='procesar_reserva'),   
]

