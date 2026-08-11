# Prueba manual del generador de tipos de otrosí

Prueba corta que cubre los 6 tipos de campo, los 3 filtros y los 5 marcadores
de concordancia, con tabla, viñetas y negrita en el cuerpo.

## 1. Crea un tipo nuevo

Pestaña «Tipos de otrosí» → «Nuevo tipo, vacío». Rellena:

| Campo del editor | Valor de prueba |
|---|---|
| Nombre del tipo | Prueba de plantilla |
| Título del encabezado | DOCUMENTO DE PRUEBA |
| Prefijo del nombre de archivo | prueba |

## 2. Llena la tabla «Campos»

La primera fila ya viene vacía; usa el botón **+** para agregar las otras cinco.

| Clave | Etiqueta | Tipo | Obligatorio | Opciones | Ejemplo |
|---|---|---|---|---|---|
| nombre | Nombre de prueba | texto | ✓ | | Ana Pérez |
| documento | Documento de prueba | cedula | ✓ | | 1020345678 |
| edad | Edad de prueba | entero | ✓ | | 34 |
| fecha_prueba | Fecha de prueba | fecha | ✓ | | 2026-08-10 |
| ciudad | Ciudad de prueba | lista | ✓ | Bogotá; Medellín | Bogotá |
| genero_prueba | Género de prueba | genero | ✓ | *(déjalo vacío: se rellena solo)* | Femenino |

Deja el resto de columnas (Ayuda, Grupo, Sugerencias, No futura, Posterior a,
Artículo minúscula, La rellena la app) en blanco o sin marcar.

## 3. Pega esto en «Cuerpo del otrosí»

```
Este documento de prueba certifica que **{{nombre}}**, {{identificado}} con documento No. {{documento}}, de {{edad}} años, actúa en calidad de {{teletrabajador}}, residente en {{ciudad}}, a partir del {{fecha_prueba}}.

**Cláusula de prueba:** Se registran las condiciones {{del_teletrabajador}} y el compromiso {{de_la_misma}}.

| Campo | Valor |
|---|---|
| Ciudad | {{ciudad:minusculas}} |
| Edad | {{edad}} |

- Primera condición asignada {{al_teletrabajador}}.
- Segunda condición de prueba, sin marcadores.

Para constancia firma el documento **{{nombre:mayusculas}}**. {{teletrabajador:mayuscula}} certifica la veracidad de estos datos.
```

## 4. Qué debería pasar

- **0 errores y 0 avisos** debajo del editor.
- La previsualización muestra la tabla, la negrita, la viñeta y las cinco
  frases de concordancia ya resueltas.
- En «Un otrosí», generar produce un `.docx` con: negrita, tabla con bordes,
  dos viñetas, la cédula con puntos, la fecha en letras, la ciudad en
  minúsculas dentro de la tabla y en mayúsculas fuera de ella, y la
  concordancia de género correcta.
- En «Carga masiva», la plantilla de Excel trae un desplegable para «Ciudad
  de prueba» y otro para «Género de prueba».

## Qué cubre cada pieza

| Elemento | Dónde se prueba |
|---|---|
| `texto` | `nombre` |
| `cedula` | `documento` |
| `entero` | `edad` |
| `fecha` | `fecha_prueba` |
| `lista` | `ciudad` |
| `genero` | `genero_prueba` (marcadores `identificado`, `teletrabajador`, `al_teletrabajador`, `del_teletrabajador`, `de_la_misma`) |
| Filtro `:mayusculas` | `{{nombre:mayusculas}}` |
| Filtro `:minusculas` | `{{ciudad:minusculas}}` |
| Filtro `:mayuscula` | `{{teletrabajador:mayuscula}}` |
| Negrita, tabla, viñetas | cuerpo de arriba |
