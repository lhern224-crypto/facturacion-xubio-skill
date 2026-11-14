"""Convierte los reportes de ventas y compras exportados de Xubio en los CSV del panel.

Uso:
  python normalizar_reportes.py --ventas ventas.xls --compras compras.xls --anio 2026 --salida carpeta

Salida:
  ventas.csv  -> fecha,numero,cliente,tipo_cliente,subtotal,iva,retefuente,reteiva,reteica,total
  compras.csv -> fecha,numero,proveedor,concepto,subtotal,iva

Requiere: pip install pandas openpyxl xlrd
"""
import argparse
import csv
import sys
import unicodedata
from pathlib import Path

import pandas as pd

# Encabezados posibles en los reportes de Xubio (en minúsculas y sin tildes).
# Si un reporte usa otro nombre, añádelo aquí.
SINONIMOS = {
    "fecha": ["fecha", "fecha comprobante", "fecha emision", "fecha factura"],
    "numero": ["numero", "nro", "numero comprobante", "comprobante", "factura"],
    "cliente": ["cliente", "razon social", "nombre cliente", "tercero"],
    "proveedor": ["proveedor", "razon social", "nombre proveedor", "tercero"],
    "nit": ["nit", "identificacion", "nit/cc", "documento"],
    "tipo_cliente": ["tipo cliente", "tipo persona", "tipo de persona", "tipo contribuyente"],
    "concepto": ["concepto", "descripcion", "detalle", "observaciones"],
    # Libro IVA Ventas/Compras de Xubio Colombia: "Total Gravado", "Total IVA", "Retenciones IVA".
    "subtotal": ["total gravado", "subtotal", "base", "base gravable", "neto", "importe neto", "valor antes de iva"],
    "gravado_0": ["total gravado 0%"],
    "excluido": ["total excluido"],
    "iva": ["total iva", "iva", "iva 19%", "impuesto iva", "valor iva"],
    "retefuente": ["retefuente", "retencion en la fuente", "rete fuente", "retencion fuente"],
    "reteiva": ["retenciones iva", "reteiva", "rete iva", "retencion iva", "retencion de iva"],
    "reteica": ["reteica", "rete ica", "retencion ica", "retencion de ica"],
    "total": ["total", "importe total", "valor total"],
    "estado": ["estado"],
    "tipo": ["tipo", "tipo comprobante"],
}

OBLIGATORIAS_VENTAS = ["fecha", "numero", "cliente", "subtotal", "iva"]
OBLIGATORIAS_COMPRAS = ["fecha", "numero", "proveedor", "subtotal", "iva"]


def limpio(texto):
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(t.lower().replace(".", " ").replace("_", " ").split())


def leer(path):
    path = Path(path)
    if path.suffix.lower() in (".csv", ".txt"):
        texto = path.read_text(encoding="utf-8-sig", errors="replace")
        sep = max([",", ";", "\t"], key=texto.count)
        filas = list(csv.reader(texto.splitlines(), delimiter=sep))
        ancho = max(len(f) for f in filas)
        crudo = pd.DataFrame([f + [None] * (ancho - len(f)) for f in filas], dtype=str)
    else:
        crudo = pd.read_excel(path, header=None, dtype=str)
    # Los reportes suelen traer títulos arriba: busca la fila con más encabezados conocidos.
    conocidos = {s for lista in SINONIMOS.values() for s in lista}
    mejor, puntos = 0, -1
    for i in range(min(30, len(crudo))):
        p = sum(limpio(v) in conocidos for v in crudo.iloc[i].tolist())
        if p > puntos:
            mejor, puntos = i, p
    df = crudo.iloc[mejor + 1:].copy()
    df.columns = [limpio(c) for c in crudo.iloc[mejor].tolist()]
    return df.dropna(how="all")


def mapear(df, campos, obligatorias, nombre):
    salida = pd.DataFrame()
    faltan = []
    for campo in campos:
        col = next((s for s in SINONIMOS.get(campo, [campo]) if s in df.columns), None)
        if col is None:
            if campo in obligatorias:
                faltan.append(campo)
            salida[campo] = None
        else:
            salida[campo] = df[col].values
    if faltan:
        sys.exit(f"[{nombre}] No encontré las columnas {faltan}. Encabezados del archivo: {list(df.columns)}")
    return salida


def numero(serie):
    s = serie.fillna("0").astype(str).str.replace(r"[^\d,.\-]", "", regex=True)
    # Formato colombiano 1.234.567,89 -> 1234567.89
    s = s.where(~s.str.contains(","), s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    # Conserva el signo: las notas crédito vienen en negativo y deben restar.
    return pd.to_numeric(s, errors="coerce").fillna(0).round(0).astype("int64")


def con_signo(rete, base):
    # Retenciones siempre restan; en una nota crédito se devuelven (signo de la base).
    signo = base.apply(lambda b: -1 if b < 0 else 1)
    return rete.abs() * signo


def fecha(serie):
    # Acepta AAAA-MM-DD (también con hora, como trae Excel) y DD/MM/AAAA, que es el formato de Xubio.
    s = serie.fillna("").astype(str).str.strip()
    iso = s.str.match(r"^\d{4}-\d{2}-\d{2}")
    f = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    f[iso] = pd.to_datetime(s[iso].str.slice(0, 10), format="%Y-%m-%d", errors="coerce")
    f[~iso] = pd.to_datetime(s[~iso], dayfirst=True, errors="coerce")
    if f.isna().any():
        malas = s[f.isna()].tolist()[:5]
        print(f"Aviso: {int(f.isna().sum())} fechas no se pudieron leer, por ejemplo {malas}")
    return f.dt.strftime("%Y-%m-%d")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ventas", required=True)
    ap.add_argument("--compras", required=True)
    ap.add_argument("--anio", type=int, required=True)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)

    v = mapear(leer(a.ventas),
               ["fecha", "tipo", "numero", "cliente", "nit", "tipo_cliente", "subtotal", "gravado_0",
                "excluido", "iva", "retefuente", "reteiva", "reteica", "total", "estado"],
               OBLIGATORIAS_VENTAS, "ventas")
    v["fecha"] = fecha(v["fecha"])
    for c in ["subtotal", "gravado_0", "excluido", "iva", "retefuente", "reteiva", "reteica", "total"]:
        v[c] = numero(v[c])
    # Base total = gravado + gravado 0% + excluido.
    v["subtotal"] = v["subtotal"] + v["gravado_0"] + v["excluido"]
    for c in ["retefuente", "reteiva", "reteica"]:
        v[c] = con_signo(v[c], v["subtotal"])
    # Las notas crédito comparten número con su factura: se marcan para distinguirlas.
    es_nc = v["tipo"].fillna("").map(limpio).str.startswith("nota credito")
    v.loc[es_nc, "numero"] = "NC " + v.loc[es_nc, "numero"].astype(str)
    if v["estado"].notna().any():
        v = v[~v["estado"].fillna("").str.lower().str.contains("anulad")]
    v["tipo_cliente"] = v["tipo_cliente"].fillna("")
    sin_tipo = v["tipo_cliente"] == ""
    # Sin columna de tipo: NIT de 9 dígitos que empieza por 8 o 9 suele ser empresa.
    nit = v["nit"].fillna("").astype(str).str.replace(r"\D", "", regex=True)
    v.loc[sin_tipo, "tipo_cliente"] = nit[sin_tipo].str.match(r"^[89]\d{8}").map(
        {True: "Empresa", False: "Persona natural"})
    # Total = lo que efectivamente paga el cliente (después de retenciones).
    v["total"] = v["subtotal"] + v["iva"] - v["retefuente"] - v["reteiva"] - v["reteica"]
    v = v[v["fecha"].str.startswith(str(a.anio), na=False)].sort_values("fecha")
    v[["fecha", "numero", "cliente", "tipo_cliente", "subtotal", "iva", "retefuente",
       "reteiva", "reteica", "total"]].to_csv(out / "ventas.csv", index=False, encoding="utf-8")

    c = mapear(leer(a.compras), ["fecha", "numero", "proveedor", "concepto", "subtotal", "gravado_0",
                                 "excluido", "iva", "estado"],
               OBLIGATORIAS_COMPRAS, "compras")
    c["fecha"] = fecha(c["fecha"])
    for col in ["subtotal", "gravado_0", "excluido", "iva"]:
        c[col] = numero(c[col])
    c["subtotal"] = c["subtotal"] + c["gravado_0"] + c["excluido"]
    if c["estado"].notna().any():
        c = c[~c["estado"].fillna("").str.lower().str.contains("anulad")]
    c["concepto"] = c["concepto"].fillna("")
    c = c[c["fecha"].str.startswith(str(a.anio), na=False)].sort_values("fecha")
    # compras_xubio.csv es solo de referencia: el panel usa compras.csv del portal DIAN
    # (normalizar_dian_recibidos.py), que es más completo. No sobrescribirlo.
    c[["fecha", "numero", "proveedor", "concepto", "subtotal", "iva"]].to_csv(
        out / "compras_xubio.csv", index=False, encoding="utf-8")

    print(f"ventas.csv: {len(v)} facturas, subtotal {v['subtotal'].sum():,}, IVA {v['iva'].sum():,}")
    print(f"compras_xubio.csv (referencia): {len(c)} facturas, IVA {c['iva'].sum():,}")


if __name__ == "__main__":
    main()
