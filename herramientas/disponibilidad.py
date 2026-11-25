import argparse, datetime, json, sqlite3, time, urllib.request
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('--url', default='http://127.0.0.1:8000')
p.add_argument('--archivo', default='monitoreo/disponibilidad.db')
p.add_argument('--intervalo', type=int, default=30)
p.add_argument('--reporte', action='store_true')
p.add_argument('--muestras', type=int, default=0)
a = p.parse_args()
Path(a.archivo).parent.mkdir(parents=True, exist_ok=True)
c = sqlite3.connect(a.archivo)
c.execute('CREATE TABLE IF NOT EXISTS muestras(fecha TEXT,ok INTEGER,segundos REAL)')
if a.reporte:
    filas = c.execute('SELECT substr(fecha,1,7),COUNT(*),SUM(ok) FROM muestras GROUP BY substr(fecha,1,7)').fetchall()
    print(json.dumps([{'mes': r[0], 'muestras': r[1], 'porcentaje_observado': 100 * r[2] / r[1]} for r in filas], ensure_ascii=False))
    raise SystemExit()
i = 0
try:
    while a.muestras == 0 or i < a.muestras:
        inicio = time.perf_counter()
        ok = 0
        try:
            with urllib.request.urlopen(a.url + '/salud', timeout=5) as r:
                ok = int(r.status == 200 and json.load(r).get('ok') is True)
        except Exception:
            pass
        c.execute('INSERT INTO muestras VALUES(?,?,?)', (datetime.datetime.now(datetime.timezone.utc).isoformat(), ok, time.perf_counter() - inicio))
        c.commit()
        i += 1
        if a.muestras == 0 or i < a.muestras:
            time.sleep(max(1, a.intervalo))
except KeyboardInterrupt:
    pass
