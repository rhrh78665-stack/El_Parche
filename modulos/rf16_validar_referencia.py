from nucleo import *

@accion('validar_referencia', 'cajera', 'medio,referencia')
def procesar(c, d, u):
    if d['medio'] not in ['Nequi', 'Daviplata', 'transferencia']:
        return None
    r = texto(d.get('referencia', ''), 100).upper()
    exigir(not c.execute('SELECT 1 FROM pagos WHERE referencia=?', (r,)).fetchone(), 'Referencia repetida')
    return r
