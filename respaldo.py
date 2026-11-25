import argparse, hashlib, json, os, sqlite3, time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from nucleo import DB, conectar, exigir
from bloqueo import bloquear

def huella(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def copiar(carpeta='respaldos'):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.db'
    archivo = carpeta / nombre
    temporal = archivo.with_suffix('.tmp')
    with conectar() as origen:
        with closing(sqlite3.connect(temporal)) as destino, destino:
            origen.backup(destino)
            exigir(destino.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Copia inválida')
    os.replace(temporal, archivo)
    os.chmod(archivo, 384)
    archivo.with_suffix('.sha256').write_text(huella(archivo) + '\n')
    for p in carpeta.glob('*.db'):
        if time.time() - p.stat().st_mtime > 30 * 86400:
            p.unlink()
            p.with_suffix('.sha256').unlink(missing_ok=True)
    return str(archivo)

def restaurar(archivo):
    archivo = Path(archivo)
    sello = archivo.with_suffix('.sha256')
    exigir(archivo.is_file() and sello.is_file(), 'Falta la copia o su suma de verificación')
    exigir(huella(archivo) == sello.read_text().strip(), 'La copia fue alterada o está incompleta')
    with bloquear(DB + '.lock'):
        with closing(sqlite3.connect(archivo)) as origen, origen:
            exigir(origen.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Copia inválida')
            exigir(origen.execute("SELECT 1 FROM sqlite_master WHERE name='usuarios'").fetchone(), 'La copia no corresponde a la aplicación')
            if Path(DB).is_file():
                copiar('respaldos_antes_restaurar')
            with closing(sqlite3.connect(DB)) as destino, destino:
                origen.backup(destino)
    return {'restaurado': True}

def trabajador(detener):
    while not detener.wait(20):
        try:
            with conectar() as c:
                fila = c.execute("SELECT valor FROM configuracion WHERE clave='respaldo_solicitud'").fetchone()
                solicitud = json.loads(fila[0]) if fila else None
            if solicitud:
                copiar()
                with conectar() as c:
                    c.execute("DELETE FROM configuracion WHERE clave='respaldo_solicitud' AND valor=?", (json.dumps(solicitud),))
        except Exception:
            Path('respaldos').mkdir(exist_ok=True)
            Path('respaldos/estado.json').write_text(json.dumps({'ok': False, 'fecha': datetime.now(timezone.utc).isoformat(), 'mensaje': 'No se pudo completar la copia. Revisar espacio y permisos.'}))
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('accion', choices=['crear', 'restaurar'])
    p.add_argument('--archivo')
    a = p.parse_args()
    t = time.perf_counter()
    resultado = copiar() if a.accion == 'crear' else restaurar(a.archivo or '')
    print(json.dumps({'resultado': resultado, 'segundos': time.perf_counter() - t}, ensure_ascii=False))
