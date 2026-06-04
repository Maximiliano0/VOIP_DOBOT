# Dobot Magician E6 - Documentacion tecnica del proyecto

![Brazo robotico / referencia de plataforma](../engitbook/script/images/load.png)

## Resumen

Estado actual del proyecto:

- Control robot-side en Lua para DobotStudio Pro 4.4.
- Cliente TCP manual robusto con reconexion en Python.
- Deteccion de voz offline local con Vosk.
- Integracion voz + TCP con envio directo de comandos.
- Script de demostracion pick/place en grupo 05.

## Arquitectura actual

- `dobot_scripts/01_test/`: pruebas y seguridad (homing, movilidad, colision).
- `dobot_scripts/02_com/tcp_cmd.lua`: servidor TCP del robot.
- `dobot_scripts/05_pick/pick_place.lua`: ejemplo de pick/place con `ToolDO`.
- `pc_scripts/02_com/send_cmd/send_cmd.py`: cliente TCP manual GUI/CLI.
- `pc_scripts/03_ml/voice_word_gui.py`: voz local (sin envio TCP).
- `pc_scripts/04_voice_cmd/voice_cmd.py`: voz con envio TCP integrado.
- `engitbook/`: referencia API Lua (solo lectura).

## Comandos vigentes

- Movimiento: `derecha`, `izquierda`, `arriba`, `abajo`, `home`, `origen`.
- Gripper: `abrir_gripper`, `cerrar_gripper`.
- Ventosa: `activar_ventosa`, `desactivar_ventosa`, `test_ventosa`.
- Servicio: `ping`, `salir`.

Alias:

- `origen -> home`
- `suction_on -> activar_ventosa`
- `suction_off -> desactivar_ventosa`
- `test_suction -> test_ventosa`

## Entorno y build

Dependencias generales en `project_docs/requirements.txt`.

Usar siempre Python de `.venv` para build de ejecutables.

Ejecutables actuales:

- `pc_scripts/02_com/send_cmd/dist/send_cmd_gui.exe`
- `pc_scripts/03_ml/dist/voice_word_gui.exe`
- `pc_scripts/04_voice_cmd/dist/voice_cmd.exe`

## Flujo operativo recomendado

1. Ejecutar `dobot_scripts/02_com/tcp_cmd.lua` en el robot.
2. Verificar conectividad con `ping 192.168.5.1`.
3. Abrir `send_cmd.py` o `voice_cmd.py` en PC.
4. Para voz, validar primero en `voice_word_gui.py`.
5. Probar `test_ventosa` antes de operacion con pieza.

## Navegacion

- [Indice global](../INDEX.md)
- [Grupo 01 - Pruebas robot](grupos/01_grupo_test.md)
- [Grupo 02 - Comunicacion TCP](grupos/02_grupo_com_tcp.md)
- [Grupo 03 - Voz local](grupos/03_grupo_voz_local.md)
- [Grupo 04 - Voz + TCP](grupos/04_grupo_voz_tcp.md)
- [Grupo 05 - Pick and place](grupos/05_grupo_pick.md)
- [Teoria - Voz](teoria/teoria_modelo_deteccion_voz.md)
- [Teoria - Movimiento](teoria/teoria_brazo_joints_movimientos.md)
- [Teoria - TCP](teoria/teoria_tcp_y_arquitectura.md)
- [Teoria - Seguridad](teoria/teoria_seguridad_operacion.md)

## Seguridad minima

- E-stop accesible.
- Velocidades conservadoras en pruebas.
- Zona despejada.
- Verificar estado seguro de ventosa y HOME antes de operar.
