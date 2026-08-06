from django import forms

from accounts.models import User
from calendario.models import CapaCalendario, Evento, Tarea
from proyectos.models import Proyecto


class EventoForm(forms.ModelForm):
    asignados = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 8}),
    )

    class Meta:
        model = Evento
        fields = (
            'titulo',
            'descripcion',
            'tipo',
            'ubicacion',
            'inicio',
            'fin',
            'proyecto',
            'capa',
            'asignados',
        )
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'inicio': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'fin': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'proyecto': forms.Select(attrs={'class': 'form-control'}),
            'capa': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proyecto'].queryset = Proyecto.objects.all().order_by('nombre')
        self.fields['proyecto'].required = False
        self.fields['capa'].required = False
        if user is not None:
            self.fields['capa'].queryset = CapaCalendario.objects.filter(user=user)
        else:
            self.fields['capa'].queryset = CapaCalendario.objects.none()


class TareaForm(forms.ModelForm):
    asignados = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 8}),
    )

    class Meta:
        model = Tarea
        fields = (
            'titulo',
            'descripcion',
            'prioridad',
            'deadline',
            'proyecto',
            'capa',
            'asignados',
            'completada',
        )
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prioridad': forms.Select(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'proyecto': forms.Select(attrs={'class': 'form-control'}),
            'capa': forms.Select(attrs={'class': 'form-control'}),
            'completada': forms.CheckboxInput(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proyecto'].queryset = Proyecto.objects.all().order_by('nombre')
        self.fields['proyecto'].required = False
        self.fields['capa'].required = False
        if user is not None:
            self.fields['capa'].queryset = CapaCalendario.objects.filter(user=user)
        else:
            self.fields['capa'].queryset = CapaCalendario.objects.none()
