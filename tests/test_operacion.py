import unittest, tempfile, os, sys, uuid, sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nucleo
import servidor

class Operacion(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        nucleo.DB = str(Path(self.tmp.name) / 'test.db')
        os.environ['PARCHE_ADMIN_PIN'] = '93847561'
        nucleo.iniciar()
        self.admin = {'id': 'admin', 'rol': 'administrador'}
        for id, rol in [('caja', 'cajera'), ('chef', 'cocina'), ('moto', 'domiciliario')]:
            self.runop('guardar_usuario', {'id': id, 'nombre': id, 'rol': rol, 'pin': '84736251', 'activo': True})

    def tearDown(self):
        self.tmp.cleanup()

    def runop(self, n, d, u=None, id=None):
        return nucleo.ejecutar(n, d, u or self.admin, id or str(uuid.uuid4()))

    def preparar(self):
        self.runop('guardar_insumo', {'id': 'pan', 'nombre': 'Pan', 'unidad': 'unidad', 'minimo': 2})
        self.runop('registrar_compra', {'proveedor': 'Panadería', 'fecha': '2026-11-25', 'insumos': [{'insumo': 'pan', 'cantidad': 10, 'costo': 10000}]})
        self.runop('guardar_producto', {'id': 'h', 'nombre': 'Hamburguesa', 'categoria': 'Comidas', 'precio': 15000, 'modificadores': ['sin cebolla'], 'activo': True})
        self.runop('guardar_receta', {'producto': 'h', 'insumos': [{'insumo': 'pan', 'cantidad': 1}]})
        return self.runop('registrar_pedido', {'canal': 'mesa', 'mesa': '1', 'lineas': [{'producto': 'h', 'cantidad': 2}]}, {'id': 'caja', 'rol': 'cajera'})['id']

    def test_ciclo_y_reintento(self):
        p = self.preparar()
        chef = {'id': 'chef', 'rol': 'cocina'}
        id = str(uuid.uuid4())
        d = {'pedido': p, 'estado': 'en preparación'}
        self.runop('estado_cocina', d, chef, id)
        self.runop('estado_cocina', d, chef, id)
        with nucleo.conectar() as c:
            self.assertEqual(c.execute("SELECT stock FROM insumos WHERE id='pan'").fetchone()[0], 8)
        with self.assertRaises(ValueError):
            self.runop('consumir_receta', {'pedido': p}, chef)
        self.runop('estado_cocina', {'pedido': p, 'estado': 'listo'}, chef)
        caja = {'id': 'caja', 'rol': 'cajera'}
        self.runop('abrir_caja', {'base': 50000}, caja)
        with self.assertRaises(ValueError):
            self.runop('cobrar_pedido', {'pedido': p, 'pagos': [{'medio': 'efectivo', 'valor': 1}]}, caja)
        self.runop('cobrar_pedido', {'pedido': p, 'pagos': [{'medio': 'efectivo', 'valor': 30000}]}, caja)
        r = self.runop('cerrar_caja', {'contado': 80000}, caja)
        self.assertEqual(r['diferencia'], 0)

    def test_permisos_auditoria(self):
        with self.assertRaises(ValueError):
            self.runop('guardar_insumo', {}, {'id': 'chef', 'rol': 'cocina'})
        with nucleo.conectar() as c:
            with self.assertRaises(sqlite3.IntegrityError):
                c.execute('DELETE FROM auditoria')

    def test_transaccion_sin_stock(self):
        p = self.preparar()
        self.runop('ajustar_inventario', {'insumo': 'pan', 'conteo': 0, 'motivo': 'merma'})
        with self.assertRaises(ValueError):
            self.runop('estado_cocina', {'pedido': p, 'estado': 'en preparación'}, {'id': 'chef', 'rol': 'cocina'})
        with nucleo.conectar() as c:
            self.assertEqual(nucleo.pedido(c, p)['estado'], 'recibido')

    def test_referencia(self):
        p = self.preparar()
        caja = {'id': 'caja', 'rol': 'cajera'}
        self.runop('abrir_caja', {'base': 0}, caja)
        self.runop('cobrar_pedido', {'pedido': p, 'pagos': [{'medio': 'Nequi', 'valor': 30000, 'referencia': 'ABC'}]}, caja)
        p2 = self.preparar()
        with self.assertRaises(ValueError):
            self.runop('cobrar_pedido', {'pedido': p2, 'pagos': [{'medio': 'Nequi', 'valor': 30000, 'referencia': 'abc'}]}, caja)

    def test_consentimiento(self):
        with self.assertRaises(ValueError):
            self.runop('guardar_cliente_visual', {'celular': '3001234567', 'nombre': 'Ana', 'direccion': 'Calle 1', 'barrio': 'Centro', 'referencia': 'Puerta', 'autorizacion_medio': ''}, {'id': 'caja', 'rol': 'cajera'})
if __name__ == '__main__':
    unittest.main()

class FlujosAdicionales(unittest.TestCase):
    setUp = Operacion.setUp
    tearDown = Operacion.tearDown
    runop = Operacion.runop
    preparar = Operacion.preparar

    def test_domicilio(self):
        self.preparar()
        caja = {'id': 'caja', 'rol': 'cajera'}
        chef = {'id': 'chef', 'rol': 'cocina'}
        moto = {'id': 'moto', 'rol': 'domiciliario'}
        self.runop('guardar_cliente_visual', {'celular': '3001234567', 'nombre': 'Cliente de prueba', 'direccion': 'Dirección de prueba', 'barrio': 'Barrio de prueba', 'referencia': 'Puerta principal', 'autorizacion_medio': 'Formulario'}, caja)
        p = self.runop('registrar_pedido', {'canal': 'WhatsApp', 'cliente': '3001234567', 'lineas': [{'producto': 'h', 'cantidad': 1}]}, caja)['id']
        self.runop('estado_cocina', {'pedido': p, 'estado': 'en preparación'}, chef)
        self.runop('estado_cocina', {'pedido': p, 'estado': 'listo'}, chef)
        self.runop('despachar_domicilio', {'pedido': p, 'domiciliario': 'moto', 'contraentrega': True}, caja)
        rows = self.runop('mis_domicilios', {}, moto)
        self.assertEqual(rows[0]['datos_cliente']['celular'], '3001234567')
        self.runop('entregar_pedido', {'pedido': p}, moto)
        cuadre = self.runop('cuadre_domiciliario', {'domiciliario': 'moto', 'desde': '2000', 'hasta': '2099'}, caja)
        self.assertEqual(cuadre[0]['pendiente_cobrar'], 15000)

    def test_personalizacion_y_cancelacion(self):
        p = self.preparar()
        caja = {'id': 'caja', 'rol': 'cajera'}
        lines = self.runop('lineas_operables', {}, caja)
        self.runop('modificar_linea', {'linea': lines[0]['id'], 'modificadores': ['sin cebolla'], 'observacion': 'Bien cocida'}, caja)
        result = self.runop('detalle_pedido', {'pedido': p}, caja)
        self.assertEqual(result['lineas'][0]['observacion'], 'Bien cocida')
        self.runop('abrir_caja', {'base': 0}, caja)
        self.runop('cobrar_pedido', {'pedido': p, 'pagos': [{'medio': 'efectivo', 'valor': 30000}]}, caja)
        with self.assertRaises(ValueError):
            self.runop('cancelar_pedido', {'pedido': p, 'motivo': 'cliente desistió'}, caja)
        self.runop('cancelar_pedido', {'pedido': p, 'motivo': 'cliente desistió'})
        state = self.runop('estado_caja', {}, caja)
        self.assertEqual(state['efectivo'], 0)

    def test_reportes(self):
        p = self.preparar()
        caja = {'id': 'caja', 'rol': 'cajera'}
        self.runop('abrir_caja', {'base': 50000}, caja)
        self.runop('cobrar_pedido', {'pedido': p, 'pagos': [{'medio': 'efectivo', 'valor': 10000}, {'medio': 'Nequi', 'valor': 20000, 'referencia': 'REP-1'}]}, caja)
        self.runop('cerrar_caja', {'contado': 60000}, caja)
        ventas = self.runop('reporte_ventas', {'desde': '2000', 'hasta': '2099'})
        self.assertEqual(sum((x['total'] for x in ventas['cobros'])), 30000)
        cierres = self.runop('historial_cajas', {'desde': '2000', 'hasta': '2099', 'cajera': ''})
        self.assertEqual(cierres[0]['diferencia'], 0)
        self.assertEqual(self.runop('reporte_atencion', {'desde': '2000', 'hasta': '2099'})['cancelados'], [])

    def test_operacion_interna_y_usuario_desactivado(self):
        p = self.preparar()
        caja = {'id': 'caja', 'rol': 'cajera'}
        with self.assertRaises(ValueError):
            self.runop('consumir_receta', {'pedido': p}, {'id': 'chef', 'rol': 'cocina'})
        self.runop('guardar_usuario', {'id': 'caja', 'nombre': 'Caja', 'rol': 'cajera', 'pin': '', 'activo': False})
        with self.assertRaises(ValueError):
            self.runop('cola_pedidos', {}, caja)
