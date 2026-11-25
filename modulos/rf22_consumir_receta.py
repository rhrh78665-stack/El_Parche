from nucleo import *

@accion('consumir_receta', 'cocina', 'pedido')
def procesar(c, d, u):
    p = pedido(c, d['pedido'])
    exigir(p['estado'] == 'recibido', 'Ya consumido o estado inválido')
    exigir(all((c.execute('SELECT 1 FROM recetas WHERE producto=?', (l['producto'],)).fetchone() for l in c.execute('SELECT producto FROM lineas WHERE pedido=?', (p['id'],)))), 'Defina todas las recetas antes de preparar')
    for r in c.execute('SELECT r.insumo,SUM(r.cantidad*l.cantidad) AS cantidad FROM lineas l JOIN recetas r ON r.producto=l.producto WHERE l.pedido=? GROUP BY r.insumo', (p['id'],)).fetchall():
        exigir(c.execute('UPDATE insumos SET stock=stock-? WHERE id=? AND stock>=?', (r['cantidad'], r['insumo'], r['cantidad'])).rowcount, 'Existencias insuficientes')
        c.execute('INSERT INTO movimientos(insumo,cantidad,tipo,detalle,fecha) VALUES(?,?,?,?,?)', (r['insumo'], -r['cantidad'], 'consumo', p['id'], ahora()))
    return {'ok': True}
