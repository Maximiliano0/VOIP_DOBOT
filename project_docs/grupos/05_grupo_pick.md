# Grupo 05 - Pick and place basico

Este grupo contiene un ejemplo robot-side de secuencia pick/place en Lua.

## Objetivo

- Demostrar una secuencia minima de toma y deposito.
- Validar uso de puntos ensenados y ventosa de herramienta.

## Script actual

- `dobot_scripts/05_pick/pick_place.lua`
  - Requiere puntos ensenados en DobotStudio:
    - `P1` (HOME)
    - `P2` (PICK)
    - `P3` (PLACE)
  - Flujo implementado:
    1. `MovJ(P1)`
    2. `MovJ(P2)`
    3. `ToolDO(1, ON)`
    4. `MovJ(P3)`
    5. `ToolDO(1, OFF)`
    6. `MovJ(P1)`
  - Usa `SpeedFactor(40)` para operar en modo conservador.

## Requisitos

- Script ejecutado como main thread (cabecera Lua incluida en archivo).
- Puntos `P1`, `P2`, `P3` correctamente ensenados.
- Conexion y estado seguro del efector final.

## Nota de seguridad

Ejecutar con zona despejada y E-stop accesible, especialmente en la primera corrida despues de ensenar puntos.
