from nucleo import *

@accion('entregar_pedido', 'domiciliario', 'pedido')
def procesar(c, d, u):
    p = pedido(c, d['pedido'])
    exigir(p['domiciliario'] == u['id'] and p['estado'] == 'despachado', 'Pedido no asignado o no despachado')
    c.execute("UPDATE pedidos SET estado='entregado',entrega=? WHERE id=?", (ahora(), p['id']))
    return {'ok': True}
