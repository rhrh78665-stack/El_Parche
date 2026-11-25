from nucleo import *

@accion('historial_cajas', 'administrador', 'desde,hasta,cajera')
def procesar(c, d, u):
    return [dict(r) for r in c.execute("SELECT * FROM cajas WHERE cierre IS NOT NULL AND apertura>=? AND apertura<=? AND (?='' OR cajera=?) ORDER BY apertura DESC", (d['desde'], d['hasta'], d.get('cajera', ''), d.get('cajera', '')))]
