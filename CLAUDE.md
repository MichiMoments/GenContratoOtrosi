# GenOtrosi

Streamlit tool for generating the **otrosí de teletrabajo híbrido** — the hybrid
telework amendment to a labor contract — for Universidad de los Andes. HR staff
fill in a form for one employee at a time and download a `.docx` ready for
signature. The codebase, UI text, variable names, and comments are entirely in
**Spanish** — this is intentional (the domain, the template, and the end users
are Spanish-speaking) and should not be translated when editing.

## Why this exists

Contract amendments are currently a manual, ad-hoc drafting process. The
operational pain point driving this project is volume and cadence: amendments
get processed in batches roughly every 15 days, and manual drafting is the
bottleneck. The app is deliberately architected so that a future bulk/mass mode
can reuse the same document-generation logic — see [documento.py](documento.py)'s
module docstring. That bulk mode does not exist yet; today the app handles one
otrosí per form submission.

## Architecture

Two-module split, deliberately:

- [otrosi.py](otrosi.py) — Streamlit UI only. `render_formulario` renders all 14
  fields and returns a **flat dict** — that dict *is* the contract between the UI
  and the document generator. `campos_faltantes` validates it, `resumen` renders
  the values for on-screen verification.
- [documento.py](documento.py) — has **no Streamlit dependency**, by design, so
  that a future batch/mass entry point can call `render_markdown` /
  `markdown_a_docx` / `nombre_archivo` directly per record without going through
  the UI. Given the flat dict, it renders a Jinja2 template to Markdown, then
  converts that Markdown to a `.docx` via `python-docx`.

The payload is flat (not `{generales, detalle}`) because a bulk-mode spreadsheet
row maps onto it one-to-one — `df.to_dict("records")` needs no mapping layer.
`StrictUndefined` in the Jinja env is what makes a missing key fail loudly at
render time instead of silently emitting a blank field into a legal document.

When adding a field, keep this split: widget + label + validation in `otrosi.py`,
wording and layout in `documento.py` / the template.

## Domain model

The 14 fields of the flat payload:

| Field | Code key | Type |
|---|---|---|
| Employee name | `nombre` | string |
| ID number (cédula) | `documento_identidad` | int, printed via the `cedula` filter as `1.020.345.678` |
| Contract start date | `fecha_ingreso` | date |
| Job title | `cargo` | string |
| Department | `dependencia` | string — printed verbatim, article included (`la Dirección de…`) |
| Unit | `unidad` | string |
| Gender | `teletrabajadora` | bool — `True` = feminine |
| Telework start date | `fecha_inicio_teletrabajo` | date |
| Days per week | `dos_dias` | bool — `True` = "Dos (2) días por semana" |
| Telework address | `direccion` | string |
| City/municipality | `ciudad` | string, free text (any Colombian municipality) |
| Computer | `computador` | string |
| Computer type | `tipo_computador` | string |
| Signature date | `fecha_firma` | date, defaults to today |

`ETIQUETAS` in `otrosi.py` is the single source of truth for labels — the same
string appears in the widget, the validation error, and the verification summary.

### Gender agreement

`«Teletrabajadora»` in the source document alternates between feminine and
masculine, and Spanish contracts `a`+`el` → `al` and `de`+`el` → `del`. So the
`CONCORDANCIA` dict in `documento.py` enumerates **whole phrases**, not just the
noun — inserting `"el Teletrabajador"` after `de` would produce `de el`.

| Key | Feminine | Masculine |
|---|---|---|
| `identificado` | identificada | identificado |
| `teletrabajador` | la Teletrabajadora | el Teletrabajador |
| `al_teletrabajador` | a la Teletrabajadora | al Teletrabajador |
| `del_teletrabajador` | de la Teletrabajadora | del Teletrabajador |
| `de_la_misma` | de la misma | del mismo |

In the template: `{{ teletrabajador }}` mid-sentence,
`{{ teletrabajador | mayuscula_inicial }}` sentence-initial, `{{ teletrabajador | upper }}`
in the signature block. Jinja's own `|capitalize` is wrong here — it lowercases
the rest of the string.

## Template (`plantillas/`)

One template: [otrosi_teletrabajo_hibrido.md.j2](plantillas/otrosi_teletrabajo_hibrido.md.j2),
a verbatim transcription of the institutional PDF. No base/block inheritance —
that existed only to share boilerplate across five document types that no longer
exist.

`markdown_a_docx` in `documento.py` converts the *rendered* Markdown to `.docx`
by hand-parsing a narrow subset, **block by block** (blank line = block
separator, so a paragraph can span several source lines):

- paragraphs — consecutive non-blank lines, joined with a space
- `- ` bullets
- `**bold**`
- `| a | b |` tables (a `|---|---|` separator row, if present, is discarded)
- `<!-- tabla-sin-bordes -->` — makes the **next** table borderless
- leading spaces on a block's first line → left indent, 0.25" per 4 spaces

**Nothing else is supported** — no headings, links, or other Markdown; anything
else passes through as a literal paragraph. Three traps when editing the
template: no wrapped line may begin with `- ` or `|`, and no table cell may
contain a literal `|`.

The page header (logo + title) and the 4-line footer are built in Python by
`_construir_encabezado` / `_construir_pie`, **not** in the Markdown. Two reasons:
Markdown cannot express page furniture at all, and the footer contains a literal
`|` ("Universidad de los Andes **|** Vigilada Mineducación") that the table
parser would misread. `different_first_page_header_footer` is left `False`, which
is what makes both repeat on every page.

`plantillas/LogoUninades.png` is embedded into the header via `add_picture` at
1.2" wide. python-docx reads PNGs natively — **Pillow is not a dependency**, do
not add it.

## Known limitations

- **The logo prints soft.** `LogoUninades.png` is 141×66 px; at 1.2" that is
  ~118 dpi against ~300 dpi for crisp print. Fix by dropping a higher-resolution
  file at the same path — no code change needed.
- **Page breaks do not match the PDF.** Calibri metrics and spacing differ from
  the original typesetting, so page count may vary.
- **The `missolicitudes` URL is plain text**, not a hyperlink — python-docx has
  no hyperlink API.
- **Column widths (2.6"/3.9") and the 6.5 pt footer are estimates**, not measured
  from the PDF.
- **Original typos are transcribed verbatim** (e.g. "definidos por misma", missing
  "la", in Parágrafo 3 of CLÁUSULA SEGUNDA). This is official legal wording;
  don't silently "fix" it — raise it instead.
- **No bulk/mass-generation entry point yet** (CLI, spreadsheet upload). This is
  the stated end goal; only the single-record Streamlit form exists so far. The
  flat payload and the Streamlit-free `documento.py` are the groundwork for it.

## Running it

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run otrosi.py
```

Generated `.docx` files are meant to land in a local `documentos/` folder
(gitignored, doesn't exist by default — the current app only offers a browser
download, it doesn't write to disk itself).

## Conventions

- Spanish throughout: identifiers, UI labels, docstrings, comments. Keep it that way.
- `snake_case` for functions/variables; Spanish domain terms (`otrosi`,
  `plantillas`, `concordancia`, `teletrabajador`) are the established vocabulary
  — don't rename to English equivalents.
- One-line docstrings with an `input -> output` example on helpers; `_`-prefixed
  privates.
- Comments are rare and used only for non-obvious caveats (the `isinstance(True, int)`
  ordering in `campos_faltantes`, why justification is per-paragraph rather than
  on the `Normal` style, why the header tab stop is recomputed). Match that density.
