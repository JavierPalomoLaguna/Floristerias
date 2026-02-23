from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(DefaultUserAdmin):
    def has_delete_permission(self, request, obj=None):
        # Solo permite borrar si el usuario actual es superusuario
        # y el objeto a borrar NO es superusuario
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        # Elimina la acción masiva de "Eliminar seleccionados" si no es superusuario
        if not request.user.is_superuser:
            actions.pop('delete_selected', None)
        return actions
    
    def has_change_permission(self, request, obj=None):
        # Si el objeto es un superusuario y el usuario actual NO lo es, denegar edición
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            if 'is_superuser' in form.base_fields:
                form.base_fields['is_superuser'].disabled = True
        return form