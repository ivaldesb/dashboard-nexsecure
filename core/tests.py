"""Smoke test end-to-end: login wall, permisos por rol y pantallas clave."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from proyectos.models import EstadoProyecto, Proyecto

User = get_user_model()


class SmokeTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('admin', 'admin@x.cl', 'pass1234')
        cls.tecnico = User.objects.create_user('tecnico', 'tec@x.cl', 'pass1234', tag='Técnico')
        cls.cliente_user = User.objects.create_user('cliente', 'cli@x.cl', 'pass1234')
        cls.cliente = Cliente.objects.create(
            tipo='empresa', nombre_empresa='ACME', email='cli@x.cl', user=cls.cliente_user
        )
        # Estado visible al cliente (borrador/creado no lo son)
        cls.estado = EstadoProyecto.objects.get(slug='instalacion-en-progreso')
        cls.estado_interno = EstadoProyecto.objects.get(slug='borrador')
        cls.proyecto = Proyecto.objects.create(
            nombre='Proyecto X', estado=cls.estado, creado_por=cls.admin, codigo='100',
        )
        cls.proyecto.equipo.add(cls.tecnico)
        cls.proyecto.clientes.add(cls.cliente)

    def test_anonimo_redirige_a_login(self):
        resp = self.client.get(reverse('core:dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('accounts:login'), resp.url)

    def test_login_y_pantallas_admin(self):
        self.client.login(username='admin', password='pass1234')
        for name in [
            'core:dashboard', 'accounts:user_list', 'accounts:role_list',
            'clientes:list', 'proyectos:list', 'proyectos:estado_list',
            'activos:list', 'incidencias:list', 'calendario:list',
            'finanzas:dashboard', 'marketing:stub',
        ]:
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 200, f'{name} -> {resp.status_code}')

    def test_detalle_proyecto_todas_las_pestanas(self):
        self.client.login(username='admin', password='pass1234')
        url = reverse('proyectos:detail', args=[self.proyecto.pk])
        for tab in ['resumen', 'activos', 'documentos', 'incidencias', 'presupuestos', 'timeline', 'descargas', 'mantenimiento']:
            resp = self.client.get(url, {'tab': tab})
            self.assertEqual(resp.status_code, 200, f'tab {tab} -> {resp.status_code}')

    def test_equipo_ve_su_proyecto_y_no_finanzas(self):
        self.client.login(username='tecnico', password='pass1234')
        resp = self.client.get(reverse('proyectos:detail', args=[self.proyecto.pk]))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('finanzas:dashboard'))
        self.assertIn(resp.status_code, (302, 403))

    def test_cliente_ve_proyecto_vinculado(self):
        self.client.login(username='cliente', password='pass1234')
        resp = self.client.get(reverse('proyectos:detail', args=[self.proyecto.pk]))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('clientes:portal'))
        self.assertEqual(resp.status_code, 200)

    def test_cliente_no_ve_borrador(self):
        borrador = Proyecto.objects.create(
            nombre='Secreto', estado=self.estado_interno, creado_por=self.admin, codigo='101',
        )
        borrador.clientes.add(self.cliente)
        self.client.login(username='cliente', password='pass1234')
        resp = self.client.get(reverse('proyectos:detail', args=[borrador.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_otro_usuario_no_ve_proyecto(self):
        User.objects.create_user('externo', 'ext@x.cl', 'pass1234')
        self.client.login(username='externo', password='pass1234')
        resp = self.client.get(reverse('proyectos:detail', args=[self.proyecto.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_crear_proyecto_genera_ppto_inicial_y_timeline(self):
        self.client.login(username='admin', password='pass1234')
        resp = self.client.post(reverse('proyectos:create'), {
            'nombre': 'Nuevo', 'descripcion': '', 'estado': self.estado_interno.pk,
            'codigo': '',
        })
        self.assertEqual(resp.status_code, 302)
        nuevo = Proyecto.objects.get(nombre='Nuevo')
        self.assertEqual(nuevo.presupuestos.filter(tipo='inicial').count(), 1)
        self.assertGreaterEqual(nuevo.timeline.count(), 1)

    def test_pdf_reporte(self):
        self.client.login(username='admin', password='pass1234')
        resp = self.client.get(reverse('proyectos:pdf_reporte', args=[self.proyecto.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
