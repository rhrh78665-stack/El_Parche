from nucleo import *

@accion('cancelar_pedido', 'cajera,administrador', 'pedido,motivo')
def procesar(c, d, u):
    p = pedido(c, d['pedido'])
    exigir(p['estado'] not in ['entregado', 'cancelado'], 'Estado inválido')
    exigir(not p['pagado'] or u['rol'] == 'administrador', 'Solo administrador anula pedidos cobrados')
    exigir(d['motivo'] in ['cliente desistió', 'demora', 'falta de insumo', 'error de registro'], 'Motivo inválido')
    c.execute("UPDATE pedidos SET estado='cancelado',motivo=? WHERE id=?", (d['motivo'], p['id']))
    if p['pagado']:
        c.execute('UPDATE pagos SET anulado=1 WHERE pedido=?', (p['id'],))
    auditar(c, u, 'anulacion' if p['pagado'] else 'cancelacion', p['id'], d)
    return {'ok': True, 'advertencia': 'Registrar devolución física por el procedimiento del negocio si hubo cobro; no se repone inventario consumido.'}
