import unittest
import uuid
import test_operacion as soporte
import nucleo
import identidad

class DosRoles(unittest.TestCase):
    tearDown = soporte.Operacion.tearDown
    runop = soporte.Operacion.runop

    def setUp(self):
        soporte.Operacion.setUp(self)
        identidad.inicializar_cuentas()
        self.rest = {'id': 'restaurante', 'rol': 'restaurante'}
        self.cliente = {'id': 'cliente', 'rol': 'cliente'}

    def test_solo_dos_roles(self):
        self.assertEqual(identidad.ROLES, {'restaurante', 'cliente'})
        self.assertEqual(set(identidad.TABS), identidad.ROLES)
        self.assertIn('seguimiento', self.runop('portal_perfil', {}, self.cliente)['pestanas'])
        self.assertNotIn('equipo', self.runop('portal_perfil', {}, self.rest)['pestanas'])

    def test_accesos_concretos(self):
        with nucleo.conectar() as c:
            for id, pin in [('restaurante', '48261937'), ('cliente', '73619482')]:
                u = c.execute('SELECT * FROM usuarios WHERE id=?', (id,)).fetchone()
                self.assertEqual(u['pin'], nucleo.clave(pin, u['sal']))

    def test_reinicio_no_duplica(self):
        with nucleo.conectar() as c:
            n = c.execute('SELECT COUNT(*) FROM pedidos_simulados').fetchone()[0]
        identidad.inicializar_cuentas()
        with nucleo.conectar() as c:
            self.assertEqual(n, c.execute('SELECT COUNT(*) FROM pedidos_simulados').fetchone()[0])

    def test_ciclo_entero_sin_otro_rol(self):
        id = self.runop('portal_crear_pedido', {'restaurante': 'res_01', 'lineas': [{'producto': 'res_01_p01', 'cantidad': 1}], 'direccion': 'Calle 5 # 27-42', 'barrio': 'San Fernando', 'celular': '3005550148', 'consentimiento': True}, self.cliente)['id']
        for estado in ['en preparación', 'listo', 'en ruta']:
            self.runop('portal_estado_pedido', {'pedido': id, 'estado': estado}, self.rest)
        p = self.runop('portal_pedido', {'pedido': id}, self.cliente)
        with self.assertRaises(ValueError):
            self.runop('portal_estado_pedido', {'pedido': id, 'estado': 'entregado', 'valor_cobrado': 0}, self.rest)
        self.runop('portal_estado_pedido', {'pedido': id, 'estado': 'entregado', 'valor_cobrado': p['total']}, self.rest)
        p = self.runop('portal_pedido', {'pedido': id}, self.cliente)
        self.assertEqual(p['pago_estado'], 'cobrado')
        self.assertEqual([e['estado'] for e in p['historial_estados']], ['recibido', 'en preparación', 'listo', 'en ruta', 'entregado'])

    def test_cliente_no_opera_restaurante(self):
        for action in ['portal_panel', 'portal_guardar_producto', 'portal_inventario', 'portal_reportes']:
            with self.assertRaises(ValueError):
                self.runop(action, {}, self.cliente)

    def test_otro_restaurante(self):
        for action in ['portal_restaurante', 'portal_pedidos']:
            with self.assertRaises(ValueError):
                self.runop(action, {'restaurante': 'res_02'}, self.rest)

    def test_pedido_ajeno(self):
        with nucleo.conectar() as c:
            id = c.execute("SELECT id FROM pedidos_simulados WHERE restaurante='res_02' LIMIT 1").fetchone()[0]
        for u in [self.rest, self.cliente]:
            with self.assertRaises(ValueError):
                self.runop('portal_pedido', {'pedido': id}, u)

    def test_queja_respuesta_y_estado(self):
        pedidos = self.runop('portal_pedidos', {}, self.cliente)
        abiertos = self.runop('portal_quejas', {}, self.cliente)
        ids = {q['pedido'] for q in abiertos}
        id = next((p['id'] for p in pedidos if p['id'] not in ids))
        q = self.runop('portal_crear_queja', {'pedido': id, 'asunto': 'Consulta de entrega', 'mensaje': 'Quiero verificar mi dirección'}, self.cliente)['id']
        self.runop('portal_responder_queja', {'queja': q, 'mensaje': 'Ya revisamos los datos', 'estado': 'resuelta'}, self.rest)
        q = next((x for x in self.runop('portal_quejas', {}, self.cliente) if x['id'] == q))
        self.assertEqual(q['estado'], 'resuelta')
        self.assertEqual(len(q['mensajes']), 2)

    def test_cliente_no_resuelve_su_queja(self):
        q = self.runop('portal_quejas', {}, self.cliente)[0]
        with self.assertRaises(ValueError):
            self.runop('portal_responder_queja', {'queja': q['id'], 'mensaje': 'Cambiar estado', 'estado': 'resuelta'}, self.cliente)

    def test_queja_ajena_y_doble(self):
        with self.assertRaises(ValueError):
            self.runop('portal_responder_queja', {'queja': 'inexistente', 'mensaje': 'Hola'}, self.rest)
        q = self.runop('portal_quejas', {}, self.cliente)[0]
        with self.assertRaises(ValueError):
            self.runop('portal_crear_queja', {'pedido': q['pedido'], 'asunto': 'Otra', 'mensaje': 'Duplicada'}, self.cliente)

    def test_sin_cuentas_extra_en_carga(self):
        with nucleo.conectar() as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM usuarios WHERE id LIKE 'cocina.%' OR id LIKE 'rest.%'").fetchone()[0], 0)

    def test_menus_con_recetas_y_reservas(self):
        menu = self.runop('portal_restaurante', {}, self.rest)
        self.assertEqual(len(menu['menu']), 6)
        self.assertTrue(self.runop('portal_inventario', {}, self.rest))
        for p in self.runop('portal_pedidos', {}, self.cliente):
            self.assertEqual(p['usuario_cliente'], 'cliente')
