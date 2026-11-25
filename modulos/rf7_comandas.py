from nucleo import *

@accion('comandas', 'cocina,cajera,administrador', '')
def procesar(c, d, u):
    salida = []
    for p in c.execute("SELECT * FROM pedidos WHERE estado IN ('recibido','en preparación','listo') ORDER BY fecha"):
        item = dict(p)
        item['lineas'] = [dict(l) for l in c.execute('SELECT * FROM lineas WHERE pedido=?', (p['id'],))]
        salida.append(item)
    return salida
