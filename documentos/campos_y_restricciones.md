# Campos de un otrosí: tipos, longitudes y restricciones

Guía para quien **diligencia** un otrosí en la aplicación y para quien **define un
tipo nuevo** desde la pestaña «Tipos de otrosí».

La app no genera un solo documento: genera los **tipos de otrosí** que estén
definidos. Cada tipo son sus campos y el texto del documento, con los datos que
cambian de persona a persona marcados entre llaves. Por eso esta guía tiene dos
mitades:

- **[§1](#1-los-seis-tipos-de-campo) a [§7](#7-por-qué-existe-cada-restricción)** —
  lo que vale para cualquier tipo: qué acepta cada tipo de campo, qué caracteres
  están prohibidos, cómo se escriben las fechas.
- **[§8](#8-cómo-se-escribe-el-cuerpo-de-un-tipo)** — cómo escribir el texto de un
  tipo nuevo, y qué avisa el revisor.
- **[§9](#9-el-tipo-integrado-otrosí-de-teletrabajo-híbrido)** — los 14 campos del
  otrosí de teletrabajo híbrido, como ejemplo concreto y como referencia.

**Dos palabras que se usan todo el tiempo:**

| | Qué significa |
|---|---|
| **Error** | Bloquea. En el formulario no se genera el `.docx`; en la carga masiva **se bloquea el lote completo**, no solo esa fila. Se listan todos a la vez para corregirlos de una pasada. |
| **Aviso** | No bloquea. Es algo que casi siempre es un error de digitación, pero que también puede ser correcto, así que lo decide una persona. |

Los encabezados de la hoja de Excel **son** las etiquetas de los campos, verbatim.
La tabla «Campo / Obligatorio / Tipo / Valores permitidos / Ejemplo» de la hoja
`Instrucciones` **se genera desde el tipo**, así que no puede desincronizarse; esta
guía se escribe a mano y sí puede, ojo con eso.

---

## 1. Los seis tipos de campo

El tipo de un campo decide **tres cosas a la vez**: el widget del formulario, cómo
se lee la celda de Excel y **cómo se imprime en el documento**. Por eso al escribir
el cuerpo no hace falta indicar formatos: `{{fecha_ingreso}}` sale «3 de agosto de
2026» porque ese campo es de tipo fecha.

| Tipo | En el formulario | En el Excel | Cómo se imprime |
|---|---|---|---|
| **Texto** | Cuadro de texto, o desplegable que acepta escribir otra cosa si el campo trae sugerencias | Texto | tal cual |
| **Cédula** | Cuadro numérico, solo enteros, mínimo 1 | Celda numérica, o texto de solo dígitos (se admiten `.` `,` `'` `-` y espacios como separadores) | con puntos de mil: `1.020.345.678` |
| **Número entero** | Igual que la cédula | Igual que la cédula | sin puntos: `1020345678` |
| **Fecha** | Calendario, del 01/01/1970 al 31/12/2100 | Celda con **formato de fecha**; como texto, solo `AAAA-MM-DD` | en largo: «3 de agosto de 2026» |
| **Lista** | Botones si hay hasta 4 opciones, desplegable si hay más | Desplegable con las opciones del campo | la opción elegida, tal cual |
| **Género** | Dos botones: Femenino / Masculino | Desplegable `Femenino` / `Masculino` | **no se imprime solo**: decide la concordancia de todo el documento, ver [§6](#6-el-campo-de-género) |

Antes de validar nada, los campos de **texto** se limpian solos: se unifican los
espacios raros (incluido el espacio duro que deja copiar de una página web), se
borran los caracteres invisibles de ancho cero, se colapsan los espacios repetidos
en uno y se quitan los de los extremos. Eso no se avisa: no cambia el dato.

### Banderas que puede llevar un campo

Se marcan al definir el tipo y son opcionales:

| Bandera | Qué hace |
|---|---|
| **Obligatorio** | Si está vacío, no se genera el documento. Por defecto sí. |
| **No futura** | Rechaza (error) una fecha posterior a hoy. En el formulario el calendario ni deja elegirla. |
| **Posterior a** | Avisa si esta fecha es anterior a otra que se le indique. |
| **Artículo minúscula** | Avisa si el texto empieza por `La `, `El `, `Los ` o `Las `. Ver [§5](#5-los-campos-que-abren-un-renglón). |
| **La rellena la app** | El campo puede ir en blanco: en el Excel lo rellena el selector del lote, y en el formulario viene con la fecha de hoy. |
| **Sugerencias** | Atajos de un desplegable que **igual acepta escribir cualquier otra cosa**. No es una restricción. |

---

## 2. Las longitudes: nadie las valida

**Hoy nada en el programa rechaza un valor por ser largo**, ni en el formulario ni
en la carga masiva. Tampoco hay un límite para el cuerpo de un tipo. Lo único que
pasa si te pasas es que el texto ocupa más renglones y puede mover el salto de
página.

Los números de más abajo son **mi criterio a partir del ancho real de cada sitio
del documento**, no una norma institucional. La aritmética, a la vista.

**Cuántos caracteres caben en un renglón.** El avance medio de Calibri 11 pt es de
**4,65 pt por carácter** (negrita 4,74), medido sobre 8 cadenas realistas en
español — direcciones bogotanas, nombres completos, cargos institucionales — con
una dispersión estrecha, de 4,53 a 4,76. Las celdas de tabla tienen 108 twips
(0,075") de margen interno a cada lado.

| Sitio | Ancho | Ancho útil | Caracteres por renglón |
|---|---|---|---|
| Celda de una tabla de dos columnas | 3,9" | 3,75" = 270 pt | **58** |
| Celda de una tabla sin bordes (firmas) | 3,25" | 3,10" = 223 pt | **48** (47 en negrita) |
| Párrafo normal | 6,5" | 6,5" = 468 pt | **101** |
| Párrafo con sangría de 0,25" | 6,25" | 450 pt | **97** |
| Párrafo con sangría de 0,5" | 6,0" | 432 pt | **93** |

**Son estimaciones**, aunque el avance esté medido: Word aplica su propio kerning
y justificación, y corta por palabra, así que el renglón real nunca se llena del
todo. Cuenta con un 10 % menos.

En un **párrafo** el texto fluye y pasarse no cuesta nada. En una **celda de tabla**
pasarse hace crecer la fila y mueve el salto de página: ahí es donde el largo
importa de verdad.

**El nombre del archivo.** Se arma como el prefijo del tipo + el nombre sin tildes
+ `_AAAAMMDD.docx`. Para el tipo integrado eso son **33 caracteres fijos** más el
nombre; con un nombre de 120 el archivo queda en 153, y el límite de Windows por
cada tramo de la ruta es 255. Verificado: **el programa no recorta**, un nombre de
300 caracteres produce un archivo de 333.

**Los dígitos de la cédula.** Lo habitual son 8 o 10, que son los dos ejemplos que
hay en este proyecto (`52.832.252` y `1.020.345.678`). **No consulté ninguna fuente
legal** y no afirmo que exista un máximo. Lo único que el programa exige es que sea
un número entero mayor que cero; **no cuenta los dígitos**.

---

## 3. Caracteres que no se pueden usar

Estos sí son errores de verdad, en los dos modos, y bloquean.

| No uses | En qué campos | Qué pasaría si se dejara pasar |
|---|---|---|
| `\|` (barra vertical) | los de texto | El documento se arma con tablas de Markdown, donde `\|` separa columnas. `Calle 1 \| Apto 2` genera una celda de más, y **`Apto 2` desaparece del documento sin ningún error**. |
| `**` (dos asteriscos) | los de texto | Es la marca de negrita. `Ana **Bea** Ruiz` sale con la negrita invertida y sin los asteriscos; en número impar, los asteriscos se imprimen tal cual en el contrato. |
| `-` o `\|` **al principio** del campo | los de texto | Convierte el resto de la frase del contrato en una viñeta o en una tabla. Ver [§5](#5-los-campos-que-abren-un-renglón). |
| Caracteres de control | los de texto | Word no los admite y el `.docx` fallaría al guardarse. Se rechazan en la carga para que el error salga antes y no a mitad del lote. |

Las **opciones de un campo de lista** tampoco pueden llevar `|` ni `**`: eso se
rechaza al guardar el tipo, no al diligenciar.

**Salto de línea dentro de una celda (Alt+Enter): aviso, no error.** Es
frecuentísimo en direcciones. El salto se une en un solo renglón
(`Calle 1 # 2-3` + Alt+Enter + `Apto 401` → `Calle 1 # 2-3 Apto 401`), que es lo
que se quería decir, y la fila queda marcada con un aviso para que lo confirmes.
No bloquea el lote. Si se dejara pasar sin unir, **partiría la tabla del documento
en dos**.

**Sí puedes usar** tildes, `ñ`, `Ñ`, `#`, `-`, `.`, `,`, `°`, `/`, `(`, `)`, `&`,
`'`, `"` y números. Nada de eso rompe el documento.

---

## 4. Las fechas: escríbelas como fecha, no como texto

**En el formulario** no hay nada que pensar: los campos de fecha son un
**calendario**. Haces clic y eliges el día. Se muestra como `DD/MM/YYYY`, pero lo
que se guarda es una fecha de verdad, así que ahí no te puedes equivocar de formato.

**En el Excel**, las columnas de fecha de la plantilla **ya vienen con formato de
fecha puesto**. En el caso normal solo escribes `15/01/2020` y listo.

✅ Una celda con formato de fecha, escrita como `15/01/2020`
✅ Texto `2020-01-15` (año-mes-día)
❌ Texto `15/01/2020` · ❌ Texto `03/04/2026` · ❌ el número `45000` en una celda sin formato de fecha

### Cómo saber si la celda quedó como fecha o como texto

El problema solo aparece si esa columna se volvió texto: porque alguien le cambió
el formato, o porque pegaste datos de otro sistema. Se ve de un vistazo, **por la
alineación**: Excel pega los números y las fechas a la derecha, y el texto a la
izquierda.

| Cómo se ve en la celda | Qué es | ¿Sirve? |
|---|---|---|
| pegada a la **derecha** | fecha de verdad | ✅ |
| pegada a la **izquierda** | texto | ❌ se rechaza |

Si te quedó a la izquierda: selecciona la columna, ponle formato de **Fecha** y
**vuelve a escribir el dato**. Cambiar el formato no convierte solo lo que ya
estaba escrito como texto: sigue siendo texto hasta que lo reescribes.

Y si quieres una forma que funciona **siempre**, sin fijarte en el formato de la
celda: escribe la fecha al revés, `2020-01-15`, en orden **año-mes-día**. Eso se
acepta incluso como texto, porque solo tiene una lectura posible.

Suena exagerado, pero es la restricción más importante de la plantilla:
**`03/04/2026` puede ser el 3 de abril o el 4 de marzo, y las dos lecturas son
válidas.** No hay forma de saber cuál quisiste, y adivinar significa imprimir una
fecha equivocada en un contrato firmado sin que nadie se dé cuenta. Así que se
rechaza y te lo pide de nuevo.

En cambio, si la celda tiene formato de fecha, Excel ya decidió qué día es y no
queda nada que interpretar.

La **vista previa** es la red de seguridad: muestra «3 de abril de 2026» en letras,
donde un día y un mes al revés salta a la vista.

---

## 5. Los campos que abren un renglón

Si un campo cae **al principio de un renglón** del cuerpo, un `-` o un `|` iniciales
no ensucian el texto: **rompen la estructura del documento**. El `-` convierte el
resto de la frase del contrato en una viñeta; el `|` la convierte en una tabla de
una celda con bordes.

Por eso ningún campo de texto puede empezar por `-` ni por `|`, en ningún tipo. Y
por eso, al guardar un tipo, el revisor **avisa de cada marcador que abre un
renglón**: son los sitios delicados de la plantilla.

### Los campos con artículo

Un campo marcado como «artículo minúscula» se imprime **tal cual, a mitad de
frase**, así que tiene que traer su propio artículo en minúscula:

✅ `la Dirección de Gestión Humana y Desarrollo Organizacional`
❌ `Dirección de Gestión Humana y Desarrollo Organizacional`
❌ `La Dirección de Gestión Humana y Desarrollo Organizacional`

Sin artículo sale «se desempeña como Analista en Dirección de Gestión Humana», que
no es español. Con mayúscula sale «en La Dirección de…» a mitad de oración.

La plantilla no puede poner el artículo por ti porque depende del sustantivo que
escribas: **la** Dirección, **el** Departamento, **la** Vicerrectoría, **los**
Servicios.

Si empieza por `La `, `El `, `Los ` o `Las ` en mayúscula sale un **aviso**: casi
siempre es la autocorrección de Excel, que capitaliza la primera letra de cada
celda. Es aviso y no corrección automática porque esto es un documento legal y el
programa no reescribe texto legal en silencio.

---

## 6. El campo de género

Un tipo puede tener **un** campo de género, y es el de más impacto de todos: no se
imprime por sí mismo, sino que decide cinco frases que se pueden usar cuantas veces
haga falta en el cuerpo.

| Marcador | Femenino | Masculino |
|---|---|---|
| `{{identificado}}` | identificada | identificado |
| `{{teletrabajador}}` | la Teletrabajadora | el Teletrabajador |
| `{{al_teletrabajador}}` | a la Teletrabajadora | al Teletrabajador |
| `{{del_teletrabajador}}` | de la Teletrabajadora | del Teletrabajador |
| `{{de_la_misma}}` | de la misma | del mismo |

Son **frases completas y no solo el sustantivo** porque el castellano contrae
`a`+`el` y `de`+`el`: «de {el Teletrabajador}» daría «de el». Y son **fijas**: no se
pueden renombrar ni añadir otras desde la web.

En el tipo integrado esto son **32 sustituciones** a lo largo del documento.
Equivocar el género no produce una errata: produce un documento entero mal
concordado.

En el Excel se escribe con palabras y no con `VERDADERO`/`FALSO` porque quien llena
la fila debe leer lo que va a salir impreso. Un `VERDADERO` en esa columna se
rechaza y te remite al desplegable.

**Si pegas datos, Excel borra el desplegable.** Por eso al leer se aceptan también
`F`, `fem`, `femenina`, `mujer`, `M`, `masc`, `masculina` y `hombre`, sin importar
mayúsculas ni tildes: la plantilla previene, la lectura perdona lo que tiene una
sola interpretación posible.

---

## 7. Por qué existe cada restricción

La estrictez vive en tres capas, a propósito:

1. **La plantilla de Excel previene** — formato de fecha en las columnas de fecha,
   formato de número en las de cédula, desplegables en las de lista y de género.
2. **La lectura rechaza y nunca adivina** — si un dato admite dos lecturas, se
   devuelve el error en vez de elegir una.
3. **La vista previa confirma** — muestra los valores ya convertidos a como saldrán
   impresos, que es donde una persona detecta lo que ninguna validación puede.

Lo que no puede ser la capa de validación son los filtros que arman el documento:
son tolerantes **a propósito**, para poder recibir datos de cualquier origen. El
que formatea la cédula acepta `52.832.252` con puntos; si le llega basura, devuelve
algo con forma de cédula en vez de quejarse. Por eso la validación va antes y en un
módulo aparte, compartido por los dos modos: así el formulario y la carga masiva no
pueden divergir.

Y por debajo hay una red que **falla ruidosamente**, para que nunca salga un
documento a medias: si el cuerpo usa un marcador que no está en los datos, el
renderizado se detiene con un error en vez de dejar un hueco en blanco en el
contrato.

---

## 8. Cómo se escribe el cuerpo de un tipo

El cuerpo es el texto del otrosí, con los datos que cambian de persona a persona
puestos entre dobles llaves.

```
Entre LA UNIVERSIDAD y **{{nombre}}**, {{identificado}} con cédula de
ciudadanía No. {{documento_identidad}}, quien ingresó el {{fecha_ingreso}},
en adelante {{teletrabajador}}, se acuerda:
```

**No es un lenguaje de programación.** No hay condicionales ni bucles ni funciones:
solo marcadores. Si escribes `{%` o `{#` sale un error, porque eso se imprimiría
tal cual en el contrato.

### Marcadores

- `{{clave}}` — el valor del campo cuya **clave** sea esa, ya formateado según su
  tipo.
- `{{clave:mayuscula}}` — con la primera letra en mayúscula. Para cuando el
  marcador abre una frase.
- `{{clave:mayusculas}}` y `{{clave:minusculas}}` — todo en mayúsculas o en
  minúsculas. `mayusculas` es lo que se usa en un bloque de firmas.

Esos tres son **los únicos** filtros que existen. El separador es `:` y no `|`
justamente porque el `|` delimita las celdas de las tablas.

Una clave que no sea un campo del tipo es un **error al guardar**: es lo que evita
que salga un documento con un hueco en blanco.

### El Markdown que existe

El conversor a `.docx` entiende **solo esto**:

| Se escribe | Sale |
|---|---|
| líneas seguidas, separadas de las siguientes por una línea en blanco | un párrafo justificado |
| `**negrita**` | negrita |
| `- ` al principio de una línea | una viñeta |
| `\| a \| b \|`, una línea por fila | una tabla con bordes |
| `<!-- tabla-sin-bordes -->` antes de una tabla | esa tabla sin bordes |
| espacios al principio de la primera línea de un párrafo | sangría, un cuarto de pulgada por cada 4 espacios |

**Nada más.** Un `# Título`, un `[enlace](dirección)`, una `*cursiva*` o un `> cita`
**se imprimen literales**, con el `#` y los corchetes incluidos. El revisor te avisa
de cada uno. Las listas numeradas (`1. `) también se imprimen literales, y eso suele
ser justo lo que se quiere.

### Tres trampas

1. **Ninguna línea de un párrafo puede empezar por `- ` ni por `|`.** Si partes un
   párrafo largo en varias líneas y una de las siguientes empieza así, cortas el
   párrafo y conviertes el resto en una viñeta o en una tabla. Es error.
2. **Ninguna celda de tabla puede contener un `|` literal.** Y todas las filas de una
   tabla tienen que tener el mismo número de celdas: la tabla se dimensiona con la
   primera fila y **las celdas de más se pierden sin avisar**. Es error.
3. **Los `**` van en pareja.** Un número impar en un mismo párrafo invierte la
   negrita desde ahí y deja los asteriscos impresos. Es error.

### El encabezado, el pie y el logo no se tocan

De un tipo solo se puede cambiar el **título** que sale centrado arriba. El logo y
las cuatro líneas del pie son iguales en cualquier otrosí y no se escriben en el
cuerpo: el pie lleva un `|` literal («Universidad de los Andes **|** Vigilada
Mineducación») que el lector de tablas malinterpretaría.

### Previsualiza siempre

El botón **«Descargar el .docx de muestra»** rellena el tipo con el ejemplo de cada
campo y genera el documento. **Ábrelo.** Es la única forma de ver de verdad si una
tabla quedó partida o si un título se imprimió literal; el revisor atrapa mucho,
pero no puede ver cómo queda la página.

### Lo guardado vive en el disco del servidor

Un tipo creado en la web se guarda en el servidor. **Si no sabes si ese disco
sobrevive a un reinicio o a un redespliegue, exporta el `.json` y guárdalo tú**: es
el único respaldo, y con «Importar un .json» se recupera tal cual.

El otrosí de teletrabajo híbrido viene con la app y su texto original está en el
repositorio. Se puede editar, y entonces aparece un botón **«Restaurar el
original»** que descarta los cambios y vuelve al texto de siempre.

---

## 9. El tipo integrado: otrosí de teletrabajo híbrido

Los 14 campos, todos obligatorios. `L##` es la línea de
[la plantilla](plantillas/otrosi_teletrabajo_hibrido.md) donde se imprime.

| Campo (encabezado del Excel) | Clave | Tipo | Largo sugerido | Dónde se imprime |
|---|---|---|---|---|
| Nombre | `nombre` | Texto | 120 | Párrafo de apertura, en negrita (L5) · bloque de firmas (L170) · **nombre del archivo** |
| Documento de identidad | `documento_identidad` | Cédula | 6 a 10 dígitos | Párrafo de apertura (L6), como `1.020.345.678` |
| Fecha de ingreso | `fecha_ingreso` | Fecha, **no futura** | — | Párrafo de apertura (L8) |
| Cargo | `cargo` | Texto | 80 | Párrafo de apertura (L8) · bloque de firmas (L171) |
| Dependencia | `dependencia` | Texto, **artículo minúscula** | 160 | Párrafo de apertura (L9) — **abre el renglón** |
| Unidad | `unidad` | Texto | 100 | Párrafo de apertura, a mitad de renglón (L9) |
| Género en el documento | `teletrabajadora` | Género | — | No se imprime: decide **32** concordancias |
| Fecha de inicio del teletrabajo | `fecha_inicio_teletrabajo` | Fecha, **posterior a** la de ingreso | — | Cláusula primera (L19) |
| Días de teletrabajo asignados | `dias_teletrabajo` | Lista | — | Tabla de condiciones (L24) |
| Dirección del lugar de teletrabajo | `direccion` | Texto | 120 | Tabla de condiciones (L25) |
| Ciudad o municipio donde teletrabajará | `ciudad` | Texto, con 6 sugerencias | 50 | Tabla de condiciones (L26) |
| Computador | `computador` | Texto | 120 | Párrafo con sangría (L43) |
| Tipo de computador | `tipo_computador` | Texto | 60 | Párrafo con sangría (L45) |
| Fecha de firma | `fecha_firma` | Fecha, **la rellena la app** | — | Párrafo de cierre (L164) · nombre del archivo |

**«Fecha de firma» es el único campo que puede ir en blanco en el Excel.** El
selector «Fecha de firma del lote» rellena todas las filas que dejes vacías, que es
el caso normal: un lote, una fecha. La columna existe para la excepción, y si
escribes una fecha ahí, esa le gana al selector.

**Días de teletrabajo asignados**: los dos textos del desplegable son
**literalmente** los que se imprimen en el contrato, «Dos (2) días por semana» o
«Tres (3) días por semana». Al leer también se aceptan `dos`, `2`, `tres` y `3`.

**Ciudad o municipio**: la lista de seis ciudades del formulario es solo un atajo,
**puedes escribir cualquier municipio de Colombia**, y en el Excel es una columna de
texto normal. Se aclara porque la lista *parece* una restricción y no lo es.

**Cuidado con la notación científica en la cédula.** Si la columna es estrecha y no
tiene formato de número, Excel muestra `1,02E+09`. Mientras siga siendo un número no
pasa nada, pero si ese texto llega a guardarse como texto —al «pegar solo valores»,
o dando una vuelta por `.csv`— el documento saldría con la cédula **`10.209`**: seis
dígitos en vez de diez, sin ningún error visible. La plantilla pone formato de
número en esa columna justamente para que no ocurra, y la carga rechaza cualquier
cosa que no sean dígitos.

**El nombre del archivo.** Cada `.docx` se llama
`otrosi_teletrabajo_ana_maria_ruiz_20260810.docx`, con el nombre sin tildes y en
minúsculas. Como se quitan las tildes, **«María García» y «Maria Garcia» producen el
mismo nombre**. Cuando dos filas del lote coinciden, la segunda recibe un sufijo
`_2` (después `_3`, etc.) y sale un **aviso** con el nombre final, para que nadie
pierda un documento en silencio dentro del `.zip`. Si un nombre no deja ninguna
letra utilizable, se usa el número de la fila.

> **Ojo:** la etiqueta de la columna no siempre es idéntica al rótulo impreso en el
> otrosí. La columna dice «Días de teletrabajo asignad**os**» y la tabla del
> documento imprime «asignad**o**»; la columna dice «Ciudad o municipio donde
> teletrabajará» y el documento «Ciudad/municipio donde teletrabajará». La
> plantilla es transcripción literal del PDF institucional y **no se corrige**.

---

## 10. Errores frecuentes y cómo resolverlos

### Al diligenciar

| Lo que ves | Qué hacer |
|---|---|
| «dale formato de fecha a la celda; como texto solo se acepta AAAA-MM-DD» | Selecciona la columna en Excel y ponle formato de Fecha, o escribe `2026-04-03`. |
| «un número suelto es un serial de Excel» | La celda tiene un número con formato General. Ponle formato de Fecha. |
| «quita «\|»» / «quita «**»» | Borra ese carácter del campo. Para separar partes de una dirección usa una coma. |
| «no puede empezar por «-»» | Quita el guion inicial. |
| «no es un número; escríbela solo con dígitos» | Quita «CC», letras o la notación científica de la cédula. |
| «usa la lista desplegable» | La celda tiene `VERDADERO`/`FALSO`. Escribe el texto de la opción. |
| «faltan datos en …» | Esa fila está a medio llenar. Complétala o **borra la fila entera** — las filas totalmente vacías se ignoran sin ruido. |
| «tiene columnas repetidas» | Hay dos columnas con el mismo encabezado. Deja una sola. |
| «reconocí N de M encabezados. Faltan: …» | Se renombró o borró un encabezado, o hay celdas combinadas en la fila 1. Descarga la plantilla otra vez. |
| «No pude abrir el archivo como libro de Excel» | Es un `.csv` o un `.xls` con el nombre cambiado. Ábrelo y usa «Guardar como → Libro de Excel (.xlsx)». |
| «No encontré la hoja «Otrosíes»» | Se renombró la hoja o se pegaron los datos en otra. Usa la plantilla descargada. |
| «Subiste la plantilla vacía» | No hay filas con datos debajo del encabezado. |
| «trae más de 300 filas» | Pártelo en varios archivos. |
| Los desplegables no funcionan | El archivo abrió en Vista Protegida: pulsa «Habilitar edición». |
| Una columna llena con fórmulas llega vacía | Abre y guarda el archivo en Excel antes de subirlo. |

### Al definir un tipo

| Lo que ves | Qué hacer |
|---|---|
| «no es un campo de este tipo, así que el documento saldría con un hueco» | El marcador está mal escrito o falta declarar el campo. Copia el nombre de la lista de marcadores disponibles. |
| «Este editor no usa Jinja» | Quita los `{% %}` o `{# #}`: aquí no hay condicionales. |
| «la fila tiene N celdas y la primera de la tabla tiene M» | Iguala el número de `\|` en todas las filas de esa tabla. |
| «empieza por «\|» justo debajo de un párrafo» | Deja una línea en blanco entre el párrafo y la tabla. |
| «lleva un «\|» en medio de un párrafo» | Ese carácter solo vale para tablas. Quítalo. |
| «número impar de «**»» | Falta cerrar una negrita. |
| «no aparece en el cuerpo» (aviso) | Ese campo se va a pedir pero no se imprime. Ponlo en el cuerpo o quítalo. |
| «La clave … está reservada» | Es uno de los cinco marcadores de género. Ponle otro nombre al campo. |
| «necesita al menos dos opciones» | Un campo de lista con una sola opción no es una elección. |
| «Alguien más guardó este tipo mientras lo editabas» | Otra persona guardó después de que tú lo abriste. Exporta tu versión, vuelve a abrir el tipo y aplica los cambios sobre la nueva. |

---

## 11. Qué está medido y qué está estimado

Con el mismo criterio que la sección «Known limitations» de [CLAUDE.md](CLAUDE.md).

**Medido o verificado ejecutando el código:** que el motor de marcadores produce un
Markdown **byte a byte idéntico** al que producía la plantilla de Jinja, en las dos
ramas de género; los anchos de 2,6"/3,9" y de 3,25"/3,25"; el margen interno de
celda de 108 twips; las sangrías de 0,25" y 0,5"; los 33 caracteres fijos del nombre
de archivo y que no se recorta (un nombre de 300 da un archivo de 333); las cuatro
salidas erróneas del formateador de cédula (`1020345678.0` → `10.203.456.780`,
`'1.02E+09'` → `10.209`, `-5` → `5`, `0` → vacío); las 32 sustituciones de
concordancia; el avance de Calibri 11 pt de 4,65 pt por carácter (4,74 en negrita),
con dispersión de 4,53 a 4,76; los 42 ms y ~44 KB por documento; que las líneas de
la plantilla donde cae cada campo son las de la tabla del §9; y que cada regla del
revisor de tipos dispara con su caso.

**Estimado — trátalo como tal:**

| Cifra | Por qué es estimación |
|---|---|
| 58 / 48 / 101 / 97 / 93 caracteres por renglón | Se derivan del avance medido, pero Word aplica su propio kerning y justificación y corta por palabra. No se contaron en un `.docx` abierto. |
| Los largos sugeridos del §9 (120, 80, 160, 100, 120, 50, 120, 60) | Criterio propio a partir de los anchos. **Ningún requisito los exige y nada los valida.** |
| «6 a 10 dígitos» en la cédula | **No es un dato legal.** Solo están verificados los dos ejemplos del proyecto (8 y 10 dígitos). No sé si existe un máximo legal, y el programa no cuenta dígitos. |
| «Ningún municipio se pasa de 50 caracteres» | No se consultó el listado DIVIPOLA. |
| Que el tope de 300 filas sea el adecuado | Sale de los 42 ms medidos por documento: 300 filas son unos 13 segundos de espera. El tope es una decisión, no un límite técnico. |
| Los topes de Excel (32.767 caracteres por celda, 1.024 visibles) | Especificaciones publicadas por Microsoft, no comprobadas aquí. Quedan muy por encima de cualquier uso real. |

**Lo que hoy no comprueba nadie**, dicho de frente:

- **Ninguna longitud de ningún campo**, ni del cuerpo de un tipo. Un pegado
  desbocado en la dirección llega entero al documento.
- **Los dígitos de la cédula.** `1` y `999999999999` pasan los dos.
- **Que el texto tenga sentido.** `Nombre = "x"` pasa.
- **Que las fechas sean coherentes entre sí** más allá de las dos banderas.
- **Que el cuerpo de un tipo diga algo jurídicamente correcto.** El revisor
  comprueba la estructura del documento, no el contenido legal.
- **Quién editó un tipo y cuándo.** La app no tiene inicio de sesión: cualquiera con
  el enlace puede cambiar el texto de un otrosí y no queda rastro de autoría.
