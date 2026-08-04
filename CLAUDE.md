# GenOtrosi

Streamlit tool for generating "otrosí" documents — labor contract amendment
addenda — for Universidad de los Andes. HR/legal staff fill in a form for one
employee at a time and download a `.docx` ready for signature (after legal
review). The codebase, UI text, variable names, and comments are entirely in
**Spanish** — this is intentional (the domain, the templates, and the end
users are Spanish-speaking) and should not be translated when editing.

## Why this exists

Contract amendments are currently a manual, ad-hoc drafting process. The
operational pain point driving this project is volume and cadence: amendments
get processed in batches roughly every 15 days, and manual drafting is the
bottleneck. The app is deliberately architected so that a future bulk/mass
mode can reuse the same document-generation logic — see [documento.py](documento.py)'s
module docstring. That bulk mode does not exist yet; today the app handles
one otrosí per form submission.

## Architecture

Two-module split, deliberately:

- [otrosi.py](otrosi.py) — Streamlit UI only. Renders the global fields
  (`render_globales`) plus one of five per-type field renderers (`RENDERERS`,
  keyed 1–5), validates required fields (`campos_faltantes`), and assembles a
  `payload` dict: `{tipo_id, tipo, generales, detalle}`. `generales` holds the
  fields common to every otrosí type; `detalle` holds the fields specific to
  the selected type. This payload shape is the contract between the UI and
  the document generator.
- [documento.py](documento.py) — has **no Streamlit dependency**, by design,
  so that a future batch/mass entry point can call `render_markdown` /
  `markdown_a_docx` directly per record without going through the UI. Given a
  `payload`, it renders a Jinja2 template to Markdown, then converts that
  Markdown to a `.docx` via `python-docx`. Custom Jinja filters: `moneda`
  (Colombian currency formatting), `fecha_larga`, `fecha_hora_larga`.

When adding a new otrosí type or field, keep this split: form/validation logic
in `otrosi.py`, payload-to-document logic in `documento.py`.

## Templates (`plantillas/`)

Jinja2 templates using base + block inheritance: [base.md.j2](plantillas/base.md.j2)
contains the fixed contract boilerplate (parties, signature block) and
defines a `clausula` block; each `N_<tipo>.md.j2` extends it and fills
`clausula` with that type's specific language.

`markdown_a_docx` in `documento.py` converts the *rendered* Markdown to
`.docx` by hand-parsing a narrow subset: `# ` / `## ` headings, `- ` bullets,
`**bold**`, and paragraphs separated by blank lines. **No tables, links, or
other Markdown constructs are supported** — any new or edited template must
stay within this subset, or `markdown_a_docx` will render it incorrectly
(most other syntax just passes through as a literal paragraph).

Every template carries a `REVISIÓN JURÍDICA PENDIENTE` comment, and the
`EMPLEADOR` dict in `documento.py` (NIT, legal representative) is a marked
placeholder pending confirmation from RRHH. Treat all contract wording as
draft legal language, not final — don't remove these markers or present the
output as signature-ready unless told the legal/HR review has happened.

## Domain model

### Fields common to every otrosí type (`generales`)

| Field | Code key | Type |
|---|---|---|
| Employee name | `nombre_empleado` | string |
| Employee ID (cédula) | `cedula` | string (free text, not int — preserves formatting) |
| Contract number | `numero_contrato` | string |
| Otrosí date | `fecha_otrosi` | datetime |
| City | `ciudad` | enum, see `CIUDADES` in [otrosi.py](otrosi.py) |

### The 5 types (`tipo_id` 1–5, `detalle`)

1. **Salary increase/adjustment** (`render_incremento_salarial` / `1_incremento_salarial.md.j2`) — `salario_anterior`/`salario_nuevo` (`{monto, nota}`), `periodicidad` (`{valor, unidad: días|meses}`), `fecha_efectividad`.
2. **Role change / promotion** (`render_cambio_cargo` / `2_cambio_cargo.md.j2`) — `cargo_anterior`, `cargo_nuevo`, `area` (`oficina|casa`), `jefe_inmediato`, `funciones_nuevas` (list), optional `salario` (`{monto, nota}`).
3. **Change of workplace** (`render_cambio_lugar` / `3_cambio_lugar.md.j2`) — `lugar_anterior`, `lugar_nuevo`, `tipo_modalidad` (`remoto|híbrido|oficina`).
4. **Schedule/shift change** (`render_cambio_jornada` / `4_cambio_jornada.md.j2`) — `jornada_anterior_horas`, `jornada_nueva_horas` (int hours), optional `horario_anterior`/`horario_nuevo`.
5. **Contract renewal** (`render_renovacion_contrato` / `5_renovacion_contrato.md.j2`) — `fecha_vencimiento_actual`, `periodo_prueba_dias`; if `termino_fijo`: `nuevo_plazo_dias`, `fecha_terminacion`.

This mirrors the original business brief field-by-field; if the two ever
diverge, treat the brief as intent and the code as current implementation
status, and call out the gap rather than silently picking one.

## Known gaps vs. the original brief

Not yet implemented anywhere in the code — don't assume these exist:

- Contractor's address (*dirección del contratista*).
- Whether equipment is the contractor's own or provided by the university.
- "Modalidad" and "nombre de usuario" as fields at the *global* level (as
  opposed to `tipo_modalidad`, which only exists inside the workplace-change
  type today).
- A bulk/mass-generation entry point (CLI, batch upload, etc.) that reuses
  `documento.py` across many records — this is the stated end goal, but only
  the single-record Streamlit form exists so far.

## Running it

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run otrosi.py
```

Generated `.docx` files are meant to land in a local `documentos/` folder
(gitignored, doesn't exist by default — the current app only offers a
browser download, it doesn't write to disk itself).

## Conventions

- Spanish throughout: identifiers, UI labels, docstrings, comments. Keep it that way.
- `snake_case` for functions/variables; Spanish domain terms (`otrosi`, `plantillas`, `detalle`, `generales`) are the established vocabulary — don't rename to English equivalents.
- Comments are rare and used only for non-obvious caveats (legal-review-pending markers, format notes like the currency helper). Match that density.
