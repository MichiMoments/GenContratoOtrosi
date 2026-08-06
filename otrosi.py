"""Otrosí de teletrabajo híbrido - front-end Streamlit."""

from datetime import date

import streamlit as st

import documento

# Las etiquetas de las opciones son literalmente el texto que sale en el documento,
# para que el formulario no pueda desincronizarse de lo que se firma.
GENERO = {
    True: "Femenino — «la Teletrabajadora», «identificada»",
    False: "Masculino — «el Teletrabajador», «identificado»",
}

DIAS = documento.DIAS_TELETRABAJO

# Atajo para los casos frecuentes; el selectbox acepta cualquier otro municipio.
CIUDADES_FRECUENTES = [
    "Bogotá D.C.",
    "Medellín",
    "Cali",
    "Barranquilla",
    "Cartagena",
    "Bucaramanga",
]

# Única fuente de verdad de las etiquetas: widget, mensaje de error y resumen.
ETIQUETAS = {
    "nombre": "Nombre",
    "documento_identidad": "Documento de identidad",
    "fecha_ingreso": "Fecha de ingreso",
    "cargo": "Cargo",
    "dependencia": "Dependencia",
    "unidad": "Unidad",
    "teletrabajadora": "Género en el documento",
    "fecha_inicio_teletrabajo": "Fecha de inicio del teletrabajo",
    "dos_dias": "Días de teletrabajo asignados",
    "direccion": "Dirección del lugar de teletrabajo",
    "ciudad": "Ciudad o municipio donde teletrabajará",
    "computador": "Computador",
    "tipo_computador": "Tipo de computador",
    "fecha_firma": "Fecha de firma",
}

# Hoy todos los campos son obligatorios; este es el único lugar donde se decide.
OBLIGATORIOS = tuple(ETIQUETAS)

FECHA_MINIMA = date(1970, 1, 1)
FECHA_MAXIMA = date(2100, 12, 31)

MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def campos_faltantes(campos):
    faltantes = []
    for label, valor in campos:
        if isinstance(valor, bool):  # isinstance(True, int) es True: esta rama va primero
            continue
        if valor is None:
            faltantes.append(label)
        elif isinstance(valor, str) and not valor.strip():
            faltantes.append(label)
        elif isinstance(valor, int) and valor <= 0:
            faltantes.append(label)
    return faltantes


def render_formulario():
    """Los 14 campos del otrosí; devuelve el payload plano que consume documento.py."""
    datos = {}

    st.subheader("Datos de la persona teletrabajadora")
    datos["nombre"] = st.text_input(ETIQUETAS["nombre"], key="nombre")
    datos["documento_identidad"] = st.number_input(
        ETIQUETAS["documento_identidad"],
        min_value=1,
        value=None,
        step=1,
        format="%d",
        placeholder="Solo números, sin puntos",
        key="documento_identidad",
    )
    datos["fecha_ingreso"] = st.date_input(
        ETIQUETAS["fecha_ingreso"],
        value=None,
        min_value=FECHA_MINIMA,  # sin esto el calendario solo llega a hoy - 10 años
        max_value=date.today(),
        format="DD/MM/YYYY",
        key="fecha_ingreso",
    )
    datos["cargo"] = st.text_input(ETIQUETAS["cargo"], key="cargo")
    datos["dependencia"] = st.text_input(
        ETIQUETAS["dependencia"],
        placeholder="la Dirección de Gestión Humana y Desarrollo Organizacional",
        help="Se imprime tal cual, incluido el artículo: «se desempeña como X en ___ en Y».",
        key="dependencia",
    )
    datos["unidad"] = st.text_input(ETIQUETAS["unidad"], key="unidad")
    datos["teletrabajadora"] = st.radio(
        ETIQUETAS["teletrabajadora"],
        [True, False],
        index=None,
        format_func=lambda valor: GENERO[valor],
        help="Define la concordancia de género en todo el documento.",
        key="teletrabajadora",
    )

    st.subheader("Condiciones de teletrabajo")
    datos["fecha_inicio_teletrabajo"] = st.date_input(
        ETIQUETAS["fecha_inicio_teletrabajo"],
        value=None,
        min_value=FECHA_MINIMA,
        max_value=FECHA_MAXIMA,
        format="DD/MM/YYYY",
        key="fecha_inicio_teletrabajo",
    )
    datos["dos_dias"] = st.radio(
        ETIQUETAS["dos_dias"],
        [True, False],
        index=None,
        format_func=lambda valor: DIAS[valor],
        key="dos_dias",
    )
    datos["direccion"] = st.text_input(ETIQUETAS["direccion"], key="direccion")
    datos["ciudad"] = st.selectbox(
        ETIQUETAS["ciudad"],
        CIUDADES_FRECUENTES,
        index=None,
        accept_new_options=True,
        placeholder="Selecciona o escribe el municipio",
        key="ciudad",
    )

    st.subheader("Equipo asignado")
    datos["computador"] = st.text_input(ETIQUETAS["computador"], key="computador")
    datos["tipo_computador"] = st.text_input(
        ETIQUETAS["tipo_computador"], key="tipo_computador"
    )

    st.subheader("Firma")
    datos["fecha_firma"] = st.date_input(
        ETIQUETAS["fecha_firma"],
        value=date.today(),
        min_value=FECHA_MINIMA,
        max_value=FECHA_MAXIMA,
        format="DD/MM/YYYY",
        key="fecha_firma",
    )

    return datos


def resumen(datos):
    """Valores tal como quedarán impresos, para verificarlos antes de descargar."""
    # usa los mismos filtros que el .docx, así el resumen no puede desincronizarse
    impreso = {
        "documento_identidad": f"No. {documento.cedula(datos['documento_identidad'])}",
        "fecha_ingreso": documento.fecha_larga(datos["fecha_ingreso"]),
        "fecha_inicio_teletrabajo": documento.fecha_larga(datos["fecha_inicio_teletrabajo"]),
        "fecha_firma": documento.fecha_larga(datos["fecha_firma"]),
        "teletrabajadora": GENERO[datos["teletrabajadora"]],
        "dos_dias": DIAS[datos["dos_dias"]],
    }
    return [(ETIQUETAS[clave], impreso.get(clave, datos[clave])) for clave in ETIQUETAS]


def mostrar_resultado(resultado):
    st.divider()
    st.success("Documento generado.")

    st.subheader("Verifica antes de descargar")
    st.caption(
        "Refleja los datos del último «Generar otrosí». Si cambias un campo, "
        "vuelve a generarlo."
    )
    for etiqueta, valor in resumen(resultado["datos"]):
        st.markdown(f"- **{etiqueta}:** {valor}")

    # on_click="ignore" evita el rerun que antes borraba este bloque al descargar
    st.download_button(
        "Descargar .docx",
        data=resultado["docx"],
        file_name=resultado["archivo"],
        mime=MIME_DOCX,
        on_click="ignore",
        type="primary",
    )

    with st.expander("Ver Markdown intermedio (no es el .docx)"):
        st.caption("No incluye el encabezado, el pie ni el logo: esos los arma documento.py.")
        st.code(resultado["markdown"], language="markdown")


def main():
    st.set_page_config(page_title="Otrosí de teletrabajo híbrido", page_icon="📄")
    st.title("Otrosí de teletrabajo híbrido")
    st.caption("Universidad de los Andes — Dirección de Gestión Humana y Desarrollo Organizacional")

    # el formulario evita que cada tecleo dispare un rerun, y deja los valores en
    # pantalla alineados con el documento que se generó
    with st.form("otrosi_teletrabajo"):
        datos = render_formulario()
        enviado = st.form_submit_button("Generar otrosí", type="primary")

    if enviado:
        faltantes = campos_faltantes(
            [(ETIQUETAS[clave], datos[clave]) for clave in OBLIGATORIOS]
        )
        if faltantes:
            # no dejar descargable el documento anterior junto a un error
            st.session_state.pop("resultado", None)
            st.error("Faltan campos obligatorios: " + ", ".join(faltantes))
        else:
            md = documento.render_markdown(datos)
            st.session_state["resultado"] = {
                "datos": datos,
                "markdown": md,
                "docx": documento.markdown_a_docx(md),
                "archivo": documento.nombre_archivo(datos),
            }

    resultado = st.session_state.get("resultado")
    if resultado:
        mostrar_resultado(resultado)


if __name__ == "__main__":
    main()
