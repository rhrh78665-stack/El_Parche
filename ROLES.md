# Restaurante y Cliente

Solo se habilitan dos roles en el acceso web: Restaurante y Cliente. Las cuentas antiguas se conservan en la base para no destruir registros históricos, pero los roles anteriores no pueden iniciar sesión ni utilizar sesiones previas en este portal.

Restaurante: inicio, pedidos, preparación, menú y recetas, inventario, quejas, reportes y configuración. Gestiona preparación, despacho y confirmación de entrega con validación del recaudo, sin exigir una cuenta de cocina o de reparto.

Cliente: restaurantes, carrito, seguimiento, pedidos, historial, quejas y perfil. Solo puede consultar y reportar problemas de sus pedidos. Las conversaciones se comparten exclusivamente con el restaurante del pedido.

## Accesos para evaluación local

Usuario restaurante, PIN 48261937, asociado con Brasa & Pan.
Usuario cliente, PIN 73619482, nombre Valentina Rojas.

Son accesos de prueba conocidos, exclusivamente para evaluación local. Los PIN se almacenan con sal y scrypt. La migración no restablece PIN, perfiles, pedidos ni inventario en arranques posteriores. Si ya existe uno de esos identificadores antes de la migración, se detiene sin sobrescribir su cuenta.

Los pedidos, personas y negocios precargados constituyen datos de evaluación, no transacciones comerciales reales. Esta aclaración se mantiene fuera de la interfaz. Las fotos se conservan del catálogo anterior.

La bitácora de estados registra cada transición nueva; los pedidos previos se incorporan con su estado conocido, sin inventar tiempos intermedios. Las recetas y reservas descuentan inventario una sola vez al iniciar la preparación. Las quejas permiten respuesta y estados abierta, en atención y resuelta.
