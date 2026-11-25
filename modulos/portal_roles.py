from nucleo import accion, CONSULTAS, exigir, auditar, config, texto, numero
from identidad import perfil, alcance
import portal
import simulacion
LECTURAS = {'portal_perfil': ('administrador,restaurante,cocina,cliente,domiciliario,cajera,mesero', lambda c, d, u: perfil(c, u)), 'portal_directorio': ('administrador,cliente', lambda c, d, u: [{k: v for k, v in r.items() if k not in ['modo', 'fuente']} for r in simulacion.listar(c, d)]), 'portal_restaurante': ('administrador,restaurante,cocina,cliente', portal.menu), 'portal_pedidos': ('administrador,restaurante,cocina,cliente,domiciliario', portal.pedidos), 'portal_pedido': ('administrador,restaurante,cocina,cliente,domiciliario', lambda c, d, u: portal.serializar_pedido(c, u, portal.comprobar_pedido(c, u, d['pedido']))), 'portal_panel': ('administrador,restaurante', lambda c, d, u: portal.resumen(c, u)), 'portal_inventario': ('restaurante', lambda c, d, u: portal.inventario(c, u)), 'portal_receta': ('restaurante,cocina', portal.receta), 'portal_usuarios': ('administrador,restaurante', lambda c, d, u: portal.usuarios(c, u)), 'portal_domiciliarios': ('restaurante', lambda c, d, u: [dict(r) for r in c.execute("SELECT id,nombre FROM usuarios WHERE rol='domiciliario' AND activo=1 ORDER BY nombre")]), 'portal_reportes': ('administrador,restaurante', portal.reportes), 'portal_version_privacidad': ('administrador,restaurante,cocina,cliente,domiciliario,cajera,mesero', lambda c, d, u: {'version': config(c, 'version_privacidad', 0)})}
ESCRITURAS = {'portal_crear_pedido': ('cliente', portal.crear_pedido), 'portal_registrar_pedido': ('restaurante', portal.crear_pedido), 'portal_estado_pedido': ('restaurante,cocina,cliente,domiciliario', portal.cambiar_estado), 'portal_guardar_producto': ('restaurante', portal.guardar_producto), 'portal_guardar_receta': ('restaurante', portal.guardar_receta), 'portal_ajustar_inventario': ('restaurante', portal.ajustar), 'portal_registrar_compra': ('restaurante', portal.compra), 'portal_guardar_usuario': ('administrador,restaurante', portal.guardar_usuario), 'portal_guardar_perfil': ('cliente,domiciliario', portal.guardar_perfil)}
import dos_roles
LECTURAS['portal_pedido'] = ('restaurante,cliente', dos_roles.ver_pedido)
LECTURAS['portal_quejas'] = ('restaurante,cliente', dos_roles.listado)
ESCRITURAS['portal_crear_queja'] = ('cliente', dos_roles.crear)
ESCRITURAS['portal_responder_queja'] = ('restaurante,cliente', dos_roles.responder)
for key in ['portal_usuarios', 'portal_domiciliarios']:
    LECTURAS.pop(key, None)
ESCRITURAS.pop('portal_guardar_usuario', None)
LECTURAS = {k: (','.join((r for r in roles.split(',') if r in ['restaurante', 'cliente'])), fn) for k, (roles, fn) in LECTURAS.items()}
ESCRITURAS = {k: (','.join((r for r in roles.split(',') if r in ['restaurante', 'cliente'])), fn) for k, (roles, fn) in ESCRITURAS.items()}
for nombre, (roles, fn) in {**LECTURAS, **ESCRITURAS}.items():
    accion(nombre, roles, '')(fn)
CONSULTAS.update(LECTURAS)

@accion('portal_guardar_restaurante', 'restaurante', '')
def guardar_restaurante(c, d, u):
    id = alcance(c, u)
    exigir(not d.get('restaurante') or d['restaurante'] == id, 'Acceso denegado a este restaurante')
    estado = d['estado']
    exigir(estado in ['abierto', 'pausado'], 'Estado inválido')
    minimo = int(numero(d['tiempo_min'], 10))
    maximo = int(numero(d['tiempo_max'], minimo))
    exigir(maximo <= 120, 'El tiempo máximo es de 120 minutos')
    envio = int(numero(d['envio']))
    exigir(envio <= 30000, 'Revisa el costo de envío')
    c.execute('UPDATE restaurantes SET nombre=?,descripcion=?,estado=?,tiempo_min=?,tiempo_max=?,envio=? WHERE id=?', (texto(d['nombre'], 100), texto(d['descripcion'], 300), estado, minimo, maximo, envio, id))
    auditar(c, u, 'restaurante_actualizado', id, {'estado': estado})
    return {'ok': True}

@accion('portal_estado_restaurante', 'administrador', '')
def estado_restaurante(c, d, u):
    exigir(d['estado'] in ['abierto', 'pausado'], 'Estado inválido')
    exigir(c.execute('UPDATE restaurantes SET estado=? WHERE id=?', (d['estado'], d['restaurante'])).rowcount, 'Restaurante no disponible')
    auditar(c, u, 'restaurante_estado', d['restaurante'], {'estado': d['estado']})
    return {'ok': True}
