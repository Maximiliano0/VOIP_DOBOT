# Teoria - TCP y arquitectura de integracion PC-Robot

## Arquitectura logica

- Robot (Lua): servidor TCP que recibe texto por linea.
- PC (Python): cliente TCP que envia comandos.
- Usuario: interactua por GUI o voz.

## Motivo de conexion persistente

Mantener un socket abierto evita costo de reconexion por cada comando y reduce fallos de sesion.

## Contrato de protocolo

- 1 comando por linea (UTF-8 + salto de linea).
- 1 respuesta por linea.
- Comandos atomicos y de bajo acoplamiento.

## Manejo de fallos

- Timeout configurable.
- Reconexion automatica si el socket cae.
- Respuestas de error legibles para diagnostico.

## Ventajas de esta arquitectura

- Simple de depurar.
- Compatible con GUI y CLI.
- Facil de extender con nuevos comandos.
