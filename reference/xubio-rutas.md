# Rutas en Xubio Colombia

Confirmadas en la primera sincronización real (12/11/2026), salvo las marcadas "sin confirmar".
La app está en https://xubio.com/NXV/ (si xubio.com redirige a la página pública /ar/, pulsar "Iniciar sesión": con la sesión abierta entra directo al panel).

## Reportes que usa `sincronizar`

| Qué | Ruta | URL directa |
|---|---|---|
| **Libro IVA Ventas** (fuente de ventas.csv) | Impuestos › IVA › Libro IVA Ventas | https://xubio.com/NXV/impuestos/libro-iva-ventas-co |
| **Libro IVA Compras** (fuente de compras.csv) | Impuestos › IVA › Libro IVA Compras | https://xubio.com/NXV/impuestos/libro-iva-compras-co |
| Informe de Retenciones y Otros Impuestos | Impuestos › Retenciones › Informe de Retenciones y Otros Impuestos | https://xubio.com/NXV/impuestos/retenciones-y-otros-impuestos |
| Análisis de Facturas de Venta (detalle por ítem, sin IVA) | Reportes › Ventas › Análisis de Facturas de Venta | https://xubio.com/NXV/reportes/ventas/analisis-de-facturas-de-venta |

Cómo se usan:
1. Al abrir, sale el diálogo "Elige los filtros". Los libros de IVA proponen el cuatrimestre en curso: cambiar Desde a 01/01/AAAA y Hasta a 31/12/AAAA. Las fechas son tres cajas (día, mes, año): usar `find` + `form_input` en cada caja; escribir con el teclado no funciona. Luego "Aceptar".
2. Exportar: "Acciones" › "Exportar" › "Exportar a Excel". Hacer clic en Acciones y Exportar por referencia (`find`), no por coordenadas: un clic que cae en la tabla abre el menú de columna. El submenú se abre a la derecha; pasar el mouse en horizontal hasta "Exportar a Excel".
3. El archivo llega a Descargas como "Libro IVA Ventas.xlsx" / "Libro IVA Compra.xlsx" (con " (1)", " (2)"… si ya existe). Tomar el más reciente y copiarlo a `<carpeta_datos>/exportaciones/AAAA-MM-DD/`.

Columnas del Libro IVA (ventas y compras): Fecha (AAAA-MM-DD), Tipo (Factura / Nota Crédito), Comprobante, Cliente o Proveedor, Identificación, Moneda Transaccional, Cotización, Neto Gravado e IVA por tarifa (19%, 16%, 5%; productos y servicios), Total Gravado, Total IVA, Retenciones IVA, Total Gravado 0%, Total Excluido, Total. Las notas crédito vienen en negativo y comparten número con su factura.

Retenciones: si el informe dice "Sin Movimientos", no descargarlo. A 12/11/2026 Xubio no tenía retenciones ni retefuente registradas.

## Otras rutas

| Qué | Ruta |
|---|---|
| Inicio con accesos rápidos | Comprobantes de Venta / Compra / Clientes / Proveedores (Ver, Nuevo) |
| Nueva cotización | Ventas › Cotizaciones › Nueva Cotización (sin confirmar) |
| Tablero de cotizaciones | Reportes › Ventas › Tablero de Cotizaciones |
| Enviar cotización | Abrir la cotización › Enviar por email (solo con aprobación; sin confirmar) |
| Nueva factura de venta (confirmado 14/11/2026) | https://xubio.com/NXV/ventas/nuevo-comprobante-de-venta-co — Cliente (escribir y elegir), Producto/Servicio, Centro de Costo, Cantidad, Precio sin IVA; Tab para recalcular. "Guardar" no transmite; "Guardar y Enviar a la DIAN" transmite (~15 s) y ya no se puede anular ni editar (solo nota crédito). |
| Enviar factura por email | Botón "Enviar por email" › Enviar. No muestra destinatario (usa el email del cliente) ni confirmación, y "Ver Historial" no lo registra: verificar antes que el cliente tenga email. |
| PDF de la factura | Imprimir › Factura (versión 1.9) › Imprimir › icono de descarga del visor. Si en Descargas queda un .tmp, es el PDF completo (verificar %PDF/%%EOF) y se copia con el nombre final. |
| Importar facturas de venta | Ventas › Facturas de venta › Importar (sin confirmar) |

## Datos del negocio vistos en Xubio

- Circuito contable: "Contabilidad Colombia". Moneda: Pesos Colombianos.
- Facturas con el prefijo de numeración del negocio.
- IVA cuatrimestral (los libros proponen por defecto el cuatrimestre).

## Importar compras (verificado con piloto el 12/11/2026)

- Ruta: Compras › Comprobantes de Compra › Acciones › Importar › Desde Excel. El "Descargar modelo" de Xubio apunta a Argentina y está roto; el modelo de Colombia está en https://ayuda.xubio.com/help/downloads/co-como-importo-mis-facturas-de-compra/modelo-importacion-compras-1.xls (copia en `<carpeta_datos>/plantillas/`).
- Generar con `scripts/generar_import_compras.py`. **La columna IVA es el VALOR en pesos, no el porcentaje** (con 19 quedó $19 de IVA).
- TIPO 1 factura, 3 nota crédito (valores en positivo; Xubio la pone en negativo), 99 documento equivalente.
- Proveedor por nombre exacto de Xubio; debe existir antes. Usar los productos de compra que ya existan en Xubio.
- El archivo a subir debe estar en la carpeta de la sesión (file_upload no lee Documentos).
- Al crear un proveedor a mano, el botón Guardar a veces no responde con clic por referencia: hacer clic por coordenadas y verificar buscándolo en la lista antes de reintentar (evita duplicados).
- Para borrar: marcar casillas › Acciones › Eliminar › confirmar "Eliminar" en el diálogo "Pregunta".
- Importación masiva: Xubio ABORTA en el primer error y deja importadas las anteriores. Leer "Detalle del Proceso", excluir las ya importadas (por número) y reintentar. Errores vistos: producto excluido de IVA con IVA ("El producto 'ASESORIA' no puede tener IVA") y comprobante en cero ("Debe especificar al menos un item"; el script ya los omite).
- Si el proveedor en Xubio tiene condición IVA "No Aplica" (o tiene tipo de identificación Cédula: con CC el formulario ni muestra "Condición IVA"), Xubio importa la compra pero pone el IVA en 0 sin avisar. Arreglo: abrir el proveedor, Tipo de Identificación = 31-Nit, Condición IVA = IVA, Guardar (clic por coordenadas); luego borrar y reimportar sus compras.
- "No Aplica" sí se puede elegir a mano en el formulario de proveedor (con Tipo de Identificación 31-Nit), aunque no por el importador. Verificar siempre exportando Comprobantes de Compra (Acciones › Exportar › Excel) y cruzando por número contra compras.csv.

## Importar proveedores (Compras › Proveedores › Acciones › Importar)

- No usa el formato de la exportación: es un asistente que empareja columnas. Usar `scripts/generar_import_proveedores.py` (encabezados "primer apellido", "razón social", "código", "tipo de identificación", "número de identificación", "condición de iva", "tipo de organización") y asignar cada columna en las listas (el encabezado se redibuja tras cada cambio: asignar de a una).
- Valores = CÓDIGOS: tipo de organización `PN`/`PJ`; tipo de identificación `NIT`; condición de IVA `IVA`. "No Aplica" NO funciona por importador (ni `No Aplica`, ni `NO_APLICA`, ni vacío): esos proveedores se crean a mano en el formulario.
- Si el NIT ya existe (aunque sea como cliente) da "El número de identificación ya ha sido cargado".
- Exportar proveedores: Acciones › Exportar › Descargar datos → "Importacion de NXVOrganizacion.xlsx" (NIT en columna CUIT, nombre exacto en Nombre).

## Formato del importador

- Archivo Excel 97-2003 (`.xls`), fechas `DD/MM/AAAA`, impuestos en positivo, retenciones en negativo, productos con código de unidad DIAN.
