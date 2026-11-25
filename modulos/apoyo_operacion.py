from nucleo import *

@accion('mis_domicilios', 'domiciliario', '')
def domicilios(c, d, u):
    salida = []
    for r in c.execute("SELECT * FROM pedidos WHERE domiciliario=? AND estado IN ('despachado','entregado') ORDER BY salida DESC", (u['id'],)):
        p = dict(r)
        cliente = c.execute('SELECT nombre,celular,direccion,barrio,referencia FROM clientes WHERE celular=?', (p['cliente'],)).fetchone()
        p['datos_cliente'] = dict(cliente) if cliente else None
        salida.append(p)
    return salida

@accion('entregar_local', 'cajera,mesero', 'pedido')
def local(c, d, u):
    p = pedido(c, d['pedido'])
    exigir(p['estado'] == 'listo' and p['canal'] in ['mesa', 'mostrador', 'Rappi', 'DiDi Food'], 'Estado o canal inválido')
    c.execute("UPDATE pedidos SET estado='entregado',entrega=? WHERE id=?", (ahora(), p['id']))
    return {'ok': True}

@accion('ver_auditoria', 'administrador', '')
def auditoria(c, d, u):
    return [dict(r) for r in c.execute('SELECT * FROM auditoria ORDER BY id DESC LIMIT 500')]

@accion('listar_usuarios', 'administrador,cajera', '')
def usuarios(c, d, u):
    return [dict(r) for r in c.execute('SELECT id,nombre,rol,activo FROM usuarios')]

@accion('pedidos_operables', 'administrador,cajera,mesero,cocina,domiciliario', '')
def pedidos_operables(c, d, u):
    if u['rol'] == 'domiciliario':
        return [dict(r) for r in c.execute("SELECT * FROM pedidos WHERE domiciliario=? AND estado='despachado' ORDER BY fecha DESC", (u['id'],))]
    return [dict(r) for r in c.execute("SELECT * FROM pedidos WHERE estado NOT IN ('cancelado','entregado') ORDER BY fecha DESC")]

@accion('detalle_pedido', 'administrador,cajera,mesero,cocina,domiciliario', 'pedido')
def detalle(c, d, u):
    p = pedido(c, d['pedido'])
    exigir(u['rol'] != 'domiciliario' or p['domiciliario'] == u['id'], 'Pedido no asignado')
    return {'pedido': p, 'lineas': [dict(r) for r in c.execute('SELECT * FROM lineas WHERE pedido=?', (p['id'],))]}

@accion('lineas_operables', 'cajera,mesero', '')
def lineas(c, d, u):
    return [dict(r) for r in c.execute("SELECT l.* FROM lineas l JOIN pedidos p ON p.id=l.pedido WHERE p.estado='recibido' ORDER BY l.id DESC")]

@accion('modificadores_producto', 'administrador,cajera,mesero', 'producto')
def modificadores(c, d, u):
    r = c.execute('SELECT modificadores FROM productos WHERE id=?', (d['producto'],)).fetchone()
    exigir(r, 'Producto no encontrado')
    return {'opciones': json.loads(r['modificadores'])}

@accion('estado_caja', 'cajera', '')
def estado_caja(c, d, u):
    r = c.execute('SELECT * FROM cajas WHERE cajera=? AND cierre IS NULL', (u['id'],)).fetchone()
    if not r:
        return {'caja': None}
    pagos = [dict(x) for x in c.execute('SELECT * FROM pagos WHERE caja=? AND anulado=0 ORDER BY fecha DESC', (r['id'],))]
    return {'caja': dict(r), 'pagos': pagos, 'efectivo': sum((x['valor'] for x in pagos if x['medio'] == 'efectivo'))}

@accion('guardar_cliente_visual', 'cajera', 'celular,nombre,direccion,barrio,referencia,autorizacion_medio')
def cliente(c, d, u):
    celular = texto(d['celular'], 20)
    exigir(celular.isdigit(), 'Celular inválido')
    medio = texto(d['autorizacion_medio'], 100)
    c.execute('INSERT INTO clientes VALUES(?,?,?,?,?,?,?) ON CONFLICT(celular) DO UPDATE SET nombre=excluded.nombre,direccion=excluded.direccion,barrio=excluded.barrio,referencia=excluded.referencia,autorizacion_fecha=excluded.autorizacion_fecha,autorizacion_medio=excluded.autorizacion_medio', (celular, texto(d['nombre']), texto(d['direccion']), texto(d['barrio']), texto(d['referencia']), ahora(), medio))
    return {'ok': True}
