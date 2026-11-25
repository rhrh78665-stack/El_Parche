import unittest
import test_operacion as soporte

class Configuracion(unittest.TestCase):
    setUp = soporte.Operacion.setUp
    tearDown = soporte.Operacion.tearDown
    runop = soporte.Operacion.runop

    def test_cambio_sin_codigo(self):
        self.runop('configurar_operacion', {'demora': 7, 'medios': ['efectivo', 'Nequi']})
        r = self.runop('preferencias_operacion', {}, {'id': 'chef', 'rol': 'cocina'})
        self.assertEqual(r['demora'], 7)
        self.assertEqual(r['medios'], ['efectivo', 'Nequi'])
