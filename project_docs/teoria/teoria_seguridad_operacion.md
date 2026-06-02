# Teoria - Seguridad operativa en celdas roboticas

![Referencia de advertencias operativas](../../engitbook/script/images/warn.png)

## Enfoque de seguridad por capas

La operacion segura no depende de una sola barrera, sino de varias capas tecnicas y procedimentales.

Capas relevantes en este proyecto:

- Prevencion por software: `CheckMovJ` y `CheckMovL` antes de mover.
- Limites dinamicos: `SpeedFactor`, `a`, `v`, distancia de retroceso y sensibilidad de colision.
- Protecciones del controlador: collision detection, SafeSkin y zonas virtuales.
- Procedimientos humanos: validacion de entorno, E-stop accesible, checklist de arranque.

## Riesgos especificos de control por voz

- Falsos positivos por ruido impulsivo o conversaciones cercanas.
- Comandos no intencionales por terceros en el area.
- Dependencia de calidad de audio (microfono, eco, reverberacion).

## Mitigaciones tecnicas recomendadas

- Vocabulario cerrado de comandos (ya aplicado).
- Confirmacion de estado en GUI (log y ultimo comando).
- Umbrales operativos conservadores de velocidad durante comisionado.
- Priorizar comando `home` como estrategia de recuperacion.
- Posibilidad de desactivar envio automatico y operar solo en modo manual.

## Mitigaciones procedimentales

- Delimitar zona de trabajo y acceso.
- Probar primero en vacio y sin carga de riesgo.
- Definir plan de parada y recuperacion ante evento inseguro.
- Registrar incidentes y ajustar parametros de sensibilidad.

## Checklist minimo de puesta en marcha

- Espacio libre y sin obstrucciones.
- Robot en postura conocida (`home`).
- Conexion TCP verificada con `ping`.
- Prueba de deteccion de voz en local antes de habilitar envio.
- Operador con acceso inmediato a parada de emergencia.

## Nota de cumplimiento

La aplicacion de software es un componente de la estrategia de seguridad, pero no sustituye evaluacion de riesgo de celda, hardware de seguridad ni cumplimiento normativo del fabricante/integrador.

## Referencias cruzadas internas

- Fundamentos de voz y ASR: [teoria_modelo_deteccion_voz.md](teoria_modelo_deteccion_voz.md)
- Cinematica y trayectorias: [teoria_brazo_joints_movimientos.md](teoria_brazo_joints_movimientos.md)
- Arquitectura de comunicacion TCP: [teoria_tcp_y_arquitectura.md](teoria_tcp_y_arquitectura.md)

## Referencias (APA 7)

International Organization for Standardization. (2011). ISO 10218-1:2011 Robots and robotic devices - Safety requirements for industrial robots - Part 1: Robots.

International Organization for Standardization. (2011). ISO 10218-2:2011 Robots and robotic devices - Safety requirements for industrial robots - Part 2: Robot systems and integration.

International Organization for Standardization. (2016). ISO/TS 15066:2016 Robots and robotic devices - Collaborative robots.

National Institute of Standards and Technology. (2020). NISTIR 8286: Integrating cybersecurity and enterprise risk management (ERM).
