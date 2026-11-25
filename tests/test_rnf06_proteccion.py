import unittest
import nucleo
import test_operacion as soporte

class Proteccion(unittest.TestCase):
    setUp = soporte.Operacion.setUp
    tearDown = soporte.Operacion.tearDown
    runop = soporte.Operacion.runop

    def test_pin_hash_sal(self):
        with nucleo.conectar() as c:
            rows = c.execute('SELECT pin,sal FROM usuarios').fetchall()
            self.assertEqual(len({r['sal'] for r in rows}), len(rows))
            for r in rows:
                self.assertNotIn(r['pin'], ['93847561', '84736251'])
                self.assertEqual(len(r['pin']), 128)
