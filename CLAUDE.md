# GenOtrosi

Streamlit tool that generates **otrosíes** — amendments to a labor contract — for
Universidad de los Andes. It is a small template engine, not one hard-coded
document: HR staff define **tipos de otrosí** (an otrosí type = its fields plus the
document text with the per-person values marked), and each type can then be filled
one person at a time in a form, or in bulk from an Excel sheet. The codebase, UI
text, variable names, and comments are entirely in **Spanish** — this is intentional
(the domain, the template, and the end users are Spanish-speaking) and should not be
translated when editing.

## Why this exists

Contract amendments are currently a manual, ad-hoc drafting process. The
operational pain point driving this project is volume and cadence: amendments get
processed in batches roughly every 15 days, and manual drafting was the bottleneck.
The bulk mode exists precisely for that cadence; the single-record form is kept for
one-off corrections and re-issues.

The **type editor** exists because a second kind of otrosí used to mean a developer
touching five separate places in the code. Now it means filling in a form.

## Architecture

Five modules, and the rule that holds the whole thing together: **Streamlit lives
only in the UI layer.** Acyclic, no inverted dependencies:

```
otrosi.py     Streamlit UI (three tabs)      -> tipos, campos, masivo, documento
masivo.py     Excel <-> payloads + .zip      -> tipos, campos, documento
campos.py     coercion + validation          -> documento
tipos.py      type descriptors on disk       -> documento
documento.py  marcadores -> Markdown -> docx -> (nothing)
```

- [otrosi.py](otrosi.py) — Streamlit only. A type selector **above** `st.tabs`, then
  three tabs. `render_formulario(tipo)` dispatches on each field's type and returns a
  **flat dict** — that dict *is* the contract between the UI and the document
  generator. `resumen` renders the values for on-screen verification; `_vista_previa`
  does the same for a bulk batch.
- [tipos.py](tipos.py) — **no Streamlit.** The only module that knows files exist.
  Loads/saves/validates descriptors. `validar` is the substantial part.
- [campos.py](campos.py) — **no Streamlit.** Everything that depends on the *data
  type* rather than on the otrosí: the five coercers, the forbidden characters, the
  date policy, and the validation both modes share — `faltantes`, `revisar` (hard
  errors), `avisos` (suspicions), `normalizar` (one raw spreadsheet row → payload).
- [masivo.py](masivo.py) — **no Streamlit.** Builds the `.xlsx` template from the
  type, reads an uploaded workbook into records, packs the `.docx` files into a
  `.zip`. Its `progreso` callback is what lets Streamlit move a progress bar without
  `masivo.py` importing Streamlit.
- [documento.py](documento.py) — **no Streamlit and no template library.**
  Substitutes the type's `cuerpo` markers into Markdown, then converts that Markdown
  to a `.docx` via `python-docx`.

The payload is flat (not `{generales, detalle}`) because a bulk-mode spreadsheet row
maps onto it one-to-one, with no mapping layer in between. Build those dicts with
explicit per-field coercion rather than handing a dataframe row straight over — see
the `cedula` note under Known limitations for why.

**Why not pandas**, even though Streamlit already pulls it in: `read_excel` is the
direct route to the floating-point `cedula` bug (Excel stores every number as a
double, and pandas hands it over as one), it coerces missing values to `NaN`, and it
does not even save the dependency — it needs `openpyxl` as its xlsx engine anyway.
`masivo.py` reads cells through openpyxl and coerces each field explicitly. Note
`st.data_editor` in the type editor is fed a list of dicts and **returns a list of
dicts**, so pandas stays out of that too.

When adding a **field type**, keep the split: widget in `otrosi.py`, coercion in
`campos.py`, Excel format in `masivo.py`, print format in `documento.FORMATOS`,
validation in `tipos.validar`. Adding a *field* to an existing type needs no code —
that is the whole point.

## The type descriptor

A type is a **plain JSON-serializable dict**, same criterion as the payload. Loaded
by `tipos.cargar`, which fills in every default so a hand-written `.json` needs only
`clave`, `etiqueta` and `tipo` per field.

```
plantillas/
  LogoUninades.png
  teletrabajo_hibrido.json        the built-in type: metadata + the 14 fields
  otrosi_teletrabajo_hibrido.md   its cuerpo
  personalizadas/                the app writes here; overrides by id
```

`cuerpo_archivo` points at a sibling `.md` so the **built-in legal text is versioned
in git line by line** instead of being a 9 KB string with `\n` inside a JSON. Types
created in the web carry the body **inline** under `cuerpo`, so the file is
self-contained and exporting it is portable. `tipos.cargar` resolves either form;
`tipos.exportar` always inlines. A `cuerpo_archivo` is rejected on import — it would
let an uploaded `.json` read an arbitrary server file.

`plantillas/personalizadas/<id>.json` **overrides** the built-in of the same id;
deleting it restores the repo text. That is what makes "everything is editable"
recoverable — see Known limitations. Those files are deliberately **not**
gitignored: committing one makes a web-created type survive a redeploy.

`_origen` and `_marca` (the mtime at load, used to detect a lost write) are internal;
`_serializar` strips every `_`-prefixed key.

### The six field types

The field type decides **three things at once**: the form widget, how the Excel cell
is coerced, and **how the value prints**. That is why the template language needs no
formatting filters.

| `tipo` | Payload | Prints as | Widget | Excel column |
|---|---|---|---|---|
| `texto` | `str` | verbatim | `text_input`, or `selectbox` if it has `sugerencias` | text |
| `cedula` | `int` | `1.020.345.678` | `number_input` | `#,##0` |
| `entero` | `int` | plain digits | `number_input` | `#,##0` |
| `fecha` | `date` | `3 de agosto de 2026` | `date_input` | `DD/MM/YYYY` |
| `lista` | `str` (the chosen option) | verbatim | `radio` ≤4 options, else `selectbox` | dropdown |
| `genero` | `bool` | nothing on its own: **injects the 5 concordance phrases** | `radio` over `[True, False]` | dropdown |

Per-field flags carry what used to be hard-coded rules, with nothing lost:
`no_futura` (error), `posterior_a` (aviso), `articulo_minuscula` (aviso),
`opcional_en_hoja` (the batch date fills it; in the form it defaults to today),
`grupo` (the form's `st.subheader` groupings), `sugerencias`, `sinonimos`, `ancho`.

`INICIALES_PROHIBIDAS` applies to **every** text field: with a body anyone can write,
there is no longer a single field that can open a rendered line.

## The template language

```
{{clave}}      {{clave:mayuscula}}      {{clave:mayusculas}}      {{clave:minusculas}}
```

`documento.MARCADOR` + `documento.separar_marcador` + `documento.FILTROS` are the
whole language, and `tipos.py` imports all three rather than defining its own — if
the validator's regex diverged from the renderer's it would approve a body that then
fails to render.

- **The separator is `:`, not `|`.** The `|` delimits table cells in this Markdown
  dialect and the signature block has a marker *inside* a cell
  (`| LA UNIVERSIDAD, | {{teletrabajador:mayusculas}}, |`). `|` is still tolerated on
  read for anyone coming from Jinja.
- **A key that is not a declared field or a concordance name raises at render time.**
  That is what replaced `StrictUndefined`, and it is why `documento.contexto` only
  puts keys that are actually *in* `datos` into the context: a missing key must fail
  loudly instead of emitting a blank into a legal document.
- A `genero` field's own key is **not** a valid marker — its value is a bool.
- `{%` and `{#` are an explicit error ("this editor does not use Jinja").

**Jinja2 is gone from `requirements.txt`.** Because a person's text never reaches an
expression evaluator, the whole class of template injection (`{{ ''.__class__ }}` →
code execution) does not exist: substitution is a `re.sub` against a dict of declared
keys. Safe by construction, not by sandbox.

### Gender agreement

Fixed by decision — a `genero` field always injects exactly these five, and they
cannot be renamed or extended from the web. `CONCORDANCIA` enumerates **whole
phrases**, not just the noun, because Spanish contracts `a`+`el` → `al` and
`de`+`el` → `del`: inserting `"el Teletrabajador"` after `de` would produce `de el`.

| Key | Feminine | Masculine |
|---|---|---|
| `identificado` | identificada | identificado |
| `teletrabajador` | la Teletrabajadora | el Teletrabajador |
| `al_teletrabajador` | a la Teletrabajadora | al Teletrabajador |
| `del_teletrabajador` | de la Teletrabajadora | del Teletrabajador |
| `de_la_misma` | de la misma | del mismo |

`documento.GENERO` (the two option texts) lives next to `CONCORDANCIA` because they
are two halves of the same fact, keyed by the same bool. `campos.GENERO_SINONIMOS`
and `GENERO_BOOL` derive from it.

## The Markdown subset (`documento.markdown_a_docx`)

Converts the *rendered* Markdown **block by block** (blank line = block separator, so
a paragraph can span several source lines):

- paragraphs — consecutive non-blank lines, joined with a space
- `- ` bullets
- `**bold**`
- `| a | b |` tables (a `|---|---|` separator row, if present, is discarded)
- `<!-- tabla-sin-bordes -->` — makes the **next** table borderless
- leading spaces on a block's first line → left indent, 0.25" per 4 spaces

**Nothing else is supported** — no headings, links, or other Markdown; anything else
passes through as a literal paragraph.

The page header (logo + title) and the 4-line footer are built in Python by
`_construir_encabezado` / `_construir_pie`, **not** in the Markdown. Two reasons:
Markdown cannot express page furniture at all, and the footer contains a literal `|`
("Universidad de los Andes **|** Vigilada Mineducación") that the table parser would
misread. Only the **title** comes from the type.
`different_first_page_header_footer` is left `False`, which is what makes both repeat
on every page.

`plantillas/LogoUninades.png` is embedded into the header via `add_picture` at 1.2"
wide. python-docx reads PNGs natively — **Pillow is not a dependency**, do not add it
to `requirements.txt`. (It shows up in the venv anyway, because Streamlit pulls it
in; that is not a reason to rely on it here.)

## `tipos.validar` — the checker

The highest-value piece, because the converter above fails **silently**. Every rule
maps to a concrete defect. Structural checks run on the body **with markers replaced
by a neutral token**, because that is the real order: substitute, then parse Markdown.
Getting that backwards would flag the signature block's in-cell marker as a table
with three cells.

Errors: unknown marker · malformed marker · unknown filter · `{%`/`{#` · `|` in a
non-table line · a table row whose cell count differs from the block's first row
(`_escribir_tabla` sizes from `len(filas[0])` and the `zip()` **drops the rest with no
error**) · a paragraph continuation line starting with `- ` or `|` · an odd number of
`**` in a block (`_escribir_runs` splits on parity) · empty body · no fields ·
invalid/duplicate/reserved key · duplicate label (`_mapa_columnas` would reject the
Excel) · a `lista` with fewer than two options · more than one `genero` · an option
containing `|`/`**` · an `id` outside `^[a-z0-9_]{1,60}$` (it becomes a path) ·
`campo_nombre`/`campo_fecha_archivo` pointing at a missing or wrong-typed field.

Avisos: a declared field that never appears in the body · a marker that opens a line ·
unsupported Markdown (`#`, `>`, ```` ``` ````, links, single-`*` italics) · a
`<!-- tabla-sin-bordes -->` with no table after it.

**Ordered lists are deliberately not flagged.** `1. ` prints literally, which is
exactly what the built-in template wants for `1. Computador:`, and warning about it
would be crying wolf. The built-in type validates with **zero errors and zero
avisos** — keep it that way, it is what makes the checker trustworthy.

## Carga masiva (`masivo.py`)

The `.xlsx` has two sheets: **`Otrosíes`** (row 1 = the type's labels in field order,
frozen; 300 formatted rows) and **`Instrucciones`** (how to fill it in, plus a
per-field table generated from the type so it cannot drift). `wb.active = 0` so the
book opens on the data sheet. There is deliberately **no example row** — the example
lives in `Instrucciones`, so nobody accidentally generates an otrosí for an invented
person.

Non-obvious things that are load-bearing:

- **`DataValidation.formula1` points at cells in `Instrucciones`**, not at an inline
  `'"Femenino,Masculino"'` list. An inline list's separator depends on Excel's UI
  language, and when it mismatches the dropdown just silently does not appear. Those
  same cells double as the visible "valores permitidos" table.
- **The dropdown columns are computed, not hard-coded.** `_campos_lista` assigns each
  choice field a consecutive column from `H`, and the range is sized to the option
  count — a type with four choice fields gets `H`, `I`, `J`, `K`.
- **`showDropDown` is left unset.** The OOXML flag is inverted: `"1"` *hides* the
  arrow. Verified in the emitted XML — openpyxl writes `showDropDown="0"`.
- **Number formats are set cell by cell**, rows 2..301. That *creates* the cells, so
  `max_row` is 301 on a blank template. `_fila_vacia` is what makes that harmless: a
  fully empty row is skipped silently, a partially filled one is a hard error. That
  distinction is what stops a person from vanishing from a batch unnoticed.
- **`read_only=True` is not used** — `ReadOnlyWorksheet` has no `ws.cell()` and its
  `max_row` can be `None`. At 300 rows the memory saving is pointless.
- **Text dates are rejected on purpose.** `03/04/2026` parses fine as both 3 April
  and 4 March, so a strict `strptime` does not raise — it emits the wrong date into a
  signed contract. Only real Excel dates and ISO `YYYY-MM-DD` are accepted, with the
  regex ahead of `date.fromisoformat` because in 3.11 `"20260403"` also parses. A bare
  number in a *date-formatted* cell is fine (Excel already decided what day it is); a
  bare number in a General cell is rejected as an ambiguous serial.
- **Filenames are de-duplicated in `masivo`, not in `documento`.** `_nombres_unicos`
  suffixes `_2`, `_3` and reports each rename as an aviso. An empty slug is detected
  by comparing against `nombre_archivo` with the name field blanked, rather than by
  pattern-matching the filename, so it does not depend on that format.
- Row errors block the whole batch (the generate button is disabled); avisos never do.
  `MAXIMO_FILAS = 300` rests on a **measured** 42 ms per document — ~13 s for a full
  batch.

## The type editor tab

- The draft lives in `st.session_state["borrador"]` as the **baseline as opened**, and
  `_editor` returns a *new* dict each rerun without touching it. That matters:
  `st.data_editor` with a `key` stores edits as a delta against the data it receives,
  so feeding it the already-edited table would apply them twice. It is handed
  `st.session_state["tipos_campos_base"]`, set once by `_abrir`.
- `_de_tabla` preserves per-field keys the table does not show (notably `sinonimos`)
  by matching on `clave`, so renaming a label does not silently drop the spellings
  that were already accepted.
- Widget keys in the form are namespaced `campo_{tipo_id}_{clave}` — two types sharing
  a field name would otherwise collide in `DuplicateWidgetID`.
- Changing the type selector pops `resultado` and `masivo` from session state, for the
  same reason a failed validation pops `resultado`: never leave a downloadable
  document from the previous type next to the new one.
- `guardar` compares the target's mtime against `_marca` and refuses a **lost write**.
  With no login and everything editable, two people saving the same type is real.

## Known limitations

- **The app writes to disk for the first time**, in `plantillas/personalizadas/`.
  I do not know where this app is hosted, so **I do not know whether that disk
  survives** a restart or a redeploy. If it does not, created types vanish with no
  warning. The «Exportar .json» button is the mitigation and the editor tab says so on
  screen. **Assumption:** the Streamlit process can write to the project directory; if
  it cannot, `guardar` fails and `PERSONALIZADAS` has to become configurable.
- **No login, everything editable, no audit trail.** Anyone with the URL can rewrite
  the legal text that gets signed, and nothing records who or when beyond the file
  mtime. «Restaurar el original» recovers a built-in type; a web-created type has
  nowhere to go back to except its exported `.json`. This was an explicit decision.
- **Page furniture is not configurable.** The logo and the four footer lines stay in
  `documento.py`; a type can only change the header title.
- **Anyone pasting a contract from Word will hit the Markdown subset** — headings,
  numbered lists and italics print literally. The checker and the preview make that
  *visible*, which is all that is possible without widening the converter.
- **The logo prints soft.** `LogoUninades.png` is 141×66 px; at 1.2" that is ~118 dpi
  against ~300 dpi for crisp print. Fix by dropping a higher-resolution file at the
  same path — no code change needed.
- **Page breaks do not match the PDF.** Calibri metrics and spacing differ from the
  original typesetting, so page count may vary.
- **The `missolicitudes` URL is plain text**, not a hyperlink — python-docx has no
  hyperlink API.
- **Column widths (2.6"/3.9") and the 6.5 pt footer are estimates**, not measured from
  the PDF.
- **Original typos are transcribed verbatim** (e.g. "definidos por misma", missing
  "la", in Parágrafo 3 of CLÁUSULA SEGUNDA). This is official legal wording; don't
  silently "fix" it — raise it instead.
- **No field length is validated anywhere**, and neither is a body's. Not in the form
  (no `max_chars` — it truncates a paste silently, which is the same class of silent
  data loss as the `|` bug), not in the bulk load. A runaway paste into a text field
  reaches the `.docx`, and an absurdly long name produces an absurdly long filename
  (`nombre_archivo` does not truncate: 300 chars in, 333 out). The suggested lengths
  are documented in [campos_y_restricciones.md](campos_y_restricciones.md) and
  enforced by nobody. This was a deliberate call, not an oversight.
- **The cédula's digit count is not checked** either — `1` and `999999999999` both
  pass. Worth knowing: a 10-digit cap would double as a second line of defence
  against the float bug below, since `cedula(1020345678.0)` yields exactly 11 digits.
- **Pasting into the Excel template destroys the dropdowns.** Excel pastes the source
  cell's validation over the target's. That is why `campos.GENERO_SINONIMOS` and a
  field's `sinonimos` are generous when reading even though the template offers only
  the listed options.
- **No per-row download in bulk mode** — it is the whole `.zip` or nothing.
- **The dropdown arrow, the localized number formats, and whether Excel-saved cells
  come back as `datetime`/`int` can only be confirmed by opening the file in real
  Excel.** They fail *silently* (a file that opens fine but has no dropdown), not with
  an exception, and the entire date policy plus the cédula fix rest on the last one.

The next three are properties of `documento.py`, which exists precisely to be called
*without* the UI. All callers guard them via `campos.py` and `tipos.validar`; **any
new non-UI caller has to do the same.**

- **A `|` or `**` in a field value silently corrupts the document.** Text fields get
  substituted into `| a | b |` table rows, so `direccion = "Calle 1 | Apto 2"` renders
  a three-cell row; `_escribir_tabla` sizes the table from `len(filas[0])` (two
  columns) and the `zip()` discards the rest — `Apto 2` vanishes with no error. A `**`
  shifts the parity in `_escribir_runs` and inverts the bold. A newline is worse: it
  ends the table block and splits the table in two. `campos.revisar` rejects the first
  two; the newline is collapsed to a space with an aviso.
- **`cedula` mis-renders a float.** `cedula(1020345678.0)` returns
  `"10.203.456.780"` — `str(float)` keeps the `.0` and the `re.sub(r"\D", …)` swallows
  the dot, adding a digit. `cedula("1.02E+09")` is worse: `"10.209"`, six digits
  instead of ten. `st.number_input` hands over an `int` and `campos._entero` never
  routes a float through `str()`, so both modes are safe today.
- **`nombre_archivo` can collide.** `_slug` strips accents and lowercases, so
  "María García" and "Maria Garcia" produce the same filename, and a name with no
  ASCII-able characters produces an empty part that is dropped
  (`otrosi_teletrabajo_20260806.docx`). Harmless for one browser download at a time;
  `masivo._nombres_unicos` de-duplicates for the `.zip`.

## Running it

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run otrosi.py
```

Generated `.docx` files are meant to land in a local `documentos/` folder
(gitignored, doesn't exist by default — the app only offers a browser download, it
doesn't write to disk itself, other than saved types).

`tipos.py`, `campos.py` and `masivo.py` are usable without Streamlit, which is what
keeps the layering honest. To check that it stays true:

```python
import sys
from datetime import date
import tipos, campos, masivo, documento
tipo = tipos.cargar("teletrabajo_hibrido")
assert not tipos.validar(tipo)[0]
xlsx = masivo.construir_plantilla(tipo)
registros, errores = masivo.leer_libro(tipo, xlsx, date.today())
paquete, fallos, generados = masivo.generar_zip(tipo, registros)
assert "streamlit" not in sys.modules
```

**The regression that matters most** when touching the renderer: render
`teletrabajo_hibrido` with a fixed payload for both gender branches and diff the
Markdown against a saved reference. The migration from Jinja to markers was verified
byte-for-byte that way, and it is the only thing that guarantees the signed document
did not change.

## Conventions

- Spanish throughout: identifiers, UI labels, docstrings, comments. Keep it that way.
- `snake_case` for functions/variables; Spanish domain terms (`otrosi`, `plantillas`,
  `concordancia`, `teletrabajador`, `marcadores`) are the established vocabulary —
  don't rename to English equivalents.
- One-line docstrings with an `input -> output` example on helpers; `_`-prefixed
  privates.
- Comments are rare and used only for non-obvious caveats (the `isinstance(True, int)`
  ordering in `campos.faltantes`, why justification is per-paragraph rather than on the
  `Normal` style, why the header tab stop is recomputed, why the Excel dropdowns point
  at a range instead of an inline list, why the filter separator is `:`, why
  `data_editor` is handed a fixed baseline). Match that density.
- **`campos._INVISIBLES` must keep its `\uXXXX` escapes.** Writing those characters
  literally is invisible in a diff and un-editable; it has already regressed twice.
- Spanish identifiers include the accented ones: `_pestaña_individual`,
  `HOJA_DATOS = "Otrosíes"`. Python 3 allows them and the repo uses them.
