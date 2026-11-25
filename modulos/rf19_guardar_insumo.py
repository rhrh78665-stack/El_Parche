from nucleo import *

@accion('guardar_insumo', 'administrador', 'id,nombre,unidad,minimo')
def procesar(c, d, u):
    exigir(d['unidad'] in ['unidad', 'gramo', 'mililitro'], 'Unidad inválida')
    id = texto(d['id'])
    minimo = numero(d['minimo'])
    r = c.execute('SELECT unidad FROM insumos WHERE id=?', (id,)).fetchone()
    exigir(not r or r['unidad'] == d['unidad'], 'No cambie la unidad de un insumo existente')
    c.execute('INSERT INTO insumos VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre,minimo=excluded.minimo', (id, texto(d['nombre']), d['unidad'], 0, minimo))
    return {'id': id}
