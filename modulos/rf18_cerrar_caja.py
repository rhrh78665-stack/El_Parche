from nucleo import *

@accion('cerrar_caja', 'cajera', 'contado')
def procesar(c, d, u):
    caja = c.execute('SELECT * FROM cajas WHERE cajera=? AND cierre IS NULL', (u['id'],)).fetchone()
    exigir(caja, 'Sin caja abierta')
    medios = {r['medio']: r['total'] for r in c.execute('SELECT medio,SUM(valor) AS total FROM pagos WHERE caja=? AND anulado=0 GROUP BY medio', (caja['id'],))}
    esperado = caja['base'] + medios.get('efectivo', 0)
    contado = dinero(d['contado'])
    diferencia = contado - esperado
    c.execute('UPDATE cajas SET cierre=?,contado=?,diferencia=? WHERE id=?', (ahora(), contado, diferencia, caja['id']))
    auditar(c, u, 'cierre_caja', caja['id'], {'medios': medios, 'esperado': esperado, 'contado': contado, 'diferencia': diferencia})
    configurar(c, 'respaldo_pendiente', True)
    return {'medios': medios, 'esperado': esperado, 'diferencia': diferencia}
