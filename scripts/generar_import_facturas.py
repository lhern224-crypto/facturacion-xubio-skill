"""Genera el .xls de importación de facturas de venta de Xubio a partir de cotizaciones aprobadas.

Uso:
  python generar_import_facturas.py --aprobadas aprobadas.csv --plantilla facturas_venta.xls --salida import.xls

aprobadas.csv (una fila por ítem):
  fecha,cliente,nit,producto,codigo_producto,cantidad,precio,descuento_pct,iva_pct,retefuente_pct,reteiva_pct,reteica_por_mil,observaciones

El script lee los encabezados de la plantilla oficial de Xubio y llena cada columna por nombre,
así sigue funcionando si Xubio cambia el orden. Reglas del importador: fechas DD/MM/AAAA,
impuestos en positivo, retenciones en negativo.

Requiere: pip install pandas xlrd xlwt
"""
import argparse
import sys
import unicodedata

import pandas as pd
import xlrd
import xlwt


def limpio(t):
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode()
    return " ".join(t.lower().replace(".", " ").replace("_", " ").split())


# encabezado de la plantilla (limpio) -> función que da el valor desde la fila
def construir_mapa():
    def pct(r, c):
        return float(r.get(c) or 0) / 100

    def base(r):
        return round(float(r["cantidad"]) * float(r["precio"]) * (1 - pct(r, "descuento_pct")), 2)

    return {
        "fecha": lambda r: pd.to_datetime(r["fecha"], dayfirst=False).strftime("%d/%m/%Y"),
        "fecha emision": lambda r: pd.to_datetime(r["fecha"]).strftime("%d/%m/%Y"),
        "cliente": lambda r: r["cliente"],
        "razon social": lambda r: r["cliente"],
        "nit": lambda r: r["nit"],
        "identificacion": lambda r: r["nit"],
        "producto": lambda r: r["producto"],
        "codigo producto": lambda r: r.get("codigo_producto", ""),
        "cantidad": lambda r: float(r["cantidad"]),
        "precio": lambda r: float(r["precio"]),
        "precio unitario": lambda r: float(r["precio"]),
        "descuento": lambda r: float(r.get("descuento_pct") or 0),
        "iva": lambda r: abs(round(base(r) * pct(r, "iva_pct"), 2)),
        "retefuente": lambda r: -abs(round(base(r) * pct(r, "retefuente_pct"), 2)),
        "retencion en la fuente": lambda r: -abs(round(base(r) * pct(r, "retefuente_pct"), 2)),
        "reteiva": lambda r: -abs(round(base(r) * pct(r, "iva_pct") * pct(r, "reteiva_pct"), 2)),
        "reteica": lambda r: -abs(round(base(r) * float(r.get("reteica_por_mil") or 0) / 1000, 2)),
        "observaciones": lambda r: r.get("observaciones", ""),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aprobadas", required=True)
    ap.add_argument("--plantilla", required=True)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()

    filas = pd.read_csv(a.aprobadas, dtype=str).fillna("").to_dict("records")
    if not filas:
        sys.exit("No hay cotizaciones aprobadas.")

    hoja = xlrd.open_workbook(a.plantilla).sheet_by_index(0)
    encabezados = [hoja.cell_value(0, c) for c in range(hoja.ncols)]
    mapa = construir_mapa()
    sin_mapa = [h for h in encabezados if limpio(h) not in mapa]
    if sin_mapa:
        print(f"Aviso: columnas de la plantilla sin dato (quedan vacías): {sin_mapa}")

    libro = xlwt.Workbook(encoding="utf-8")
    ws = libro.add_sheet(hoja.name)
    for c, h in enumerate(encabezados):
        ws.write(0, c, h)
    for i, r in enumerate(filas, start=1):
        for c, h in enumerate(encabezados):
            f = mapa.get(limpio(h))
            ws.write(i, c, f(r) if f else "")
    libro.save(a.salida)
    print(f"{a.salida}: {len(filas)} ítems. Revísalo antes de subirlo a Xubio.")


if __name__ == "__main__":
    main()
