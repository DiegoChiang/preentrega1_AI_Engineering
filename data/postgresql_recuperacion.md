# Recuperación de PostgreSQL

## Respaldo y objetivos

PostgreSQL genera un respaldo completo diario a las 02:00 UTC y archiva WAL continuamente en un
bucket cifrado. El objetivo de punto de recuperación es de cinco minutos y el objetivo de tiempo de
recuperación es de sesenta minutos. Los respaldos se retienen por treinta días.

## Restauración a un punto en el tiempo

La restauración debe ejecutarse en una instancia aislada. Primero se recupera el último respaldo
completo y luego se reproducen los segmentos WAL hasta el instante aprobado. La instancia restaurada
no recibe tráfico de clientes hasta completar las validaciones de integridad.

Las validaciones obligatorias incluyen: conteo de pagos por estado, suma de importes por moneda,
integridad de claves foráneas y comparación de una muestra de identificadores con el sistema de
conciliación. Si alguna validación falla, la instancia no puede promoverse.

## Promoción y retorno

La promoción requiere aprobación del responsable de incidentes y del responsable de datos. Se
pausan las escrituras, se registra el último LSN disponible y se actualiza el endpoint de base de
datos. Después se habilita tráfico de lectura y, tras diez minutos sin errores, tráfico de escritura.

No se permite eliminar la instancia anterior durante las primeras 24 horas. Los logs, resultados de
validación, tiempos de cada paso y personas que aprobaron la promoción deben conservarse en el
registro del incidente.

## Señales de escalamiento

La corrupción de páginas, la pérdida de segmentos WAL, una diferencia contable o una restauración
que exceda cuarenta y cinco minutos requieren escalamiento inmediato. Una sospecha de acceso no
autorizado también debe notificarse al equipo de seguridad antes de promover cualquier copia.
