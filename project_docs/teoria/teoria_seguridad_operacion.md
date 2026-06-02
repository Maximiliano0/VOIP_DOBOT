# Teoria - Seguridad operativa en celdas roboticas

## Capas de seguridad consideradas

- Planeamiento seguro: checks previos (`CheckMovJ`, `CheckMovL`).
- Parametros conservadores de velocidad y aceleracion para pruebas.
- Collision detection del controlador.
- SafeSkin y zonas virtuales (cuando estan configuradas en controlador).

## Riesgos del control por voz

- Falsos positivos por ruido.
- Activaciones no intencionales por terceros.
- Retrasos en deteccion en ambientes adversos.

## Mitigaciones recomendadas

- Validar reconocimiento local antes del envio automatico.
- Mantener boton de parada de emergencia accesible.
- Limitar amplitud y velocidad de movimientos comandados por voz.
- Operar inicialmente sin carga o con carga conocida.

## Criterios de puesta en marcha

- Workspace despejado.
- Home verificado.
- Conexion TCP estable.
- Operador entrenado en parada y recuperacion.
