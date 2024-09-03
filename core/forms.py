from django import forms
from .models import Tema

class TemaForm(forms.ModelForm):
    class Meta:
        model = Tema
        fields = ['nome', 'descricao']
