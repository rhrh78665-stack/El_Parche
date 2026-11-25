from nucleo import *

@accion('guardar_producto', 'administrador', 'id,nombre,categoria,precio,modificadores:json,activo:bool')
def procesar(c, d, u):
    id = texto(d['id'])
    precio = dinero(d['precio'])
    op = d['modificadores']
    exigir(isinstance(op, list) and all((isinstance(x, str) and len(x) <= 80 for x in op)), 'Modificadores inválidos')
    c.execute('INSERT INTO productos VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre,categoria=excluded.categoria,precio=excluded.precio,modificadores=excluded.modificadores,activo=excluded.activo', (id, texto(d['nombre']), texto(d['categoria']), precio, json.dumps(op), int(bool(d['activo']))))
    auditar(c, u, 'cambio_producto_precio', id, d)
    return {'id': id}
