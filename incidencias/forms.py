from django import forms

from activos.models import Activo
from incidencias.models import Incidencia


class IncidenciaForm(forms.ModelForm):
    class Meta:
        model = Incidencia
        fields = ['titulo', 'descripcion', 'diagnostico', 'causas', 'recomendaciones', 'activos']
        widgets = {
            'activos': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 6}),
        }

    def __init__(self, *args, proyecto=None, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('titulo', 'descripcion', 'diagnostico', 'causas', 'recomendaciones'):
            self.fields[name].widget.attrs.setdefault('class', 'form-control')
        for name in ('descripcion', 'diagnostico', 'causas', 'recomendaciones'):
            self.fields[name].widget.attrs.setdefault('rows', 3)
        qs = Activo.objects.none()
        if proyecto is not None:
            qs = Activo.objects.filter(proyecto=proyecto)
        elif self.instance and self.instance.pk:
            qs = Activo.objects.filter(proyecto=self.instance.proyecto)
        self.fields['activos'].queryset = qs
        self.fields['activos'].required = False


class FotoUploadForm(forms.Form):
    imagen = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'}),
    )
