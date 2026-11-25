from nucleo import *

@accion('pedido_mesa', 'mesero', 'mesa,lineas:json')
def procesar(c, d, u):
    d['canal'] = 'mesa'
    return ACCIONES['registrar_pedido']['fn'](c, d, u)
