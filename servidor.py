import json, os, ssl, secrets, time, importlib.util
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from nucleo import *
for archivo in sorted(Path(__file__).with_name('modulos').glob('*.py')):
    spec = importlib.util.spec_from_file_location(archivo.stem, archivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

class Handler(BaseHTTPRequestHandler):

    def log_message(self, *args):
        pass

    def responder(self, status, valor, tipo='application/json', cookie=None):
        data = json.dumps(valor, ensure_ascii=False).encode() if tipo == 'application/json' else valor
        self.send_response(status)
        self.send_header('Content-Type', tipo + '; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Cache-Control', 'no-store' if tipo == 'application/json' else 'no-cache')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(data)

    def usuario(self, c):
        cookies = dict((x.strip().split('=', 1) for x in self.headers.get('Cookie', '').split(';') if '=' in x))
        token = cookies.get('sesion', '')
        r = c.execute('SELECT u.id,u.nombre,u.rol FROM sesiones s JOIN usuarios u ON u.id=s.usuario WHERE s.token=? AND s.expira>? AND u.activo=1', (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone()
        exigir(r, 'Inicie sesión')
        return dict(r)

    def do_GET(self):
        try:
            path = urlparse(self.path).path
            if path == '/salud':
                return self.responder(200, {'ok': True})
            if path == '/api/catalogo':
                with conectar() as c:
                    u = self.usuario(c)
                return self.responder(200, {'usuario': u, 'acciones': {k: {'campos': v['campos']} for k, v in ACCIONES.items() if u['rol'] in v['roles'] and k not in ['consumir_receta', 'validar_referencia']}})
            if path.startswith('/features/') and Path(path).name in {p.name for p in Path(__file__).with_name('web').joinpath('features').glob('*.js')}:
                return self.responder(200, (Path(__file__).with_name('web') / 'features' / Path(path).name).read_bytes(), 'application/javascript')
            archivos = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css', '/sw.js': 'sw.js'}
            exigir(path in archivos, 'Ruta inexistente')
            archivo = Path(__file__).with_name('web') / archivos[path]
            tipo = 'text/html' if path == '/' else 'text/css' if path.endswith('.css') else 'application/javascript'
            self.responder(200, archivo.read_bytes(), tipo)
        except ValueError as e:
            self.responder(401, {'error': str(e)})

    def do_POST(self):
        try:
            exigir(self.headers.get('X-Parche') == '1', 'Petición inválida')
            origen = self.headers.get('Origin')
            exigir(not origen or urlparse(origen).netloc == self.headers.get('Host'), 'Origen inválido')
            n = int(self.headers.get('Content-Length', '0'))
            exigir(0 < n <= 200000, 'Solicitud demasiado grande')
            d = json.loads(self.rfile.read(n))
            exigir(isinstance(d, dict), 'JSON inválido')
            if self.path == '/api/login':
                with conectar() as c:
                    id = texto(d['id'])
                    r = c.execute('SELECT * FROM usuarios WHERE id=? AND activo=1', (id,)).fetchone()
                    intento = c.execute('SELECT * FROM intentos WHERE usuario=?', (id,)).fetchone()
                    exigir(not intento or intento['fallos'] < 5 or time.time() - intento['ultimo'] > 300, 'Espere 5 minutos')
                    pin = d.get('pin', '')
                    exigir(isinstance(pin, str) and len(pin) <= 64, 'PIN inválido')
                    valido = r is not None and hmac.compare_digest(clave(pin, r['sal']), r['pin'])
                    if not valido:
                        fallos = intento['fallos'] + 1 if intento and time.time() - intento['ultimo'] <= 300 else 1
                        c.execute('INSERT OR REPLACE INTO intentos VALUES(?,?,?)', (id, fallos, time.time()))
                        c.commit()
                        raise ValueError('Credenciales incorrectas')
                    c.execute('DELETE FROM intentos WHERE usuario=?', (id,))
                    token = secrets.token_urlsafe(32)
                    c.execute('INSERT INTO sesiones VALUES(?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), id, time.time() + 12 * 3600))
                return self.responder(200, {'ok': True}, cookie='sesion=' + token + '; HttpOnly; SameSite=Strict; Path=/' + ('; Secure' if os.environ.get('PARCHE_TLS_CERT') else ''))
            with conectar() as c:
                u = self.usuario(c)
            if self.path == '/api/logout':
                with conectar() as c:
                    c.execute('DELETE FROM sesiones WHERE usuario=?', (u['id'],))
                return self.responder(200, {'ok': True}, cookie='sesion=; Max-Age=0; Path=/; HttpOnly; SameSite=Strict')
            exigir(self.path.startswith('/api/accion/'), 'Ruta inválida')
            id = texto(self.headers.get('Idempotency-Key', ''), 100)
            salida = ejecutar(self.path.rsplit('/', 1)[-1], d, u, id)
            self.responder(200, salida)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError, sqlite3.IntegrityError) as e:
            self.responder(400, {'error': str(e) if isinstance(e, ValueError) else 'Datos inválidos o conflicto de integridad'})
        except Exception:
            self.responder(500, {'error': 'Error interno; operación revertida'})

def main():
    iniciar()
    host = os.environ.get('PARCHE_HOST', '127.0.0.1')
    cert = os.environ.get('PARCHE_TLS_CERT')
    exigir(host in ['127.0.0.1', 'localhost'] or cert, 'Configure TLS antes de exponer el servidor en la red')
    server = ThreadingHTTPServer((host, int(os.environ.get('PARCHE_PORT', '8000'))), Handler)
    if cert:
        contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        contexto.minimum_version = ssl.TLSVersion.TLSv1_2
        contexto.load_cert_chain(cert, os.environ['PARCHE_TLS_KEY'])
        server.socket = contexto.wrap_socket(server.socket, server_side=True)
    print('El Parche listo en el puerto', server.server_port)
    server.serve_forever()
if __name__ == '__main__':
    main()
