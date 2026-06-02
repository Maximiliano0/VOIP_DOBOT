# Grupo 01 - Pruebas robot (dobot_scripts/01_test)

Este grupo contiene pruebas de movilidad, homing y seguridad que se ejecutan directamente en el controlador del robot (Lua en DobotStudio Pro 4.4).

## Objetivo

- Validar movimiento base del robot.
- Probar rangos de joints y verificaciones previas.
- Evaluar configuraciones de seguridad y prevencion de colisiones.

## Aplicaciones .lua

- `dobot_scripts/01_test/go_home.lua`
  - Lleva el robot a HOME con `CheckMovJ` previo.
  - Ajusta `SpeedFactor` para homing seguro.

- `dobot_scripts/01_test/mobility.lua`
  - Prueba movimiento por joint (J1..J6) y trayectorias cartesianas con `MovL`.
  - Util para validacion rapida post-instalacion.

- `dobot_scripts/01_test/max_test.lua`
  - Recorre rangos min/max por joint a alta velocidad.
  - Requiere limites reales configurados antes de ejecutar.

- `dobot_scripts/01_test/collision.lua`
  - Prueba capas de seguridad: collision level, SafeSkin, paredes virtuales y checks de alcance.
  - Incluye target intencionalmente inalcanzable para validar rechazos del planificador.

## Aplicaciones .py

- No hay scripts Python en este grupo.

## Entradas/salidas

- Entrada: ejecucion local en controlador Dobot.
- Salida: movimiento fisico del robot y logs en consola Lua.

## Riesgos operativos

- Ejecutar solo con espacio despejado.
- Mantener E-stop accesible.
- Revisar limites y parametros antes de pruebas de rango maximo.
