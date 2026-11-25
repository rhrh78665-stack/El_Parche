from nucleo import *

@accion('guardar_receta', 'administrador', 'producto,insumos:json')
def procesar(c, d, u):
    exigir(c.execute('SELECT 1 FROM productos WHERE id=?', (d['producto'],)).fetchone(), 'Producto inexistente')
    exigir(isinstance(d['insumos'], list) and d['insumos'], 'Receta vacía')
    c.execute('DELETE FROM recetas WHERE producto=?', (d['producto'],))
    for x in d['insumos']:
        c.execute('INSERT INTO recetas VALUES(?,?,?)', (d['producto'], x['insumo'], numero(x['cantidad'], 0.001)))
    return {'ok': True}
