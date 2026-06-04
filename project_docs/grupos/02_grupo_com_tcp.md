# Grupo 02 - Comunicacion TCP robot-PC

Puente principal entre PC (Python) y robot (Lua) por Ethernet/TCP.

## Objetivo

- Enviar comandos operativos al robot en tiempo real.
- Mantener conexion persistente y reconectar cuando sea necesario.

## Scripts actuales

- `dobot_scripts/02_com/tcp_cmd.lua`
  - Servidor TCP robot-side (`192.168.5.1:6001` por defecto).
  - Acepta un cliente, detecta desconexion y reabre listener.
  - Responde siempre 1 linea por comando.
  - Comandos:
    - Movimiento: `derecha`, `izquierda`, `arriba`, `abajo`, `home`, `origen`
    - Gripper: `abrir_gripper`, `cerrar_gripper`
    - Ventosa: `activar_ventosa`, `desactivar_ventosa`, `test_ventosa`
    - Servicio: `ping`, `salir`
  - Alias: `suction_on`, `suction_off`, `test_suction`, `exit`.
  - Ventosa configurable por `SUCTION_OUTPUT_MODE`.

- `pc_scripts/02_com/send_cmd/send_cmd.py`
  - GUI Tkinter + modo CLI.
  - Envio con reconexion automatica en `RobotConnection`.
  - Normaliza alias de operador y ventosa.

- `pc_scripts/02_com/send_cmd/send_cmd_config.json`
  - Config local de IP, puerto y timeout.

## Protocolo de aplicacion

- Transporte: TCP.
- Codificacion: UTF-8.
- Formato: 1 comando por linea terminada en `\n`.
- Respuesta: 1 linea por comando (`ok ...`, `pong`, `err ...`, `bye`).

## Flujo recomendado

1. Ejecutar `tcp_cmd.lua` en el robot.
2. Abrir `send_cmd.py` o `send_cmd_gui.exe` en PC.
3. Probar `ping`.
4. Operar comandos de movimiento/ventosa.
