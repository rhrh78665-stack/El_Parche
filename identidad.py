import json
import os
import re
import secrets
import sqlite3
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from nucleo import conectar, exigir, texto, clave, ahora, config
ROLES = {'restaurante', 'cliente'}
TABS = {'restaurante': ['inicio', 'pedidos', 'cocina', 'menu', 'inventario', 'quejas', 'reportes', 'ajustes'], 'cliente': ['explorar', 'carrito', 'seguimiento', 'mis_pedidos', 'historial', 'quejas', 'perfil']}
ETIQUETAS = {'administrador': 'Administración', 'restaurante': 'Restaurante', 'cocina': 'Cocina', 'cliente': 'Cliente', 'domiciliario': 'Domiciliario'}
SCHEMA = '\nCREATE TABLE IF NOT EXISTS accesos_restaurante(usuario TEXT PRIMARY KEY REFERENCES usuarios(id),restaurante TEXT NOT NULL REFERENCES restaurantes(id));\nCREATE TABLE IF NOT EXISTS perfiles_cliente(usuario TEXT PRIMARY KEY REFERENCES usuarios(id),celular TEXT,direccion TEXT,barrio TEXT,autorizacion TEXT);\nCREATE TABLE IF NOT EXISTS insumos_restaurante(id TEXT PRIMARY KEY,restaurante TEXT NOT NULL REFERENCES restaurantes(id),nombre TEXT,unidad TEXT,stock REAL NOT NULL CHECK(stock>=0),minimo REAL NOT NULL CHECK(minimo>=0));\nCREATE TABLE IF NOT EXISTS recetas_restaurante(producto TEXT REFERENCES menus_restaurantes(id),insumo TEXT REFERENCES insumos_restaurante(id),cantidad REAL NOT NULL CHECK(cantidad>0),PRIMARY KEY(producto,insumo));\nCREATE TABLE IF NOT EXISTS reservas_restaurante(pedido TEXT REFERENCES pedidos_simulados(id),insumo TEXT REFERENCES insumos_restaurante(id),cantidad REAL NOT NULL CHECK(cantidad>0),PRIMARY KEY(pedido,insumo));\nCREATE TABLE IF NOT EXISTS movimientos_restaurante(id INTEGER PRIMARY KEY,restaurante TEXT REFERENCES restaurantes(id),insumo TEXT REFERENCES insumos_restaurante(id),cantidad REAL,tipo TEXT,motivo TEXT,usuario TEXT REFERENCES usuarios(id),fecha TEXT);\nCREATE TABLE IF NOT EXISTS compras_restaurante(id TEXT PRIMARY KEY,restaurante TEXT REFERENCES restaurantes(id),proveedor TEXT,fecha TEXT,costo INTEGER CHECK(costo>=0),usuario TEXT REFERENCES usuarios(id));\nCREATE INDEX IF NOT EXISTS accesos_por_restaurante ON accesos_restaurante(restaurante);\nCREATE INDEX IF NOT EXISTS insumos_por_restaurante ON insumos_restaurante(restaurante);\nCREATE INDEX IF NOT EXISTS reservas_por_insumo ON reservas_restaurante(insumo);\n'
INGREDIENTES = {'Hamburguesas': [('Pan brioche', 'unidad', 1), ('Carne de res', 'gramo', 150), ('Queso cheddar', 'gramo', 35), ('Vegetales frescos', 'gramo', 45), ('Tocineta', 'gramo', 25), ('Salsa de la casa', 'mililitro', 25)], 'Pizzas': [('Masa artesanal', 'unidad', 1), ('Mozzarella', 'gramo', 130), ('Salsa de tomate', 'mililitro', 80), ('Toppings', 'gramo', 70), ('Albahaca', 'gramo', 4), ('Aceite de oliva', 'mililitro', 6)], 'Perros calientes': [('Pan de perro', 'unidad', 1), ('Salchicha premium', 'unidad', 1), ('Queso rallado', 'gramo', 35), ('Papas crujientes', 'gramo', 50), ('Cebolla', 'gramo', 15), ('Salsas', 'mililitro', 25)], 'Pollo y alitas': [('Alitas', 'unidad', 6), ('Papas rústicas', 'gramo', 150), ('Salsa BBQ', 'mililitro', 35), ('Apio y zanahoria', 'gramo', 50), ('Mezcla de especias', 'gramo', 6), ('Aceite', 'mililitro', 25)], 'Tacos': [('Tortillas de maíz', 'unidad', 3), ('Proteína preparada', 'gramo', 150), ('Vegetales', 'gramo', 60), ('Guacamole', 'gramo', 35), ('Queso', 'gramo', 25), ('Salsa de la casa', 'mililitro', 30)], 'Salchipapas': [('Papas', 'gramo', 250), ('Salchicha', 'unidad', 1), ('Queso', 'gramo', 50), ('Proteína preparada', 'gramo', 80), ('Maíz dulce', 'gramo', 40), ('Salsas', 'mililitro', 35)], 'Sushi': [('Arroz de sushi', 'gramo', 180), ('Nori', 'unidad', 1), ('Relleno fresco', 'gramo', 80), ('Aguacate y pepino', 'gramo', 60), ('Ajonjolí', 'gramo', 5), ('Salsa de soya', 'mililitro', 20)], 'Sándwiches': [('Pan artesanal', 'unidad', 1), ('Proteína preparada', 'gramo', 120), ('Queso', 'gramo', 35), ('Vegetales', 'gramo', 60), ('Mantequilla', 'gramo', 8), ('Salsa de hierbas', 'mililitro', 25)], 'Bowls': [('Arroz y granos', 'gramo', 180), ('Proteína preparada', 'gramo', 120), ('Vegetales frescos', 'gramo', 150), ('Aguacate', 'gramo', 50), ('Semillas', 'gramo', 12), ('Aderezo', 'mililitro', 25)], 'Arepas': [('Arepa de maíz', 'unidad', 1), ('Proteína preparada', 'gramo', 110), ('Queso', 'gramo', 40), ('Aguacate', 'gramo', 45), ('Hogao', 'mililitro', 30), ('Salsa de ajo', 'mililitro', 20)]}

def preparar(c):
    c.executescript(SCHEMA)
    from dos_roles import SCHEMA as extra
    c.executescript(extra)
    columnas = {r['name'] for r in c.execute('PRAGMA table_info(pedidos_simulados)')}
    for nombre, tipo in [('usuario_cliente', 'TEXT REFERENCES usuarios(id)'), ('domiciliario_usuario', 'TEXT REFERENCES usuarios(id)'), ('direccion', 'TEXT'), ('celular', 'TEXT'), ('pago_estado', "TEXT DEFAULT 'pendiente'"), ('medio_pago', "TEXT DEFAULT 'contraentrega'")]:
        if nombre not in columnas:
            c.execute('ALTER TABLE pedidos_simulados ADD COLUMN ' + nombre + ' ' + tipo)
    if 'activo' not in {r['name'] for r in c.execute('PRAGMA table_info(menus_restaurantes)')}:
        c.execute('ALTER TABLE menus_restaurantes ADD COLUMN activo INTEGER NOT NULL DEFAULT 1')
    if config(c, 'inventario_portal_v1', False):
        return
    for r in c.execute('SELECT id,categoria FROM restaurantes').fetchall():
        ingredientes = INGREDIENTES[r['categoria']]
        for i, (nombre, unidad, cantidad) in enumerate(ingredientes):
            id = r['id'] + '_i' + str(i + 1)
            stock = 180 if unidad == 'unidad' else 45000 if unidad == 'gramo' else 18000
            minimo = 20 if unidad == 'unidad' else 3000 if unidad == 'gramo' else 1000
            if i == 5:
                stock = minimo * 0.8
            c.execute('INSERT OR IGNORE INTO insumos_restaurante VALUES(?,?,?,?,?,?)', (id, r['id'], nombre, unidad, stock, minimo))
        for p in c.execute('SELECT id FROM menus_restaurantes WHERE restaurante=?', (r['id'],)).fetchall():
            for i, (_, _, cantidad) in enumerate(ingredientes):
                c.execute('INSERT OR IGNORE INTO recetas_restaurante VALUES(?,?,?)', (p['id'], r['id'] + '_i' + str(i + 1), cantidad))
    c.execute("UPDATE pedidos_simulados SET pago_estado='cobrado' WHERE estado='entregado' AND pago_estado='pendiente'")
    for p in c.execute("SELECT id FROM pedidos_simulados WHERE estado='recibido'").fetchall():
        for x in c.execute('SELECT r.insumo,SUM(r.cantidad*l.cantidad) AS cantidad FROM lineas_simuladas l JOIN recetas_restaurante r ON r.producto=l.producto WHERE l.pedido=? GROUP BY r.insumo', (p['id'],)).fetchall():
            c.execute('INSERT OR IGNORE INTO reservas_restaurante VALUES(?,?,?)', (p['id'], x['insumo'], x['cantidad']))
    c.execute("INSERT INTO configuracion(clave,valor) VALUES('inventario_portal_v1','true')")

def alcance(c, u):
    r = c.execute('SELECT restaurante FROM accesos_restaurante WHERE usuario=?', (u['id'],)).fetchone()
    exigir(r is not None, 'Tu cuenta necesita un restaurante asignado. Contacta a administración.')
    return r['restaurante']

def restaurante_permitido(c, u, id=None):
    if u['rol'] in ['restaurante', 'cocina']:
        propio = alcance(c, u)
        exigir(not id or id == propio, 'Acceso denegado a este restaurante')
        return propio
    exigir(u['rol'] == 'administrador' or u['rol'] == 'cliente', 'Acceso denegado')
    exigir(id, 'Selecciona un restaurante')
    return id

def perfil(c, u):
    usuario = dict(c.execute('SELECT id,nombre,rol,activo FROM usuarios WHERE id=?', (u['id'],)).fetchone())
    rest = None
    if u['rol'] in ['restaurante', 'cocina']:
        id = alcance(c, u)
        rest = dict(c.execute('SELECT * FROM restaurantes WHERE id=?', (id,)).fetchone())
    cliente = c.execute('SELECT celular,direccion,barrio,autorizacion FROM perfiles_cliente WHERE usuario=?', (u['id'],)).fetchone()
    return {'usuario': usuario, 'rol_nombre': ETIQUETAS.get(u['rol'], 'Cuenta pendiente'), 'restaurante': rest, 'cliente': dict(cliente) if cliente else {}, 'pestanas': TABS.get(u['rol'], [])}

def slug(nombre):
    return re.sub('[^a-z0-9]+', '.', unicodedata.normalize('NFKD', nombre).encode('ascii', 'ignore').decode().lower()).strip('.')

def inicializar_cuentas():
    from dos_roles import preparar_accesos
    return preparar_accesos()
