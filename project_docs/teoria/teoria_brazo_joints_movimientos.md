# Teoria - Brazo robotico, joints y movimientos

## Cinematica basica

Un robot articulado de 6 ejes se controla en dos espacios:

- Espacio articular (joints): angulos de J1..J6.
- Espacio cartesiano: pose del TCP (x, y, z, rx, ry, rz).

## Tipos de movimiento usados

- `MovJ`: interpola en espacio articular.
- `RelJointMovJ`: desplazamiento relativo por joints.
- `MovL`: movimiento lineal del TCP en espacio cartesiano.

## Parametros de trayectoria

- Aceleracion y velocidad (`a`, `v`).
- SpeedFactor global.
- Blend/radio para continuidad en trayectorias lineales.

## Verificaciones previas

Antes de ejecutar trayectorias, se usan checks para evitar movimientos invalidos:

- `CheckMovJ`
- `CheckMovL`

Estos checks ayudan a detectar singularidades, limites de alcance y errores de trayectoria.

## Aplicacion al proyecto

- Comandos de voz y TCP mapean a acciones de joints sencillas (`arriba`, `abajo`, `derecha`, `izquierda`) y `home`.
- Se prioriza claridad operacional sobre complejidad de planeamiento.
