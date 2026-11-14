# Instalación y configuración

## Requisitos

- Claude Code (app de escritorio o CLI) con la extensión Claude in Chrome.
- Una cuenta de Xubio Colombia con la sesión iniciada en Chrome.
- Python 3.10 o superior con `pandas`, `openpyxl`, `xlrd` y `xlwt`.
- Opcional: conector de Gmail, para leer solicitudes de cotización.

## Pasos

1. Copia esta carpeta a `~/.claude/skills/facturacion-xubio/`.
2. Copia `config.example.json` como `config.json` y completa:
   - `panel_url`: el artefacto donde quieres ver el panel de impuestos.
   - `carpeta_datos`: carpeta local para exportaciones, plantillas e importaciones.
   - `ultimo_digito_nit` y `vencimientos_iva`: según el calendario tributario de la DIAN.
   - Etiquetas de Gmail para solicitudes nuevas y procesadas.
3. En `scripts/crear_clasificacion_inicial.py`, llena cada categoría con los NIT de tus proveedores.
4. Descarga una vez las plantillas oficiales de importación de Xubio a `<carpeta_datos>/plantillas/`.
5. Pide a Claude: "sincroniza Xubio".

## Ejecución programada

Calendario sugerido, como tareas programadas de Claude:

| Día | Hora | Modos |
|---|---|---|
| Lunes | 8:00 | `sincronizar` + `cotizaciones` |
| Miércoles | 8:00 | `cotizaciones` + `facturar` |
| Viernes | 15:00 | `sincronizar` + `cotizaciones` + `impuestos` |
| Días 1–10 de ene, may, sep | 8:00 | `impuestos` con alerta de IVA |

Las tareas necesitan el PC encendido, la app de Claude abierta y Chrome con la sesión de Xubio.

## Carpeta de datos

```
<carpeta_datos>/
  exportaciones/AAAA-MM-DD/   reportes descargados
  panel/                      CSV normalizados
  plantillas/                 modelos de importación de Xubio
  import/                     archivos generados para importar
  clasificacion_proveedores.csv
  cotizaciones.csv
```

Esta carpeta contiene tus datos contables: no la subas a un repositorio público.
