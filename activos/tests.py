from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from activos.forms import ActivoForm
from activos.models import CategoriaActivo
from proyectos.models import EstadoProyecto, Proyecto

User = get_user_model()


class ActivoFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u1', password='x')
        self.estado = EstadoProyecto.objects.first() or EstadoProyecto.objects.create(
            nombre='Activo', slug='activo', orden=1,
        )
        self.proyecto = Proyecto.objects.create(
            nombre='P1', codigo='9001', estado=self.estado, creado_por=self.user,
        )
        self.proyecto.equipo.add(self.user)

    def test_categorias_seeded(self):
        self.assertTrue(CategoriaActivo.objects.filter(nombre='Cámara').exists())
        self.assertGreaterEqual(CategoriaActivo.objects.count(), 5)

    def test_form_has_single_ip_and_factura(self):
        form = ActivoForm(user=self.user)
        self.assertIn('ip_dominio', form.fields)
        self.assertNotIn('ip', form.fields)
        self.assertIn('factura', form.fields)
        self.assertNotIn('factura_boleta', form.fields)
        self.assertGreater(form.fields['categoria'].queryset.count(), 0)
        self.assertEqual(form.fields['archivo_compra'].label, 'Foto caja o S/N')

    def test_create_get_modal(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse('activos:create'), {'proyecto': self.proyecto.pk, 'modal': '1'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Foto caja o S/N')
        self.assertContains(r, 'IP / dominio')
        self.assertNotContains(r, 'name="ip"')
        self.assertContains(r, 'Cámara')
