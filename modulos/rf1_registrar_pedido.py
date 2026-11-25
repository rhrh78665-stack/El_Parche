from nucleo import *

@accion('registrar_pedido', 'cajera,mesero', 'canal,mesa,cliente,lineas:json')
def procesar(c, d, u):
    canal = d['canal']
    exigir(canal in ['mesa', 'mostrador', 'WhatsApp', 'llamada', 'Rappi', 'DiDi Food'], 'Canal inválido')
    if u['rol'] == 'mesero':
        exigir(canal == 'mesa', 'El mesero solo registra mesas')
    mesa = str(d.get('mesa', ''))
    exigir(canal != 'mesa' or (mesa.isdigit() and 1 <= int(mesa) <= 12), 'Mesa inválida')
    lineas = d['lineas']
    exigir(isinstance(lineas, list) and 0 < len(lineas) <= 100, 'Incluya productos')
    id = d.get('id') or str(uuid.uuid4())
    exigir(isinstance(id, str) and str(uuid.UUID(id)) == id, 'Identificador de pedido inválido')
    total = 0
    items = []
    for l in lineas:
        p = c.execute('SELECT * FROM productos WHERE id=? AND activo=1', (l['producto'],)).fetchone()
        exigir(p is not None, 'Producto no disponible')
        exigir(c.execute('SELECT 1 FROM recetas WHERE producto=?', (p['id'],)).fetchone(), 'Defina la receta del producto antes de venderlo')
        n = numero(l['cantidad'], 1)
        exigir(n.is_integer() and n <= 100, 'Cantidad inválida')
        n = int(n)
        obs = l.get('observacion', '')
        exigir(isinstance(obs, str) and len(obs) <= 100, 'Observación de máximo 100 caracteres')
        opciones = l.get('modificadores', [])
        exigir(isinstance(opciones, list) and all((x in json.loads(p['modificadores']) for x in opciones)), 'Modificador inválido')
        for r in c.execute('SELECT r.cantidad,i.stock FROM recetas r JOIN insumos i ON i.id=r.insumo WHERE producto=?', (p['id'],)):
            exigir(r['stock'] >= r['cantidad'] * n, 'Insumos insuficientes')
        total += p['precio'] * n
        items.append((id, p['id'], p['nombre'], n, p['precio'], json.dumps(opciones), obs))
    c.execute('INSERT INTO pedidos(id,canal,mesa,cliente,estado,fecha,total) VALUES(?,?,?,?,?,?,?)', (id, canal, mesa, d.get('cliente', ''), 'recibido', ahora(), total))
    c.executemany('INSERT INTO lineas(pedido,producto,nombre,cantidad,precio,modificadores,observacion) VALUES(?,?,?,?,?,?,?)', items)
    return {'id': id, 'total': total}
