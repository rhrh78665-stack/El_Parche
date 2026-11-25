from nucleo import *

@accion('pedidos_demorados', 'cajera,administrador', '')
def procesar(c, d, u):
    minutos = config(c, 'demora', 5)
    return [dict(r) for r in c.execute("SELECT * FROM pedidos WHERE estado='recibido' AND (julianday('now')-julianday(fecha))*1440>?", (minutos,))]
