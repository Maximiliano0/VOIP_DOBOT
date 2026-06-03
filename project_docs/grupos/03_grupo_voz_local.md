# Grupo 03 - Deteccion de voz local (sin envio TCP)

Este grupo implementa deteccion offline de palabras clave por microfono para pruebas de reconocimiento.

## Objetivo

- Detectar palabras: `derecha`, `izquierda`, `home`, `origen`, `arriba`, `abajo`, `activar ventosa`, `desactivar ventosa`.
- Probar calidad de reconocimiento en GUI local.

## Aplicaciones .py

- `pc_scripts/03_ml/voice_word_gui.py`
  - GUI Tkinter para iniciar/detener escucha.
  - Usa Vosk + `sounddevice` en un hilo de trabajo.
  - Incluye mapeo de alias: `origen -> home` y comandos de ventosa a comandos TCP canónicos.
  - Muestra texto parcial/final y conteo de detecciones.

- `pc_scripts/03_ml/requirements.txt`
  - Dependencias del modulo de voz.

- `pc_scripts/03_ml/model/`
  - Modelo Vosk en espanol (`vosk-model-small-es-0.42`).

## Aplicaciones .lua

- No hay scripts Lua en este grupo.

## Notas

- Este grupo no envia comandos al robot; solo valida reconocimiento.
- Es la base del grupo 04.
