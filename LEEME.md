# El Parche · Requisitos funcionales

Servidor Python 3.12 o superior con SQLite. Interfaz web sin dependencias externas. No requiere instalar paquetes de Python ni Node.js.

## Cargar en una carpeta vacía

Los archivos .patch se aplican desde la carpeta donde vivirá el proyecto. Se admite una carpeta con .git; no se crea ningún repositorio ni commit.

El_Parche_RF_Visual.patch contiene toda la aplicación. Alternativamente, aplique EP_000_base_visual.patch y luego EP_RF01 a EP_RF30 en orden. No aplique ambas alternativas sobre la misma carpeta. Los parches individuales requieren el conjunto completo antes de iniciar.

## Ejecutar

```powershell
py -3 iniciar.py
```

La primera vez se solicita crear y confirmar el PIN del usuario admin. El navegador se abre en http://127.0.0.1:8000. La base nueva comienza vacía: no se inventan ventas, pedidos ni estadísticas.

Si está ejecutando la versión anterior en otra consola, deténgala con Ctrl+C antes de iniciar esta. Esta entrega instala una aplicación nueva en la carpeta que elija; no importa automáticamente la base de la carpeta Descargas ni modifica esa copia.

## Preparar el restaurante

1. Ingrese como admin y abra Equipo. Cree cuentas para cajera, cocina, mesero y domiciliario. Cada persona tiene su PIN.
2. En Inventario cree insumos con unidad y mínimo. Registre una compra para ingresar las existencias.
3. En Menú y recetas cree productos con precio y modificadores. Defina sus recetas. Sin receta o sin existencias el producto se muestra agotado.
4. Cierre sesión e ingrese como cajera. En Caja abra un turno con la base inicial.
5. En Pedidos seleccione Nuevo pedido. Elija canal y mesa, agregue productos de las tarjetas y personalice cada línea antes de enviar.
6. En otro perfil o navegador ingrese como cocina. Comience la preparación y marque la comanda como lista. Al comenzar se descuenta inventario en una transacción.
7. Cajera registra el cobro con uno o varios medios. Transferencias exigen referencia única. El operador confirma el ingreso real en su banco.
8. Para domicilios propios registre el cliente con autorización, use su celular en el pedido y asigne un domiciliario cuando esté listo. El domiciliario ve dirección y confirma entrega. Cajera registra el cobro al conciliar el recaudo.
9. Para mesa, mostrador y plataformas, abra el detalle y registre la entrega cuando esté listo.
10. Cierre caja con el efectivo contado. Administrador puede revisar reportes y cierres.

El administrador administra catálogo, inventario, equipo y reportes; la cuenta cajera opera pedidos y cobros. Las opciones cambian según el rol.

## Alcance

Treinta RF con módulos identificables. RF-16 valida referencias dentro del cobro; RF-22 consume recetas dentro del cambio a preparación. Sus pantallas no muestran botones técnicos para ejecutar esas operaciones por separado.

Los modificadores no incluyen sobreprecio ni ingredientes extra: esa política no está definida en el documento. Configure productos separados para adiciones con precio hasta acordar la regla de negocio. Los productos desactivados no aparecen en la carta; para reactivarlos use su código en Crear o editar producto.

Las cancelaciones cobradas requieren administrador. Sus pagos se excluyen de los reportes; la devolución física se realiza por el procedimiento del restaurante. No se repone automáticamente un insumo ya consumido.

No incluye integraciones bancarias, bot de WhatsApp, APIs de plataformas, facturación electrónica ni diseño de logo. Los controles de RNF y sus límites están detallados en ESTADO_RNF.md. La aceptación de rendimiento visible, disponibilidad mensual, compatibilidad física y privacidad en dispositivos desconectados sigue pendiente.

La interfaz conserva pedidos y cobros en IndexedDB cuando no puede contactar el servidor. Una operación pendiente no equivale a una comanda entregada ni a un cobro conciliado. Abra Pendientes para sincronizar y resolver rechazos. Se necesita una sesión iniciada y consultas previas del menú y de caja; no existe un nuevo login sin servidor. No borre el almacenamiento con operaciones pendientes.

## Validación

```powershell
py -3 -m unittest discover -s tests -v
```

Veinticinco pruebas Python de lógica y controles y comprobaciones de sintaxis Python/JavaScript. Aplicación y comparación de todos los parches en carpeta vacía. La inspección visual e interacción de extremo a extremo en un navegador quedan pendientes: el entorno de revisión no pudo iniciar su navegador local ni acceder al servidor desde el navegador remoto. No se presentan como pruebas aprobadas.

El servidor escucha en 127.0.0.1. Para probar LAN requiere certificados confiables y variables PARCHE_HOST, PARCHE_TLS_CERT y PARCHE_TLS_KEY. Las validaciones de campo pendientes se indican en ESTADO_RNF.md.
