import unittest, sqlite3
import nucleo
import test_operacion as soporte

class Auditoria(unittest.TestCase):
    setUp = soporte.Operacion.setUp
    tearDown = soporte.Operacion.tearDown
    runop = soporte.Operacion.runop

    def test_cadena(self):
        with nucleo.conectar() as c:
            resultado = nucleo.verificar_auditoria(c)
            self.assertGreater(resultado['registros'], 0)
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute("UPDATE sellos_auditoria SET huella='x'")
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute('DELETE FROM auditoria')
