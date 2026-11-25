RNF-11

El servidor cierra conexiones al salir del contexto, usa WAL e índices de pedidos, cobros, recetas, cajas y operaciones. No hay borrado automático del historial financiero. La herramienta carga_historica.py genera por defecto 913.000 registros de prueba en una base temporal y mide una consulta. Esta prueba de índices no demuestra por sí sola RNF-01 ni el funcionamiento completo con cinco años; falta una carga representativa con ocho usuarios sobre la aplicación.
