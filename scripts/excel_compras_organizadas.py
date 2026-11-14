"""Genera un Excel organizado de las compras (facturas recibidas DIAN).

Uso:
  python excel_compras_organizadas.py --compras compras.csv --salida Compras_2026_organizadas.xlsx

Hojas: Resumen (por categoría), Por mes (categoría x mes), Por proveedor, Detalle,
Pendientes Xubio (no registradas), Por clasificar.
Requiere: pip install pandas openpyxl
"""
import argparse

import pandas as pd
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def formatear(ws, moneda_desde=2):
    ws.freeze_panes = "A2"
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F4E78")
    for i, col in enumerate(ws.columns, start=1):
        largo = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[get_column_letter(i)].width = min(max(10, largo + 2), 60)
        if i >= moneda_desde:
            for c in col[1:]:
                if isinstance(c.value, (int, float)):
                    c.number_format = '"$" #,##0'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compras", required=True)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()

    c = pd.read_csv(a.compras, dtype={"nit": str, "numero": str})
    c["mes"] = pd.to_datetime(c["fecha"]).dt.month.map(lambda m: f"{m:02d}-{MESES[m - 1]}")

    resumen = (c.groupby("categoria").agg(documentos=("total", "size"), base=("subtotal", "sum"),
                                          iva=("iva", "sum"), otros_impuestos=("otros_impuestos", "sum"),
                                          total=("total", "sum"))
               .sort_values("total", ascending=False).reset_index())
    resumen.loc[len(resumen)] = ["TOTAL", resumen.documentos.sum(), resumen.base.sum(), resumen.iva.sum(),
                                 resumen.otros_impuestos.sum(), resumen.total.sum()]
    por_mes = c.pivot_table(index="categoria", columns="mes", values="total", aggfunc="sum", fill_value=0)
    por_mes["Total"] = por_mes.sum(axis=1)
    por_mes = por_mes.sort_values("Total", ascending=False).reset_index()
    por_prov = (c.groupby(["categoria", "proveedor", "nit"])
                .agg(documentos=("total", "size"), iva=("iva", "sum"), total=("total", "sum"))
                .reset_index().sort_values(["categoria", "total"], ascending=[True, False]))
    cols = ["fecha", "numero", "proveedor", "nit", "categoria", "concepto", "subtotal", "iva",
            "otros_impuestos", "total", "en_xubio"]
    detalle = c.sort_values("fecha")[cols]

    with pd.ExcelWriter(a.salida, engine="openpyxl") as w:
        resumen.to_excel(w, sheet_name="Resumen", index=False)
        por_mes.to_excel(w, sheet_name="Por mes", index=False)
        por_prov.to_excel(w, sheet_name="Por proveedor", index=False)
        detalle.to_excel(w, sheet_name="Detalle", index=False)
        detalle[detalle.en_xubio != "Sí"].to_excel(w, sheet_name="Pendientes Xubio", index=False)
        detalle[detalle.categoria == "Por clasificar"].to_excel(w, sheet_name="Por clasificar", index=False)
        desde = {"Resumen": 3, "Por mes": 2, "Por proveedor": 5, "Detalle": 7,
                 "Pendientes Xubio": 7, "Por clasificar": 7}
        for nombre, ws in w.sheets.items():
            formatear(ws, desde[nombre])
        w.sheets["Resumen"].cell(row=len(resumen) + 1, column=1).font = Font(bold=True)
    print(f"{a.salida}: {len(c)} documentos, {c.categoria.nunique()} categorías")


if __name__ == "__main__":
    main()
