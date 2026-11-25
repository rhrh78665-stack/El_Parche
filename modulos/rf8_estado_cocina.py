from nucleo import *

@accion('estado_cocina', 'cocina', 'pedido,estado')
def procesar(c, d, u):
    p = pedido(c, d['pedido'])
    destino = d['estado']
    exigir((p['estado'], destino) in [('recibido', 'en preparación'), ('en preparación', 'listo')], 'Transición inválida')
    if destino == 'en preparación':
        ACCIONES['consumir_receta']['fn'](c, {'pedido': p['id']}, u)
    c.execute('UPDATE pedidos SET estado=? WHERE id=?', (destino, p['id']))
    return {'ok': True}
