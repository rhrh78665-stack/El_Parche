import json
import uuid
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from nucleo import exigir, texto, dinero, ahora
SCHEMA = "\nCREATE TABLE IF NOT EXISTS restaurantes(id TEXT PRIMARY KEY,nombre TEXT NOT NULL,categoria TEXT NOT NULL,descripcion TEXT,barrio TEXT,foto TEXT,fuente TEXT,color TEXT,tiempo_min INTEGER,tiempo_max INTEGER,envio INTEGER,valoracion REAL,estado TEXT NOT NULL,modo TEXT NOT NULL DEFAULT 'simulado');\nCREATE TABLE IF NOT EXISTS menus_restaurantes(id TEXT PRIMARY KEY,restaurante TEXT NOT NULL REFERENCES restaurantes(id),nombre TEXT NOT NULL,descripcion TEXT,precio INTEGER NOT NULL CHECK(precio>=0),foto TEXT,categoria TEXT,stock INTEGER NOT NULL CHECK(stock>=0),destacado INTEGER,alergenos TEXT);\nCREATE TABLE IF NOT EXISTS pedidos_simulados(id TEXT PRIMARY KEY,restaurante TEXT NOT NULL REFERENCES restaurantes(id),cliente TEXT NOT NULL,barrio TEXT,estado TEXT NOT NULL,fecha TEXT NOT NULL,actualizado TEXT NOT NULL,total INTEGER NOT NULL,envio INTEGER NOT NULL,observacion TEXT,domiciliario TEXT,origen TEXT NOT NULL DEFAULT 'simulado');\nCREATE TABLE IF NOT EXISTS lineas_simuladas(id INTEGER PRIMARY KEY,pedido TEXT NOT NULL REFERENCES pedidos_simulados(id),producto TEXT NOT NULL REFERENCES menus_restaurantes(id),nombre TEXT,cantidad INTEGER NOT NULL CHECK(cantidad>0),precio INTEGER NOT NULL CHECK(precio>=0));\nCREATE INDEX IF NOT EXISTS menus_por_restaurante ON menus_restaurantes(restaurante);\nCREATE INDEX IF NOT EXISTS simulados_estado_fecha ON pedidos_simulados(estado,fecha);\nCREATE INDEX IF NOT EXISTS simulados_restaurante_fecha ON pedidos_simulados(restaurante,fecha);\nCREATE INDEX IF NOT EXISTS lineas_simuladas_pedido ON lineas_simuladas(pedido);\n"
TRANSICIONES = {'recibido': ['en preparación', 'cancelado'], 'en preparación': ['listo', 'cancelado'], 'listo': ['en ruta'], 'en ruta': ['entregado'], 'entregado': [], 'cancelado': []}

def preparar(c):
    c.executescript(SCHEMA)
    base = Path(__file__).with_name('datos_demo')
    restaurantes = json.loads((base / 'restaurantes.json').read_text(encoding='utf-8'))
    menus = json.loads((base / 'menus.json').read_text(encoding='utf-8'))
    for item in restaurantes:
        c.execute('INSERT OR IGNORE INTO restaurantes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)', tuple((item[k] for k in ['id', 'nombre', 'categoria', 'descripcion', 'barrio', 'foto', 'fuente', 'color', 'tiempo_min', 'tiempo_max', 'envio', 'valoracion', 'estado', 'modo'])))
    for item in menus:
        c.execute('INSERT OR IGNORE INTO menus_restaurantes(id,restaurante,nombre,descripcion,precio,foto,categoria,stock,destacado,alergenos) VALUES(?,?,?,?,?,?,?,?,?,?)', (item['id'], item['restaurante'], item['nombre'], item['descripcion'], item['precio'], item['foto'], item['categoria'], item['stock'], int(item['destacado']), json.dumps(item['alergenos'], ensure_ascii=False)))
    marca = c.execute("SELECT valor FROM configuracion WHERE clave='catalogo_simulacion_1'").fetchone()
    if marca:
        return
    nombres = ['Valentina Rojas', 'Andrés Molina', 'Laura Castaño', 'Mateo Salazar', 'Daniela Ruiz', 'Santiago Vélez', 'Camila Torres', 'Sebastián Ríos', 'Mariana Ortiz', 'Juan Esteban Gil', 'Paula Restrepo', 'Nicolás Acosta', 'Alejandra López', 'David Muñoz', 'Natalia Herrera', 'Felipe Castro', 'Sara Montoya', 'Julián Vargas', 'Isabela Pardo', 'Tomás Valencia', 'Carolina Mora', 'Samuel Medina', 'Lucía Gómez', 'Gabriel Rivas']
    ahora_dt = datetime.now(timezone.utc)
    for dia in range(7):
        for indice in range(24):
            lugar = restaurantes[(dia * 7 + indice) % len(restaurantes)]
            productos = [p for p in menus if p['restaurante'] == lugar['id']]
            seleccion = [productos[indice % 6], productos[(indice + 2) % 6]]
            estado = 'entregado' if dia else ['recibido', 'en preparación', 'listo', 'en ruta', 'entregado', 'entregado', 'entregado', 'cancelado'][indice % 8]
            fecha = (ahora_dt - timedelta(days=dia, minutes=indice * 17 + 10)).isoformat()
            id = str(uuid.uuid5(uuid.NAMESPACE_URL, 'el-parche/simulacion-1/' + str(dia) + '/' + str(indice)))
            total = sum((p['precio'] for p in seleccion)) + lugar['envio']
            c.execute('INSERT OR IGNORE INTO pedidos_simulados(id,restaurante,cliente,barrio,estado,fecha,actualizado,total,envio,observacion,domiciliario,origen) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', (id, lugar['id'], nombres[(dia + indice) % len(nombres)], lugar['barrio'], estado, fecha, fecha, total, lugar['envio'], '', ['Carlos Rivas', 'Ezequiel López', 'Daniel Torres'][indice % 3], 'simulado'))
            c.executemany('INSERT INTO lineas_simuladas(pedido,producto,nombre,cantidad,precio) VALUES(?,?,?,?,?)', [(id, p['id'], p['nombre'], 1, p['precio']) for p in seleccion])
    c.execute("INSERT INTO configuracion(clave,valor) VALUES('catalogo_simulacion_1','true')")

def listar(c, d):
    normalizar = lambda v: ''.join((x for x in unicodedata.normalize('NFD', str(v)) if unicodedata.category(x) != 'Mn')).casefold()
    q = normalizar(d.get('buscar', '')).strip()[:100]
    categoria = str(d.get('categoria', ''))
    rows = [dict(r) for r in c.execute('SELECT r.*,COUNT(m.id) AS productos FROM restaurantes r LEFT JOIN menus_restaurantes m ON m.restaurante=r.id GROUP BY r.id ORDER BY r.nombre')]
    return [r for r in rows if (not categoria or r['categoria'] == categoria) and (not q or q in normalizar(r['nombre'] + ' ' + r['categoria'] + ' ' + r['barrio']))]

def detalle(c, d):
    r = c.execute('SELECT * FROM restaurantes WHERE id=?', (d['restaurante'],)).fetchone()
    exigir(r, 'Restaurante no encontrado')
    productos = []
    for p in c.execute('SELECT * FROM menus_restaurantes WHERE restaurante=? ORDER BY destacado DESC,id', (r['id'],)):
        producto = dict(p)
        producto['alergenos'] = json.loads(producto['alergenos'])
        productos.append(producto)
    pedidos = [dict(p) for p in c.execute('SELECT * FROM pedidos_simulados WHERE restaurante=? ORDER BY fecha DESC LIMIT 20', (r['id'],))]
    return {'restaurante': dict(r), 'menu': productos, 'pedidos': pedidos, 'transiciones': TRANSICIONES, 'modo': 'simulado'}

def resumen(c, d):
    fecha = (datetime.now(timezone.utc) - timedelta(hours=5)).date()
    inicio = (fecha - timedelta(days=6)).isoformat()
    agrupados = {r['dia']: dict(r) for r in c.execute("SELECT date(fecha,'-5 hours') AS dia,COUNT(*) AS pedidos,SUM(CASE WHEN estado='entregado' THEN total ELSE 0 END) AS ventas FROM pedidos_simulados WHERE datetime(fecha,'-5 hours')>=? GROUP BY dia", (inicio,))}
    dias = []
    for i in range(6, -1, -1):
        dia = (fecha - timedelta(days=i)).isoformat()
        item = agrupados.get(dia, {'pedidos': 0, 'ventas': 0})
        dias.append({'dia': dia, 'pedidos': item['pedidos'], 'ventas': item['ventas'] or 0})
    pedidos = [dict(p) for p in c.execute('SELECT p.*,r.nombre AS restaurante_nombre,r.foto AS restaurante_foto,r.categoria FROM pedidos_simulados p JOIN restaurantes r ON r.id=p.restaurante ORDER BY p.fecha DESC LIMIT 12')]
    populares = [dict(p) for p in c.execute("SELECT r.id,r.nombre,r.categoria,r.foto,COUNT(p.id) AS pedidos,COALESCE(SUM(CASE WHEN p.estado='entregado' THEN p.total ELSE 0 END),0) AS ventas FROM restaurantes r LEFT JOIN pedidos_simulados p ON p.restaurante=r.id GROUP BY r.id ORDER BY pedidos DESC,r.nombre LIMIT 4")]
    return {'restaurantes': c.execute('SELECT COUNT(*) FROM restaurantes').fetchone()[0], 'abiertos': c.execute("SELECT COUNT(*) FROM restaurantes WHERE estado='abierto'").fetchone()[0], 'productos': c.execute('SELECT COUNT(*) FROM menus_restaurantes').fetchone()[0], 'activos': c.execute("SELECT COUNT(*) FROM pedidos_simulados WHERE estado NOT IN ('entregado','cancelado')").fetchone()[0], 'ventas_hoy': sum((p['ventas'] for p in dias if p['dia'] == fecha.isoformat())), 'serie': dias, 'recientes': pedidos, 'populares': populares, 'modo': 'simulado'}

def crear_pedido(c, d):
    r = c.execute('SELECT * FROM restaurantes WHERE id=?', (d['restaurante'],)).fetchone()
    exigir(r, 'Restaurante no encontrado')
    exigir(r['estado'] == 'abierto', 'La cocina está pausada')
    cliente = texto(d['cliente'], 100)
    barrio = texto(d['barrio'], 100)
    observacion = str(d.get('observacion', ''))
    exigir(len(observacion) <= 100, 'La observación admite máximo 100 caracteres')
    lineas = d['lineas']
    exigir(isinstance(lineas, list) and 0 < len(lineas) <= 30, 'Selecciona al menos un producto')
    agrupadas = {}
    for l in lineas:
        n = l['cantidad']
        exigir(type(n) is int and 1 <= n <= 20, 'Cantidad inválida')
        producto = texto(l['producto'], 80)
        agrupadas[producto] = agrupadas.get(producto, 0) + n
    items = []
    total = r['envio']
    for id, cantidad in agrupadas.items():
        p = c.execute('SELECT * FROM menus_restaurantes WHERE id=? AND restaurante=?', (id, r['id'])).fetchone()
        exigir(p, 'El producto no pertenece a este restaurante')
        exigir(cantidad <= 20, 'Máximo 20 unidades por producto')
        exigir(c.execute('UPDATE menus_restaurantes SET stock=stock-? WHERE id=? AND stock>=?', (cantidad, id, cantidad)).rowcount, 'No hay suficiente disponibilidad')
        items.append((p, cantidad))
        total += p['precio'] * cantidad
    id = d.get('id') or str(uuid.uuid4())
    exigir(isinstance(id, str) and str(uuid.UUID(id)) == id, 'Identificador inválido')
    fecha = ahora()
    c.execute('INSERT INTO pedidos_simulados(id,restaurante,cliente,barrio,estado,fecha,actualizado,total,envio,observacion,domiciliario,origen) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', (id, r['id'], cliente, barrio, 'recibido', fecha, fecha, total, r['envio'], observacion, '', 'simulado'))
    c.executemany('INSERT INTO lineas_simuladas(pedido,producto,nombre,cantidad,precio) VALUES(?,?,?,?,?)', [(id, p['id'], p['nombre'], n, p['precio']) for p, n in items])
    return {'id': id, 'total': total, 'estado': 'recibido', 'modo': 'simulado'}

def estado_pedido(c, d):
    p = c.execute('SELECT * FROM pedidos_simulados WHERE id=?', (d['pedido'],)).fetchone()
    exigir(p, 'Pedido no encontrado')
    estado = d['estado']
    exigir(estado in TRANSICIONES.get(p['estado'], []), 'Transición de estado inválida')
    if estado == 'cancelado' and p['estado'] == 'recibido':
        for l in c.execute('SELECT producto,cantidad FROM lineas_simuladas WHERE pedido=?', (p['id'],)).fetchall():
            c.execute('UPDATE menus_restaurantes SET stock=stock+? WHERE id=?', (l['cantidad'], l['producto']))
    domiciliario = p['domiciliario']
    if estado == 'en ruta':
        domiciliario = texto(d.get('domiciliario', ''), 100)
    c.execute('UPDATE pedidos_simulados SET estado=?,actualizado=?,domiciliario=? WHERE id=?', (estado, ahora(), domiciliario, p['id']))
    return {'id': p['id'], 'estado': estado, 'modo': 'simulado'}
