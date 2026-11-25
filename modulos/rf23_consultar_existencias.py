from nucleo import *

@accion('consultar_existencias', 'administrador,cocina', '')
def procesar(c, d, u):
    return [dict(r) for r in c.execute('SELECT *,stock<=minimo AS alerta FROM insumos ORDER BY nombre')]
