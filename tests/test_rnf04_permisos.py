import test_operacion as soporte
import unittest

class Permisos(unittest.TestCase):
    setUp = soporte.Operacion.setUp
    tearDown = soporte.Operacion.tearDown
    runop = soporte.Operacion.runop

    def test_matriz_roles(self):
        for usuario, rol in [('caja', 'cajera'), ('chef', 'cocina'), ('moto', 'domiciliario')]:
            for accion in ['guardar_producto', 'ajustar_inventario', 'reporte_ventas', 'guardar_usuario']:
                with self.subTest(rol=rol, accion=accion):
                    with self.assertRaises(ValueError):
                        self.runop(accion, {}, {'id': usuario, 'rol': rol})

    def test_no_suplantacion(self):
        with self.assertRaises(ValueError):
            self.runop('guardar_producto', {}, {'id': 'caja', 'rol': 'administrador'})
