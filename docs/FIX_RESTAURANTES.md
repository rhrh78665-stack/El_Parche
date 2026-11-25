# Restaurantes y actualización visual

El fix añade un catálogo de simulación con 30 cocinas ficticias, 10 especialidades, 180 platos y 168 pedidos iniciales. Incluye 25 fotografías locales de referencia y la mascota proporcionada para El Parche. Los datos se insertan una sola vez al arrancar; reiniciar no duplica registros ni reinicia cambios de la simulación.

Administrador puede buscar por nombre, especialidad o barrio, filtrar cocinas abiertas, guardar favoritos en el navegador, consultar menús, crear pedidos de prueba, avanzar sus estados, asignar un domiciliario y pausar o reabrir una cocina. Pedidos muestra el seguimiento global con filtros. Los pedidos simulados tienen disponibilidad propia y no modifican las tablas de pedidos, pagos, cajas ni insumos de la operación real.

El resumen conserva sus elementos en las actualizaciones periódicas. Solo cambian textos y filas con datos distintos. Los sondeos no se superponen, se pausan con la pestaña oculta o un formulario abierto y no reinician el pedido que se está armando. La fecha de ventas de hoy corresponde a UTC-5.

La nueva paleta combina crema, coral, carbón, miel y tonos suaves de salvia. La navegación, las tarjetas y los botones tienen transiciones breves; se respeta la preferencia de movimiento reducido. El logo se integra sin modificar el archivo recibido.

Para ejecutar desde la raíz: py -3 iniciar.py. Ingresar con admin y el PIN ya existente; abrir Restaurantes. Si la sesión conservaba la página anterior, recargar con Ctrl+F5.

Validación: 33 pruebas Python, prueba de transporte con almacenamiento simulado y comprobación en Chromium de escritorio y viewport móvil. Se verifican 30 tarjetas, filtros, búsqueda sin tildes, menú, creación y avance de pedido, listado global y conservación de nodos del resumen. El catálogo no habilita todavía cuentas independientes por restaurante ni un portal de clientes: ese aislamiento requiere el siguiente cambio de roles.
