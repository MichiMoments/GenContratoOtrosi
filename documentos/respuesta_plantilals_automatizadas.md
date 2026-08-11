# Plantillas automatizadas: tipos de otrosí definibles desde la web

Resumen de la implementación del motor de tipos de otrosí, con lo verificado, lo
supuesto y lo que queda pendiente de comprobar a mano.

---

## Lo que hay ahora

Una pestaña nueva, **«Tipos de otrosí»**: se define el nombre, el título del
encabezado, los campos (en una tabla) y se pega el texto del contrato con los datos
variables entre `{{llaves}}`. Al guardar, ese tipo aparece en el selector de arriba y
queda automatizado en los dos modos que ya existían — formulario y carga masiva con
su propio Excel, sus propios desplegables y su propia hoja de instrucciones.

Debajo, los cuatro módulos dejaron de tener el otrosí de teletrabajo cableado y ahora
reciben un **descriptor de tipo**. Hay un módulo nuevo, [tipos.py](tipos.py), único
sitio que sabe que hay archivos en disco.

```
otrosi.py     UI Streamlit (tres pestañas)    -> tipos, campos, masivo, documento
masivo.py     Excel <-> payloads + .zip       -> tipos, campos, documento
campos.py     coerción y validación           -> documento
tipos.py      descriptores en disco           -> documento
documento.py  marcadores -> Markdown -> .docx -> (nada)
```

---

## Lo que más importa que sepas

### El documento firmado no cambió

Antes de tocar código guardé el Markdown que producía la plantilla de Jinja para las
dos ramas de género, y el motor nuevo lo reproduce **byte a byte** (11.966 y 11.936
caracteres, idénticos).

La migración de la plantilla la hice con un script que sustituye solo los `{{...}}` y
**aserta que el texto fuera de los marcadores no cambió**, en vez de reescribir 180
líneas de texto legal a mano.

### Jinja2 salió de las dependencias

Como el texto que escribe una persona nunca llega a un evaluador de expresiones, la
clase entera de inyección de plantillas no existe: la sustitución es una `re.sub`
contra un diccionario de claves declaradas.

### El validador tiene 15 reglas de error y 4 de aviso

Cada una atada a un fallo concreto del conversor a `.docx`. La más valiosa es la fila
de tabla con celdas de más, que hoy `_escribir_tabla` descarta con un `zip()` sin
decir nada. El tipo integrado pasa con **cero errores y cero avisos** — importante,
porque un validador que grita en falso no se lee.

### Una desviación del plan aprobado

El separador de filtros iba a ser `|`, pero el bloque de firmas tiene un marcador
**dentro de una celda de tabla**:

```
| LA UNIVERSIDAD, | {{teletrabajador:mayusculas}}, |
```

…y `|` es justo el carácter que delimita celdas. Al renderizar no hay problema (la
sustitución ocurre antes de parsear el Markdown), pero significaba que el validador no
podía rechazar un `|` suelto sin excepciones. Lo cambié a `:`. El `|` se sigue
aceptando por tolerancia.

---

## Dos cosas que no sé y no inventé

**No sé dónde está hospedada la app**, así que no sé si `plantillas/personalizadas/`
sobrevive a un redespliegue. La pestaña lo dice en pantalla y ofrece exportar el
`.json`. Además dejé esos archivos **fuera de `.gitignore` a propósito**: si un tipo
tiene que ser permanente, se commitea y sobrevive.

**Estoy suponiendo** que el proceso de Streamlit puede escribir en el directorio del
proyecto. Si no puede, `guardar` falla y habrá que hacer configurable la ruta.

Y una consecuencia de la decisión de «todo editable» que conviene tener presente:
cualquiera con el enlace puede reescribir el texto legal y **no queda rastro de quién
ni cuándo**. Implementé «Restaurar el original» (el texto de git se conserva y
editarlo solo escribe un override), así que es reversible para el tipo integrado; un
tipo creado en la web solo tiene su `.json` exportado.

---

## Verificación

| Suite | Resultado |
|---|---|
| Patrón oro contra Jinja | idéntico en las dos ramas de género |
| Validador de tipos (33 casos + 7 `id` maliciosos) | todo dispara |
| Carga masiva (los 5 defectos históricos + 10 datos malos) | todo atrapado en la carga |
| Interfaz con `AppTest` (24 comprobaciones) | las 3 pestañas montan; el modo individual da el mismo nombre de archivo |
| Persistencia: guardar/exportar/borrar/importar/restaurar/escritura perdida | ida y vuelta idéntica |
| Tipo nuevo de punta a punta (4 desplegables en H–K) | genera los `.docx` con concordancia correcta |

Estado del árbol de trabajo al terminar: 4 modificados, 6 nuevos, 1 borrado
(recuperable con `git checkout`). Nada commiteado.

---

## Lo que sigue sin poder automatizarse

Queda pendiente abrir el `.xlsx` en **Excel de verdad** para confirmar tres cosas:

1. que la flecha del desplegable aparece,
2. que `#,##0` se localiza como `1.020.345.678`,
3. y sobre todo que un archivo **guardado desde Excel** devuelve las fechas como
   fecha y los enteros como entero.

Toda la política de fechas y el arreglo de la cédula descansan en el punto 3, y falla
en silencio: el archivo abre bien, simplemente no hace lo que debería.
