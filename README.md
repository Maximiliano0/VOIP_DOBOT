# Dobot Magician E6 - Control por TCP y voz

<p align="center">
  <img src="project_docs/media/Magician%20E6.jpg" alt="Dobot Magician E6" width="320"/>
</p>

<p align="center">
  Integracion PC-Robot con GUI, TCP persistente y comandos por voz offline.
</p>

## Navegacion rapida

- [Indice global](INDEX.md)
- [Documentacion tecnica](project_docs/README.md)
- [Dependencias](project_docs/requirements.txt)

## Resumen

Proyecto para controlar un Dobot Magician E6 por Ethernet desde PC con dos modos principales:

- Envio manual de comandos TCP.
- Deteccion de voz de palabras clave y envio automatico al robot.

## Objetivo

Implementar una arquitectura simple, robusta y reproducible para:

- Probar movilidad y seguridad del robot (Lua).
- Exponer un servidor de comandos en el controlador (Lua).
- Controlar por GUI en PC (Python).
- Integrar reconocimiento de voz offline (Vosk) para comandos operativos.

## Estructura del proyecto

- `dobot_scripts/`
  - `01_test/`: pruebas de movilidad, homing y seguridad.
  - `02_com/tcp_cmd.lua`: servidor TCP robot-side.

- `pc_scripts/`
  - `02_com/send_cmd/send_cmd.py`: cliente TCP manual (GUI/CLI).
  - `03_ml/voice_word_gui.py`: deteccion de voz local.
  - `04_voice_cmd/voice_cmd.py`: integracion voz + envio TCP.

- `engitbook/`
  - Referencia API offline de Dobot (fuente de verdad para funciones Lua).

- `project_docs/`
  - Requisitos unificados, documentacion por grupos, teoria y evidencia.

## Dependencias de entorno

Instalar desde:

- `project_docs/requirements.txt`

Comando sugerido:

```bash
python -m pip install -r project_docs/requirements.txt
```

## Modos de uso

- `02_com`: control manual por GUI/CLI via TCP.
- `03_ml`: deteccion de voz local (sin envio a robot).
- `04_voice_cmd`: deteccion de voz + envio TCP integrado.

## Flujo rapido de uso

1. En el robot, ejecutar `dobot_scripts/02_com/tcp_cmd.lua`.
2. En el PC, iniciar una app:
   - Manual TCP: `pc_scripts/02_com/send_cmd/send_cmd.py`
   - Voz local: `pc_scripts/03_ml/voice_word_gui.py`
   - Voz + TCP: `pc_scripts/04_voice_cmd/voice_cmd.py`
3. Verificar conectividad con `ping`.
4. Operar comandos (`derecha`, `izquierda`, `arriba`, `abajo`, `home`/`origen`, `activar_ventosa`, `desactivar_ventosa`).

## Ejecutables .exe

El proyecto incluye builds en `dist/` para uso en Windows sin abrir terminal.

- `pc_scripts/03_ml/dist/voice_word_gui.exe`
- `pc_scripts/04_voice_cmd/dist/voice_cmd.exe`

## Seguridad

- Mantener E-stop accesible durante pruebas.
- Iniciar con velocidades bajas y workspace despejado.
- Validar reconocimiento de voz antes de habilitar envio automatico.

## Documentacion incluida en project_docs

- Portada de documentacion: `project_docs/README.md`
- Indice navegable: `INDEX.md`
- Documentos por grupo: `project_docs/grupos/`
- Documentos teoricos: `project_docs/teoria/`
- Evidencia multimedia: `project_docs/media/`
