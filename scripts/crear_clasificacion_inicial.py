"""Crea (o completa) clasificacion_proveedores.csv a partir de compras.csv.

Uso:
  python crear_clasificacion_inicial.py --compras compras.csv --salida clasificacion_proveedores.csv

Columnas: nit,proveedor,categoria,descontable
- Si el archivo ya existe, conserva lo que la usuaria haya editado y solo agrega proveedores nuevos.
- Proveedores nuevos sin regla quedan en "Por clasificar".
"""
import argparse
from pathlib import Path

import pandas as pd

# Llena cada lista con los NIT o cédulas de tus proveedores, ej. ["900123456"]
CATEGORIAS = {
    "Materiales y ferretería": [],
    "Diseño, impresión y papelería": [],
    "Tecnología y equipos": [],
    "Software y suscripciones": [],
    "Transporte, viajes y envíos": [],
    "Telecomunicaciones y servicios públicos": [],
    "Seguros y salud": [],
    "Trámites y gremios": [],
    "Servicios de personas naturales": [],
    "Alimentación y restaurantes": [],
    "Mercado y consumo": [],
    "Almacenes y tiendas": [],
    "Ropa, accesorios y cuidado personal": [],
    "Mascotas": [],
}
REGLA = {nit: cat for cat, nits in CATEGORIAS.items() for nit in nits}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compras", required=True)
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()

    c = pd.read_csv(a.compras, dtype={"nit": str})
    prov = c.groupby("nit")["proveedor"].first().reset_index()
    salida = Path(a.salida)
    previo = pd.read_csv(salida, dtype=str) if salida.exists() else pd.DataFrame(
        columns=["nit", "proveedor", "categoria", "descontable"])
    nuevos = prov[~prov["nit"].isin(previo["nit"])].copy()
    nuevos["categoria"] = nuevos["nit"].map(REGLA).fillna("Por clasificar")
    nuevos["descontable"] = "Sí"
    todo = pd.concat([previo, nuevos], ignore_index=True).sort_values(["categoria", "proveedor"])
    todo.to_csv(salida, index=False, encoding="utf-8-sig")
    print(f"{len(todo)} proveedores ({len(nuevos)} nuevos). Por clasificar: "
          f"{(todo['categoria'] == 'Por clasificar').sum()}")


if __name__ == "__main__":
    main()
