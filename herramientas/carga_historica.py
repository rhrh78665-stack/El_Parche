import argparse, json, sqlite3, time, tempfile, datetime, uuid, random
p = argparse.ArgumentParser()
p.add_argument('--dias', type=int, default=1826)
p.add_argument('--pedidos-dia', type=int, default=500)
a = p.parse_args()
inicio = time.perf_counter()
with tempfile.TemporaryDirectory() as carpeta:
    c = sqlite3.connect(carpeta + '/carga.db')
    c.execute('CREATE TABLE pedidos(id TEXT PRIMARY KEY,fecha TEXT,canal TEXT,estado TEXT,total INTEGER)')
    c.execute('CREATE INDEX fecha_canal ON pedidos(fecha,canal)')
    c.execute('CREATE INDEX estado_fecha ON pedidos(estado,fecha)')
    fecha = datetime.datetime.now(datetime.timezone.utc)
    for dia in range(a.dias):
        f = (fecha - datetime.timedelta(days=dia)).isoformat()
        c.executemany('INSERT INTO pedidos VALUES(?,?,?,?,?)', [(str(uuid.uuid4()), f, 'WhatsApp', 'entregado', 15000) for _ in range(a.pedidos_dia)])
    c.commit()
    t = time.perf_counter()
    cantidad = c.execute('SELECT COUNT(*) FROM pedidos').fetchone()[0]
    consulta = c.execute('SELECT canal,SUM(total) FROM pedidos WHERE fecha>=? GROUP BY canal', ((fecha - datetime.timedelta(days=30)).isoformat(),)).fetchall()
    segundos = time.perf_counter() - t
    c.close()
    print(json.dumps({'registros': cantidad, 'generacion_segundos': time.perf_counter() - inicio, 'consulta_segundos': segundos, 'alcance': 'índices de tabla sintética; falta validar flujo completo RNF-01 sobre la base real'}, ensure_ascii=False))
