"""
Indexa los PDF de Solicitudes de Transferencia y Padrones y sube a Supabase
los links de SharePoint por patente (tabla: documentos_transferencia).

Uso:
    python scripts/indexar_documentos.py            -> indexa y sube
    python scripts/indexar_documentos.py --prueba   -> solo muestra lo encontrado
"""
import os
import re
import sys
import datetime
from urllib.parse import quote

# CONFIGURACIÓN DE CARPETAS (rutas sincronizadas en el PC) Y SU URL EN SHAREPOINT
HOME = os.path.expanduser("~")

CARPETA_SOLICITUDES = os.getenv(
    "RUTA_SOLICITUDES",
    os.path.join(HOME, "OneDrive - Macal", "GERENCIA DVL - Documentos",
                 "Subastas", "Solicitudes Transferencia"),
)
URL_SOLICITUDES = ("https://macal1.sharepoint.com/sites/GERENCIADVL/"
                   "Documentos compartidos/Subastas/Solicitudes Transferencia")

CARPETA_PADRONES = os.getenv(
    "RUTA_PADRONES",
    os.path.join(HOME, "OneDrive - Macal", "GERENCIA DVL - Documentos",
                 "Subastas", "Padron Autos"),
)
URL_PADRONES = ("https://macal1.sharepoint.com/sites/GERENCIADVL/"
                "Documentos compartidos/Subastas/Padron Autos")

TABLA = "documentos_transferencia"

# Nombres de archivo esperados
#   Solicitud:  FLKR37.pdf  /  FLKR37 REINGRESO.pdf
#   Padrón:     T_600030147987_PZZL73_20260903.pdf
RE_SOLICITUD = re.compile(r"^([A-Z0-9]{5,7})(\s*REINGRESO)?\.PDF$", re.IGNORECASE)
RE_PADRON = re.compile(r"^T_(\d+)_([A-Z0-9]{5,7})_(\d{8})\.PDF$", re.IGNORECASE)


def armar_url(base, carpeta_local, ruta_archivo):
    relativa = os.path.relpath(ruta_archivo, carpeta_local).replace("\\", "/")
    return quote(base, safe=":/") + "/" + quote(relativa, safe="/")


def recorrer(carpeta):
    if not os.path.isdir(carpeta):
        print(f"⚠ No existe la carpeta: {carpeta}")
        return
    for raiz, _, archivos in os.walk(carpeta):
        for nombre in archivos:
            yield raiz, nombre


def indexar():
    docs = {}  # ppu -> dict
    no_reconocidos = []

    # Solicitudes
    for raiz, nombre in recorrer(CARPETA_SOLICITUDES):
        m = RE_SOLICITUD.match(nombre.strip())
        if not m:
            if nombre.lower().endswith(".pdf"):
                no_reconocidos.append(nombre)
            continue
        ppu = m.group(1).upper()
        url = armar_url(URL_SOLICITUDES, CARPETA_SOLICITUDES, os.path.join(raiz, nombre))
        campo = "url_reingreso" if m.group(2) else "url_solicitud"
        docs.setdefault(ppu, {"ppu": ppu})[campo] = url

    # Padrones (si hay más de uno por patente, se deja el más reciente)
    for raiz, nombre in recorrer(CARPETA_PADRONES):
        m = RE_PADRON.match(nombre.strip())
        if not m:
            if nombre.lower().endswith(".pdf"):
                no_reconocidos.append(nombre)
            continue
        ppu = m.group(2).upper()
        fecha = datetime.datetime.strptime(m.group(3), "%Y%m%d").strftime("%Y-%m-%d")
        reg = docs.setdefault(ppu, {"ppu": ppu})
        if reg.get("fecha_padron") and reg["fecha_padron"] >= fecha:
            continue
        reg["fecha_padron"] = fecha
        reg["url_padron"] = armar_url(URL_PADRONES, CARPETA_PADRONES, os.path.join(raiz, nombre))

    # Completar columnas para que todos los registros tengan la misma forma
    columnas = ["ppu", "url_solicitud", "url_reingreso", "url_padron", "fecha_padron"]
    registros = [{c: d.get(c) for c in columnas} for d in docs.values()]
    return registros, no_reconocidos


def subir(registros):
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv()
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise Exception("Faltan SUPABASE_URL o SUPABASE_KEY en .env")
    supabase = create_client(url, key)

    print("Limpiando tabla...")
    supabase.table(TABLA).delete().neq("ppu", "").execute()
    for i in range(0, len(registros), 500):
        lote = registros[i:i + 500]
        supabase.table(TABLA).insert(lote).execute()
        print(f"✔ Registros {i + 1} - {i + len(lote)} cargados.")


if __name__ == "__main__":
    print("=" * 60)
    print("INDEXADOR DE DOCUMENTOS")
    print("=" * 60)
    registros, no_reconocidos = indexar()
    print(f"Patentes con documentos : {len(registros)}")
    print(f"  con solicitud         : {sum(1 for r in registros if r['url_solicitud'])}")
    print(f"  con reingreso         : {sum(1 for r in registros if r['url_reingreso'])}")
    print(f"  con padrón            : {sum(1 for r in registros if r['url_padron'])}")
    if no_reconocidos:
        print(f"PDF con nombre no reconocido ({len(no_reconocidos)}):")
        for n in no_reconocidos[:20]:
            print("   -", n)

    if "--prueba" in sys.argv:
        for r in registros[:5]:
            print(r)
        print("Modo prueba: no se subió nada.")
    else:
        subir(registros)
        print("Proceso finalizado correctamente.")
