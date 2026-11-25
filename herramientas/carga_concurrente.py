import argparse, concurrent.futures, json, statistics, time, urllib.request, uuid
p = argparse.ArgumentParser()
p.add_argument('--url', default='http://127.0.0.1:8000')
p.add_argument('--usuarios', type=int, default=8)
p.add_argument('--peticiones', type=int, default=240)
a = p.parse_args()

def consultar(i):
    t = time.perf_counter()
    with urllib.request.urlopen(a.url + '/salud', timeout=5) as r:
        assert r.status == 200
    return time.perf_counter() - t
with concurrent.futures.ThreadPoolExecutor(max_workers=a.usuarios) as e:
    tiempos = sorted(e.map(consultar, range(a.peticiones)))
p95 = tiempos[min(len(tiempos) - 1, int(len(tiempos) * 0.95))]
print(json.dumps({'muestras': len(tiempos), 'p95_segundos': p95, 'salud_menor_3s': p95 < 3, 'alcance': 'HTTP salud; no certifica entrega de comandas'}, ensure_ascii=False))
raise SystemExit(0 if p95 < 3 else 1)
