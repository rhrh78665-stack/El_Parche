import unittest
import uuid
import test_operacion as soporte
import nucleo

class Catalogo(unittest.TestCase):
    setUp = soporte.Operacion.setUp
    tearDown = soporte.Operacion.tearDown
    runop = soporte.Operacion.runop

    def elegir(self):
        return self.runop('detalle_restaurante', {'restaurante': 'res_01'})

    def pedido(self, producto=None):
        detalle = self.elegir()
        return {'restaurante': 'res_01', 'cliente': 'Cliente de prueba', 'barrio': 'San Fernando', 'observacion': 'Sin sal adicional', 'lineas': [{'producto': producto or detalle['menu'][0]['id'], 'cantidad': 2}]}

    def test_treinta_restaurantes_y_ciento_ochenta_platos(self):
        restaurantes = self.runop('listar_restaurantes', {})
        self.assertEqual(len(restaurantes), 30)
        self.assertEqual(len({r['nombre'] for r in restaurantes}), 30)
        self.assertEqual(len({r['categoria'] for r in restaurantes}), 10)
        with nucleo.conectar() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM menus_restaurantes').fetchone()[0], 180)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM pedidos_simulados').fetchone()[0], 168)
        nucleo.iniciar()
        with nucleo.conectar() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM pedidos_simulados').fetchone()[0], 168)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM lineas_simuladas').fetchone()[0], 336)

    def test_filtros(self):
        self.assertEqual(len(self.runop('listar_restaurantes', {'categoria': 'Pizzas'})), 3)
        pedidos = self.runop('listar_pedidos_restaurantes', {'restaurante': 'res_01', 'estado': 'recibido'})
        self.assertTrue(all((p['restaurante'] == 'res_01' and p['estado'] == 'recibido' for p in pedidos)))
        rows = self.runop('listar_restaurantes', {'buscar': 'masa madre'})
        self.assertEqual(rows[0]['nombre'], 'Masa Madre 72')
        self.assertEqual(self.runop('listar_restaurantes', {'buscar': 'maiz y calle'})[0]['nombre'], 'Maíz y Calle')

    def test_idempotencia_y_stock(self):
        d = self.pedido()
        detalle = self.elegir()
        p = detalle['menu'][0]
        id = str(uuid.uuid4())
        a = self.runop('simular_pedido_restaurante', d, id=id)
        b = self.runop('simular_pedido_restaurante', d, id=id)
        self.assertEqual(a, b)
        actualizado = self.elegir()['menu'][0]
        self.assertEqual(actualizado['stock'], p['stock'] - 2)
        self.assertEqual(a['total'], p['precio'] * 2 + detalle['restaurante']['envio'])

    def test_rechaza_producto_de_otra_cocina(self):
        ajeno = self.runop('detalle_restaurante', {'restaurante': 'res_02'})['menu'][0]['id']
        antes = self.elegir()['menu'][0]['stock']
        with self.assertRaises(ValueError):
            self.runop('simular_pedido_restaurante', self.pedido(ajeno))
        self.assertEqual(self.elegir()['menu'][0]['stock'], antes)

    def test_ciclo_de_entrega(self):
        id = self.runop('simular_pedido_restaurante', self.pedido())['id']
        with self.assertRaises(ValueError):
            self.runop('estado_pedido_simulado', {'pedido': id, 'estado': 'entregado'})
        for estado in ['en preparación', 'listo', 'en ruta', 'entregado']:
            d = {'pedido': id, 'estado': estado, 'domiciliario': 'Carlos Rivas'}
            self.assertEqual(self.runop('estado_pedido_simulado', d)['estado'], estado)
        with self.assertRaises(ValueError):
            self.runop('estado_pedido_simulado', {'pedido': id, 'estado': 'recibido'})

    def test_cancelacion_restituye_disponibilidad_una_vez(self):
        p = self.elegir()['menu'][0]
        id = self.runop('simular_pedido_restaurante', self.pedido())['id']
        op = str(uuid.uuid4())
        d = {'pedido': id, 'estado': 'cancelado'}
        self.runop('estado_pedido_simulado', d, id=op)
        self.runop('estado_pedido_simulado', d, id=op)
        self.assertEqual(self.elegir()['menu'][0]['stock'], p['stock'])

    def test_cocina_pausada_no_recibe_pedidos(self):
        self.runop('estado_restaurante_simulado', {'restaurante': 'res_01', 'estado': 'pausado'})
        with self.assertRaises(ValueError):
            self.runop('simular_pedido_restaurante', self.pedido())

    def test_aisla_simulacion_y_permisos(self):
        self.runop('simular_pedido_restaurante', self.pedido())
        with nucleo.conectar() as c:
            for tabla in ['pedidos', 'pagos', 'cajas', 'insumos']:
                self.assertEqual(c.execute('SELECT COUNT(*) FROM ' + tabla).fetchone()[0], 0)
        with self.assertRaises(ValueError):
            self.runop('listar_restaurantes', {}, {'id': 'caja', 'rol': 'cajera'})
