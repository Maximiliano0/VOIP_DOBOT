# Teoria - Deteccion de voz con Vosk (palabras clave)

## Enfoque del proyecto

El sistema usa reconocimiento automatico de voz offline con Vosk para detectar un vocabulario cerrado orientado a control del robot.

Palabras objetivo:

- derecha
- izquierda
- home
- origen
- arriba
- abajo
- activar ventosa
- desactivar ventosa

Este enfoque reduce ambiguedad semantica y limita acciones posibles, lo cual es deseable para tareas de mando operativo.

## Que modelo usa Vosk en este proyecto

El proyecto usa `vosk-model-small-es-0.42` (espanol), que internamente corresponde a un pipeline Kaldi con:

- Modelo acustico tipo chain/nnet3 TDNN (se observa en el README del modelo y rutas `exp/chain/tdnn/...`).
- Front-end de caracteristicas basado en MFCC.
- Normalizacion de caracteristicas (CMVN), visible en archivos de `ivector/global_cmvn.stats`.
- Extraccion de informacion de hablante por i-vectors (`ivector/final.ie`, `final.mat`, `final.dubm`).
- Grafo de decodificacion WFST (`graph/HCLr.fst`, `graph/Gr.fst`).

## Tecnicas involucradas

### MFCC

Los Mel-Frequency Cepstral Coefficients transforman la senal de audio en descriptores compactos que aproximan la percepcion auditiva humana en banda mel. En ASR clasico, MFCC sigue siendo una representacion estandar por su robustez y costo computacional moderado.

### HMM + DNN (hibrido)

El decodificador de Kaldi combina modelado temporal probabilistico (HMM) con redes neuronales profundas (DNN/TDNN) para estimar probabilidades acusticas por estado fonetico.

### i-vectors

i-vectors modelan variabilidad de canal y hablante en un espacio de baja dimension, mejorando adaptacion del reconocimiento en condiciones reales.

### WFST

La decodificacion por transductores de estados finitos ponderados (WFST) integra modelo acustico, lexico y lenguaje en una sola estructura eficiente de busqueda.

## Gramatica cerrada en la aplicacion

La app usa `KaldiRecognizer(model, rate, grammar_json)` para restringir busqueda a las palabras objetivo. Practicamente esto:

- Disminuye falsos positivos.
- Reduce latencia de decision.
- Mejora estabilidad del comando en entornos ruidosos moderados.

## Flujo de inferencia en este proyecto

1. Captura de audio en tiempo real (`sounddevice`, 16 kHz, mono).
2. Extraccion de caracteristicas (MFCC + normalizacion).
3. Estimacion acustica con red TDNN chain (Kaldi).
4. Decodificacion WFST con restriccion de gramatica.
5. Emision de palabra final y activacion de comando.

## Criterios de calidad recomendados

- Medir tasa de falsos positivos por hora en entorno real.
- Medir latencia voz-a-comando (objetivo practico: < 500 ms en LAN).
- Registrar confusiones entre pares de palabras similares y ajustar microfono/umbral operativo.

## Ventajas y limites en control de robot

Ventajas:

- Funcionamiento offline (sin nube ni latencia de red externa).
- Reproducibilidad en planta/LAN aislada.
- Mayor control de seguridad al limitar vocabulario.

Limitaciones:

- Sensible a distancia del microfono y ruido impulsivo.
- Puede confundir palabras foneticamente cercanas si el audio es deficiente.
- No sustituye enclavamientos de seguridad fisica y logica.

## Recomendaciones practicas

- Mantener sample rate de 16 kHz (coherente con el modelo small-es).
- Usar microfono cercano y consistente.
- Validar primero en modo local (03_ml) y luego habilitar envio al robot (04_voice_cmd).
- Mantener comando `home`/`origen` disponible como accion de recuperacion operativa.

## Referencias (APA 7)

Davis, S. B., & Mermelstein, P. (1980). Comparison of parametric representations for monosyllabic word recognition in continuously spoken sentences. IEEE Transactions on Acoustics, Speech, and Signal Processing, 28(4), 357-366. https://doi.org/10.1109/TASSP.1980.1163420

Dehak, N., Kenny, P. J., Dehak, R., Dumouchel, P., & Ouellet, P. (2011). Front-end factor analysis for speaker verification. IEEE Transactions on Audio, Speech, and Language Processing, 19(4), 788-798. https://doi.org/10.1109/TASL.2010.2064307

Povey, D., Ghoshal, A., Boulianne, G., Burget, L., Glembek, O., Goel, N., Hannemann, M., Motlicek, P., Qian, Y., Schwarz, P., Silovsky, J., Stemmer, G., & Vesely, K. (2011). The Kaldi speech recognition toolkit. In IEEE 2011 Workshop on Automatic Speech Recognition and Understanding.

Rabiner, L. R. (1989). A tutorial on hidden Markov models and selected applications in speech recognition. Proceedings of the IEEE, 77(2), 257-286. https://doi.org/10.1109/5.18626

Vosk API. (n.d.). Vosk speech recognition toolkit. https://alphacephei.com/vosk/
