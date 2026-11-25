from nucleo import *

@accion('integridad_auditoria', 'administrador', '')
def procesar(c, d, u):
    return verificar_auditoria(c)
CONSULTAS.add('integridad_auditoria')
