# Carga masiva de otrosíes desde Excel

## Context

Hoy el único punto de entrada es el formulario web, y genera **un** otrosí por
envío. Según [CLAUDE.md](CLAUDE.md), los otrosíes se procesan en lotes cada ~15
días: la persona que usa el sitio no tiene forma de cargar los datos de muchos
contratos de una sola vez, así que el cuello de botella sigue siendo teclear una
persona a la vez.

Se añade el modo masivo que la arquitectura ya venía preparando: **descargar una
plantilla de Excel** (una fila por persona), **llenarla**, **subirla** y obtener
**un `.zip` con todos los `.docx`**. El modo individual se conserva intacto.

`documento.py` **no se toca**. Que no importe Streamlit y que reciba un dict
plano era precisamente el andamiaje para esto; el modo masivo lo llama tal cual.

### Tres defectos reales que el modo masivo vuelve peligrosos

Verificados leyendo el código, no supuestos. Hoy son latentes porque una persona
revisa el `resumen()` en pantalla; con 80 filas nadie los ve.

1. **Cédula flotante → documento con la cédula equivocada.**
   `documento.cedula(1020345678.0)` devuelve `"10.203.456.780"`: `str(float)`
   conserva el `.0` y el `re.sub(r"\D", "", ...)` de
   [documento.py:84](documento.py#L84) se come el punto y suma un dígito. Excel
   guarda todo número como *double*, así que este es el camino **normal** al
   leer una hoja, no un caso raro. Es la razón de fondo para no usar
   `pandas.read_excel`.
2. **Un `|` en cualquier campo de texto trunca el `.docx` en silencio.**
   `direccion = "Calle 1 | Apto 2"` renderiza una fila de 3 celdas, pero
   `_escribir_tabla` dimensiona la tabla con `len(filas[0])` = 2 y el `zip()` de
   [documento.py:259-262](documento.py#L259-L262) descarta el resto: se imprime
   `Calle 1` y `Apto 2` desaparece, sin excepción. Un salto de línea (Alt+Enter,
   frecuentísimo en direcciones) es peor: parte la tabla en dos.
   `CLAUDE.md` ya advierte del `|`, pero dirigido a quien edita la plantilla, no
   a los **datos**.
3. **Nombres de archivo repetidos dentro del `.zip`.** `_slug`
   ([documento.py:297](documento.py#L297)) quita tildes y baja a minúsculas, así
   que `"María García"` y `"Maria Garcia"` producen el mismo nombre; `zipfile`
   escribe entradas duplicadas sin quejarse y al descomprimir una pisa a la
   otra. Un nombre sin caracteres ASCII deja `otrosi_teletrabajo__20260806.docx`.

Los tres se arreglan aquí porque el modo masivo los activa. El (2) se arregla
para **ambos** modos: la validación vive en el módulo compartido.

## Decisiones confirmadas con el usuario

| Punto | Decisión |
|---|---|
| Formato y dependencia | **Excel `.xlsx` con `openpyxl`.** Se descarta CSV (sin desplegables ni formatos, y el round-trip en Excel es-CO usa `;` y corrompe tildes) y se descarta pandas (no evita la dependencia —tampoco trae motor— y su `read_excel` es justo el origen del bug de la cédula flotante). |
| Filas con errores | **Bloquean el lote completo.** El botón de generar queda deshabilitado y se listan todos los problemas a la vez, con fila y campo, para corregirlos de una pasada. Nunca un `.zip` al que le falten tres personas sin que se note. |
| Fecha de firma | **Columna en la hoja + selector único en la app.** La columna cubre la excepción; el selector rellena todas las filas que se dejen en blanco (el caso normal: un lote, una fecha de firma). |

---

## Arquitectura

Se mantiene la regla que ya sostiene el proyecto: **Streamlit solo en la capa de
UI**. Grafo acíclico, sin ciclos ni dependencias invertidas:

```
otrosi.py     UI Streamlit (dos pestañas)          -> campos, masivo, documento
masivo.py     Excel <-> payloads + .zip            -> campos, documento
campos.py     registro de campos + coerción        -> documento
documento.py  Markdown/.docx                       -> (sin cambios)
```

### `campos.py` — módulo nuevo, sin Streamlit

Existe porque `masivo.py` necesita **las mismas etiquetas y las mismas reglas de
validación** que el formulario, y no puede importar `otrosi.py` sin arrastrar
Streamlit por debajo de la capa de UI. Duplicar las etiquetas daría dos fuentes
de verdad para los nombres de los campos de un documento legal, que es lo que
`CLAUDE.md` prohíbe explícitamente.

Se **mueven** desde `otrosi.py` sin cambiar su contenido: `ETIQUETAS`,
`OBLIGATORIOS`, `FECHA_MINIMA`, `FECHA_MAXIMA`. Se **queda** en `otrosi.py` el
dict `GENERO`, porque sus valores son copy de interfaz
(`"Femenino — «la Teletrabajadora», «identificada»"`): la raya y las comillas
angulares no sirven en un desplegable de Excel.

```python
"""Registro de los campos del otrosí: etiquetas, obligatoriedad y coerción.

Sin dependencia de Streamlit: el formulario y la carga masiva validan con las
mismas reglas y las mismas etiquetas.
"""

ETIQUETAS = {...}                                        # movido tal cual
OBLIGATORIOS = tuple(ETIQUETAS)                          # el orden del dict es el de las columnas
TIPOS = {...}                                            # clave -> 'texto'|'entero'|'fecha'|'lista'
GENERO_TEXTO = {True: "Femenino", False: "Masculino"}    # lo que va en el Excel
DIAS_TEXTO = documento.DIAS_TELETRABAJO                  # verbatim: el desplegable dice lo que dirá el otrosí
PROHIBIDOS = "|"                                         # rompe las tablas del conversor a .docx

def faltantes(datos):
    """Claves obligatorias vacías del payload: {'cargo': ''} -> ['cargo']."""

def normalizar(fila):
    """Fila cruda del Excel al payload plano -> (datos, errores, avisos)."""

def _texto(valor):      """Normaliza NFKC y colapsa espacios: ' Ana\xa0Ruiz\n' -> 'Ana Ruiz'."""
def _entero(valor):     """Cédula desde int, float entero o texto: '1.020.345.678' -> 1020345678."""
def _fecha(valor):      """Solo fechas reales de Excel o texto ISO; lo ambiguo se rechaza, no se adivina."""
def _opcion(valor, sinonimos):  """Texto del desplegable a bool: 'Femenino' -> True."""
```

**Cambio de firma de `campos_faltantes` → `faltantes(datos)`.** Hoy recibe
`[(etiqueta, valor)]` y devuelve etiquetas; el modo masivo necesita **claves**
para marcar columnas y para no reportar dos veces un campo que ya falló en la
coerción. Pasa a recibir el payload y devolver claves. El sitio de llamada en
`otrosi.py` queda igual de corto:

```python
if faltas := campos.faltantes(datos):
    st.error("Faltan campos obligatorios: " + ", ".join(campos.ETIQUETAS[c] for c in faltas))
```

Se conserva **literal** el comentario del `isinstance(True, int)`: `CLAUDE.md` lo
nombra como caveat intencional.

`normalizar` devuelve errores ya redactados en español con la etiqueta dentro
(`'«Fecha de ingreso»: escríbela con formato de fecha, no como texto'`). El
número de fila lo antepone `masivo.py`, que es el único módulo que sabe que
existen las hojas de cálculo.

### `masivo.py` — módulo nuevo, sin Streamlit

```python
"""Carga masiva de otrosíes: plantilla de Excel, lectura de filas y .zip de .docx.

Sin dependencia de Streamlit, igual que documento.py: la interfaz solo entrega
bytes y muestra lo que devuelven estas funciones.
"""

HOJA_DATOS, HOJA_INSTRUCCIONES = "Otrosíes", "Instrucciones"
FILAS_PLANTILLA = 300
MAXIMO_FILAS = 300          # ~50 ms por documento: 300 filas son ~15 s de espera
FILAS_ENCABEZADO = 10       # hasta qué fila se busca el encabezado

def construir_plantilla():
    """Arma el .xlsx vacío (hoja de datos + instrucciones) y devuelve los bytes."""

def leer_libro(contenido, fecha_firma_defecto):
    """Lee el .xlsx cargado -> (registros, errores): un registro por fila con datos."""

def generar_zip(registros, progreso=None):
    """Genera un .docx por registro y los empaqueta en un .zip -> (bytes, fallos)."""

def _hoja_datos(libro):        """Ubica la hoja por nombre y si no por encabezados; wb.active puede ser «Instrucciones»."""
def _mapa_columnas(hoja):      """Etiqueta -> índice de columna, tolerante a mayúsculas, tildes y espacios."""
def _fila_vacia(valores):      """True si todas las celdas mapeadas están vacías: relleno de la plantilla."""
def _nombres_unicos(registros):"""Nombres del .zip sin colisiones: dos grafías de un nombre dan el mismo slug."""
def _avisos_cruzados(registros):"""Avisos entre filas: cédulas repetidas y archivos renombrados."""
```

Un `registro` es `{"fila": 7, "datos": {...}, "errores": [...], "avisos": [...]}`.

`progreso` es un `Callable[[int, int], None]` que se invoca por documento. Ese
callback es lo que permite mover una barra de progreso de Streamlit **sin
importar Streamlit** — la misma disciplina que ya sigue `documento.py`.

---

## La plantilla de Excel

**Hoja 1 — `Otrosíes`**
- Fila 1: las 14 etiquetas en el orden de inserción de `ETIQUETAS` (los dicts de
  Python preservan el orden; no hace falta una constante `ORDEN` aparte).
  Negrita, con relleno, `freeze_panes="A2"`.
- Anchos por columna; formato `DD/MM/YYYY` en las tres columnas de fecha y
  `#,##0` en `documento_identidad`. **Nunca** formato Texto (`@`) en las fechas:
  rompería justo lo que se quiere lograr.
- `DataValidation` de lista en las dos columnas booleanas, filas 2..301,
  `allow_blank=True`, con `errorTitle`/`error` en español:
  - Género: `Femenino` / `Masculino`
  - Días: los dos valores de `documento.DIAS_TELETRABAJO`, textuales
- **Sin fila de ejemplo.** El ejemplo va en la hoja de instrucciones, para que
  nadie genere por accidente un otrosí a nombre de una persona inventada.

**Hoja 2 — `Instrucciones`**
- Cómo diligenciar: 1 fila = 1 persona; no traduzcas ni borres los encabezados
  (puedes añadir columnas propias, se ignoran); escribe las fechas **como
  fecha**, no como texto; usa los desplegables; **no uses el carácter `|`**; si
  el archivo abre en Vista Protegida, pulsa «Habilitar edición».
- Tabla por campo: Campo | Obligatorio | Tipo | Valores permitidos | Ejemplo,
  **generada desde `ETIQUETAS` + `TIPOS`** para que no pueda desincronizarse.

---

## Reglas de coerción y validación

La estrictez vive en tres capas: la **plantilla** previene (formatos y
desplegables), `campos.normalizar` **rechaza** (nunca adivina) y la **vista
previa** confirma. Los filtros de `documento.py` son deliberadamente tolerantes
—el docstring de `cedula` dice *"Tolera '52.832.252' de una carga masiva"*— así
que **no pueden ser la capa de validación**.

| Campo(s) | Llega como | Regla | Se rechaza |
|---|---|---|---|
| los 8 de texto | `str` | NFKC (NBSP→espacio), quitar `​﻿`, `re.sub(r"\s+", " ")`, `strip()` | vacío |
| los 8 de texto | `int`/`float` | `str(int(v))` si es entero | float con decimales |
| los 8 de texto | cualquiera | **contiene `\|` → error duro** | siempre (defecto 2) |
| `documento_identidad` | `int` | tal cual | `<= 0` |
| idem | `float` | solo si `is_integer()`, y **nunca** vía `str()` | `1020345678.5` (defecto 1) |
| idem | `str` | quitar `. , ' -` y espacios; el resto debe ser todo dígitos | `"CC 1020345678"`, `"1.02E+09"` |
| las 3 fechas | `datetime` | `.date()` | fuera de 1970–2100 |
| las 3 fechas | `str` | **solo** `^\d{4}-\d{2}-\d{2}$` + `date.fromisoformat` | `"03/04/2026"`, `"45000"` |
| las 3 fechas | `int`/`float` | — | siempre (serial de Excel ambiguo) |
| `teletrabajadora` | `str` | sin tildes y en minúsculas: `femenino/f/fem/mujer`→True, `masculino/m/masc/hombre`→False | lo demás, mostrando los válidos |
| `dos_dias` | `str` / `int` | textos del desplegable, o `dos`/`2` → True, `tres`/`3` → False | lo demás |
| ambos booleanos | `bool` | — | siempre: «usa la lista desplegable» |

**Las fechas de texto se rechazan a propósito.** `03/04/2026` puede ser 3 de
abril o 4 de marzo y **ambas lecturas parsean bien**, así que un `strptime`
estricto no lanza excepción: emite la fecha equivocada en un contrato firmado.
No hay señal en banda para distinguirlas. Se aceptan solo fechas reales de Excel
(sin ambigüedad posible) y el ISO `YYYY-MM-DD`, con la regex por delante porque
`date.fromisoformat("20260403")` **sí** parsea en Python 3.11+ y dejaría pasar un
error de tecleo de 8 dígitos.

Validaciones semánticas por fila, ya normalizada:

| Regla | Severidad | Motivo |
|---|---|---|
| `fecha_ingreso <= hoy` | **error** | el formulario ya lo impone con `max_value=date.today()`; si masivo no, se vuelve un bypass de la UI |
| `fecha_inicio_teletrabajo >= fecha_ingreso` | aviso | el mejor detector de columnas intercambiadas o de día/mes al revés |
| `dependencia` empieza por `^(La\|El\|Los\|Las) ` | aviso | casi seguro autocorrección de Excel; se imprime a mitad de frase → «se desempeña como X en **La Dirección de**…». Nunca reescribir texto legal en silencio |

Validaciones entre filas:

| Regla | Severidad | Notas |
|---|---|---|
| fila totalmente vacía | **omitir en silencio** | dar formato a 300 filas *crea* las celdas: `max_row` será 301 aunque estén vacías |
| fila parcialmente llena | **error, jamás omitir** | esta distinción es la que evita perder a una persona sin avisar |
| nombre de archivo repetido | auto-resolver + informar | sufijo `_2`, `_3` por orden de fila; se listan los renombres. `documento.nombre_archivo` **no se toca** (defecto 3) |
| slug vacío | auto-resolver | se sustituye por el número de fila |
| cédula repetida | aviso | legítimo en una corrección + reexpedición; bloquear sería hostil |
| encabezado duplicado | **error duro** | «gana el último» sería silencioso |
| más de `MAXIMO_FILAS` | **error duro** | mensaje pidiendo partir el archivo |
| cero filas con datos | error amable | «Subiste la plantilla vacía» |

---

## `otrosi.py` — cambios

Diff pequeño y de bajo riesgo: usando `from campos import ETIQUETAS, OBLIGATORIOS`
las ~16 referencias dentro de `render_formulario` quedan **byte a byte iguales**.

- Un import nuevo; se borra el bloque de constantes movidas y `campos_faltantes`.
- `main()` pasa a `st.set_page_config` + título + `st.tabs` y delega:
  - `_pestaña_individual()` — el cuerpo actual de `main()`, sin tocar.
  - `_pestaña_masiva()` — plantilla → carga → vista previa → generar → `.zip`.
  - `_vista_previa(registros)` — los registros con **los mismos filtros del
    `.docx`**, igual que ya hace `resumen()`.

### Flujo de la pestaña «Carga masiva»

1. **Paso 1** — `st.download_button("Descargar plantilla", data=masivo.construir_plantilla)`.
   Se pasa la **función**, no los bytes: no se construye nada hasta el clic.
   `on_click="ignore"` y `key=` propio.
2. **Paso 2** — `st.file_uploader(type=["xlsx"], key=...)` + el selector de fecha
   de firma del lote (por defecto hoy), que rellena las filas en blanco.
3. **Parsear en cada rerun**, sin caché: son decenas de milisegundos y elimina
   toda una clase de bugs de caché obsoleta. `try/except` para `BadZipFile` e
   `InvalidFileException` → «vuelve a guardarlo como Libro de Excel (.xlsx)».
4. **Mostrar** en orden: `st.error` con los errores bloqueantes como
   `Fila 7 · «Fecha de ingreso»: …` (tope ~50, «y N más»); `st.warning` con los
   avisos; `st.dataframe` con la vista previa de las filas válidas, con columna
   `Fila` y **todos los valores ya renderizados** (`fecha_larga` → «3 de abril de
   2026», `cedula`, «la Teletrabajadora», el texto de los días). Es donde un
   humano detecta al instante un «4 de marzo» que en `03/04/2026` no vería.
5. **Generar** — `st.button("Generar N otrosíes", type="primary", disabled=bool(errores))`.
   Los avisos informan; los errores bloquean.
6. **Al pulsar** — `st.status` + `st.progress` movidos por el callback
   `progreso`. Se guarda en `st.session_state["masivo"]` con la **huella sha256**
   del archivo subido; si en un rerun la huella cambia, se descarta — el análogo
   masivo del comentario que ya existe: *«no dejar descargable el documento
   anterior junto a un error»*.
7. **Resultado** — `st.download_button("Descargar .zip", on_click="ignore")` y un
   expander con los nombres generados y los fallos por fila. Una fila que falle
   al renderizar no mata el lote: el resto se entrega, anotado.

Dos detalles de Streamlit ya verificados contra la 1.60.0 instalada: con
`st.tabs` por defecto **ambos cuerpos se ejecutan en cada rerun** (correcto aquí,
pero deliberado), y cada widget nuevo necesita `key=` propio o salta
`DuplicateWidgetID`.

---

## Archivos

| Archivo | Cambio |
|---|---|
| `campos.py` | **nuevo** — registro de campos y coerción, sin Streamlit |
| `masivo.py` | **nuevo** — plantilla, lectura y `.zip`, sin Streamlit |
| [otrosi.py](otrosi.py) | dos pestañas; constantes y validación movidas a `campos.py` |
| `requirements.txt` | `+ openpyxl==<versión que resuelva pip>` (con `==`, como los otros tres pines) |
| [CLAUDE.md](CLAUDE.md) | actualizado (abajo) |
| [documento.py](documento.py) | **sin cambios** |

**Instalación:** `pip install openpyxl` en el venv (arrastra `et-xmlfile`; no se
pinean transitivas, el archivo actual tampoco lo hace). **Quien hospede el sitio
debe reinstalar `requirements.txt`**, o la pestaña masiva fallará al importar.

### `CLAUDE.md`

- Intro y «Why this exists»: los dos modos; se borra *«That bulk mode does not
  exist yet»*.
- «Architecture»: cuatro módulos, el grafo y la regla «Streamlit solo en la UI».
  La frase de `ETIQUETAS` como única fuente de verdad se mueve a `campos.py`.
- **Corregir la línea 35**: *«`df.to_dict("records")` needs no mapping layer»*
  describe hoy un diseño que se descartó. Reescribir para decir que la fila mapea
  1:1 con el payload, sin implicar pandas, y dejar registrado **por qué** pandas
  queda fuera (cédulas flotantes, coerción a NaN).
- Sección nueva «Carga masiva»: nombres de las hojas, por qué se rechazan las
  fechas de texto, la prohibición del `|` y el truncamiento que evita, el
  desduplicado de nombres de archivo y el tope de filas.
- «Known limitations»: se reemplaza el punto de «no bulk entry point yet» por los
  reales (desplegables que se pierden al pegar, fechas de texto rechazadas por
  diseño, sin descarga individual por fila, tope de filas).

---

## Verificación

1. `pip install openpyxl` y `streamlit run otrosi.py`. **Comprobar primero que el
   modo individual sigue funcionando igual** (es lo único que el refactor pone en
   riesgo): formulario vacío → lista de faltantes; formulario completo → `.docx`.
2. Descargar la plantilla y abrirla en Excel: dos hojas, encabezado congelado, la
   flecha del desplegable visible en las dos columnas booleanas, las tres
   columnas de fecha con formato de fecha.
3. Llenar 3 filas (una femenina 2 días, una masculina 3 días, una con la fecha de
   firma en blanco), subirla y verificar la vista previa contra lo tecleado.
   Generar y abrir los tres `.docx`.
4. **Pruebas de los tres defectos**, que deben fallar en la carga y no en el
   documento:
   - dirección `Calle 1 | Apto 2` → error de fila, no un `.docx` truncado
   - dirección con Alt+Enter → error de fila, no una tabla partida
   - cédula en una celda numérica → payload `int`, y en el documento
     `1.020.345.678` (no `10.203.456.780`)
   - dos filas «María García» / «Maria Garcia» → dos entradas distintas en el
     `.zip`, con el renombre informado
5. Fecha como texto `03/04/2026` → rechazada con mensaje claro. Como fecha real →
   aceptada y mostrada «3 de abril de 2026» en la vista previa.
6. Fila parcialmente llena → error. Fila totalmente vacía → omitida sin ruido.
7. Subir un `.csv` renombrado a `.xlsx` → mensaje pidiendo guardarlo como `.xlsx`.
8. **Contrato sin UI** (lo que mantiene viva la separación): en una consola,
   `import masivo`, `construir_plantilla()`, `leer_libro(bytes, date.today())` y
   `generar_zip(...)` sin importar Streamlit.

---

## Detalles de openpyxl a verificar tras instalar — no asumir

No hay openpyxl en el entorno, así que no he podido comprobarlos leyendo su
código. Estos fallan **en silencio** (archivo que abre bien pero sin desplegable)
en vez de lanzar excepción:

1. **`showDropDown`**: en OOXML, `showDropDown="1"` **oculta** la flecha. Dejarlo
   sin poner y confirmar que la flecha aparece.
2. **Lista en línea**: `formula1='"Femenino,Masculino"'` — confirmar que la coma
   funciona en un Excel en español (algunos locales usan `;`) y que la `í` de
   «días» sobrevive. Si falla, usar un rango en `Instrucciones`
   (`formula1="=Instrucciones!$H$2:$H$3"`), que es a prueba de locale.
3. Orden de `ws.add_data_validation(dv)` frente a `dv.add("G2:G301")`.
4. **Que las celdas con formato de fecha vuelvan como `datetime.datetime`** —
   toda la política de fechas descansa en esto. Verificar contra un archivo
   guardado por Excel de verdad, no solo por openpyxl.
5. Si los enteros vuelven como `int` o como `float` en un archivo guardado por
   Excel (es lo que dispara el defecto 1).
6. Los códigos de formato numérico son en-US (`DD/MM/YYYY`, `#,##0`) y Excel los
   localiza; comprobar si hace falta `[$-es-CO]`.
7. **`data_only=True`** devuelve el valor *cacheado* de una fórmula: `None` si el
   archivo nunca lo abrió y guardó Excel. Si alguien llena una columna con
   BUSCARV y no guarda desde Excel, llegaría vacía. Verificar y ponerlo en las
   instrucciones.
8. **No usar `read_only=True`**: `ReadOnlyWorksheet` da `None` en `max_row` y no
   tiene `ws.cell()`. Con 300 filas no hace falta.

El coste por documento (~50 ms, ~44 KB) es una **estimación** de la que depende
el tope de 300 filas; se mide en el paso 3 de verificación y se ajusta la
constante si hace falta.

## Dónde se rompe esto en manos reales

Ordenado por probabilidad × daño. Cada uno ya tiene su mitigación arriba.

1. **`wb.active` es «Instrucciones»** — `active` es la hoja seleccionada al
   guardar. Por eso se localiza por nombre y, si no, por encabezados.
2. **Pegar destruye los desplegables** — Excel pega también la validación. Tras
   pegar, el género llega como `"F"` o `"MUJER "`. Por eso el diccionario de
   sinónimos al leer es generoso aunque la plantilla ofrezca solo dos opciones.
3. **`|` o Alt+Enter en una dirección** — en Bogotá se escribe
   `"Calle 1 # 2-3 | Apto 401"` constantemente.
4. **El encabezado no está en la fila 1** — alguien añade un título. Se barren
   las primeras 10 filas y se informa cuál se usó.
5. **Encabezados combinados** — openpyxl devuelve el valor solo en la celda
   superior izquierda; el error debe imprimir los encabezados encontrados junto a
   los esperados.
6. **Guardado como `.csv` o `.xls`** — `type=["xlsx"]` filtra el diálogo del
   navegador, no un archivo renombrado.
7. **Vista Protegida** — un archivo descargado del sitio abre en solo lectura y
   los desplegables parecen muertos hasta «Habilitar edición».
8. **Caracteres invisibles** — `strip()` quita el NBSP inicial y final, pero
   `​` no es espacio y sobrevive; de ahí el NFKC más el borrado explícito.
