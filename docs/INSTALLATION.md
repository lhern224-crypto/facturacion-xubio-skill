# Installation and setup

[Español](INSTALACION.md)

## Requirements

- Claude Code (desktop app or CLI) with the Claude in Chrome extension.
- A Xubio Colombia account, signed in on Chrome.
- Python 3.10 or later with `pandas`, `openpyxl`, `xlrd` and `xlwt`.
- Optional: the Gmail connector, to read quote requests.

## Steps

1. Copy this folder to `~/.claude/skills/facturacion-xubio/`.
2. Copy `config.example.json` as `config.json` and fill in:
   - `panel_url`: the artifact where you want to see the tax dashboard.
   - `carpeta_datos`: a local folder for exports, templates and import files.
   - `ultimo_digito_nit` and `vencimientos_iva`: from the DIAN tax calendar.
   - The Gmail labels for new and processed requests.
3. In `scripts/crear_clasificacion_inicial.py`, fill each category with your suppliers' tax IDs (NIT).
4. Download Xubio's official import templates once to `<carpeta_datos>/plantillas/`.
5. Ask Claude: "sincroniza Xubio".

## Scheduled runs

Suggested calendar, as Claude scheduled tasks:

| Day | Time | Modes |
|---|---|---|
| Monday | 8:00 | `sincronizar` + `cotizaciones` |
| Wednesday | 8:00 | `cotizaciones` + `facturar` |
| Friday | 15:00 | `sincronizar` + `cotizaciones` + `impuestos` |
| Days 1–10 of Jan, May, Sep | 8:00 | `impuestos` with VAT filing alert |

The tasks need the PC on, the Claude app open, and Chrome signed in to Xubio.

## Data folder

```
<carpeta_datos>/
  exportaciones/YYYY-MM-DD/   downloaded reports
  panel/                      normalized CSV files
  plantillas/                 Xubio import templates
  import/                     generated import files
  clasificacion_proveedores.csv
  cotizaciones.csv
```

This folder holds your accounting data: do not upload it to a public repository.
