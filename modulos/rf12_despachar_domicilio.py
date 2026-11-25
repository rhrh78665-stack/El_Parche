from nucleo import *

@accion('despachar_domicilio', 'cajera', 'pedido,domiciliario,contraentrega:bool')
def procesar(c, d, u):
    p = pedido(c, d['pedido'])
    exigir(p['estado'] == 'listo' and p['canal'] in ['WhatsApp', 'llamada'], 'Solo domicilio propio listo')
    r = c.execute("SELECT 1 FROM usuarios WHERE id=? AND rol='domiciliario' AND activo=1", (d['domiciliario'],)).fetchone()
    exigir(r, 'Domiciliario inválido')
    exigir(not d['contraentrega'] or not p['pagado'], 'Ya pagado')
    c.execute("UPDATE pedidos SET domiciliario=?,salida=?,estado='despachado',contraentrega=? WHERE id=?", (d['domiciliario'], ahora(), int(bool(d['contraentrega'])), p['id']))
    return {'ok': True}
