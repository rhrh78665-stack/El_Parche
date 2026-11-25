import json
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from nucleo import exigir, texto, numero, dinero, clave, ahora, auditar
from identidad import alcance, perfil, restaurante_permitido, ROLES
import simulacion

def reservar(c, pedido):
    if c.execute('SELECT 1 FROM reservas_restaurante WHERE pedido=?', (pedido,)).fetchone():
        return
    cantidades = c.execute('SELECT r.insumo,SUM(r.cantidad*l.cantidad) AS cantidad FROM lineas_simuladas l JOIN recetas_restaurante r ON r.producto=l.producto WHERE l.pedido=? GROUP BY r.insumo', (pedido,)).fetchall()
    for linea in c.execute('SELECT producto FROM lineas_simuladas WHERE pedido=?', (pedido,)).fetchall():
        exigir(c.execute('SELECT 1 FROM recetas_restaurante WHERE producto=?', (linea['producto'],)).fetchone(), 'El producto necesita una receta antes de venderse')
    for x in cantidades:
        stock = c.execute('SELECT stock FROM insumos_restaurante WHERE id=?', (x['insumo'],)).fetchone()[0]
        reservado = c.execute('SELECT COALESCE(SUM(cantidad),0) FROM reservas_restaurante WHERE insumo=?', (x['insumo'],)).fetchone()[0]
        exigir(stock - reservado >= x['cantidad'], 'No hay ingredientes suficientes para completar este pedido')
        c.execute('INSERT INTO reservas_restaurante VALUES(?,?,?)', (pedido, x['insumo'], x['cantidad']))

def comprobar_pedido(c, u, id):
    p = c.execute('SELECT p.*,r.nombre AS restaurante_nombre,r.foto AS restaurante_foto FROM pedidos_simulados p JOIN restaurantes r ON r.id=p.restaurante WHERE p.id=?', (id,)).fetchone()
    exigir(p, 'Pedido no disponible')
    if u['rol'] in ['restaurante', 'cocina']:
        exigir(p['restaurante'] == alcance(c, u), 'Pedido no disponible')
    elif u['rol'] == 'cliente':
        exigir(p['usuario_cliente'] == u['id'], 'Pedido no disponible')
    elif u['rol'] == 'domiciliario':
        exigir(p['domiciliario_usuario'] == u['id'], 'Pedido no disponible')
    else:
        exigir(u['rol'] == 'administrador', 'Acceso denegado')
    return dict(p)

def serializar_pedido(c, u, p):
    p = dict(p)
    p.pop('origen', None)
    p['lineas'] = [dict(x) for x in c.execute('SELECT producto,nombre,cantidad,precio FROM lineas_simuladas WHERE pedido=? ORDER BY id', (p['id'],))]
    if u['rol'] == 'cocina':
        for key in ['direccion', 'celular', 'total', 'envio', 'pago_estado', 'medio_pago', 'usuario_cliente', 'domiciliario_usuario']:
            p.pop(key, None)
        for l in p['lineas']:
            l.pop('precio', None)
    return p

def pedidos(c, d, u):
    where = []
    params = []
    if u['rol'] in ['restaurante', 'cocina']:
        id = alcance(c, u)
        exigir(not d.get('restaurante') or d['restaurante'] == id, 'Acceso denegado a este restaurante')
        where.append('p.restaurante=?')
        params.append(id)
    elif u['rol'] == 'cliente':
        where.append('p.usuario_cliente=?')
        params.append(u['id'])
    elif u['rol'] == 'domiciliario':
        where.append("p.domiciliario_usuario=? AND p.estado IN ('en ruta','entregado')")
        params.append(u['id'])
    else:
        exigir(u['rol'] == 'administrador', 'Acceso denegado')
    if d.get('restaurante'):
        where.append('p.restaurante=?')
        params.append(d['restaurante'])
    if d.get('estado'):
        exigir(d['estado'] in simulacion.TRANSICIONES, 'Estado inválido')
        where.append('p.estado=?')
        params.append(d['estado'])
    sql = 'SELECT p.*,r.nombre AS restaurante_nombre,r.foto AS restaurante_foto FROM pedidos_simulados p JOIN restaurantes r ON r.id=p.restaurante'
    if where:
        sql += ' WHERE ' + ' AND '.join(where)
    sql += ' ORDER BY p.fecha DESC LIMIT 500'
    return [serializar_pedido(c, u, p) for p in c.execute(sql, params).fetchall()]

def menu(c, d, u):
    id = restaurante_permitido(c, u, d.get('restaurante'))
    datos = simulacion.detalle(c, {'restaurante': id})
    resultado = []
    for p in datos['menu']:
        faltante = c.execute('SELECT 1 FROM recetas_restaurante r JOIN insumos_restaurante i ON i.id=r.insumo WHERE r.producto=? AND i.stock-COALESCE((SELECT SUM(cantidad) FROM reservas_restaurante WHERE insumo=i.id),0)<r.cantidad LIMIT 1', (p['id'],)).fetchone()
        receta = c.execute('SELECT 1 FROM recetas_restaurante WHERE producto=?', (p['id'],)).fetchone()
        p['disponible'] = bool(p['activo'] and p['stock'] > 0 and (not faltante) and receta)
        if u['rol'] == 'cliente':
            if not p['activo']:
                continue
            p.pop('stock', None)
        resultado.append(p)
    return {'restaurante': datos['restaurante'], 'menu': resultado}

def crear_pedido(c, d, u):
    if u['rol'] == 'cliente':
        exigir(not d.get('usuario_cliente') or d['usuario_cliente'] == u['id'], 'No puedes pedir en nombre de otra cuenta')
        p = perfil(c, u)
        nombre = p['usuario']['nombre']
        direccion = texto(d.get('direccion') or p['cliente'].get('direccion', ''), 200)
        barrio = texto(d.get('barrio') or p['cliente'].get('barrio', ''), 100)
        celular = texto(d.get('celular') or p['cliente'].get('celular', ''), 20)
        exigir(d.get('consentimiento') is True, 'Confirma el uso de tus datos para gestionar el pedido')
        cliente = u['id']
        restaurante = restaurante_permitido(c, u, d.get('restaurante'))
    else:
        exigir(u['rol'] == 'restaurante', 'Acceso denegado')
        restaurante = alcance(c, u)
        exigir(not d.get('restaurante') or d['restaurante'] == restaurante, 'Acceso denegado a este restaurante')
        nombre = texto(d['cliente'], 100)
        direccion = texto(d['direccion'], 200)
        barrio = texto(d['barrio'], 100)
        celular = texto(d['celular'], 20)
        cliente = None
    exigir(celular.isdigit() and 10 <= len(celular) <= 13, 'Revisa el número de celular')
    for l in d['lineas']:
        p = c.execute('SELECT activo FROM menus_restaurantes WHERE id=? AND restaurante=?', (l['producto'], restaurante)).fetchone()
        exigir(p and p['activo'], 'Producto no disponible en este restaurante')
    payload = {**d, 'restaurante': restaurante, 'cliente': nombre, 'barrio': barrio}
    resultado = simulacion.crear_pedido(c, payload)
    c.execute('UPDATE pedidos_simulados SET usuario_cliente=?,direccion=?,celular=?,origen=?,pago_estado=?,medio_pago=? WHERE id=?', (cliente, direccion, celular, 'cliente' if cliente else 'restaurante', 'pendiente', 'contraentrega', resultado['id']))
    reservar(c, resultado['id'])
    c.execute('INSERT INTO estados_pedido(pedido,estado,fecha,detalle) VALUES(?,?,?,?)', (resultado['id'], 'recibido', ahora(), 'Pedido recibido por el restaurante'))
    auditar(c, u, 'pedido_creado', resultado['id'], {'restaurante': restaurante, 'total': resultado['total']})
    return {'id': resultado['id'], 'total': resultado['total'], 'estado': 'recibido'}

def cambiar_estado(c, d, u):
    p = comprobar_pedido(c, u, d['pedido'])
    destino = d['estado']
    rol = u['rol']
    exigir(rol != 'administrador', 'Administración supervisa pedidos; su gestión corresponde al restaurante')
    if rol == 'cocina':
        exigir((p['estado'], destino) in [('recibido', 'en preparación'), ('en preparación', 'listo')], 'Cocina solo puede iniciar o terminar la preparación')
    elif rol == 'cliente':
        exigir(p['estado'] == 'recibido' and destino == 'cancelado', 'Solo puedes cancelar un pedido que aún no entró a cocina')
    elif rol == 'domiciliario':
        exigir(p['estado'] == 'en ruta' and destino == 'entregado', 'Solo puedes confirmar una entrega asignada')
        exigir(dinero(d.get('valor_cobrado', -1)) == p['total'], 'El recaudo debe coincidir con el total del pedido')
    elif rol == 'restaurante':
        exigir(destino in ['en preparación', 'listo', 'en ruta', 'entregado', 'cancelado'], 'Estado inválido')
    else:
        raise ValueError('Acceso denegado')
    exigir(destino in simulacion.TRANSICIONES.get(p['estado'], []), 'Este pedido ya cambió de estado. Actualiza la pantalla.')
    if destino == 'cancelado':
        exigir(p['estado'] in ['recibido', 'en preparación'], 'No se puede cancelar un pedido despachado')
    if destino == 'en preparación':
        reservar(c, p['id'])
        for reserva in c.execute('SELECT * FROM reservas_restaurante WHERE pedido=?', (p['id'],)).fetchall():
            exigir(c.execute('UPDATE insumos_restaurante SET stock=stock-? WHERE id=? AND stock>=?', (reserva['cantidad'], reserva['insumo'], reserva['cantidad'])).rowcount, 'No hay ingredientes suficientes')
            c.execute('INSERT INTO movimientos_restaurante(restaurante,insumo,cantidad,tipo,motivo,usuario,fecha) VALUES(?,?,?,?,?,?,?)', (p['restaurante'], reserva['insumo'], -reserva['cantidad'], 'preparación', p['id'], u['id'], ahora()))
        c.execute('DELETE FROM reservas_restaurante WHERE pedido=?', (p['id'],))
    if destino == 'cancelado':
        exigir(texto(d.get('motivo', ''), 150), 'Registra el motivo')
        if p['estado'] == 'recibido':
            for l in c.execute('SELECT producto,cantidad FROM lineas_simuladas WHERE pedido=?', (p['id'],)).fetchall():
                c.execute('UPDATE menus_restaurantes SET stock=stock+? WHERE id=?', (l['cantidad'], l['producto']))
        c.execute('DELETE FROM reservas_restaurante WHERE pedido=?', (p['id'],))
    courier_id = p['domiciliario_usuario']
    courier = p['domiciliario']
    if destino == 'en ruta':
        exigir(rol == 'restaurante', 'El despacho corresponde al restaurante')
        courier_id = None
        courier = ''
    if destino == 'entregado':
        exigir(rol == 'restaurante', 'La entrega la confirma el restaurante')
        exigir(dinero(d.get('valor_cobrado', -1)) == p['total'], 'El recaudo debe coincidir con el total del pedido')
    c.execute("UPDATE pedidos_simulados SET estado=?,actualizado=?,domiciliario_usuario=?,domiciliario=?,pago_estado=CASE WHEN ?='entregado' THEN 'cobrado' ELSE pago_estado END WHERE id=?", (destino, ahora(), courier_id, courier, destino, p['id']))
    c.execute('INSERT INTO estados_pedido(pedido,estado,fecha,detalle) VALUES(?,?,?,?)', (p['id'], destino, ahora(), d.get('motivo', '')))
    auditar(c, u, 'pedido_estado', p['id'], {'estado': destino, 'restaurante': p['restaurante'], 'motivo': d.get('motivo', '')})
    return {'id': p['id'], 'estado': destino}

def inventario(c, u):
    id = alcance(c, u)
    return [dict(r) for r in c.execute('SELECT i.*,COALESCE(SUM(r.cantidad),0) AS reservado,i.stock-COALESCE(SUM(r.cantidad),0) AS disponible FROM insumos_restaurante i LEFT JOIN reservas_restaurante r ON r.insumo=i.id WHERE i.restaurante=? GROUP BY i.id ORDER BY i.nombre', (id,))]

def ajustar(c, d, u):
    id = alcance(c, u)
    r = c.execute('SELECT * FROM insumos_restaurante WHERE id=? AND restaurante=?', (d['insumo'], id)).fetchone()
    exigir(r, 'Insumo no disponible')
    conteo = numero(d['conteo'])
    motivo = texto(d['motivo'], 150)
    reserva = c.execute('SELECT COALESCE(SUM(cantidad),0) FROM reservas_restaurante WHERE insumo=?', (r['id'],)).fetchone()[0]
    exigir(conteo >= reserva, 'La cantidad no puede ser menor a lo reservado por pedidos activos')
    delta = conteo - r['stock']
    c.execute('UPDATE insumos_restaurante SET stock=? WHERE id=?', (conteo, r['id']))
    c.execute('INSERT INTO movimientos_restaurante(restaurante,insumo,cantidad,tipo,motivo,usuario,fecha) VALUES(?,?,?,?,?,?,?)', (id, r['id'], delta, 'conteo', motivo, u['id'], ahora()))
    auditar(c, u, 'conteo_stock', r['id'], {'cantidad': conteo, 'motivo': motivo})
    return {'ok': True}

def compra(c, d, u):
    id = alcance(c, u)
    proveedor = texto(d['proveedor'], 100)
    lineas = d['lineas']
    exigir(isinstance(lineas, list) and 0 < len(lineas) <= 30, 'Agrega al menos un insumo')
    costo = 0
    compra_id = str(uuid.uuid4())
    for l in lineas:
        cantidad = numero(l['cantidad'], 0.001)
        costo += dinero(l['costo'])
        exigir(c.execute('UPDATE insumos_restaurante SET stock=stock+? WHERE id=? AND restaurante=?', (cantidad, l['insumo'], id)).rowcount, 'Insumo no disponible')
        c.execute('INSERT INTO movimientos_restaurante(restaurante,insumo,cantidad,tipo,motivo,usuario,fecha) VALUES(?,?,?,?,?,?,?)', (id, l['insumo'], cantidad, 'compra', compra_id, u['id'], ahora()))
    c.execute('INSERT INTO compras_restaurante VALUES(?,?,?,?,?,?)', (compra_id, id, proveedor, ahora(), costo, u['id']))
    auditar(c, u, 'compra_restaurante', compra_id, {'costo': costo, 'restaurante': id})
    return {'id': compra_id, 'costo': costo}

def guardar_producto(c, d, u):
    id = alcance(c, u)
    pid = d.get('id') or id + '_p_' + uuid.uuid4().hex[:8]
    anterior = c.execute('SELECT restaurante FROM menus_restaurantes WHERE id=?', (pid,)).fetchone()
    exigir(not anterior or anterior['restaurante'] == id, 'Producto no disponible')
    stock = numero(d['stock'])
    exigir(stock.is_integer() and stock <= 10000, 'Revisa las porciones disponibles')
    activo = d.get('activo', False)
    exigir(type(activo) is bool, 'Estado inválido')
    if activo:
        exigir(c.execute('SELECT 1 FROM recetas_restaurante WHERE producto=?', (pid,)).fetchone(), 'Configura la receta antes de publicar el producto')
    r = c.execute('SELECT * FROM restaurantes WHERE id=?', (id,)).fetchone()
    foto = d.get('foto') or r['foto']
    exigir(isinstance(foto, str) and foto.startswith('/media/') and ('..' not in foto), 'Imagen inválida')
    c.execute('INSERT INTO menus_restaurantes(id,restaurante,nombre,descripcion,precio,foto,categoria,stock,destacado,alergenos,activo) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre,descripcion=excluded.descripcion,precio=excluded.precio,foto=excluded.foto,categoria=excluded.categoria,stock=excluded.stock,alergenos=excluded.alergenos,activo=excluded.activo', (pid, id, texto(d['nombre'], 100), texto(d['descripcion'], 300), dinero(d['precio']), foto, texto(d.get('categoria') or r['categoria'], 60), int(stock), 0, json.dumps(d.get('alergenos', [])), int(activo)))
    auditar(c, u, 'producto_actualizado', pid, {'restaurante': id, 'precio': d['precio'], 'activo': activo})
    return {'id': pid}

def receta(c, d, u):
    id = alcance(c, u)
    p = c.execute('SELECT * FROM menus_restaurantes WHERE id=? AND restaurante=?', (d['producto'], id)).fetchone()
    exigir(p, 'Producto no disponible')
    return {'producto': dict(p), 'insumos': inventario(c, u), 'receta': [dict(x) for x in c.execute('SELECT r.insumo,r.cantidad,i.nombre,i.unidad FROM recetas_restaurante r JOIN insumos_restaurante i ON i.id=r.insumo WHERE producto=?', (p['id'],))]}

def guardar_receta(c, d, u):
    datos = receta(c, d, u)
    id = alcance(c, u)
    lineas = d['lineas']
    exigir(isinstance(lineas, list) and 0 < len(lineas) <= 30, 'Incluye ingredientes')
    exigir(len({x['insumo'] for x in lineas}) == len(lineas), 'No repitas ingredientes')
    for l in lineas:
        exigir(c.execute('SELECT 1 FROM insumos_restaurante WHERE id=? AND restaurante=?', (l['insumo'], id)).fetchone(), 'Insumo no disponible')
        numero(l['cantidad'], 0.001)
    c.execute('DELETE FROM recetas_restaurante WHERE producto=?', (d['producto'],))
    c.executemany('INSERT INTO recetas_restaurante VALUES(?,?,?)', [(d['producto'], x['insumo'], numero(x['cantidad'], 0.001)) for x in lineas])
    auditar(c, u, 'receta_actualizada', d['producto'], {'restaurante': id})
    return {'ok': True}

def usuarios(c, u):
    if u['rol'] == 'administrador':
        return [dict(r) for r in c.execute('SELECT u.id,u.nombre,u.rol,u.activo,a.restaurante,r.nombre AS restaurante_nombre FROM usuarios u LEFT JOIN accesos_restaurante a ON a.usuario=u.id LEFT JOIN restaurantes r ON r.id=a.restaurante ORDER BY u.rol,u.nombre')]
    id = alcance(c, u)
    return [dict(r) for r in c.execute('SELECT u.id,u.nombre,u.rol,u.activo,a.restaurante FROM usuarios u JOIN accesos_restaurante a ON a.usuario=u.id WHERE a.restaurante=? ORDER BY u.nombre', (id,))]

def guardar_usuario(c, d, u):
    id = texto(d['id'], 50)
    exigir(re.fullmatch('[a-z0-9][a-z0-9._-]{2,49}', id), 'Usa entre 3 y 50 letras minúsculas, números, puntos o guiones')
    rol = d['rol']
    exigir(rol in ROLES, 'Rol inválido')
    activo = d['activo']
    exigir(type(activo) is bool, 'Estado inválido')
    restaurante = d.get('restaurante') or None
    anterior = c.execute('SELECT * FROM usuarios WHERE id=?', (id,)).fetchone()
    if u['rol'] == 'restaurante':
        propio = alcance(c, u)
        exigir(rol in ['restaurante', 'cocina'], 'No puedes asignar ese rol')
        exigir(not restaurante or restaurante == propio, 'No puedes asignar otro restaurante')
        restaurante = propio
        if anterior:
            exigir(anterior['rol'] in ['restaurante', 'cocina'] and alcance(c, {'id': id}) == propio, 'Cuenta no disponible')
    else:
        exigir(u['rol'] == 'administrador', 'Acceso denegado')
    if rol in ['restaurante', 'cocina']:
        exigir(restaurante and c.execute('SELECT 1 FROM restaurantes WHERE id=?', (restaurante,)).fetchone(), 'Asigna un restaurante')
    else:
        restaurante = None
    exigir(id != u['id'] or (activo and rol == u['rol']), 'No puedes quitar tu propio acceso')
    if anterior and anterior['rol'] == 'administrador' and (not activo or rol != 'administrador'):
        exigir(c.execute("SELECT COUNT(*) FROM usuarios WHERE rol='administrador' AND activo=1 AND id<>?", (id,)).fetchone()[0] > 0, 'Debe permanecer al menos una cuenta administradora activa')
    pin = d.get('pin', '')
    exigir(not pin and anterior or (isinstance(pin, str) and pin.isdigit() and (8 <= len(pin) <= 64)), 'El PIN debe tener de 8 a 64 dígitos')
    sal = secrets.token_hex(16) if pin else anterior['sal']
    hashpin = clave(pin, sal) if pin else anterior['pin']
    c.execute('INSERT INTO usuarios VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre,rol=excluded.rol,sal=excluded.sal,pin=excluded.pin,activo=excluded.activo', (id, texto(d['nombre'], 100), rol, sal, hashpin, int(activo)))
    c.execute('DELETE FROM accesos_restaurante WHERE usuario=?', (id,))
    if restaurante:
        c.execute('INSERT INTO accesos_restaurante VALUES(?,?)', (id, restaurante))
    if rol == 'cliente':
        c.execute("INSERT OR IGNORE INTO perfiles_cliente VALUES(?,'','','','')", (id,))
    c.execute('DELETE FROM sesiones WHERE usuario=?', (id,))
    auditar(c, u, 'cuenta_actualizada', id, {'rol': rol, 'restaurante': restaurante, 'activo': activo})
    return {'id': id}

def guardar_perfil(c, d, u):
    nombre = texto(d['nombre'], 100)
    celular = texto(d['celular'], 20)
    exigir(celular.isdigit() and 10 <= len(celular) <= 13, 'Revisa el celular')
    exigir(d.get('consentimiento') is True, 'Confirma la autorización de uso de tus datos')
    direccion = str(d.get('direccion', ''))
    barrio = str(d.get('barrio', ''))
    exigir(len(direccion) <= 200 and len(barrio) <= 100, 'Revisa la dirección')
    c.execute('UPDATE usuarios SET nombre=? WHERE id=?', (nombre, u['id']))
    c.execute('INSERT INTO perfiles_cliente VALUES(?,?,?,?,?) ON CONFLICT(usuario) DO UPDATE SET celular=excluded.celular,direccion=excluded.direccion,barrio=excluded.barrio,autorizacion=excluded.autorizacion', (u['id'], celular, direccion, barrio, ahora()))
    auditar(c, u, 'perfil_actualizado', u['id'], {'actualizado': True})
    return {'ok': True}

def resumen(c, u):
    if u['rol'] == 'administrador':
        r = simulacion.resumen(c, {})
        r.pop('modo', None)
        r['cuentas'] = c.execute('SELECT COUNT(*) FROM usuarios WHERE activo=1').fetchone()[0]
        return r
    id = alcance(c, u)
    hoy = (datetime.now(timezone.utc) - timedelta(hours=5)).date().isoformat()
    rows = pedidos(c, {}, u)
    ventas = c.execute("SELECT COALESCE(SUM(total-envio),0),COUNT(*) FROM pedidos_simulados WHERE restaurante=? AND estado='entregado' AND date(fecha,'-5 hours')=?", (id, hoy)).fetchone()
    alertas = c.execute('SELECT COUNT(*) FROM insumos_restaurante WHERE restaurante=? AND stock<=minimo', (id,)).fetchone()[0]
    return {'activos': sum((p['estado'] not in ['entregado', 'cancelado'] for p in rows)), 'listos': sum((p['estado'] == 'listo' for p in rows)), 'ventas_hoy': ventas[0], 'entregados_hoy': ventas[1], 'productos': c.execute('SELECT COUNT(*) FROM menus_restaurantes WHERE restaurante=? AND activo=1', (id,)).fetchone()[0], 'alertas': alertas, 'recientes': rows[:8]}

def reportes(c, d, u):
    filtros = []
    params = []
    if u['rol'] == 'restaurante':
        filtros.append('restaurante=?')
        params.append(alcance(c, u))
    else:
        exigir(u['rol'] == 'administrador', 'Acceso denegado')
    desde = texto(d.get('desde', '2000-01-01'), 30)
    hasta = texto(d.get('hasta', '2099-12-31'), 30)
    filtros.extend(["date(fecha,'-5 hours')>=?", "date(fecha,'-5 hours')<=?"])
    params.extend([desde, hasta])
    where = ' AND '.join(filtros)
    dias = [dict(r) for r in c.execute("SELECT date(fecha,'-5 hours') AS dia,COUNT(*) AS pedidos,SUM(CASE WHEN estado='entregado' THEN total-envio ELSE 0 END) AS ventas,SUM(CASE WHEN estado='cancelado' THEN 1 ELSE 0 END) AS cancelados FROM pedidos_simulados WHERE " + where + ' GROUP BY dia ORDER BY dia DESC', params)]
    return {'dias': dias, 'ventas': sum((r['ventas'] for r in dias)), 'pedidos': sum((r['pedidos'] for r in dias)), 'cancelados': sum((r['cancelados'] for r in dias))}
