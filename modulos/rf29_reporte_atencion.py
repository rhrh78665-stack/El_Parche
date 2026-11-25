from nucleo import *

@accion('reporte_atencion', 'administrador', 'desde,hasta')
def procesar(c, d, u):
    return {'cancelados': [dict(r) for r in c.execute("SELECT motivo,COUNT(*) AS cantidad FROM pedidos WHERE estado='cancelado' AND fecha>=? AND fecha<=? GROUP BY motivo", (d['desde'], d['hasta']))], 'tiempos': [dict(r) for r in c.execute('SELECT canal,AVG((julianday(entrega)-julianday(fecha))*1440) AS minutos FROM pedidos WHERE entrega IS NOT NULL AND fecha>=? AND fecha<=? GROUP BY canal', (d['desde'], d['hasta']))]}
