from django import forms
from django.forms import CheckboxSelectMultiple, ModelForm

from accounts.models import User
from documentos.models import CategoriaDocumento, Documento


class DocumentoUploadForm(ModelForm):
    categoria_nueva = forms.CharField(
        required=False,
        max_length=100,
        label='Nueva categoría',
        help_text='Si rellenas esto, se crea (o reutiliza) la categoría y se asigna al documento.',
    )

    class Meta:
        model = Documento
        fields = ['titulo', 'archivo', 'categoria', 'visible_cliente', 'solo_admin']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = CategoriaDocumento.objects.all()
        self.fields['categoria'].required = False
        self.fields['categoria'].empty_label = '— Sin categoría —'
        for name, field in self.fields.items():
            if name in ('visible_cliente', 'solo_admin'):
                continue
            if getattr(field.widget, 'input_type', None) != 'checkbox':
                field.widget.attrs.setdefault('class', 'form-control')

    def clean(self):
        cleaned = super().clean()
        nueva = (cleaned.get('categoria_nueva') or '').strip()
        if nueva:
            cleaned['categoria_nueva'] = nueva
        return cleaned

    def save(self, commit=True):
        doc = super().save(commit=False)
        nueva = (self.cleaned_data.get('categoria_nueva') or '').strip()
        if nueva:
            cat, _ = CategoriaDocumento.objects.get_or_create(nombre=nueva)
            doc.categoria = cat
        if commit:
            doc.save()
            self.save_m2m()
        return doc


class DocumentoAclForm(ModelForm):
    class Meta:
        model = Documento
        fields = ['visible_cliente', 'solo_admin', 'users_allowed']
        widgets = {'users_allowed': CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['users_allowed'].queryset = User.objects.filter(is_active=True).order_by('username')
