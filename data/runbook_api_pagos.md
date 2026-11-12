# Runbook de la API de pagos

## Arquitectura

La API de pagos corre en Kubernetes bajo el deployment `payments-api`. El tráfico entra por
NGINX Ingress y se distribuye entre seis réplicas. La aplicación usa PostgreSQL como fuente de
verdad, Redis para idempotencia y Apache Kafka para publicar el evento `payment.confirmed`.
Prometheus recolecta métricas y Grafana presenta los paneles operativos.

## Indicadores de servicio

La disponibilidad objetivo es 99,9 %. La latencia p95 de `POST /payments` debe permanecer por
debajo de 800 ms. La tasa normal de respuestas 5xx es inferior a 0,5 %. Una tasa superior a 5 %
durante diez minutos constituye un incidente de severidad alta.

## Diagnóstico de errores 5xx

1. Revisar el panel `Payments / API Overview` en Grafana.
2. Consultar los logs del deployment con el identificador de correlación de la petición.
3. Verificar la conectividad con PostgreSQL y el uso del pool de conexiones.
4. Comprobar el estado de Redis. La pérdida de Redis afecta la idempotencia, pero no debe impedir
   la lectura de pagos existentes.
5. Revisar el lag del consumer de Kafka antes de reiniciar pods.

Si el pool de PostgreSQL está agotado, reducir temporalmente el tráfico de tareas administrativas
y buscar transacciones de larga duración. No se debe aumentar el tamaño del pool sin verificar el
límite `max_connections` del servidor.

## Recuperación

Un rollback se ejecuta con `kubectl rollout undo deployment/payments-api`. Después del rollback se
debe comprobar la tasa de 5xx, la latencia p95 y la publicación de eventos. La recuperación se
considera estable cuando los tres indicadores permanecen dentro de sus límites durante quince
minutos.

## Escalamiento

Escalar al equipo de base de datos si PostgreSQL rechaza conexiones o presenta réplicas con más de
cinco minutos de retraso. Escalar a seguridad ante credenciales expuestas, pagos no autorizados o
indicios de manipulación de solicitudes.
