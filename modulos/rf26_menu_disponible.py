from nucleo import *

@accion('menu_disponible', 'administrador,cajera,mesero', '')
def procesar(c, d, u):
    return [dict(r) for r in c.execute('SELECT p.*,CASE WHEN NOT EXISTS(SELECT 1 FROM recetas rr WHERE rr.producto=p.id) OR EXISTS(SELECT 1 FROM recetas r JOIN insumos i ON i.id=r.insumo WHERE r.producto=p.id AND i.stock<r.cantidad) THEN 1 ELSE 0 END AS agotado FROM productos p WHERE activo=1 ORDER BY categoria,nombre')]
