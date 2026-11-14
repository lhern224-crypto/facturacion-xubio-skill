"""Genera el .xls para importar en Xubio (Compras > Proveedores > Acciones > Importar) los proveedores
que aparecen en compras.csv (DIAN) y aún no existen en Xubio.

Uso:
  python generar_import_proveedores.py --compras compras.csv --xubio proveedores_xubio.csv \
      --personas personas_naturales.csv --salida import_proveedores.xls

- proveedores_xubio.csv: nit,proveedor_xubio (sale de la exportación de proveedores de Xubio).
- personas_naturales.csv: nit,primer_apellido,segundo_apellido,primer_nombre,otros_nombres
  (los nombres de personas naturales se separan a mano: la DIAN no trae un orden fijo).
  Todo NIT que no esté ahí se crea como persona jurídica con su razón social.
- Columnas: las mismas de la exportación de Xubio ("Importacion de NXVOrganizacion").
Requiere: pip install pandas xlwt
"""
import argparse
import re
import unicodedata

import pandas as pd
import xlwt

COLS = ["Nombre", "Codigo", "Descripcion", "Activo", "PrimerApellido", "SegundoApellido", "PrimerNombre",
        "OtrosNombres", "NombreComercial", "IDFiscal", "RazonSocial", "CUIT", "DireccionCalle",
        "NombreExtranjero", "Nacionalidad", "DireccionNro", "DireccionDpto", "CodigoPostal", "Telefono",
        "Email", "EsClienteExtranjero", "esdefault", "EsResidente", "EsCliente", "EsTercero", "EsProveedor",
        "TipoProveedor", "paissatid", "EsBanco", "UsrCode", "AgenteRetencion", "PoseeSucursales",
        "DigitoVerificacionDian", "MercadoPagoClienteId", "EmailIncluyeCco", "usoCFDI", "EmailCc",
        "EmailCco", "OrigenID", "Region", "ProductoAsociadoID", "CategoriaFiscal_Codigo",
        "CuentaIDDeudaVenta_Codigo", "IdentificacionTributaria_Codigo", "CuentaIDDeudaCompra_Codigo",
        "Pais_Codigo", "Provincia_Codigo", "ListaPrecioVenta_Codigo", "ListaPrecioCompra_Codigo",
        "Localidad_Codigo", "TipoDeOrganizacion_Codigo"]


def dv_dian(nit):
    pesos = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    s = sum(int(d) * p for d, p in zip(reversed(nit), pesos))
    r = s % 11
    return r if r < 2 else 11 - r


def codigo(nombre):
    t = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().upper()
    return re.sub(r"_+", "_", re.sub(r"[^A-Z0-9]", "_", t)).strip("_")[:50]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compras", required=True)
    ap.add_argument("--xubio", required=True)
    ap.add_argument("--personas", required=True)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()

    c = pd.read_csv(a.compras, dtype={"nit": str})
    existentes = set(pd.read_csv(a.xubio, dtype=str)["nit"])
    pn = pd.read_csv(a.personas, dtype=str).fillna("").set_index("nit")
    prov = (c.groupby("nit").agg(proveedor=("proveedor", "first"), iva=("iva", "sum")).reset_index())
    prov = prov[~prov["nit"].isin(existentes)]

    # El importador de proveedores de Xubio CO empareja columnas por estos nombres (no usa el
    # formato de la exportación). Verificado el 12/11/2026.
    simple = ["primer apellido", "segundo apellido", "primer nombre", "otros nombres", "razón social",
              "código", "tipo de identificación", "número de identificación", "condición de iva",
              "tipo de organización"]
    wb2 = xlwt.Workbook(encoding="utf-8")
    ws2 = wb2.add_sheet("Hoja1")
    for j, h in enumerate(simple):
        ws2.write(0, j, h)

    wb = xlwt.Workbook(encoding="utf-8")
    ws = wb.add_sheet("Hoja1")
    for j, h in enumerate(COLS):
        ws.write(0, j, h)
    usados = set()
    for i, (_, r) in enumerate(prov.iterrows(), start=1):
        fila = {"Activo": 1, "CUIT": r["nit"], "EsProveedor": 1, "TipoProveedor": 0, "paissatid": 0,
                "DigitoVerificacionDian": dv_dian(r["nit"]), "MercadoPagoClienteId": 0, "OrigenID": 0,
                "Region": 0, "ProductoAsociadoID": 0, "CuentaIDDeudaVenta_Codigo": "CLIENTES",
                "IdentificacionTributaria_Codigo": "NIT",
                "CuentaIDDeudaCompra_Codigo": "PROVEEDORES_NACIONALES", "Pais_Codigo": "COLOMBIA"}
        if r["iva"] > 0:
            fila["CategoriaFiscal_Codigo"] = "IVA"
        if r["nit"] in pn.index:
            p = pn.loc[r["nit"]]
            nombre = " ".join(x for x in [p.primer_nombre, p.otros_nombres, p.primer_apellido,
                                          p.segundo_apellido] if x)
            fila.update({"PrimerApellido": p.primer_apellido, "SegundoApellido": p.segundo_apellido,
                         "PrimerNombre": p.primer_nombre, "OtrosNombres": p.otros_nombres,
                         "TipoDeOrganizacion_Codigo": "PN"})
        else:
            nombre = " ".join(str(r["proveedor"]).split())
            fila.update({"RazonSocial": nombre, "TipoDeOrganizacion_Codigo": "PJ"})
        cod = codigo(nombre)
        while cod in usados:
            cod += "_2"
        usados.add(cod)
        fila.update({"Nombre": nombre, "Codigo": cod})
        for j, h in enumerate(COLS):
            if h in fila:
                ws.write(i, j, fila[h])
        es_pn = fila["TipoDeOrganizacion_Codigo"] == "PN"
        valores = [fila.get("PrimerApellido", ""), fila.get("SegundoApellido", ""),
                   fila.get("PrimerNombre", ""), fila.get("OtrosNombres", ""),
                   "" if es_pn else nombre, cod, "NIT", r["nit"],
                   # Xubio pide CÓDIGOS, no textos: "PERSONA_NATURAL no existe" -> PN/PJ.
                   # Vacío hace que Xubio salte la fila en silencio (0 importados, 0 errores).
                   "IVA" if r["iva"] > 0 else "NO_APLICA",
                   "PN" if es_pn else "PJ"]
        for j, v in enumerate(valores):
            ws2.write(i, j, v)
    wb2.save(a.salida)
    wb.save(a.salida.replace(".xls", "_formato_exportacion.xls"))
    print(f"{a.salida}: {len(prov)} proveedores nuevos "
          f"({prov['nit'].isin(pn.index).sum()} personas naturales)")


if __name__ == "__main__":
    main()
