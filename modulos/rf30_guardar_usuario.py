from nucleo import *

@accion('guardar_usuario', 'administrador', 'id,nombre,rol,pin,activo:bool')
def procesar(c, d, u):
    exigir(d['rol'] in ['administrador', 'cajera', 'mesero', 'cocina', 'domiciliario'], 'Rol inválido')
    id = texto(d['id'])
    exigir(id != u['id'] or (d['activo'] and d['rol'] == 'administrador'), 'No se quite su acceso de administrador')
    r = c.execute('SELECT * FROM usuarios WHERE id=?', (id,)).fetchone()
    pin = d.get('pin', '')
    exigir(not pin and r or (isinstance(pin, str) and pin.isdigit() and (8 <= len(pin) <= 64)), 'PIN de 8 a 64 dígitos')
    sal = secrets.token_hex(16) if pin else r['sal']
    digest = clave(pin, sal) if pin else r['pin']
    c.execute('INSERT INTO usuarios VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET nombre=excluded.nombre,rol=excluded.rol,sal=excluded.sal,pin=excluded.pin,activo=excluded.activo', (id, texto(d['nombre']), d['rol'], sal, digest, int(bool(d['activo']))))
    c.execute('DELETE FROM sesiones WHERE usuario=?', (id,))
    auditar(c, u, 'usuario', id, {'rol': d['rol'], 'activo': d['activo']})
    return {'id': id}
