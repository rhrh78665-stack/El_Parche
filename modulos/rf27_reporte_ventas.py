from nucleo import *

@accion('reporte_ventas', 'administrador', 'desde,hasta')
def procesar(c, d, u):
    return {'cobros': [dict(r) for r in c.execute('SELECT substr(pa.fecha,1,10) AS dia,p.canal,pa.medio,SUM(pa.valor) AS total FROM pagos pa JOIN pedidos p ON p.id=pa.pedido WHERE pa.anulado=0 AND pa.fecha>=? AND pa.fecha<=? GROUP BY dia,p.canal,pa.medio', (d['desde'], d['hasta']))], 'productos': [dict(r) for r in c.execute("SELECT l.nombre,SUM(l.cantidad) AS cantidad,SUM(l.cantidad*l.precio) AS total FROM lineas l JOIN pedidos p ON p.id=l.pedido WHERE p.pagado=1 AND p.estado!='cancelado' AND p.fecha>=? AND p.fecha<=? GROUP BY l.producto,l.nombre", (d['desde'], d['hasta']))]}
