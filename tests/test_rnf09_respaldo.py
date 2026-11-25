import unittest, tempfile, os
from pathlib import Path
import test_operacion as soporte
import respaldo, nucleo

class Respaldo(unittest.TestCase):
    setUp = soporte.Operacion.setUp
    tearDown = soporte.Operacion.tearDown
    runop = soporte.Operacion.runop

    def test_copia_y_restauracion(self):
        respaldo.DB = nucleo.DB
        with tempfile.TemporaryDirectory() as d:
            archivo = respaldo.copiar(d)
            with nucleo.conectar() as c:
                c.execute("UPDATE usuarios SET nombre='Cambio' WHERE id='admin'")
            actual = os.getcwd()
            try:
                os.chdir(d)
                respaldo.restaurar(archivo)
            finally:
                os.chdir(actual)
            with nucleo.conectar() as c:
                self.assertEqual(c.execute("SELECT nombre FROM usuarios WHERE id='admin'").fetchone()[0], 'Administrador')

    def test_rechaza_copia_alterada(self):
        respaldo.DB = nucleo.DB
        with tempfile.TemporaryDirectory() as d:
            archivo = respaldo.copiar(d)
            Path(archivo).write_bytes(b'alterado')
            with self.assertRaises(ValueError):
                respaldo.restaurar(archivo)

    def test_retencion(self):
        respaldo.DB = nucleo.DB
        with tempfile.TemporaryDirectory() as d:
            archivo = Path(respaldo.copiar(d))
            import time
            os.utime(archivo, (time.time() - 31 * 86400,) * 2)
            respaldo.copiar(d)
            self.assertFalse(archivo.exists())
            self.assertFalse(archivo.with_suffix('.sha256').exists())

    def test_no_restaura_con_servidor_en_uso(self):
        from bloqueo import bloquear
        respaldo.DB = nucleo.DB
        with tempfile.TemporaryDirectory() as d:
            archivo = respaldo.copiar(d)
            with bloquear(nucleo.DB + '.lock'):
                with self.assertRaises(RuntimeError):
                    respaldo.restaurar(archivo)
