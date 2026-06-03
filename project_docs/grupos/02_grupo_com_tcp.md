# Grupo 02 - Comunicacion TCP robot-PC

Este grupo implementa el puente de comandos entre PC (Python) y robot (Lua) por Ethernet/TCP.

## Objetivo

- Enviar comandos de movimiento desde el PC al robot.
- Mantener una conexion persistente para evitar reconexiones por comando.

## Aplicaciones .lua

- `dobot_scripts/02_com/tcp_cmd.lua`
  - Servidor TCP en robot (`192.168.5.1:6001` por defecto).
  - Procesa comandos de texto y responde en una linea (`ok ...`, `pong`, errores).
  - Comandos soportados: `derecha`, `izquierda`, `arriba`, `abajo`, `home`, `origen`, `abrir_gripper`, `cerrar_gripper`, `activar_ventosa`, `desactivar_ventosa`, `ping`, `salir`.
  - Alias adicionales: `suction_on` y `suction_off`.

## Aplicaciones .py

- `pc_scripts/02_com/send_cmd/send_cmd.py`
  - Cliente TCP con GUI Tkinter y modo CLI.
  - Reutiliza una sola conexion (`RobotConnection`) y reconecta si se cae.
  - Permite comandos predefinidos y personalizados.
  - Normaliza alias de operador, por ejemplo `origen -> home`.

- `pc_scripts/02_com/send_cmd/send_cmd_config.json`
  - Configuracion local para IP/puerto/timeout.

## Flujo

1. Robot ejecuta `tcp_cmd.lua`.
2. PC ejecuta `send_cmd.py`.
3. Usuario envia comando.
4. Robot ejecuta movimiento y devuelve respuesta.

## Protocolo

- Transporte: TCP.
- Formato: 1 comando por linea (`\n`).
- Respuesta: 1 linea por comando.
