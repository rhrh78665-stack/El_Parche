from nucleo import *

@accion('configurar_operacion', 'administrador', 'demora,medios:json')
def configurar_operacion(c, d, u):
    demora = numero(d['demora'], 1)
    exigir(demora <= 120, 'Alerta entre 1 y 120 minutos')
    medios = d['medios']
    exigir(isinstance(medios, list) and medios and (len(medios) <= 20) and all((isinstance(x, str) and 0 < len(x) <= 40 for x in medios)), 'Medios inválidos')
    exigir(len(set(medios)) == len(medios), 'Medios repetidos')
    configurar(c, 'demora', demora)
    configurar(c, 'medios', medios)
    auditar(c, u, 'configuracion', 'operacion', d)
    return {'ok': True}

@accion('preferencias_operacion', 'administrador,cajera,mesero,cocina,domiciliario', '')
def preferencias(c, d, u):
    return {'demora': config(c, 'demora', 5), 'medios': config(c, 'medios', ['efectivo', 'datáfono', 'Nequi', 'Daviplata', 'transferencia', 'plataforma'])}
CONSULTAS.add('preferencias_operacion')
