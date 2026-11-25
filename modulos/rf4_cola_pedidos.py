from nucleo import *

@accion('cola_pedidos', 'cajera,administrador', '')
def procesar(c, d, u):
    return [dict(r) for r in c.execute("SELECT *,CAST((julianday('now')-julianday(fecha))*86400 AS INTEGER) AS segundos FROM pedidos WHERE estado NOT IN ('entregado','cancelado') ORDER BY fecha")]
