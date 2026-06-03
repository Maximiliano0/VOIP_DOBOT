# Teoria - Brazo robotico, joints y movimientos

## Cinematica basica

Un manipulador de 6 GDL (grados de libertad) se puede describir en dos dominios:

- Espacio articular: vector de joints q = [q1, q2, ..., q6].
- Espacio cartesiano: pose del TCP [x, y, z, rx, ry, rz].

El mapeo entre ambos se realiza mediante cinematica directa e inversa. La inversa puede tener multiples soluciones o no tener solucion segun limites mecanicos y singularidades.

## Parametrizacion DH y transformaciones homogeneas

Una formulacion estandar para robots seriales es Denavit-Hartenberg (DH). Cada eslabon i se describe con parametros:

- a_i (longitud de eslabon)
- alpha_i (torsion)
- d_i (desplazamiento)
- theta_i (angulo articular)

La pose del TCP se obtiene por producto de transformaciones:

- T_0_n(q) = A_1 A_2 ... A_n

Esto permite pasar de coordenadas de joint-space a cartesian-space de forma sistematica.

## Cinematica diferencial y singularidades

La relacion entre velocidad articular y velocidad cartesiana se expresa con el Jacobiano J(q):

- x_dot = J(q) q_dot

Cuando J pierde rango (determinante cercano a cero en subespacios relevantes), aparecen singularidades. Operativamente esto puede implicar:

- Movimientos inestables o de gran velocidad articular para pequenas correcciones cartesianas.
- Errores de planificacion detectados por `CheckMovJ` y `CheckMovL`.

## Manipulabilidad y condicionamiento

Para evaluar cercania a singularidad se usan metricas como:

- Manipulabilidad de Yoshikawa: w(q) = sqrt(det(J J^T))
- Numero de condicion de J

En operacion practica, si w disminuye o el condicionamiento empeora, conviene:

- Reducir velocidad.
- Replanificar con `MovJ` hacia una configuracion mas estable.
- Evitar lineales largas cercanas a limites cinematicos.

## Cinematica inversa (IK) en control operativo

Para una pose cartesiana pueden existir:

- Multiples soluciones IK validas.
- Soluciones fuera de limites articulares.
- Ausencia de solucion.

Por esto, el flujo robusto incluye checks previos (`CheckMovJ`/`CheckMovL`) antes de ejecutar el movimiento.

## Tipos de movimiento usados en el proyecto

- `MovJ`: trayectoria planificada en joint-space.
- `RelJointMovJ`: desplazamiento incremental por articulacion.
- `MovL`: trayectoria lineal del TCP en cartesian-space.

Eleccion practica:

- `MovJ` suele ser mas robusto para reposicionamiento general.
- `MovL` se usa cuando importa geometria de trayectoria del efector final.

## Parametros de trayectoria

- Aceleracion y velocidad (`a`, `v`).
- `SpeedFactor` global como limite superior operativo.
- Parametro de blend/radio para continuidad entre segmentos.

Estos parametros controlan compromiso entre productividad y esfuerzo dinamico del robot.

## Verificaciones previas y seguridad de movimiento

Antes de ejecutar, el controlador evalua factibilidad:

- `CheckMovJ` para trayectorias articulares.
- `CheckMovL` para trayectorias lineales.

Estas funciones ayudan a detectar:

- Objetivos fuera del workspace.
- Configuraciones cercanas a singularidad.
- Violaciones de restricciones cinematicas.

## Aplicacion al caso VOIP_DOBOT

La capa de voz/TCP mapea comandos discretos a movimientos limitados:

- `derecha` y `izquierda`: ajustes articulares de orientacion.
- `arriba` y `abajo`: ajuste de inclinacion.
- `home` y `origen`: retorno a postura segura de referencia.
- `activar_ventosa` y `desactivar_ventosa`: accionamiento del efector final de succion (ES01).

El diseno prioriza control interpretable y repetible sobre planificacion compleja.

## Referencias (APA 7)

Craig, J. J. (2005). Introduction to robotics: Mechanics and control (3rd ed.). Pearson.

Lynch, K. M., & Park, F. C. (2017). Modern robotics: Mechanics, planning, and control. Cambridge University Press.

Siciliano, B., Sciavicco, L., Villani, L., & Oriolo, G. (2010). Robotics: Modelling, planning and control. Springer.

Spong, M. W., Hutchinson, S., & Vidyasagar, M. (2006). Robot modeling and control. Wiley.

Yoshikawa, T. (1985). Manipulability of robotic mechanisms. The International Journal of Robotics Research, 4(2), 3-9. https://doi.org/10.1177/027836498500400201
