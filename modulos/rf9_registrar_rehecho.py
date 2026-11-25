from nucleo import *

@accion('registrar_rehecho', 'cocina', 'pedido,motivo')
def procesar(c, d, u):
    pedido(c, d['pedido'])
    exigir(d['motivo'] in ['error de comanda', 'error de preparación'], 'Motivo inválido')
    id = str(uuid.uuid4())
    c.execute('INSERT INTO rehechos VALUES(?,?,?,?)', (id, d['pedido'], d['motivo'], ahora()))
    return {'id': id}
