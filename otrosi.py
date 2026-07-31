"""Registro de novedades laborales (otrosí)."""

from datetime import datetime


def prompt_int(label):
    while True:
        raw = input(f"{label}: ").strip()
        try:
            return int(raw)
        except ValueError:
            print("  Debe ingresar un número entero. Intente de nuevo.")


def prompt_str(label):
    while True:
        raw = input(f"{label}: ").strip()
        if raw:
            return raw
        print("  Este campo no puede estar vacío. Intente de nuevo.")


def prompt_optional_str(label):
    raw = input(f"{label} (opcional, Enter para omitir): ").strip()
    return raw if raw else None


def prompt_enum(label, options):
    while True:
        print(f"{label}:")
        for i, opt in enumerate(options, start=1):
            print(f"  {i}. {opt}")
        raw = input("Seleccione una opción: ").strip()
        try:
            idx = int(raw)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        except ValueError:
            pass
        print("  Opción inválida. Intente de nuevo.")


def prompt_date(label):
    while True:
        raw = input(f"{label} (formato YYYY-MM-DD): ").strip()
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("  Formato inválido. Use YYYY-MM-DD. Intente de nuevo.")


def prompt_datetime(label):
    while True:
        raw = input(f"{label} (formato YYYY-MM-DD HH:MM): ").strip()
        try:
            return datetime.strptime(raw, "%Y-%m-%d %H:%M")
        except ValueError:
            print("  Formato inválido. Use YYYY-MM-DD HH:MM. Intente de nuevo.")


def prompt_yes_no(label):
    while True:
        raw = input(f"{label} (s/n): ").strip().lower()
        if raw in ("s", "si", "sí"):
            return True
        if raw in ("n", "no"):
            return False
        print("  Responda 's' o 'n'.")


def prompt_list_str(label):
    print(f"{label} (ingrese una por línea, línea vacía para terminar):")
    items = []
    while True:
        raw = input("  - ").strip()
        if not raw:
            if items:
                break
            print("  Debe ingresar al menos un elemento.")
            continue
        items.append(raw)
    return items


def prompt_salario(label):
    monto = prompt_int(f"{label} - Monto")
    nota = prompt_str(f"{label} - Nota")
    return {"monto": monto, "nota": nota}


def collect_incremento_salarial():
    data = {}
    data["salario_anterior"] = prompt_salario("Salario anterior")
    data["salario_nuevo"] = prompt_salario("Salario nuevo")
    valor = prompt_int("Periodicidad - valor")
    unidad = prompt_enum("Periodicidad - unidad", ["días", "meses"])
    data["periodicidad"] = {"valor": valor, "unidad": unidad}
    data["fecha_efectividad"] = prompt_datetime("Fecha de efectividad")
    return data


def collect_cambio_cargo():
    data = {}
    data["cargo_anterior"] = prompt_str("Cargo anterior")
    data["cargo_nuevo"] = prompt_str("Cargo nuevo")
    data["area"] = prompt_enum("Área", ["oficina", "casa"])
    data["jefe_inmediato"] = prompt_str("Jefe inmediato")
    data["funciones_nuevas"] = prompt_list_str("Funciones nuevas")
    if prompt_yes_no("¿Desea registrar salario?"):
        data["salario"] = prompt_salario("Salario")
    else:
        data["salario"] = None
    return data


def collect_cambio_lugar():
    data = {}
    data["lugar_anterior"] = prompt_str("Lugar anterior de trabajo")
    data["lugar_nuevo"] = prompt_str("Lugar nuevo de trabajo")
    data["tipo_modalidad"] = prompt_enum("Tipo de modalidad", ["remoto", "híbrido", "oficina"])
    return data


def collect_cambio_jornada():
    data = {}
    data["jornada_anterior_horas"] = prompt_int("Jornada anterior (horas)")
    data["jornada_nueva_horas"] = prompt_int("Jornada nueva (horas)")
    data["horario_anterior"] = prompt_optional_str("Horario anterior")
    data["horario_nuevo"] = prompt_optional_str("Horario nuevo")
    return data


def collect_renovacion_contrato():
    data = {}
    data["fecha_vencimiento_actual"] = prompt_date("Fecha de vencimiento actual")
    data["periodo_prueba_dias"] = prompt_int("Periodo de prueba (días)")
    es_termino_fijo = prompt_yes_no("¿El contrato es a término fijo?")
    data["termino_fijo"] = es_termino_fijo
    if es_termino_fijo:
        data["nuevo_plazo_dias"] = prompt_int("Nuevo plazo (días)")
        data["fecha_terminacion"] = prompt_date("Fecha de terminación")
    else:
        data["nuevo_plazo_dias"] = None
        data["fecha_terminacion"] = None
    return data


OPCIONES = {
    1: ("Incremento/Ajuste salarial", collect_incremento_salarial),
    2: ("Cambio de cargo o promoción", collect_cambio_cargo),
    3: ("Cambio de lugar de trabajo", collect_cambio_lugar),
    4: ("Cambio de jornada", collect_cambio_jornada),
    5: ("Renovación de contrato", collect_renovacion_contrato),
}


def prompt_opcion():
    while True:
        print("\nSeleccione el tipo de cambio:")
        for numero, (nombre, _) in OPCIONES.items():
            print(f"  {numero}. {nombre}")
        raw = input("Número (1-5): ").strip()
        try:
            numero = int(raw)
            if numero in OPCIONES:
                return numero
        except ValueError:
            pass
        print("  Opción inválida. Debe ingresar un número entre 1 y 5.")


def main():
    numero = prompt_opcion()
    nombre, funcion = OPCIONES[numero]
    print(f"\n--- {nombre} ---")
    datos = funcion()
    print("\nResumen de los datos ingresados:")
    for clave, valor in datos.items():
        print(f"  {clave}: {valor}")


if __name__ == "__main__":
    main()
