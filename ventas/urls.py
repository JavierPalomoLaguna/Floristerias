from django.urls import path
from . import views
from .views import ver_factura


urlpatterns = [
    path('confirmar/', views.confirmar_pedido, name='confirmar_pedido_ventas'),
    path('notificacion/', views.notificacion_redsys, name='notificacion_redsys'),
    path('pago/', views.pago_redsys, name='pago_redsys'),
    path('exito/', views.exito_pago, name='exito_pago'),
    path('error/', views.error_pago, name='error_pago'),
    path('factura/<int:pedido_id>/', ver_factura, name='ver_factura'),
]