# facturacion-xubio

Skill de Claude Code que automatiza la facturación de un negocio pequeño en **Xubio Colombia**, que no tiene API abierta. Claude trabaja con el navegador y con scripts de Python sobre los reportes en Excel.

## Qué hace

| Modo | Resultado |
|---|---|
| `sincronizar` | Descarga los Libros de IVA de Xubio, los normaliza y actualiza un panel de impuestos (artefacto de Claude). |
| `cotizaciones` | Convierte solicitudes (Gmail con etiqueta, o archivos) en cotizaciones dentro de Xubio. |
| `facturar` | Pasa cotizaciones aprobadas a facturas de venta, una a una o con el importador masivo. |
| `impuestos` | Resume facturado, IVA del período, retenciones y próximo vencimiento. |

Las compras (IVA descontable) salen de la exportación de documentos recibidos del catálogo de la DIAN, clasificadas por proveedor como del negocio o personales.

## Cómo está construida

- `SKILL.md`: instrucciones que sigue Claude, con los modos, el calendario y las reglas de seguridad.
- `config.example.json`: configuración de ejemplo. Cópiala como `config.json` y llénala.
- `reference/xubio-rutas.md`: rutas de menú y comportamientos de Xubio ya verificados, para que Claude no los redescubra en cada ejecución.
- `scripts/`: normalizadores y generadores de archivos de importación.

| Script | Uso |
|---|---|
| `normalizar_reportes.py` | Libros IVA de Xubio → `ventas.csv` / `compras_xubio.csv` |
| `normalizar_dian_recibidos.py` | Excel de recibidos de la DIAN → `compras.csv` |
| `crear_clasificacion_inicial.py` | Primera clasificación de proveedores por categoría |
| `excel_compras_organizadas.py` | Excel de compras ordenado por categoría |
| `generar_import_proveedores.py` | Archivo para importar proveedores a Xubio |
| `generar_import_compras.py` | Archivo para importar facturas de compra |
| `generar_import_facturas.py` | Archivo para importar facturas de venta |

## Documentos

- [Instalación y configuración](docs/INSTALACION.md)
- [Seguridad y límites](docs/SEGURIDAD-Y-LIMITES.md)

## Aviso

Las cifras de impuestos son estimados para seguimiento. Revísalas con tu contador antes de declarar. Este proyecto no está afiliado a Xubio, a la DIAN ni a Anthropic.
