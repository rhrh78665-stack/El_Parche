import json, sqlite3, hashlib, os
from contextlib import closing
from pathlib import Path
from nucleo import exigir

def suprimir_en(c, celular):
    c.execute('DELETE FROM clientes WHERE celular=?', (celular,))
    c.execute("UPDATE pedidos SET cliente='' WHERE cliente=?", (celular,))
    for r in c.execute('SELECT id,accion,datos FROM operaciones').fetchall():
        datos = json.loads(r['datos'])
        if r['accion'].endswith(':guardar_cliente_visual') and datos.get('celular') == celular:
            c.execute('UPDATE operaciones SET datos=?,resultado=? WHERE id=?', (json.dumps({'suprimido': True}), json.dumps({'suprimido': True}), r['id']))
        elif datos.get('cliente') == celular:
            datos['cliente'] = ''
            c.execute('UPDATE operaciones SET datos=? WHERE id=?', (json.dumps(datos, sort_keys=True, ensure_ascii=False), r['id']))

def suprimir_respaldos(celular):
    from respaldo import huella
    for carpeta in ['respaldos', 'respaldos_antes_restaurar']:
        for archivo in Path(carpeta).glob('*.db'):
            with closing(sqlite3.connect(archivo)) as c, c:
                c.row_factory = sqlite3.Row
                exigir(c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Respaldo inválido. Resolver antes de suprimir datos.')
                suprimir_en(c, celular)
            temporal = archivo.with_suffix('.sha256.tmp')
            temporal.write_text(huella(archivo) + '\n')
            os.replace(temporal, archivo.with_suffix('.sha256'))
