import unittest, uuid
import nucleo
import test_operacion as soporte

class Idempotencia(unittest.TestCase):
    setUp = soporte.Operacion.setUp
    tearDown = soporte.Operacion.tearDown
    runop = soporte.Operacion.runop
    preparar = soporte.Operacion.preparar

    def test_pedido_reintentado(self):
        self.preparar()
        id = str(uuid.uuid4())
        op = str(uuid.uuid4())
        d = {'id': id, 'canal': 'mostrador', 'lineas': [{'producto': 'h', 'cantidad': 1}]}
        u = {'id': 'caja', 'rol': 'cajera'}
        a = self.runop('registrar_pedido', d, u, op)
        b = self.runop('registrar_pedido', d, u, op)
        self.assertEqual(a, b)
        self.assertEqual(a['id'], id)
        with nucleo.conectar() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM pedidos WHERE id=?', (id,)).fetchone()[0], 1)
