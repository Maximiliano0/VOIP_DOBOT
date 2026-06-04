# Grupo 04 - Voz a comando TCP (integrado)

Aplicacion integrada de voz + envio TCP al robot.

## Objetivo

- Escuchar comandos por microfono.
- Enviar el comando detectado al servidor Lua.
- Mantener comportamiento de envio estable, equivalente al cliente 02.

## Script actual

- `pc_scripts/04_voice_cmd/voice_cmd.py`
  - GUI con configuracion TCP (IP, puerto, timeout).
  - GUI con configuracion de voz (modelo, microfono, sample rate).
  - Deteccion de palabras por gramatica cerrada (sin prefijo de activacion).
  - Envio automatico y envio manual por botones.
  - Envio serializado con lock de red, sin descarte por debounce.
  - Alias: `origen -> home`.
  - Ventosa: `activar ventosa`, `desactivar ventosa`, `test ventosa`.

- `pc_scripts/04_voice_cmd/voice_cmd_config.json`
  - Persistencia de configuracion de la GUI.

- `pc_scripts/04_voice_cmd/dist/voice_cmd.exe`
  - Ejecutable Windows actual.

## Contraparte robot

- `dobot_scripts/02_com/tcp_cmd.lua`

## Flujo operativo

1. Ejecutar `tcp_cmd.lua` en el robot.
2. Abrir `voice_cmd.py` o `voice_cmd.exe`.
3. Verificar conectividad (`ping`).
4. Iniciar escucha.
5. Hablar comando objetivo.
6. Revisar respuesta TCP en log de la GUI.
