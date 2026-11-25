from nucleo import *

@accion('buscar_cliente', 'cajera,administrador', 'celular')
def procesar(c, d, u):
    r = c.execute('SELECT * FROM clientes WHERE celular=?', (d['celular'],)).fetchone()
    return dict(r) if r else None
