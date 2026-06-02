# Grupo 04 - Voz a comando TCP (integrado)

Este grupo integra reconocimiento de voz y envio TCP al robot en una sola aplicacion GUI.

## Objetivo

- Escuchar palabras clave por microfono.
- Enviar automaticamente el comando detectado al servidor Lua del robot.

## Aplicaciones .py

- `pc_scripts/04_voice_cmd/voice_cmd.py`
  - GUI integrada con:
    - Configuracion TCP (IP, puerto, timeout).
    - Configuracion Vosk (modelo, microfono, sample rate).
    - Envio automatico al detectar palabra objetivo.
    - Envio manual por botones.
  - IP por defecto: `192.168.5.1`.
  - Soporta ruta de modelo para script y para `.exe` empaquetado (PyInstaller).

- `pc_scripts/04_voice_cmd/voice_cmd_config.json`
  - Persistencia de configuracion usada por la GUI.

- `pc_scripts/04_voice_cmd/dist/voice_cmd.exe`
  - Ejecutable de escritorio sin consola negra (`--windowed`).

## Aplicaciones .lua

- Usa como contraparte `dobot_scripts/02_com/tcp_cmd.lua`.

## Flujo operativo

1. Arrancar `tcp_cmd.lua` en el robot.
2. Abrir `voice_cmd.py` o `voice_cmd.exe` en el PC.
3. Verificar `ping`.
4. Iniciar escucha.
5. Al detectar palabra, se envia por TCP y se muestra respuesta.
