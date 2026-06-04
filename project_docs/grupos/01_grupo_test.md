# Grupo 01 - Pruebas robot (dobot_scripts/01_test)

Scripts de prueba robot-side en Lua para DobotStudio Pro 4.4.

## Objetivo

- Verificar movilidad basica y retorno seguro.
- Validar limites y chequeos de movimiento.
- Probar funciones de seguridad del controlador.

## Scripts actuales

- `dobot_scripts/01_test/go_home.lua`
  - Ejecuta homing con `CheckMovJ` previo.
  - Fuerza ventosa en OFF antes de mover.
  - Usa `SUCTION_OUTPUT_MODE` configurable (`tool_do`, `controller_do`, `both`).

- `dobot_scripts/01_test/mobility.lua`
  - Pruebas de movimiento articular y cartesiano.

- `dobot_scripts/01_test/max_test.lua`
  - Recorrido de limites de joints (usar con precaucion).

- `dobot_scripts/01_test/collision.lua`
  - Validacion de parametros de colision y seguridad.

## Entrada y salida

- Entrada: ejecucion local desde DobotStudio Pro.
- Salida: movimiento fisico y logs por consola Lua.

## Seguridad operativa

- Espacio de trabajo despejado.
- E-stop accesible.
- Velocidades conservadoras en primera prueba.
