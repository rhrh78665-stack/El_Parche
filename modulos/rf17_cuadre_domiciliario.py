from nucleo import *

@accion('cuadre_domiciliario', 'cajera,domiciliario', 'domiciliario,desde,hasta')
def procesar(c, d, u):
    id = d['domiciliario']
    exigir(u['rol'] == 'cajera' or id == u['id'], 'Solo sus pedidos')
    return [dict(r) for r in c.execute("SELECT p.id,p.total,p.estado,p.pagado,CASE WHEN p.pagado=0 THEN p.total ELSE 0 END AS pendiente_cobrar,COALESCE(SUM(CASE WHEN pa.medio='efectivo' AND pa.anulado=0 THEN pa.valor ELSE 0 END),0) AS efectivo_registrado FROM pedidos p LEFT JOIN pagos pa ON pa.pedido=p.id WHERE p.domiciliario=? AND p.contraentrega=1 AND p.salida>=? AND p.salida<=? GROUP BY p.id", (id, d['desde'], d['hasta']))]
