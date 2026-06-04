# Grupo 03 - Deteccion de voz local (sin envio TCP)

Modulo de prueba de reconocimiento de voz offline en PC.

## Objetivo

- Validar calidad de deteccion por microfono.
- Probar vocabulario operativo antes de enviar al robot.

## Script actual

- `pc_scripts/03_ml/voice_word_gui.py`
  - GUI Tkinter para iniciar/detener escucha.
  - Reconocimiento offline con Vosk + `sounddevice`.
  - Gramatica cerrada de palabras objetivo.
  - Muestra texto parcial/final y conteo de detecciones.
  - Mapea texto detectado a comando canonico.

Palabras objetivo actuales:

- `derecha`, `izquierda`, `home`, `origen`, `arriba`, `abajo`
- `activar ventosa`, `desactivar ventosa`, `test ventosa`

Mapeos principales:

- `origen -> home`
- `activar ventosa -> activar_ventosa`
- `desactivar ventosa -> desactivar_ventosa`
- `test ventosa -> test_ventosa`

## Archivos asociados

- `pc_scripts/03_ml/requirements.txt`
- `pc_scripts/03_ml/model/`
- `pc_scripts/03_ml/dist/voice_word_gui.exe`

## Nota clave

Este grupo no envia comandos por TCP. Solo valida deteccion de voz y sirve como base para el grupo 04.
