from nucleo import *

@accion('ajustar_inventario', 'administrador', 'insumo,conteo,motivo')
def procesar(c, d, u):
    exigir(d['motivo'] in ['merma', 'daño', 'consumo del personal', 'error'], 'Motivo inválido')
    r = c.execute('SELECT stock FROM insumos WHERE id=?', (d['insumo'],)).fetchone()
    exigir(r, 'Insumo inexistente')
    n = numero(d['conteo'])
    delta = n - r['stock']
    c.execute('UPDATE insumos SET stock=? WHERE id=?', (n, d['insumo']))
    c.execute('INSERT INTO movimientos(insumo,cantidad,tipo,detalle,fecha) VALUES(?,?,?,?,?)', (d['insumo'], delta, 'ajuste', d['motivo'], ahora()))
    auditar(c, u, 'ajuste_inventario', d['insumo'], d)
    return {'diferencia': delta}
