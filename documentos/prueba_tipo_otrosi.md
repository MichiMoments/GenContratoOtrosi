# Prueba manual del generador de tipos de otrosí

Prueba corta que cubre los 5 tipos de campo, los 3 filtros y las frases derivadas,
con tabla, viñetas y negrita en el cuerpo.

Usa **Contratista** a propósito: es el caso donde el sustantivo **no cambia** entre
femenino y masculino y lo único que cambia es el artículo («la Contratista» / «el
Contratista», «a la Contratista» / «al Contratista»). Si la concordancia se resuelve
bien aquí, se resuelve en cualquier parte.

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
| genero_prueba | Género de prueba | **lista** | ✓ | Femenino; Masculino | Femenino |

Deja el resto de columnas (Ayuda, Grupo, Sugerencias, No futura, Posterior a,
Artículo minúscula, La rellena la app) en blanco o sin marcar.

> **Ya no existe un tipo «genero».** El género es un campo de **lista** con dos
> opciones que arrastra frases; así es como se puede tener «Contratista» en un tipo y
> «Teletrabajador» en otro.

## 3. Genera las frases derivadas

Baja a **«Frases derivadas»**. Bajo «Género de prueba» hay dos cuadros y un botón.
Escribe:

| Sustantivo en femenino | Sustantivo en masculino |
|---|---|
| Contratista | Contratista |

y pulsa **«Generar y reemplazar»**. La tabla tiene que quedar exactamente así:

| Marcador | Si es «Femenino» | Si es «Masculino» |
|---|---|---|
| contratista | la Contratista | el Contratista |
| al_contratista | a la Contratista | al Contratista |
| del_contratista | de la Contratista | del Contratista |
| identificado | identificada | identificado |
| de_la_misma | de la misma | del mismo |

Fíjate en lo que hizo el botón y que a mano es fácil equivocar: **`a` + `el` da `al`
y `de` + `el` da `del`**, pero en femenino se quedan como `a la` y `de la`. El nombre
de los tres primeros marcadores sale del sustantivo masculino.

A «Ciudad de prueba» déjale la tabla de frases **vacía**: un campo de lista no está
obligado a tener ninguna.

> Puedes escribir las filas a mano en vez de usar el botón, o añadir las tuyas. A
> partir de aquí son datos: si las editas, **las contracciones quedan de tu cuenta**.
> El revisor comprueba que el marcador exista, que cubra las dos opciones y que no
> lleve `|` ni `**`, pero **no comprueba la gramática**.

## 4. Pega esto en «Cuerpo del otrosí»

```
Este documento de prueba certifica que **{{nombre}}**, {{identificado}} con documento No. {{documento}}, de {{edad}} años, actúa en calidad de {{contratista}}, residente en {{ciudad}}, a partir del {{fecha_prueba}}.

**Cláusula de prueba:** Se registran las condiciones {{del_contratista}} y el compromiso {{de_la_misma}}.

| Campo | Valor |
|---|---|
| Ciudad | {{ciudad:minusculas}} |
| Edad | {{edad}} |

- Primera condición asignada {{al_contratista}}.
- Segunda condición de prueba, sin marcadores.

Para constancia firma el documento **{{nombre:mayusculas}}**. {{contratista:mayuscula}} certifica la veracidad de estos datos.
```

## 5. Qué debería pasar

- **0 errores y 0 avisos** debajo del editor.
- La previsualización muestra la tabla, la negrita, la viñeta y las cinco frases ya
  resueltas. Con el ejemplo «Femenino» debe decir **«actúa en calidad de la
  Contratista»** y **«condición asignada a la Contratista»**.
- En «Un otrosí», elige **Masculino** y genera. El `.docx` tiene que decir «el
  Contratista», «al Contratista» y «de**l** Contratista» — si en algún sitio aparece
  «de el Contratista» o «a el Contratista», la contracción está mal.
- El archivo se llama `prueba_ana_perez_20260810.docx`.
- En «Carga masiva», la plantilla de Excel trae un desplegable para «Ciudad de
  prueba» y otro para «Género de prueba», en columnas distintas de la hoja
  `Instrucciones`.

### Las dos ramas, para comparar

| | Femenino | Masculino |
|---|---|---|
| `{{identificado}}` | identificada | identificado |
| `{{contratista}}` | la Contratista | el Contratista |
| `{{al_contratista}}` | a la Contratista | al Contratista |
| `{{del_contratista}}` | de la Contratista | del Contratista |
| `{{de_la_misma}}` | de la misma | del mismo |
| `{{contratista:mayuscula}}` | La Contratista | El Contratista |

## Qué cubre cada pieza

| Elemento | Dónde se prueba |
|---|---|
| `texto` | `nombre` |
| `cedula` | `documento` (se imprime `1.020.345.678`) |
| `entero` | `edad` (se imprime `34`, sin puntos) |
| `fecha` | `fecha_prueba` (se imprime «10 de agosto de 2026») |
| `lista` sin frases | `ciudad` |
| `lista` con frases | `genero_prueba` (marcadores `contratista`, `al_contratista`, `del_contratista`, `identificado`, `de_la_misma`) |
| Contracción `a`+`el` y `de`+`el` | `{{al_contratista}}` y `{{del_contratista}}` en masculino |
| Sustantivo invariable | «Contratista» en las dos ramas: cambia el artículo, no el nombre |
| Filtro `:mayusculas` | `{{nombre:mayusculas}}` |
| Filtro `:minusculas` | `{{ciudad:minusculas}}` |
| Filtro `:mayuscula` | `{{contratista:mayuscula}}` |
| Negrita, tabla, viñetas | cuerpo del §4 |

## Variante: dos roles con género en el mismo documento

Si quieres comprobar que las concordancias no se mezclan, añade **otro** campo de
lista `genero_interventor` con las mismas dos opciones y genera sus frases con
`Interventora` / `Interventor`. Tendrás `{{interventor}}`, `{{al_interventor}}` y
`{{del_interventor}}` además de los de contratista.

Ojo con una colisión que el revisor **sí** atrapa: el generador escribe
`identificado` y `de_la_misma` para los dos campos, y un marcador solo puede venir de
un sitio. Bórralos de la tabla del segundo campo, o renómbralos
(`identificado_interventor`).
