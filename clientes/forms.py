from django import forms
from .models import Cliente
from django.contrib.auth.hashers import make_password
import re

class ClienteForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )

    class Meta:
        model = Cliente
        # ✅ QUITAMOS 'usuario' de la lista
        fields = ['nombre', 'apellidos', 'telefono', 'cif', 'email', 'provincia',
                  'localidad', 'calle', 'numero_calle', 'portal', 'escalera', 'piso', 'puerta', 'codigo_postal']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'cif': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control'}),
            'localidad': forms.TextInput(attrs={'class': 'form-control'}),
            'calle': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_calle': forms.TextInput(attrs={'class': 'form-control'}),
            'portal': forms.TextInput(attrs={'class': 'form-control'}),
            'escalera': forms.TextInput(attrs={'class': 'form-control'}),
            'piso': forms.TextInput(attrs={'class': 'form-control'}),
            'puerta': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Las contraseñas no coinciden.")

        return cleaned_data

    def clean_cif(self):
        cif = self.cleaned_data.get('cif')

        if not cif:
            raise forms.ValidationError("Este campo es obligatorio.")

        cif = cif.upper().strip()

        if not re.fullmatch(r'\d{6,8}[A-Z]', cif) and \
           not re.fullmatch(r'[XYZ]\d{6,7}[A-Z]', cif) and \
           not re.fullmatch(r'[A-HJUV]\d{6,8}', cif):
            raise forms.ValidationError("Formato de CIF/NIF/NIE no válido.")

        return cif

    def clean_password1(self):
        password = self.cleaned_data.get("password1")

        if len(password) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")

        if not any(c.isupper() for c in password):
            raise forms.ValidationError("La contraseña debe contener al menos una letra mayúscula.")

        if not any(c.isdigit() for c in password):
            raise forms.ValidationError("La contraseña debe contener al menos un número.")

        if not any(c in "!@#$%^&*()_+-=[]{}|;':\",.<>?/\\~`" for c in password):
            raise forms.ValidationError("La contraseña debe contener al menos un símbolo.")

        return password

# ✅ CAMBIAMOS LoginForm para usar email
class LoginForm(forms.Form):
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class ClienteEdicionForm(forms.ModelForm):
    class Meta:
        model = Cliente
        # ✅ Quitamos 'usuario' también de edición
        fields = ['nombre', 'apellidos', 'telefono', 'cif', 'email', 'provincia',
                  'localidad', 'calle', 'numero_calle', 'portal', 'escalera', 'piso', 'puerta', 'codigo_postal']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'cif': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control'}),
            'localidad': forms.TextInput(attrs={'class': 'form-control'}),
            'calle': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_calle': forms.TextInput(attrs={'class': 'form-control'}),
            'portal': forms.TextInput(attrs={'class': 'form-control'}),
            'escalera': forms.TextInput(attrs={'class': 'form-control'}),
            'piso': forms.TextInput(attrs={'class': 'form-control'}),
            'puerta': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'}),
        }