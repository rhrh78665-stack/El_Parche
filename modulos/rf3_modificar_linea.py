from nucleo import *

@accion('modificar_linea', 'cajera,mesero', 'linea,modificadores:json,observacion')
def procesar(c, d, u):
    r = c.execute('SELECT l.*,p.estado,pr.modificadores AS permitidos FROM lineas l JOIN pedidos p ON p.id=l.pedido JOIN productos pr ON pr.id=l.producto WHERE l.id=?', (d['linea'],)).fetchone()
    exigir(r and r['estado'] == 'recibido', 'Solo pedidos recibidos')
    obs = d.get('observacion', '')
    exigir(len(obs) <= 100, 'Máximo 100 caracteres')
    op = d['modificadores']
    exigir(isinstance(op, list) and all((x in json.loads(r['permitidos']) for x in op)), 'Modificador inválido')
    c.execute('UPDATE lineas SET modificadores=?,observacion=? WHERE id=?', (json.dumps(op), obs, d['linea']))
    return {'ok': True}
