import uuid
import secrets
from nucleo import conectar, clave, ahora, exigir, texto, config, auditar
SCHEMA = "\nCREATE TABLE IF NOT EXISTS estados_pedido(id INTEGER PRIMARY KEY,pedido TEXT NOT NULL REFERENCES pedidos_simulados(id),estado TEXT NOT NULL,fecha TEXT NOT NULL,detalle TEXT NOT NULL DEFAULT '');\nCREATE TABLE IF NOT EXISTS quejas_portal(id TEXT PRIMARY KEY,pedido TEXT NOT NULL REFERENCES pedidos_simulados(id),cliente TEXT NOT NULL REFERENCES usuarios(id),restaurante TEXT NOT NULL REFERENCES restaurantes(id),asunto TEXT NOT NULL,estado TEXT NOT NULL,creada TEXT NOT NULL,actualizada TEXT NOT NULL);\nCREATE TABLE IF NOT EXISTS mensajes_queja(id INTEGER PRIMARY KEY,queja TEXT NOT NULL REFERENCES quejas_portal(id),usuario TEXT NOT NULL REFERENCES usuarios(id),rol TEXT NOT NULL,mensaje TEXT NOT NULL,fecha TEXT NOT NULL);\nCREATE INDEX IF NOT EXISTS quejas_por_cliente ON quejas_portal(cliente);\nCREATE INDEX IF NOT EXISTS quejas_por_restaurante ON quejas_portal(restaurante);\n"

def preparar_accesos():
    from identidad import alcance
    with conectar() as c:
        c.execute('BEGIN IMMEDIATE')
        if config(c, 'dos_roles_v1', False):
            return
        for id, nombre, rol, pin in [('restaurante', 'Mariana Cortés', 'restaurante', '48261937'), ('cliente', 'Valentina Rojas', 'cliente', '73619482')]:
            anterior = c.execute('SELECT rol FROM usuarios WHERE id=?', (id,)).fetchone()
            exigir(not anterior, 'Ya existe la cuenta ' + id + '. No se cambió su PIN ni el resto de cuentas.')
            sal = secrets.token_hex(16)
            c.execute('INSERT INTO usuarios VALUES(?,?,?,?,?,1)', (id, nombre, rol, sal, clave(pin, sal)))
        c.execute('INSERT INTO accesos_restaurante VALUES(?,?)', ('restaurante', 'res_01'))
        c.execute('INSERT INTO perfiles_cliente VALUES(?,?,?,?,?)', ('cliente', '3005550148', 'Carrera 27 # 5-42', 'San Fernando', ahora()))
        pedidos = c.execute("SELECT id FROM pedidos_simulados WHERE restaurante='res_01' ORDER BY fecha DESC LIMIT 8").fetchall()
        for p in pedidos:
            c.execute("UPDATE pedidos_simulados SET usuario_cliente='cliente',cliente='Valentina Rojas',direccion='Carrera 27 # 5-42',barrio='San Fernando',celular='3005550148' WHERE id=?", (p['id'],))
        import portal
        for i, destino in enumerate(['recibido', 'en preparación', 'listo', 'en ruta']):
            pedido = portal.crear_pedido(c, {'restaurante': 'res_01', 'lineas': [{'producto': 'res_01_p0' + str(i + 1), 'cantidad': 1 + i % 2}], 'direccion': 'Carrera 27 # 5-42', 'barrio': 'San Fernando', 'celular': '3005550148', 'consentimiento': True, 'observacion': ['Sin cebolla', 'Salsa aparte', 'Bien cocido', 'Tocar el timbre'][i]}, {'id': 'cliente', 'rol': 'cliente'})
            for estado in ['en preparación', 'listo', 'en ruta']:
                if destino == 'recibido':
                    break
                portal.cambiar_estado(c, {'pedido': pedido['id'], 'estado': estado}, {'id': 'restaurante', 'rol': 'restaurante'})
                if estado == destino:
                    break
        c.execute("INSERT INTO estados_pedido(pedido,estado,fecha,detalle) SELECT p.id,p.estado,p.actualizado,'Estado registrado' FROM pedidos_simulados p WHERE NOT EXISTS(SELECT 1 FROM estados_pedido e WHERE e.pedido=p.id)")
        terminado = c.execute("SELECT id FROM pedidos_simulados WHERE usuario_cliente='cliente' AND estado='entregado' LIMIT 1").fetchone()
        if terminado:
            q = str(uuid.uuid4())
            fecha = ahora()
            c.execute('INSERT INTO quejas_portal VALUES(?,?,?,?,?,?,?,?)', (q, terminado['id'], 'cliente', 'res_01', 'Faltó una salsa del pedido', 'en atención', fecha, fecha))
            c.execute('INSERT INTO mensajes_queja(queja,usuario,rol,mensaje,fecha) VALUES(?,?,?,?,?)', (q, 'cliente', 'cliente', 'El pedido llegó bien, pero faltó la salsa de ajo. ¿Me pueden ayudar?', fecha))
            c.execute('INSERT INTO mensajes_queja(queja,usuario,rol,mensaje,fecha) VALUES(?,?,?,?,?)', (q, 'restaurante', 'restaurante', 'Gracias por avisarnos, Valentina. Estamos revisando el empaque para darte una solución.', fecha))
        c.execute("INSERT INTO configuracion VALUES('dos_roles_v1','true')")
    return True

def ver_pedido(c, d, u):
    import portal
    p = portal.serializar_pedido(c, u, portal.comprobar_pedido(c, u, d['pedido']))
    p['historial_estados'] = [dict(r) for r in c.execute('SELECT estado,fecha,detalle FROM estados_pedido WHERE pedido=? ORDER BY id', (p['id'],))]
    return p

def listado(c, d, u):
    from identidad import alcance
    where = 'q.cliente=?' if u['rol'] == 'cliente' else 'q.restaurante=?'
    arg = u['id'] if u['rol'] == 'cliente' else alcance(c, u)
    rows = [dict(r) for r in c.execute('SELECT q.*,r.nombre AS restaurante_nombre,p.estado AS pedido_estado FROM quejas_portal q JOIN restaurantes r ON r.id=q.restaurante JOIN pedidos_simulados p ON p.id=q.pedido WHERE ' + where + ' ORDER BY q.actualizada DESC', (arg,))]
    for q in rows:
        q['mensajes'] = [dict(r) for r in c.execute('SELECT rol,mensaje,fecha FROM mensajes_queja WHERE queja=? ORDER BY id', (q['id'],))]
    return rows

def crear(c, d, u):
    import portal
    p = portal.comprobar_pedido(c, u, d['pedido'])
    asunto = texto(d.get('asunto', ''), 120)
    mensaje = texto(d.get('mensaje', ''), 2000)
    exigir(asunto and mensaje, 'Escribe el asunto y el detalle')
    exigir(not c.execute("SELECT 1 FROM quejas_portal WHERE pedido=? AND estado!='resuelta'", (p['id'],)).fetchone(), 'Este pedido ya tiene una solicitud abierta. Continúa en esa conversación.')
    id = str(uuid.uuid4())
    fecha = ahora()
    c.execute('INSERT INTO quejas_portal VALUES(?,?,?,?,?,?,?,?)', (id, p['id'], u['id'], p['restaurante'], asunto, 'abierta', fecha, fecha))
    c.execute('INSERT INTO mensajes_queja(queja,usuario,rol,mensaje,fecha) VALUES(?,?,?,?,?)', (id, u['id'], u['rol'], mensaje, fecha))
    auditar(c, u, 'queja_creada', id, {'pedido': p['id']})
    return {'id': id}

def responder(c, d, u):
    propias = {q['id']: q for q in listado(c, {}, u)}
    q = propias.get(d.get('queja'))
    exigir(q, 'Solicitud no disponible')
    estado = d.get('estado', q['estado'])
    if u['rol'] == 'cliente':
        exigir(estado == q['estado'], 'Solo el restaurante puede cambiar el estado de atención')
    exigir(estado in ['abierta', 'en atención', 'resuelta'], 'Estado inválido')
    mensaje = texto(d.get('mensaje', ''), 2000)
    exigir(mensaje, 'Escribe tu respuesta')
    c.execute('INSERT INTO mensajes_queja(queja,usuario,rol,mensaje,fecha) VALUES(?,?,?,?,?)', (q['id'], u['id'], u['rol'], mensaje, ahora()))
    c.execute('UPDATE quejas_portal SET estado=?,actualizada=? WHERE id=?', (estado, ahora(), q['id']))
    auditar(c, u, 'queja_respondida', q['id'], {'estado': estado})
    return {'ok': True}
