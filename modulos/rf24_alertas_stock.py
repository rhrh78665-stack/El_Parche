from nucleo import *

@accion('alertas_stock', 'administrador,cajera', '')
def procesar(c, d, u):
    return [dict(r) for r in c.execute('SELECT * FROM insumos WHERE stock<=minimo')]
