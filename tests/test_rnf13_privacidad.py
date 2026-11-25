import unittest, tempfile, os, json
from pathlib import Path
import nucleo, respaldo
import test_operacion as soporte

class Privacidad(unittest.TestCase):
    setUp = soporte.Operacion.setUp
    tearDown = soporte.Operacion.tearDown
    runop = soporte.Operacion.runop

    def test_suprime_sin_borrar_ventas(self):
        caja = {'id': 'caja', 'rol': 'cajera'}
        d = {'celular': '3001234567', 'nombre': 'Ana', 'direccion': 'Calle 1', 'barrio': 'Centro', 'referencia': 'Puerta', 'autorizacion_medio': 'Formulario'}
        self.runop('guardar_cliente_visual', d, caja)
        actual = os.getcwd()
        with tempfile.TemporaryDirectory() as carpeta:
            try:
                os.chdir(carpeta)
                respaldo.DB = nucleo.DB
                archivo = respaldo.copiar()
                self.runop('eliminar_cliente', {'celular': d['celular']})
                with nucleo.conectar() as c:
                    self.assertIsNone(c.execute('SELECT 1 FROM clientes').fetchone())
                    self.assertNotIn('Calle 1', ' '.join((x[0] for x in c.execute('SELECT datos FROM operaciones'))))
                    self.assertGreater(nucleo.verificar_auditoria(c)['registros'], 0)
                import sqlite3
                from contextlib import closing
                with closing(sqlite3.connect(archivo)) as c, c:
                    self.assertEqual(c.execute('SELECT COUNT(*) FROM clientes').fetchone()[0], 0)
            finally:
                os.chdir(actual)

    def test_exige_autorizacion(self):
        with self.assertRaises(ValueError):
            self.runop('guardar_cliente_visual', {'celular': '3001234567', 'nombre': 'Ana', 'direccion': 'Calle 1', 'barrio': 'Centro', 'referencia': 'Puerta', 'autorizacion_medio': ''}, {'id': 'caja', 'rol': 'cajera'})
