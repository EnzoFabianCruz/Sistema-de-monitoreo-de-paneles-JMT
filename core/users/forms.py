from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm # Importante

class RegistroUsuarioForm(UserCreationForm): # Cambiamos la herencia
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email'] # La contraseña se maneja sola
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 45678912'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    # Aplicamos estilos a los campos de contraseña automáticos
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'