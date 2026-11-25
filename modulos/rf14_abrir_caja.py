from nucleo import *

@accion('abrir_caja', 'cajera', 'base')
def procesar(c, d, u):
    id = str(uuid.uuid4())
    c.execute('INSERT INTO cajas(id,cajera,base,apertura) VALUES(?,?,?,?)', (id, u['id'], dinero(d['base']), ahora()))
    return {'id': id}
