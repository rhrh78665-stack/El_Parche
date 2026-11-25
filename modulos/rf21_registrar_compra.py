from nucleo import *

@accion('registrar_compra', 'administrador', 'proveedor,fecha,insumos:json')
def procesar(c, d, u):
    id = str(uuid.uuid4())
    exigir(isinstance(d['insumos'], list) and d['insumos'], 'Compra vacía')
    costo = sum((dinero(x['costo']) for x in d['insumos']))
    c.execute('INSERT INTO compras VALUES(?,?,?,?)', (id, texto(d['proveedor']), texto(d['fecha']), costo))
    for x in d['insumos']:
        n = numero(x['cantidad'], 0.001)
        exigir(c.execute('UPDATE insumos SET stock=stock+? WHERE id=?', (n, x['insumo'])).rowcount, 'Insumo inexistente')
        c.execute('INSERT INTO movimientos(insumo,cantidad,tipo,detalle,fecha) VALUES(?,?,?,?,?)', (x['insumo'], n, 'compra', id, ahora()))
    return {'id': id, 'costo': costo}
