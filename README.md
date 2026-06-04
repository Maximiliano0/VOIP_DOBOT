# Dobot Magician E6 - Control TCP y voz offline

<p align="center">
  <img src="project_docs/media/Magician%20E6.jpg" alt="Dobot Magician E6" width="320"/>
</p>

Proyecto para operar el Dobot Magician E6 por Ethernet desde PC, con cliente TCP manual y control por voz offline (Vosk).

## Navegacion rapida

- [Indice global](INDEX.md)
- [Documentacion tecnica](project_docs/README.md)
- [Dependencias](project_docs/requirements.txt)

## Estado actual

- Robot-side estable en `dobot_scripts/02_com/tcp_cmd.lua`.
- Cliente manual estable en `pc_scripts/02_com/send_cmd/send_cmd.py`.
- Deteccion local de voz en `pc_scripts/03_ml/voice_word_gui.py`.
- Integracion voz + TCP en `pc_scripts/04_voice_cmd/voice_cmd.py`.
- Script demostrativo pick/place en `dobot_scripts/05_pick/pick_place.lua`.

## Comandos operativos vigentes

- Movimiento: `derecha`, `izquierda`, `arriba`, `abajo`, `home`, `origen`.
- Gripper: `abrir_gripper`, `cerrar_gripper`.
- Ventosa: `activar_ventosa`, `desactivar_ventosa`, `test_ventosa`.
- Servicio: `ping`, `salir`.

Alias soportados:

- `origen -> home`
- `suction_on -> activar_ventosa`
- `suction_off -> desactivar_ventosa`
- `test_suction -> test_ventosa`

## Flujo rapido

1. En el robot, ejecutar `dobot_scripts/02_com/tcp_cmd.lua`.
2. En PC, usar una de estas apps:
   - `pc_scripts/02_com/send_cmd/send_cmd.py`
   - `pc_scripts/03_ml/voice_word_gui.py`
   - `pc_scripts/04_voice_cmd/voice_cmd.py`
3. Verificar red local (`ping 192.168.5.1`).
4. Operar desde GUI o voz.

## Ejecutables Windows (.exe)

- `pc_scripts/02_com/send_cmd/dist/send_cmd_gui.exe`
- `pc_scripts/03_ml/dist/voice_word_gui.exe`
- `pc_scripts/04_voice_cmd/dist/voice_cmd.exe`

Build recomendado: usar siempre Python de `.venv`.

## Seguridad minima

- E-stop accesible.
- Velocidad conservadora al comisionar.
- Espacio despejado.
- Validar ventosa y retorno a `home` antes de operar con pieza.

## Documentacion

- Portada tecnica: `project_docs/README.md`
- Documentos por grupo: `project_docs/grupos/`
- Teoria y fundamentos: `project_docs/teoria/`
- Evidencia: `project_docs/media/`
