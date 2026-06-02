# Teoria - Deteccion de voz con Vosk (palabras clave)

## Enfoque del proyecto

El proyecto usa reconocimiento offline con Vosk para detectar un vocabulario cerrado de comandos de control.

Palabras objetivo:

- derecha
- izquierda
- home
- arriba
- abajo

## Componentes tecnicos

- Modelo acustico + lenguaje de Vosk en espanol.
- Captura de audio por `sounddevice`.
- `KaldiRecognizer` con gramatica restringida para reducir falsos positivos.

## Ventajas del vocabulario cerrado

- Menor ambiguedad.
- Mejor robustez en entornos ruidosos moderados.
- Respuestas mas predecibles para control de robot.

## Limitaciones

- Sensible a microfono y ruido ambiente.
- No reemplaza medidas de seguridad del robot.
- No reconoce frases largas fuera de la gramatica.

## Buenas practicas

- Usar microfono direccional o cercano.
- Probar sample rate correcto (16000 Hz en este proyecto).
- Validar deteccion local antes de habilitar envio automatico al robot.
