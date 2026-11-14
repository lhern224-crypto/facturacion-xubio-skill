"""Genera el .xls (Excel 97-2003) para importar compras en Xubio Colombia
(Compras > Comprobantes de Compra > Acciones > Importar > Desde Excel).

Uso:
  python generar_import_compras.py --compras compras.csv --productos productos_por_categoria.csv \
      --salida import_compras.xls [--numeros NUM1,NUM2] [--excluir-xubio]

- Una fila de encabezado por comprobante y una o dos filas de ítem:
  ítem gravado (base = IVA / 0.19, columna IVA = valor del IVA en pesos) y, si queda base
  sin IVA, un ítem con IVA 0.
- Otros impuestos (INC, ICA, etc.) se suman al ítem sin IVA para que el total cuadre.
- TIPO: 1 factura, 3 nota crédito, 99 documento equivalente/otros. Valores en positivo.
- El proveedor se escribe con el nombre tal como está en Xubio (columna proveedor_xubio de
  proveedores_xubio.csv si existe; si no, el nombre de la DIAN).
Requiere: pip install pandas xlwt
"""
import argparse
from pathlib import Path

import pandas as pd
import xlwt

COLS = ["NUMERODECONTROL", "PROVEEDOR", "TIPO", "NUMERO", "FECHA", "VENCIMIENTODELPAGO", "MONEDA",
        "COTIZACION", "FECHAFISCAL", "OBSERVACIONES", "PRODUCTOSERVICIOPERCEPCION", "CENTRODECOSTO",
        "CANTIDAD", "PRECIO", "IMPORTE", "IVA", "EXENOGRAV", "PRODUCTOOBSERVACION"]


def tipo(concepto):
    c = str(concepto).lower()
    if "crédito" in c or "credito" in c:
        return 3
    if "factura" in c:
        return 1
    return 99


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compras", required=True)
    ap.add_argument("--productos", required=True, help="CSV categoria,producto_xubio")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--numeros", help="solo estos números de comprobante (coma)")
    ap.add_argument("--proveedores-xubio", help="CSV nit,proveedor_xubio")
    ap.add_argument("--excluir-xubio", action="store_true", help="omite los que ya están en Xubio")
    ap.add_argument("--excluir-numeros", help="números ya importados (coma)")
    ap.add_argument("--excluir-nits", help="NIT a omitir (coma), p. ej. terceros que son solo clientes")
    ap.add_argument("--solo-con-proveedor", action="store_true",
                    help="solo comprobantes cuyo NIT está en --proveedores-xubio")
    a = ap.parse_args()

    c = pd.read_csv(a.compras, dtype={"nit": str, "numero": str})
    if a.numeros:
        c = c[c["numero"].isin(a.numeros.split(","))]
    if a.excluir_numeros:
        c = c[~c["numero"].isin(a.excluir_numeros.split(","))]
    if a.excluir_nits:
        c = c[~c["nit"].isin(a.excluir_nits.split(","))]
    if a.excluir_xubio and "en_xubio" in c:
        c = c[c["en_xubio"] != "Sí"]
    prod = dict(pd.read_csv(a.productos, dtype=str).values)
    nombres = {}
    if a.proveedores_xubio and Path(a.proveedores_xubio).exists():
        nombres = dict(pd.read_csv(a.proveedores_xubio, dtype=str).values)
    if a.solo_con_proveedor:
        fuera = c[~c["nit"].isin(nombres)]
        if len(fuera):
            print(f"Omitidos {len(fuera)} comprobantes sin proveedor en Xubio "
                  f"({fuera['nit'].nunique()} NIT), total {fuera['total'].abs().sum():,.0f}")
        c = c[c["nit"].isin(nombres)]

    # Xubio aborta con "Debe especificar al menos un item" si un comprobante no tiene valor.
    cero = c[(c["subtotal"].abs() + c["iva"].abs() + c.get("otros_impuestos", 0).abs()) == 0]
    if len(cero):
        print(f"Omitidos {len(cero)} comprobantes en cero: {', '.join(cero['numero'].astype(str))}")
        c = c.drop(cero.index)
    faltan = sorted(set(c["categoria"]) - set(prod))
    if faltan:
        raise SystemExit(f"Categorías sin producto de Xubio en {a.productos}: {faltan}")

    wb = xlwt.Workbook(encoding="utf-8")
    ws = wb.add_sheet("Hoja1")
    fecha_fmt = xlwt.easyxf(num_format_str="DD/MM/YYYY")
    for j, h in enumerate(COLS):
        ws.write(0, j, h)
    fila = 1
    resumen = []
    for n, (_, r) in enumerate(c.sort_values("fecha").iterrows(), start=1):
        f = pd.to_datetime(r["fecha"]).to_pydatetime()
        cab = {"NUMERODECONTROL": n, "PROVEEDOR": nombres.get(r["nit"], r["proveedor"]),
               "TIPO": tipo(r["concepto"]), "NUMERO": str(r["numero"]), "FECHA": f,
               "VENCIMIENTODELPAGO": f, "MONEDA": "Pesos Colombianos", "FECHAFISCAL": f,
               "OBSERVACIONES": f"{r['concepto']} - importado desde DIAN"}
        for j, h in enumerate(COLS):
            if h in cab:
                v = cab[h]
                ws.write(fila, j, v, fecha_fmt) if hasattr(v, "year") else ws.write(fila, j, v)
        fila += 1
        sub, iva, otros = abs(r["subtotal"]), abs(r["iva"]), abs(r.get("otros_impuestos", 0) or 0)
        base19 = round(iva / 0.19) if iva else 0
        base19 = min(base19, sub)
        resto = sub - base19 + otros
        # Xubio lee la columna IVA como VALOR en pesos (verificado en el piloto del 12/11/2026),
        # no como porcentaje.
        items = []
        if base19:
            items.append((base19, iva))
        if resto:
            items.append((resto, 0))
        for importe, valor_iva in items:
            it = {"NUMERODECONTROL": n, "PRODUCTOSERVICIOPERCEPCION": prod[r["categoria"]],
                  "CANTIDAD": 1, "PRECIO": importe, "IMPORTE": importe, "IVA": valor_iva,
                  "PRODUCTOOBSERVACION": r["proveedor"][:60]}
            for j, h in enumerate(COLS):
                if h in it:
                    ws.write(fila, j, it[h])
            fila += 1
        resumen.append((r["numero"], r["proveedor"], cab["TIPO"], sub, iva, otros, abs(r["total"])))
    wb.save(a.salida)
    print(f"{a.salida}: {len(resumen)} comprobantes, {fila - 1} filas")
    for x in resumen:
        print(" | ".join(map(str, x)))


if __name__ == "__main__":
    main()
