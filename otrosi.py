"""Registro de novedades laborales (otrosí) - front-end Streamlit."""

from datetime import date, datetime

import streamlit as st

import documento

OPCIONES = {
    1: "Incremento/Ajuste salarial",
    2: "Cambio de cargo o promoción",
    3: "Cambio de lugar de trabajo",
    4: "Cambio de jornada",
    5: "Renovación de contrato",
}

CIUDADES = ["Bogotá D.C.", "Medellín", "Cali", "Barranquilla", "Cartagena", "Bucaramanga"]


def campo_salario(label, key_prefix):
    monto = st.number_input(f"{label} - Monto", step=1, format="%d", key=f"{key_prefix}_monto")
    nota = st.text_input(f"{label} - Nota", key=f"{key_prefix}_nota")
    return {"monto": int(monto), "nota": nota}


def campo_fecha_hora(label, key_prefix):
    st.write(label)
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha", key=f"{key_prefix}_fecha")
    with col2:
        hora = st.time_input("Hora", key=f"{key_prefix}_hora")
    return datetime.combine(fecha, hora)


def campos_faltantes(campos):
    faltantes = []
    for label, valor in campos:
        if isinstance(valor, list):
            if not valor:
                faltantes.append(label)
        elif isinstance(valor, str):
            if not valor.strip():
                faltantes.append(label)
        elif valor is None:
            faltantes.append(label)
    return faltantes


def serializar(valor):
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, dict):
        return {k: serializar(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [serializar(v) for v in valor]
    return valor


def render_globales():
    """Campos comunes a todos los tipos de otrosí."""
    data = {}
    data["nombre_empleado"] = st.text_input("Nombre del empleado", key="nombre_empleado")
    data["cedula"] = st.text_input("Cédula del empleado", key="cedula")
    data["numero_contrato"] = st.text_input("Número de contrato", key="numero_contrato")
    data["fecha_otrosi"] = campo_fecha_hora("Fecha del otrosí", "otrosi")
    data["ciudad"] = st.selectbox(
        "Ciudad",
        CIUDADES,
        index=None,
        placeholder="Selecciona una ciudad",
        key="ciudad",
    )

    requeridos = [
        ("Nombre del empleado", data["nombre_empleado"]),
        ("Cédula del empleado", data["cedula"]),
        ("Número de contrato", data["numero_contrato"]),
        ("Ciudad", data["ciudad"]),
    ]
    return data, requeridos


def render_incremento_salarial():
    data = {}
    data["salario_anterior"] = campo_salario("Salario anterior", "sal_ant")
    data["salario_nuevo"] = campo_salario("Salario nuevo", "sal_nue")

    st.write("Periodicidad")
    col1, col2 = st.columns(2)
    with col1:
        valor = st.number_input("Valor", step=1, format="%d", key="periodicidad_valor")
    with col2:
        unidad = st.selectbox("Unidad", ["días", "meses"], key="periodicidad_unidad")
    data["periodicidad"] = {"valor": int(valor), "unidad": unidad}

    data["fecha_efectividad"] = campo_fecha_hora("Fecha de efectividad", "efectividad")

    requeridos = [
        ("Salario anterior - Nota", data["salario_anterior"]["nota"]),
        ("Salario nuevo - Nota", data["salario_nuevo"]["nota"]),
    ]
    return data, requeridos


def render_cambio_cargo():
    data = {}
    data["cargo_anterior"] = st.text_input("Cargo anterior", key="cargo_anterior")
    data["cargo_nuevo"] = st.text_input("Cargo nuevo", key="cargo_nuevo")
    data["area"] = st.selectbox("Área", ["oficina", "casa"], key="area")
    data["jefe_inmediato"] = st.text_input("Jefe inmediato", key="jefe_inmediato")

    funciones_raw = st.text_area("Funciones nuevas (una por línea)", key="funciones_nuevas")
    data["funciones_nuevas"] = [f.strip() for f in funciones_raw.splitlines() if f.strip()]

    registrar_salario = st.checkbox("¿Desea registrar salario?", key="registrar_salario")
    if registrar_salario:
        data["salario"] = campo_salario("Salario", "cargo_sal")
    else:
        data["salario"] = None

    requeridos = [
        ("Cargo anterior", data["cargo_anterior"]),
        ("Cargo nuevo", data["cargo_nuevo"]),
        ("Jefe inmediato", data["jefe_inmediato"]),
        ("Funciones nuevas", data["funciones_nuevas"]),
    ]
    if registrar_salario:
        requeridos.append(("Salario - Nota", data["salario"]["nota"]))

    return data, requeridos


def render_cambio_lugar():
    data = {}
    data["lugar_anterior"] = st.text_input("Lugar anterior de trabajo", key="lugar_anterior")
    data["lugar_nuevo"] = st.text_input("Lugar nuevo de trabajo", key="lugar_nuevo")
    data["tipo_modalidad"] = st.selectbox(
        "Tipo de modalidad", ["remoto", "híbrido", "oficina"], key="tipo_modalidad"
    )

    requeridos = [
        ("Lugar anterior de trabajo", data["lugar_anterior"]),
        ("Lugar nuevo de trabajo", data["lugar_nuevo"]),
    ]
    return data, requeridos


def render_cambio_jornada():
    data = {}
    data["jornada_anterior_horas"] = int(
        st.number_input("Jornada anterior (horas)", step=1, format="%d", key="jornada_anterior")
    )
    data["jornada_nueva_horas"] = int(
        st.number_input("Jornada nueva (horas)", step=1, format="%d", key="jornada_nueva")
    )
    horario_anterior = st.text_input("Horario anterior (opcional)", key="horario_anterior")
    horario_nuevo = st.text_input("Horario nuevo (opcional)", key="horario_nuevo")
    data["horario_anterior"] = horario_anterior or None
    data["horario_nuevo"] = horario_nuevo or None

    return data, []


def render_renovacion_contrato():
    data = {}
    data["fecha_vencimiento_actual"] = st.date_input(
        "Fecha de vencimiento actual", key="fecha_vencimiento"
    )
    data["periodo_prueba_dias"] = int(
        st.number_input("Periodo de prueba (días)", step=1, format="%d", key="periodo_prueba")
    )

    es_termino_fijo = st.checkbox("¿El contrato es a término fijo?", key="termino_fijo")
    data["termino_fijo"] = es_termino_fijo

    if es_termino_fijo:
        data["nuevo_plazo_dias"] = int(
            st.number_input("Nuevo plazo (días)", step=1, format="%d", key="nuevo_plazo")
        )
        data["fecha_terminacion"] = st.date_input("Fecha de terminación", key="fecha_terminacion")
    else:
        data["nuevo_plazo_dias"] = None
        data["fecha_terminacion"] = None

    return data, []


RENDERERS = {
    1: render_incremento_salarial,
    2: render_cambio_cargo,
    3: render_cambio_lugar,
    4: render_cambio_jornada,
    5: render_renovacion_contrato,
}


def main():
    st.set_page_config(page_title="Registro de novedades laborales", page_icon="📄")
    st.title("Registro de novedades laborales (otrosí)")

    st.subheader("Datos generales")
    globales, req_globales = render_globales()
    st.divider()

    opcion = st.radio(
        "Tipo de cambio",
        list(OPCIONES.keys()),
        format_func=lambda n: f"{n}. {OPCIONES[n]}",
        key="opcion",
    )

    st.subheader(OPCIONES[opcion])
    data, requeridos = RENDERERS[opcion]()

    if st.button("Enviar"):
        faltantes = campos_faltantes(req_globales + requeridos)
        if faltantes:
            st.error("Faltan campos obligatorios: " + ", ".join(faltantes))
        else:
            payload = {
                "tipo_id": opcion,
                "tipo": OPCIONES[opcion],
                "generales": globales,
                "detalle": data,
            }
            md = documento.render_markdown(payload)

            st.success("Documento generado.")
            st.warning("Texto sujeto a revisión jurídica antes de usarse en firma.")
            st.markdown(md)
            st.download_button(
                "Descargar .docx",
                data=documento.markdown_a_docx(md),
                file_name=documento.nombre_archivo(payload),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

            with st.expander("Ver datos capturados (JSON)"):
                st.json(serializar(payload))


if __name__ == "__main__":
    main()
