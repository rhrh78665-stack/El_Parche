from nucleo import *
from privacidad import suprimir_en, suprimir_respaldos

@accion('eliminar_cliente', 'administrador', 'celular')
def eliminar(c, d, u):
    celular = texto(d['celular'], 20)
    exigir(celular.isdigit(), 'Celular inválido')
    suprimir_respaldos(celular)
    suprimir_en(c, celular)
    version = config(c, 'version_privacidad', 0) + 1
    configurar(c, 'version_privacidad', version)
    auditar(c, u, 'supresion_cliente', str(uuid.uuid4()), {'version': version})
    return {'ok': True, 'version': version, 'mensaje': 'Datos eliminados de la base y respaldos administrados. Los dispositivos conectados purgarán sus cachés; los desconectados requieren reconexión.'}

@accion('version_privacidad', 'administrador,cajera,mesero,cocina,domiciliario', '')
def version(c, d, u):
    return {'version': config(c, 'version_privacidad', 0)}

@accion('listar_clientes', 'administrador,cajera', '')
def listar(c, d, u):
    return [dict(r) for r in c.execute('SELECT * FROM clientes ORDER BY nombre LIMIT 1000')]
CONSULTAS.update(['version_privacidad', 'listar_clientes'])
