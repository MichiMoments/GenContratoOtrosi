"""Generador de otrosíes - front-end Streamlit."""

import hashlib
from datetime import date

import streamlit as st

import campos
import documento
import masivo
import tipos

from campos import FECHA_MAXIMA, FECHA_MINIMA

MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MIME_ZIP = "application/zip"
MIME_JSON = "application/json"

TOPE_MENSAJES = 50  # con 300 filas la lista de errores puede tapar la pantalla entera

TOPE_RADIO = 4  # con más opciones que estas, un desplegable ocupa mucho menos

# Valores con que se previsualiza un campo al que no se le puso ejemplo.
EJEMPLO_POR_TIPO = {"texto": "(ejemplo)", "cedula": "1020345678", "entero": "1"}

ORIGENES = {
    "integrado": "viene con la app",
    "integrado_editado": "integrado, con cambios guardados aquí",
    "personalizado": "creado aquí",
}


def _etiqueta_genero(valor):
    """True -> 'Femenino — «la Teletrabajadora», «identificada»'."""
    # se arma desde CONCORDANCIA para que el formulario no pueda desincronizarse de lo
    # que dirá el documento firmado
    concordancia = documento.CONCORDANCIA[valor]
    return (
        f"{documento.GENERO[valor]} — «{concordancia['teletrabajador']}», "
        f"«{concordancia['identificado']}»"
    )


def _widget(tipo, campo):
    """Pinta el widget que corresponde al tipo del campo y devuelve su valor."""
    # la clave lleva el id del tipo: dos tipos que compartan un nombre de campo chocarían
    # en DuplicateWidgetID
    clave = f"campo_{tipo['id']}_{campo['clave']}"
    etiqueta, ayuda = campo["etiqueta"], campo["ayuda"] or None

    if campo["tipo"] in ("cedula", "entero"):
        return st.number_input(
            etiqueta, min_value=1, value=None, step=1, format="%d",
            placeholder="Solo números, sin puntos", help=ayuda, key=clave,
        )
    if campo["tipo"] == "fecha":
        return st.date_input(
            etiqueta,
            # la que rellena la app en el Excel viene puesta con la de hoy en el formulario
            value=date.today() if campo["opcional_en_hoja"] else None,
            min_value=FECHA_MINIMA,  # sin esto el calendario solo llega a hoy - 10 años
            max_value=date.today() if campo["no_futura"] else FECHA_MAXIMA,
            format="DD/MM/YYYY", help=ayuda, key=clave,
        )
    if campo["tipo"] == "genero":
        return st.radio(
            etiqueta, [True, False], index=None, format_func=_etiqueta_genero,
            help=ayuda or "Define la concordancia de género en todo el documento.", key=clave,
        )
    if opciones := tipos.opciones(campo):
        if len(opciones) <= TOPE_RADIO:
            return st.radio(etiqueta, opciones, index=None, help=ayuda, key=clave)
        return st.selectbox(etiqueta, opciones, index=None, help=ayuda, key=clave)
    if campo["sugerencias"]:
        return st.selectbox(
            etiqueta, campo["sugerencias"], index=None, accept_new_options=True,
            placeholder="Selecciona o escribe", help=ayuda, key=clave,
        )
    return st.text_input(
        etiqueta, placeholder=campo["ejemplo"] or None, help=ayuda, key=clave
    )


def render_formulario(tipo):
    """Los campos del tipo; devuelve el payload plano que consume documento.py."""
    datos, grupo = {}, None
    for campo in tipo["campos"]:
        if campo["grupo"] and campo["grupo"] != grupo:
            grupo = campo["grupo"]
            st.subheader(grupo)
        datos[campo["clave"]] = _widget(tipo, campo)
    return datos


def resumen(tipo, datos):
    """Valores tal como quedarán impresos, para verificarlos antes de descargar."""
    # el mismo contexto que usa el .docx, así el resumen no puede desincronizarse
    impreso = documento.contexto(tipo, datos)
    filas = []
    for campo in tipo["campos"]:
        clave, valor = campo["clave"], datos.get(campo["clave"])
        if campo["tipo"] == "genero":
            texto = _etiqueta_genero(valor) if isinstance(valor, bool) else ""
        elif campo["tipo"] == "cedula":
            texto = f"No. {impreso.get(clave, '')}"
        else:
            texto = impreso.get(clave, "" if valor is None else valor)
        filas.append((campo["etiqueta"], texto))
    return filas


def mostrar_resultado(tipo, resultado):
    st.divider()
    st.success("Documento generado.")

    st.subheader("Verifica antes de descargar")
    st.caption(
        "Refleja los datos del último «Generar otrosí». Si cambias un campo, "
        "vuelve a generarlo."
    )
    for etiqueta, valor in resumen(tipo, resultado["datos"]):
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


def _pestaña_individual(tipo):
    # el formulario evita que cada tecleo dispare un rerun, y deja los valores en
    # pantalla alineados con el documento que se generó
    with st.form(f"otrosi_{tipo['id']}"):
        datos = render_formulario(tipo)
        enviado = st.form_submit_button("Generar otrosí", type="primary")

    if enviado:
        problemas = []
        if faltantes := campos.faltantes(tipo, datos):
            etiquetas = tipos.etiquetas(tipo)
            problemas.append(
                "Faltan campos obligatorios: "
                + ", ".join(etiquetas[clave] for clave in faltantes)
            )
        # los mismos caracteres prohibidos que en la carga masiva: la validación vive en
        # campos.py justamente para que los dos modos no puedan divergir
        problemas.extend(campos.revisar(tipo, datos))
        if problemas:
            # no dejar descargable el documento anterior junto a un error
            st.session_state.pop("resultado", None)
            st.error("\n\n".join(problemas))
        else:
            md = documento.render_markdown(tipo, datos)
            st.session_state["resultado"] = {
                "datos": datos,
                "markdown": md,
                "docx": documento.markdown_a_docx(md, tipo["titulo"]),
                "archivo": documento.nombre_archivo(tipo, datos),
            }

    if resultado := st.session_state.get("resultado"):
        mostrar_resultado(tipo, resultado)


def _vista_previa(tipo, registros):
    """Filas válidas con los filtros del .docx: aquí se ve un «4 de marzo» al revés."""
    return [
        {"Fila": registro["fila"], "Archivo": registro["archivo"],
         **dict(resumen(tipo, registro["datos"]))}
        for registro in registros
    ]


def _recortar(mensajes):
    """Recorta la lista para no tapar la pantalla: 60 mensajes -> los 50 y «y 10 más»."""
    if len(mensajes) <= TOPE_MENSAJES:
        return mensajes
    return mensajes[:TOPE_MENSAJES] + [f"y {len(mensajes) - TOPE_MENSAJES} más"]


def _lista(mensajes):
    """Los mensajes como viñetas de Markdown para un st.error o un st.warning."""
    return "\n".join(f"- {mensaje}" for mensaje in _recortar(mensajes))


def _campo_del_lote(tipo):
    """El campo de fecha que rellena el selector del lote, si el tipo tiene alguno."""
    for campo in tipo["campos"]:
        if campo["opcional_en_hoja"] and campo["tipo"] == "fecha":
            return campo
    return None


def _pestaña_masiva(tipo):
    st.subheader("Paso 1 · Descarga la plantilla")
    st.caption(
        f"Una fila por persona, hasta {masivo.MAXIMO_FILAS}. Las instrucciones y los "
        "valores permitidos van en la segunda hoja."
    )
    st.download_button(
        "Descargar plantilla",
        # la función y no los bytes: no se arma el .xlsx hasta que se hace clic
        data=lambda: masivo.construir_plantilla(tipo),
        file_name=f"plantilla_{tipo['id']}.xlsx",
        mime=MIME_XLSX,
        on_click="ignore",
        key="masivo_plantilla",
    )

    st.subheader("Paso 2 · Sube la plantilla diligenciada")
    archivo = st.file_uploader("Archivo .xlsx", type=["xlsx"], key="masivo_archivo")
    del_lote = _campo_del_lote(tipo)
    fecha_lote = date.today()
    if del_lote:
        fecha_lote = st.date_input(
            del_lote["etiqueta"] + " del lote",
            value=date.today(),
            min_value=FECHA_MINIMA,
            max_value=FECHA_MAXIMA,
            format="DD/MM/YYYY",
            help="Rellena las filas que dejes en blanco en esa columna de la hoja.",
            key="masivo_fecha_firma",
        )
    if archivo is None:
        st.session_state.pop("masivo", None)
        return

    contenido = archivo.getvalue()
    huella = hashlib.sha256(contenido + tipo["id"].encode()).hexdigest()
    guardado = st.session_state.get("masivo")
    if guardado and guardado["huella"] != huella:
        # el análogo masivo de no dejar descargable el documento anterior junto a un error
        st.session_state.pop("masivo", None)

    # se parsea en cada rerun, sin caché: son decenas de milisegundos y elimina toda una
    # clase de errores por caché obsoleta
    registros, errores = masivo.leer_libro(tipo, contenido, fecha_lote)
    avisos = [aviso for registro in registros for aviso in registro["avisos"]]
    validos = [registro for registro in registros if not registro["errores"]]

    if errores:
        st.error(_lista(errores), title="Corrige el archivo y vuelve a subirlo")
    if avisos:
        st.warning(_lista(avisos), title="Revisa estos puntos; no impiden generar")
    if validos:
        st.subheader("Paso 3 · Verifica antes de generar")
        st.caption("Los valores ya están como saldrán impresos en el .docx.")
        st.dataframe(_vista_previa(tipo, validos), hide_index=True)

    if st.button(
        f"Generar {len(validos)} otrosíes",
        type="primary",
        disabled=bool(errores) or not validos,
        key="masivo_generar",
    ):
        with st.status(f"Generando {len(validos)} documentos…") as estado:
            barra = st.progress(0.0)
            paquete, fallos, generados = masivo.generar_zip(
                tipo,
                validos,
                lambda hechos, total: barra.progress(hechos / total, f"{hechos} de {total}"),
            )
            estado.update(label=f"{len(generados)} documentos listos.", state="complete")
        st.session_state["masivo"] = {
            "huella": huella,
            "zip": paquete,
            "fallos": fallos,
            "archivos": generados,  # solo los que de verdad entraron al .zip
        }

    guardado = st.session_state.get("masivo")
    if not guardado:
        return
    st.divider()
    st.success(f"{len(guardado['archivos'])} documentos generados.")
    st.download_button(
        "Descargar .zip",
        data=guardado["zip"],
        file_name=f"{tipo['prefijo_archivo']}_{fecha_lote:%Y%m%d}.zip",
        mime=MIME_ZIP,
        on_click="ignore",
        type="primary",
        key="masivo_zip",
    )
    if guardado["fallos"]:
        # una fila que falle al renderizar no mata el lote: el resto se entrega, anotado
        st.warning(_lista(guardado["fallos"]), title="Filas que no se pudieron generar")
    with st.expander(f"Ver los {len(guardado['archivos'])} archivos del .zip"):
        for nombre in guardado["archivos"]:
            st.markdown(f"- `{nombre}`")


# ---------------------------------------------------------------- editor de tipos


COLUMNAS = {
    "Clave": "Lo que se escribe entre {{ }} en el cuerpo. Minúsculas, sin tildes.",
    "Etiqueta": "El rótulo del formulario y el encabezado de la columna del Excel.",
    "Tipo": "Decide el widget, cómo se lee la celda de Excel y cómo se imprime.",
    "Obligatorio": "Si está vacío, no se genera el documento.",
    "Opciones": "Solo para los campos de tipo lista. Sepáralas con «;».",
    "Ejemplo": "Se muestra en las instrucciones del Excel y en la previsualización.",
    "Ayuda": "Texto del iconito de ayuda en el formulario.",
    "Grupo": "Subtítulo bajo el que se agrupa en el formulario. Opcional.",
    "Sugerencias": "Atajos de un desplegable que igual acepta escribir otra cosa. Con «;».",
    "No futura": "Rechaza una fecha posterior a hoy.",
    "Posterior a": "Clave de otra fecha: avisa si esta es anterior.",
    "Artículo minúscula": "Avisa si el texto empieza por «La», «El», «Los» o «Las».",
    "La rellena la app": "Puede ir en blanco: en el Excel la pone el lote; en el formulario, hoy.",
}


def _a_tabla(tipo):
    """Los campos como filas para el st.data_editor."""
    return [
        {
            "Clave": campo["clave"],
            "Etiqueta": campo["etiqueta"],
            "Tipo": campo["tipo"],
            "Obligatorio": campo["obligatorio"],
            "Opciones": "; ".join(campo["opciones"]),
            "Ejemplo": str(campo["ejemplo"]),
            "Ayuda": campo["ayuda"],
            "Grupo": campo["grupo"],
            "Sugerencias": "; ".join(campo["sugerencias"]),
            "No futura": campo["no_futura"],
            "Posterior a": campo["posterior_a"] or "",
            "Artículo minúscula": campo["articulo_minuscula"],
            "La rellena la app": campo["opcional_en_hoja"],
        }
        for campo in tipo["campos"]
    ]


def _de_tabla(filas, anteriores):
    """Las filas del editor de vuelta a campos, conservando lo que la tabla no muestra."""
    # los sinónimos de una lista no se editan en la tabla: se conservan por clave, para
    # que editar una etiqueta no borre en silencio las grafías que ya se aceptaban
    previos = {campo["clave"]: campo for campo in anteriores}
    nuevos = []
    for fila in filas:
        clave = str(fila.get("Clave") or "").strip()
        if not clave and not str(fila.get("Etiqueta") or "").strip():
            continue  # fila que el editor añadió y quedó vacía
        campo = dict(previos.get(clave, {}))
        campo.update({
            "clave": clave,
            "etiqueta": str(fila.get("Etiqueta") or "").strip(),
            "tipo": str(fila.get("Tipo") or "texto"),
            "obligatorio": bool(fila.get("Obligatorio")),
            "opciones": _partir(fila.get("Opciones")),
            "ejemplo": str(fila.get("Ejemplo") or "").strip(),
            "ayuda": str(fila.get("Ayuda") or "").strip(),
            "grupo": str(fila.get("Grupo") or "").strip(),
            "sugerencias": _partir(fila.get("Sugerencias")),
            "no_futura": bool(fila.get("No futura")),
            "posterior_a": str(fila.get("Posterior a") or "").strip() or None,
            "articulo_minuscula": bool(fila.get("Artículo minúscula")),
            "opcional_en_hoja": bool(fila.get("La rellena la app")),
        })
        nuevos.append(campo)
    return nuevos


def _partir(texto):
    """'a; b ; ' -> ['a', 'b']."""
    return [parte.strip() for parte in str(texto or "").split(";") if parte.strip()]


def _fila_ejemplo(tipo):
    """Una fila cruda con el ejemplo de cada campo, para previsualizar."""
    fila = {}
    for campo in tipo["campos"]:
        ejemplo = str(campo["ejemplo"]).strip()
        if not ejemplo:
            opciones = tipos.opciones(campo)
            ejemplo = (
                opciones[0] if opciones
                else date.today().isoformat() if campo["tipo"] == "fecha"
                else EJEMPLO_POR_TIPO.get(campo["tipo"], "(ejemplo)")
            )
        fila[campo["clave"]] = ejemplo
    return fila


def _previsualizar(tipo):
    """Renderiza el tipo con los ejemplos y pinta el .md y el .docx de muestra."""
    datos, errores, _ = campos.normalizar(tipo, _fila_ejemplo(tipo))
    if errores:
        st.warning(
            _lista(errores),
            title="Los ejemplos de los campos no se pudieron convertir; corrígelos para ver "
                  "la muestra completa",
        )
    try:
        md = documento.render_markdown(tipo, datos)
    except (ValueError, KeyError) as error:
        st.error(str(error), title="No se pudo renderizar")
        return
    st.download_button(
        "Descargar el .docx de muestra",
        data=documento.markdown_a_docx(md, tipo["titulo"]),
        file_name=f"muestra_{tipo['id']}.docx",
        mime=MIME_DOCX,
        on_click="ignore",
        type="primary",
        key="tipos_muestra",
    )
    st.caption(
        "Ábrelo: es la única forma de ver de verdad si una tabla quedó partida o si un "
        "título de Markdown se imprimió literal."
    )
    with st.expander("Ver el Markdown intermedio"):
        st.code(md, language="markdown")


def _editor(base):
    """El formulario de edición; devuelve un descriptor nuevo, sin tocar la base."""
    borrador = dict(base)
    st.text_input("Nombre del tipo", key="tipos_nombre")
    columnas = st.columns(2)
    with columnas[0]:
        st.text_input(
            "Título del encabezado", key="tipos_titulo",
            help="Sale centrado arriba en todas las páginas, al lado del logo.",
        )
    with columnas[1]:
        st.text_input(
            "Prefijo del nombre de archivo", key="tipos_prefijo",
            help="El .docx se llamará «prefijo_nombre_fecha.docx». Minúsculas y guion bajo.",
        )
    borrador["nombre"] = st.session_state["tipos_nombre"]
    borrador["titulo"] = st.session_state["tipos_titulo"]
    borrador["prefijo_archivo"] = st.session_state["tipos_prefijo"]

    st.subheader("Campos")
    st.caption(
        "Un campo por fila. La **clave** es lo que escribes entre `{{ }}` en el cuerpo; "
        "la **etiqueta** es lo que ve quien diligencia."
    )
    # se le pasa la tabla de cuando se abrió el tipo, NO la ya editada: con `key`, el editor
    # guarda las ediciones como un delta contra los datos que recibe, y realimentarle el
    # resultado las aplicaría dos veces
    filas = st.data_editor(
        st.session_state["tipos_campos_base"],
        num_rows="dynamic",
        hide_index=True,
        key="tipos_campos",
        column_config={
            "Tipo": st.column_config.SelectboxColumn(
                "Tipo", options=list(tipos.TIPOS_CAMPO), help=COLUMNAS["Tipo"], required=True
            ),
            **{
                nombre: (
                    st.column_config.CheckboxColumn(nombre, help=ayuda)
                    if nombre in ("Obligatorio", "No futura", "Artículo minúscula",
                                  "La rellena la app")
                    else st.column_config.TextColumn(nombre, help=ayuda)
                )
                for nombre, ayuda in COLUMNAS.items()
                if nombre != "Tipo"
            },
        },
    )
    borrador["campos"] = [
        tipos.completar_campo(campo) for campo in _de_tabla(filas, base["campos"])
    ]

    claves_texto = [c["clave"] for c in borrador["campos"] if c["tipo"] == "texto"]
    claves_fecha = [c["clave"] for c in borrador["campos"] if c["tipo"] == "fecha"]
    columnas = st.columns(2)
    with columnas[0]:
        borrador["campo_nombre"] = st.selectbox(
            "Campo que da el nombre del archivo", [None] + claves_texto,
            index=([None] + claves_texto).index(borrador["campo_nombre"])
            if borrador["campo_nombre"] in claves_texto else 0,
            key="tipos_campo_nombre",
        )
    with columnas[1]:
        borrador["campo_fecha_archivo"] = st.selectbox(
            "Campo que da la fecha del archivo", [None] + claves_fecha,
            index=([None] + claves_fecha).index(borrador["campo_fecha_archivo"])
            if borrador["campo_fecha_archivo"] in claves_fecha else 0,
            key="tipos_campo_fecha",
        )

    st.subheader("Cuerpo del otrosí")
    ayuda, texto = st.columns([1, 3])
    with ayuda:
        st.caption("**Marcadores disponibles**")
        for clave in tipos.marcadores(borrador):
            st.code(f"{{{{{clave}}}}}", language=None)
        st.caption(
            "**Markdown que existe**\n\n"
            "- párrafos separados por una línea en blanco\n"
            "- `**negrita**`\n"
            "- viñetas con `- `\n"
            "- tablas `| a | b |`\n\n"
            "Nada más: un `#` o un `[enlace](x)` se imprimen tal cual. "
            "Ninguna línea de un párrafo puede empezar por `- ` ni por `|`."
        )
    with texto:
        borrador["cuerpo"] = st.text_area(
            "Pega aquí el texto del otrosí", height=520, key="tipos_cuerpo",
            label_visibility="collapsed",
        )
    return borrador


def _acciones(borrador, errores):
    """Los botones de guardar, exportar, descartar y borrar/restaurar."""
    integrado = tipos.es_integrado(borrador["id"])
    botones = st.columns(4)
    with botones[0]:
        if st.button("Guardar", type="primary", disabled=bool(errores), key="tipos_guardar"):
            try:
                tipos.guardar(borrador)
            except (OSError, ValueError) as error:
                st.error(str(error), title="No se pudo guardar")
            else:
                st.session_state.pop("borrador", None)
                st.session_state["tipos_mensaje"] = f"Guardado «{borrador['nombre']}»."
                st.rerun()
    with botones[1]:
        st.download_button(
            "Exportar .json", data=tipos.exportar(borrador),
            file_name=f"tipo_{borrador['id']}.json", mime=MIME_JSON,
            on_click="ignore", key="tipos_exportar",
            help="Guárdalo tú: es el respaldo si el servidor pierde lo guardado.",
        )
    with botones[2]:
        if st.button("Descartar cambios", key="tipos_descartar"):
            st.session_state.pop("borrador", None)
            st.rerun()
    with botones[3]:
        rotulo = "Restaurar el original" if integrado else "Borrar el tipo"
        if st.button(rotulo, key="tipos_borrar"):
            tipos.borrar(borrador["id"])
            st.session_state.pop("borrador", None)
            st.session_state["tipos_mensaje"] = (
                f"«{borrador['id']}» volvió al texto original."
                if integrado else f"Se borró «{borrador['id']}»."
            )
            st.rerun()


def _abrir(borrador):
    """Deja el tipo en session_state como base y siembra los widgets del editor."""
    st.session_state["borrador"] = borrador
    st.session_state["tipos_nombre"] = borrador["nombre"]
    st.session_state["tipos_titulo"] = borrador["titulo"]
    st.session_state["tipos_prefijo"] = borrador["prefijo_archivo"]
    st.session_state["tipos_cuerpo"] = borrador["cuerpo"]
    st.session_state["tipos_campos_base"] = _a_tabla(borrador)
    # el delta del editor anterior no puede sobrevivir a abrir otro tipo
    st.session_state.pop("tipos_campos", None)
    st.rerun()


def _catalogo(disponibles):
    """La lista de tipos con sus acciones, cuando no se está editando ninguno."""
    st.caption(
        "Aquí se define qué otrosíes puede generar la app. Un tipo son sus campos y el "
        "texto del documento, con los campos marcados entre llaves."
    )
    if mensaje := st.session_state.pop("tipos_mensaje", None):
        st.success(mensaje)

    arriba = st.columns([1, 1, 2])
    with arriba[0]:
        if st.button("Nuevo tipo, vacío", key="tipos_nuevo"):
            _abrir(tipos.nuevo())
    with arriba[1]:
        subido = st.file_uploader(
            "Importar un .json", type=["json"], key="tipos_importar",
            label_visibility="collapsed",
        )
    if subido is not None:
        importado, errores = tipos.importar(subido.getvalue())
        if importado is None:
            st.error(_lista(errores), title="No se pudo importar")
        else:
            if errores:
                st.warning(_lista(errores), title="Se importó, pero tiene errores que corregir")
            _abrir(importado)

    st.divider()
    for identificador, tipo in disponibles.items():
        errores, avisos = tipos.validar(tipo)
        with st.container(border=True):
            st.markdown(
                f"**{tipo['nombre']}** · `{identificador}` · "
                f"{ORIGENES.get(tipo['_origen'], tipo['_origen'])}"
            )
            st.caption(
                f"{len(tipo['campos'])} campos · "
                + (f"⚠ {len(errores)} errores" if errores else "sin errores")
                + (f" · {len(avisos)} avisos" if avisos else "")
            )
            acciones = st.columns(3)
            with acciones[0]:
                if st.button("Editar", key=f"editar_{identificador}"):
                    _abrir(tipos.cargar(identificador))
            with acciones[1]:
                if st.button("Duplicar", key=f"duplicar_{identificador}"):
                    copia = tipos.cargar(identificador)
                    copia["nombre"] = f"{copia['nombre']} (copia)"
                    copia["id"] = tipos.slug_identificador(copia["nombre"])
                    copia["_origen"], copia["_marca"] = "nuevo", None
                    copia.pop("cuerpo_archivo", None)
                    _abrir(copia)
            with acciones[2]:
                st.download_button(
                    "Exportar .json", data=tipos.exportar(tipo),
                    file_name=f"tipo_{identificador}.json", mime=MIME_JSON,
                    on_click="ignore", key=f"exportar_{identificador}",
                )


def _pestaña_tipos():
    base = st.session_state.get("borrador")
    if base is None:
        _catalogo(tipos.listar())
        return

    st.caption(
        f"Editando **{base['nombre']}** · identificador `{base['id']}`. "
        "Nada se guarda hasta que pulses «Guardar»."
    )
    st.warning(
        "Lo guardado vive en el disco del servidor. Si no sabes si ese disco sobrevive a un "
        "reinicio o a un redespliegue, **exporta el .json y guárdalo tú**: es el único "
        "respaldo.",
        icon="⚠️",
    )
    # el borrador se recalcula en cada rerun a partir de los widgets; `base` no se toca,
    # porque es lo que se le entrega al data_editor
    borrador = _editor(base)
    borrador["id"] = borrador["id"] or tipos.slug_identificador(borrador["nombre"])

    st.divider()
    errores, avisos = tipos.validar(borrador)
    if errores:
        st.error(_lista(errores), title=f"{len(errores)} cosas que hay que corregir")
    if avisos:
        st.warning(_lista(avisos), title=f"{len(avisos)} avisos; no impiden guardar")
    if not errores and not avisos:
        st.success("Sin errores ni avisos.")

    _acciones(borrador, errores)
    if not errores:
        st.divider()
        st.subheader("Previsualización con los ejemplos de cada campo")
        _previsualizar(borrador)


# ---------------------------------------------------------------------------- app


def _tipo_activo(disponibles):
    """El selector de tipo; al cambiarlo se descarta lo generado con el anterior."""
    elegido = st.selectbox(
        "Tipo de otrosí",
        list(disponibles),
        format_func=lambda identificador: disponibles[identificador]["nombre"],
        key="tipo_activo",
    )
    if st.session_state.get("tipo_previo") not in (None, elegido):
        # no dejar descargable un documento del tipo anterior, igual que al fallar la
        # validación no se deja el .docx anterior junto al error
        st.session_state.pop("resultado", None)
        st.session_state.pop("masivo", None)
    st.session_state["tipo_previo"] = elegido
    return disponibles[elegido]


def main():
    st.set_page_config(page_title="Generador de otrosíes", page_icon="📄")
    st.title("Generador de otrosíes")
    st.caption(
        "Universidad de los Andes — Dirección de Gestión Humana y Desarrollo Organizacional"
    )

    disponibles = tipos.listar()
    # el selector va fuera de st.tabs y antes de ellas: las dos pestañas operativas trabajan
    # sobre el mismo tipo, y así se ve arriba a qué otrosí se refiere todo lo de abajo
    tipo = _tipo_activo(disponibles) if disponibles else None

    # st.tabs ejecuta los cuerpos de las tres en cada rerun: la pestaña masiva vuelve a leer
    # el archivo aunque estés en la individual, y es justo lo que se quiere
    individual, masiva, editor = st.tabs(["Un otrosí", "Carga masiva", "Tipos de otrosí"])

    if tipo is None:
        for pestaña in (individual, masiva):
            with pestaña:
                st.error(
                    "No hay ningún tipo de otrosí definido. Créalo en la pestaña "
                    "«Tipos de otrosí»."
                )
        with editor:
            _pestaña_tipos()
        return

    errores = tipos.validar(tipo)[0]
    with individual:
        if errores:
            st.error(
                _lista(errores),
                title=f"El tipo «{tipo['nombre']}» tiene errores: corrígelo en «Tipos de otrosí»",
            )
        else:
            _pestaña_individual(tipo)
    with masiva:
        if errores:
            st.error(f"El tipo «{tipo['nombre']}» tiene errores: corrígelo antes de usarlo.")
        else:
            _pestaña_masiva(tipo)
    with editor:
        _pestaña_tipos()


if __name__ == "__main__":
    main()
