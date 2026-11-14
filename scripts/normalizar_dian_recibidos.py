"""Convierte el listado de documentos RECIBIDOS del portal DIAN (Descargar listados) en compras.csv del panel.

Uso:
  python normalizar_dian_recibidos.py --excel recibidos.xlsx --anio 2026 --salida carpeta [--clasificacion clasificacion.csv]

Salida compras.csv:
  fecha,numero,proveedor,nit,concepto,subtotal,iva,otros_impuestos,total,descontable

- Excluye "Application response" (acuses, no son compras) y documentos en cero.
- Las notas crédito restan (valores en negativo).
- subtotal = total - IVA - otros impuestos (el listado DIAN no trae la base).
- descontable: "Sí", "No" o "Por revisar". Se toma de clasificacion.csv (columnas nit,descontable)
  si existe; si no, "Por revisar". La usuaria decide qué compras son del negocio.

Requiere: pip install pandas openpyxl
"""
import argparse
from pathlib import Path

import pandas as pd

OTROS = ["ICA", "IC", "INC", "Timbre", "INC Bolsas", "IN Carbono", "IN Combustibles",
         "IC Datos", "ICL", "INPP", "IBUA", "ICUI"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", required=True)
    ap.add_argument("--anio", type=int, required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--clasificacion")
    a = ap.parse_args()

    df = pd.read_excel(a.excel, dtype=str)
    for c in ["IVA", "Total"] + OTROS:
        df[c] = pd.to_numeric(df.get(c), errors="coerce").fillna(0)
    tipo = df["Tipo de documento"].fillna("")
    df = df[~tipo.str.startswith("Application")]
    df = df[(df["Total"] != 0) | (df["IVA"] != 0)].copy()

    signo = df["Tipo de documento"].str.lower().str.contains("crédito|credito").map({True: -1, False: 1})
    fecha = pd.to_datetime(df["Fecha Emisión"], format="%d-%m-%Y", errors="coerce")
    otros = df[OTROS].sum(axis=1)

    out = pd.DataFrame({
        "fecha": fecha.dt.strftime("%Y-%m-%d"),
        "numero": (df["Prefijo"].fillna("") + df["Folio"].fillna("")).str.strip(),
        "proveedor": df["Nombre Emisor"].fillna("").str.split().str.join(" "),
        "nit": df["NIT Emisor"].fillna(""),
        "concepto": df["Tipo de documento"],
        "subtotal": ((df["Total"] - df["IVA"] - otros) * signo).round(0).astype("int64"),
        "iva": (df["IVA"] * signo).round(0).astype("int64"),
        "otros_impuestos": (otros * signo).round(0).astype("int64"),
        "total": (df["Total"] * signo).round(0).astype("int64"),
    })
    out["categoria"] = "Por clasificar"
    out["descontable"] = "Por revisar"
    if a.clasificacion and Path(a.clasificacion).exists():
        cl = pd.read_csv(a.clasificacion, dtype=str).dropna(subset=["nit"])
        cl["nit"] = cl["nit"].str.strip()
        out["categoria"] = out["nit"].map(dict(zip(cl["nit"], cl["categoria"]))).fillna("Por clasificar")
        out["descontable"] = out["nit"].map(dict(zip(cl["nit"], cl["descontable"]))).fillna("Por revisar")

    # Cruce con Xubio: una factura DIAN está "en Xubio" si hay una compra en Xubio del mismo NIT
    # con el mismo total (±1 peso). compras_xubio.csv lo deja normalizar_reportes.py.
    out["en_xubio"] = "No"
    ref = Path(a.salida) / "compras_xubio.csv"
    if ref.exists():
        x = pd.read_csv(ref, dtype=str)
        x["total"] = pd.to_numeric(x["subtotal"]) + pd.to_numeric(x["iva"])
        claves = {(p.strip().lower(), round(t)) for p, t in zip(x["proveedor"], x["total"])}
        out["en_xubio"] = [
            "Sí" if any(p.lower().startswith(k[0][:15]) and abs(t - k[1]) <= 1 for k in claves) else "No"
            for p, t in zip(out["proveedor"], out["total"])]

    out = out[out["fecha"].str.startswith(str(a.anio), na=False)].sort_values("fecha")
    Path(a.salida).mkdir(parents=True, exist_ok=True)
    out.to_csv(Path(a.salida) / "compras.csv", index=False, encoding="utf-8")
    print(f"compras.csv: {len(out)} documentos, IVA {out['iva'].sum():,}, total {out['total'].sum():,}")
    print(out.groupby("descontable")["iva"].sum().to_string())


if __name__ == "__main__":
    main()
