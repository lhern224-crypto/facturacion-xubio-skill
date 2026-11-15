# facturacion-xubio

English | [Español](README.es.md)

A Claude Code skill that automates invoicing for a small business on **Xubio Colombia**, which has no open API. Claude works through the browser and with Python scripts over the Excel reports.

The skill's own instructions (`SKILL.md`, `reference/`) are written in Spanish, because Xubio's menus and the tax terms it handles are in Spanish.

## What it does

| Mode | Result |
|---|---|
| `sincronizar` | Downloads Xubio's VAT ledgers, normalizes them and updates a tax dashboard (a Claude artifact). |
| `cotizaciones` | Turns requests (labeled Gmail threads, or files) into quotes inside Xubio. |
| `facturar` | Turns approved quotes into sales invoices, one by one or with the bulk importer. |
| `impuestos` | Summarizes amount invoiced, VAT for the period, withholdings and the next due date. |

Purchases (deductible VAT) come from the received-documents export of the DIAN catalog, classified by supplier as business or personal.

## How it is built

- `SKILL.md`: the instructions Claude follows, with the modes, the calendar and the safety rules.
- `config.example.json`: sample configuration. Copy it as `config.json` and fill it in.
- `reference/xubio-rutas.md`: Xubio menu paths and behaviors already verified, so Claude does not rediscover them on every run.
- `scripts/`: normalizers and import-file generators.

| Script | Use |
|---|---|
| `normalizar_reportes.py` | Xubio VAT ledgers → `ventas.csv` / `compras_xubio.csv` |
| `normalizar_dian_recibidos.py` | DIAN received-documents Excel → `compras.csv` |
| `crear_clasificacion_inicial.py` | First classification of suppliers by category |
| `excel_compras_organizadas.py` | Purchases Excel sorted by category |
| `generar_import_proveedores.py` | File to import suppliers into Xubio |
| `generar_import_compras.py` | File to import purchase invoices |
| `generar_import_facturas.py` | File to import sales invoices |

## Documents

- [Installation and setup](docs/INSTALLATION.md)
- [Security and limits](docs/SECURITY-AND-LIMITS.md)

## Disclaimer

Tax figures are estimates for tracking. Review them with your accountant before filing. This project is not affiliated with Xubio, the DIAN or Anthropic.
