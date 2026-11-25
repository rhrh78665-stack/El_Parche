from nucleo import *

@accion('cobrar_pedido', 'cajera', 'pedido,pagos:json')
def procesar(c, d, u):
    p = pedido(c, d['pedido'])
    exigir(not p['pagado'] and p['estado'] != 'cancelado', 'Pedido cobrado o cancelado')
    caja = c.execute('SELECT id FROM cajas WHERE cajera=? AND cierre IS NULL', (u['id'],)).fetchone()
    exigir(caja, 'Abra la caja')
    pagos = d['pagos']
    exigir(isinstance(pagos, list) and 0 < len(pagos) <= 10, 'Pagos inválidos')
    exigir(sum((dinero(x['valor']) for x in pagos)) == p['total'], 'La suma debe coincidir con el total')
    for x in pagos:
        exigir(x['medio'] in config(c, 'medios', ['efectivo', 'datáfono', 'Nequi', 'Daviplata', 'transferencia', 'plataforma']), 'Medio inválido')
        exigir(dinero(x['valor']) > 0, 'Pago debe ser positivo')
        referencia = ACCIONES['validar_referencia']['fn'](c, x, u)
        c.execute('INSERT INTO pagos(id,pedido,caja,medio,valor,referencia,fecha) VALUES(?,?,?,?,?,?,?)', (str(uuid.uuid4()), p['id'], caja['id'], x['medio'], dinero(x['valor']), referencia, ahora()))
    c.execute('UPDATE pedidos SET pagado=1 WHERE id=?', (p['id'],))
    return {'ok': True}
