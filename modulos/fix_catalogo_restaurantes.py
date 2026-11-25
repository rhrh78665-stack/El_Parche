from nucleo import accion, CONSULTAS, exigir, auditar
import simulacion

@accion('listar_restaurantes', 'administrador', '')
def listar(c, d, u):
    return simulacion.listar(c, d)

@accion('detalle_restaurante', 'administrador', 'restaurante')
def detalle(c, d, u):
    return simulacion.detalle(c, d)

@accion('resumen_restaurantes', 'administrador', '')
def resumen(c, d, u):
    return simulacion.resumen(c, d)

@accion('simular_pedido_restaurante', 'administrador', 'restaurante,cliente,barrio,lineas')
def crear(c, d, u):
    resultado = simulacion.crear_pedido(c, d)
    auditar(c, u, 'pedido_simulado', resultado['id'], {'restaurante': d['restaurante'], 'total': resultado['total']})
    return resultado

@accion('estado_pedido_simulado', 'administrador', 'pedido,estado')
def estado(c, d, u):
    resultado = simulacion.estado_pedido(c, d)
    auditar(c, u, 'estado_simulado', resultado['id'], {'estado': resultado['estado']})
    return resultado

@accion('estado_restaurante_simulado', 'administrador', 'restaurante,estado')
def estado_restaurante(c, d, u):
    exigir(d['estado'] in ['abierto', 'pausado'], 'Estado inválido')
    exigir(c.execute('UPDATE restaurantes SET estado=? WHERE id=?', (d['estado'], d['restaurante'])).rowcount, 'Restaurante inexistente')
    auditar(c, u, 'cocina_simulada', d['restaurante'], {'estado': d['estado']})
    return {'ok': True}
CONSULTAS.update(['listar_restaurantes', 'detalle_restaurante', 'resumen_restaurantes'])

@accion('listar_pedidos_restaurantes', 'administrador', '')
def pedidos(c, d, u):
    restaurante = str(d.get('restaurante', ''))
    estado = str(d.get('estado', ''))
    exigir(not estado or estado in simulacion.TRANSICIONES, 'Estado inválido')
    return [dict(r) for r in c.execute("SELECT p.*,r.nombre AS restaurante_nombre,r.foto AS restaurante_foto,r.categoria FROM pedidos_simulados p JOIN restaurantes r ON r.id=p.restaurante WHERE (?='' OR p.restaurante=?) AND (?='' OR p.estado=?) ORDER BY p.fecha DESC LIMIT 300", (restaurante, restaurante, estado, estado))]
CONSULTAS.add('listar_pedidos_restaurantes')
