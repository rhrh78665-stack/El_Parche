import sqlite3, os, json, uuid, hashlib, hmac, secrets, time
from datetime import datetime, timezone
from pathlib import Path
DB = os.environ.get('PARCHE_DB', 'datos/parche.db')
ACCIONES = {}
CONSULTAS = set(['cola_pedidos', 'pedidos_demorados', 'comandas', 'buscar_cliente', 'cuadre_domiciliario', 'consultar_existencias', 'alertas_stock', 'menu_disponible', 'reporte_ventas', 'historial_cajas', 'reporte_atencion', 'mis_domicilios', 'ver_auditoria', 'listar_usuarios', 'pedidos_operables', 'detalle_pedido', 'lineas_operables', 'modificadores_producto', 'estado_caja'])

def accion(nombre, roles, campos):

    def registrar(fn):
        ACCIONES[nombre] = {'fn': fn, 'roles': roles.split(','), 'campos': campos}
        return fn
    return registrar

def ahora():
    return datetime.now(timezone.utc).isoformat()

def exigir(condicion, mensaje):
    if not condicion:
        raise ValueError(mensaje)

def numero(v, minimo=0):
    exigir(not isinstance(v, bool), 'Número inválido')
    n = float(v)
    exigir(n == n and abs(n) < 1000000000000.0 and (n >= minimo), 'Valor fuera de rango')
    return n

def dinero(v):
    n = numero(v)
    exigir(n.is_integer(), 'Use pesos enteros')
    return int(n)

def texto(v, maximo=200):
    exigir(isinstance(v, str) and 0 < len(v.strip()) <= maximo, 'Texto inválido')
    return v.strip()

def clave(pin, sal):
    return hashlib.scrypt(pin.encode(), salt=bytes.fromhex(sal), n=16384, r=8, p=1).hex()

def conectar():
    c = sqlite3.connect(DB, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA journal_mode=WAL')
    return c

def iniciar():
    Path(DB).parent.mkdir(parents=True, exist_ok=True)
    with conectar() as c:
        c.executescript(SCHEMA)
        if not c.execute('SELECT 1 FROM usuarios').fetchone():
            pin = os.environ.get('PARCHE_ADMIN_PIN', '')
            exigir(len(pin) >= 8 and pin.isdigit(), 'Defina PARCHE_ADMIN_PIN con al menos 8 dígitos')
            sal = secrets.token_hex(16)
            c.execute('INSERT INTO usuarios VALUES(?,?,?,?,?,1)', ('admin', 'Administrador', 'administrador', sal, clave(pin, sal)))

def auditar(c, u, tipo, objeto, datos):
    c.execute('INSERT INTO auditoria(usuario,tipo,objeto,datos,fecha) VALUES(?,?,?,?,?)', (u['id'], tipo, str(objeto), json.dumps(datos, ensure_ascii=False), ahora()))

def pedido(c, id):
    r = c.execute('SELECT * FROM pedidos WHERE id=?', (id,)).fetchone()
    exigir(r is not None, 'Pedido inexistente')
    return dict(r)

def configurar(c, k, valor):
    c.execute('INSERT INTO configuracion VALUES(?,?) ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor', (k, json.dumps(valor)))

def config(c, k, default):
    r = c.execute('SELECT valor FROM configuracion WHERE clave=?', (k,)).fetchone()
    return json.loads(r[0]) if r else default

def ejecutar(nombre, d, u, identificador):
    exigir(nombre not in ['consumir_receta', 'validar_referencia'], 'Operación interna')
    exigir(nombre in ACCIONES, 'Acción desconocida')
    a = ACCIONES[nombre]
    exigir(u['rol'] in a['roles'], 'Acceso denegado')
    with conectar() as c:
        consulta = nombre in CONSULTAS
        c.execute('BEGIN' if consulta else 'BEGIN IMMEDIATE')
        vigente = c.execute('SELECT activo,rol FROM usuarios WHERE id=?', (u['id'],)).fetchone()
        exigir(vigente and vigente['activo'] and (vigente['rol'] == u['rol']), 'Sesión revocada')
        if consulta:
            return a['fn'](c, d, u)
        anterior = c.execute('SELECT resultado,accion,datos FROM operaciones WHERE id=?', (identificador,)).fetchone()
        serial = json.dumps(d, sort_keys=True, ensure_ascii=False)
        if anterior:
            exigir(anterior['accion'] == u['id'] + ':' + nombre and anterior['datos'] == serial, 'Identificador reutilizado')
            return json.loads(anterior['resultado'])
        salida = a['fn'](c, d, u)
        c.execute('INSERT INTO operaciones VALUES(?,?,?,?,?)', (identificador, u['id'] + ':' + nombre, serial, json.dumps(salida), ahora()))
        return salida
SCHEMA = "\nCREATE TABLE IF NOT EXISTS usuarios(id TEXT PRIMARY KEY,nombre TEXT NOT NULL,rol TEXT NOT NULL,sal TEXT NOT NULL,pin TEXT NOT NULL,activo INTEGER NOT NULL);\nCREATE TABLE IF NOT EXISTS sesiones(token TEXT PRIMARY KEY,usuario TEXT REFERENCES usuarios(id),expira REAL);\nCREATE TABLE IF NOT EXISTS intentos(usuario TEXT PRIMARY KEY,fallos INTEGER,ultimo REAL);\nCREATE TABLE IF NOT EXISTS productos(id TEXT PRIMARY KEY,nombre TEXT,categoria TEXT,precio INTEGER,modificadores TEXT,activo INTEGER);\nCREATE TABLE IF NOT EXISTS insumos(id TEXT PRIMARY KEY,nombre TEXT,unidad TEXT,stock REAL,minimo REAL);\nCREATE TABLE IF NOT EXISTS recetas(producto TEXT REFERENCES productos(id),insumo TEXT REFERENCES insumos(id),cantidad REAL,PRIMARY KEY(producto,insumo));\nCREATE TABLE IF NOT EXISTS pedidos(id TEXT PRIMARY KEY,canal TEXT,mesa TEXT,cliente TEXT,estado TEXT,fecha TEXT,salida TEXT,entrega TEXT,domiciliario TEXT REFERENCES usuarios(id),total INTEGER,pagado INTEGER DEFAULT 0,contraentrega INTEGER DEFAULT 0,motivo TEXT);\nCREATE TABLE IF NOT EXISTS lineas(id INTEGER PRIMARY KEY,pedido TEXT REFERENCES pedidos(id),producto TEXT REFERENCES productos(id),nombre TEXT,cantidad INTEGER,precio INTEGER,modificadores TEXT,observacion TEXT);\nCREATE TABLE IF NOT EXISTS clientes(celular TEXT PRIMARY KEY,nombre TEXT,direccion TEXT,barrio TEXT,referencia TEXT,autorizacion_fecha TEXT,autorizacion_medio TEXT);\nCREATE TABLE IF NOT EXISTS cajas(id TEXT PRIMARY KEY,cajera TEXT REFERENCES usuarios(id),base INTEGER,apertura TEXT,cierre TEXT,contado INTEGER,diferencia INTEGER);\nCREATE UNIQUE INDEX IF NOT EXISTS caja_abierta ON cajas(cajera) WHERE cierre IS NULL;\nCREATE TABLE IF NOT EXISTS pagos(id TEXT PRIMARY KEY,pedido TEXT REFERENCES pedidos(id),caja TEXT REFERENCES cajas(id),medio TEXT,valor INTEGER,referencia TEXT UNIQUE,fecha TEXT,anulado INTEGER DEFAULT 0);\nCREATE TABLE IF NOT EXISTS movimientos(id INTEGER PRIMARY KEY,insumo TEXT REFERENCES insumos(id),cantidad REAL,tipo TEXT,detalle TEXT,fecha TEXT);\nCREATE TABLE IF NOT EXISTS compras(id TEXT PRIMARY KEY,proveedor TEXT,fecha TEXT,costo INTEGER);\nCREATE TABLE IF NOT EXISTS rehechos(id TEXT PRIMARY KEY,pedido TEXT REFERENCES pedidos(id),motivo TEXT,fecha TEXT);\nCREATE TABLE IF NOT EXISTS configuracion(clave TEXT PRIMARY KEY,valor TEXT);\nCREATE TABLE IF NOT EXISTS auditoria(id INTEGER PRIMARY KEY,usuario TEXT,tipo TEXT,objeto TEXT,datos TEXT,fecha TEXT);\nCREATE TRIGGER IF NOT EXISTS auditoria_no_update BEFORE UPDATE ON auditoria BEGIN SELECT RAISE(ABORT,'Auditoría inmutable'); END;\nCREATE TRIGGER IF NOT EXISTS auditoria_no_delete BEFORE DELETE ON auditoria BEGIN SELECT RAISE(ABORT,'Auditoría inmutable'); END;\nCREATE TABLE IF NOT EXISTS operaciones(id TEXT PRIMARY KEY,accion TEXT,datos TEXT,resultado TEXT,fecha TEXT);\nCREATE INDEX IF NOT EXISTS pedidos_estado ON pedidos(estado,fecha);\nCREATE INDEX IF NOT EXISTS pagos_fecha ON pagos(fecha);\nCREATE INDEX IF NOT EXISTS lineas_pedido ON lineas(pedido);\nCREATE INDEX IF NOT EXISTS pagos_pedido ON pagos(pedido);\nCREATE INDEX IF NOT EXISTS pagos_caja ON pagos(caja,anulado);\nCREATE INDEX IF NOT EXISTS pedidos_domiciliario ON pedidos(domiciliario,salida);\nCREATE INDEX IF NOT EXISTS sesiones_expira ON sesiones(expira);\n"
