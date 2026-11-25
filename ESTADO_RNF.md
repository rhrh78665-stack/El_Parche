# Estado de requisitos no funcionales

| RNF | Entregado | Validación pendiente |
| --- | --- | --- |
| 01 | Lecturas concurrentes, índices, refresco de 1 segundo | Latencia visible en dispositivos de la LAN |
| 02 | Formularios, etiquetas accesibles, atajo de envío | Tres usuarios nuevos, capacitación y cronómetro |
| 03 | Comandas y modificadores ampliados y contrastados | Lectura física a 1,5 metros |
| 04 | Roles, revocación, bloqueo de intentos | Revisión de despliegue |
| 05 | Registro inmutable y cadena de integridad | Protección del archivo y copia externa de la huella |
| 06 | PIN con sal y scrypt, TLS, cookies y cabeceras | Certificados confiables en equipos reales |
| 07 | Monitor independiente y reporte persistente | Mes completo y cobertura del horario |
| 08 | Cola durable, caché, reintentos y conflictos visibles | Dos horas sin conexión en navegador y conciliación |
| 09 | Copia tras cierre, retención, sumas y restauración bloqueada si está en uso | RTO con volumen real y copia externa |
| 10 | Adaptación táctil y alternativa al desenfoque | Windows y Android físicos |
| 11 | Cierre de conexiones, índices e historial sin purga automática | Carga representativa de cinco años |
| 12 | Preferencias editables y medios dinámicos | Propagación visible en otros equipos |
| 13 | Consentimiento, corrección y supresión en base y respaldos | Dispositivos desconectados y copias externas |

La existencia del control no equivale a aceptar todo el requisito. Los scripts de carga sintética indican su alcance y no sustituyen mediciones de campo. El aislamiento entre restaurantes y los roles de plataforma, restaurante y cliente requieren el siguiente cambio funcional: esta entrega mantiene los roles actuales.

Detener la aplicación antes de reconstruir el historial o restaurar datos. La reconstrucción conserva un respaldo del historial anterior fuera del repositorio. No puede eliminar copias, cachés o registros que terceros ya conserven.
