"""
Actualización automática del chat (la ejecuta el Programador de tareas de Windows).

- Si el Excel "Seguimiento Transferencias y TAG 2025 2.0" cambió -> sube los estados a Supabase.
- Si hay PDF nuevos o modificados en Solicitudes / Padrones  -> reindexa los links.
Si nada cambió, no hace nada. Todo queda registrado en logs/actualizacion_auto.log
"""
import os
import sys
import json
import datetime
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))
import indexar_documentos as idx  # noqa: E402

EXCEL_FILE = os.getenv(
    "RUTA_EXCEL_TRANSFERENCIAS",
    os.path.join(os.path.expanduser("~"), "OneDrive - Macal", "GERENCIA DVL - Documentos",
                 "Planillas", "Transferencias", "Seguimiento Transferencias y TAG 2025 2.0.xlsx"),
)
ESTADO = os.path.join(BASE_DIR, "logs", "estado_auto.json")
LOG = os.path.join(BASE_DIR, "logs", "actualizacion_auto.log")
os.makedirs(os.path.dirname(LOG), exist_ok=True)


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S}  {msg}\n")


def firma_documentos():
    """Cantidad de PDF y fecha de modificación más reciente de las carpetas de documentos."""
    total, ultima = 0, 0.0
    carpetas = [idx.CARPETA_SOLICITUDES] + idx.carpetas_padrones()
    for c in carpetas:
        for raiz, nombre in idx.recorrer(c):
            if nombre.lower().endswith(".pdf"):
                total += 1
                ultima = max(ultima, os.path.getmtime(os.path.join(raiz, nombre)))
    return f"{total}-{ultima:.0f}"


def ejecutar(script):
    python = sys.executable
    if python.lower().endswith("pythonw.exe"):
        python = python[:-5] + ".exe"  # python.exe, sin ventana gracias a CREATE_NO_WINDOW
    flags = 0x08000000 if os.name == "nt" else 0
    r = subprocess.run([python, os.path.join(BASE_DIR, "scripts", script)],
                       cwd=BASE_DIR, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", creationflags=flags)
    resumen = [l for l in r.stdout.splitlines() if "✔" not in l and l.strip() and "=====" not in l]
    for l in resumen[-8:]:
        log("   " + l)
    if r.returncode != 0:
        log("   ERROR: " + (r.stderr.strip().splitlines() or ["desconocido"])[-1])
    return r.returncode == 0


def main():
    try:
        estado = json.load(open(ESTADO, encoding="utf-8"))
    except Exception:
        estado = {}

    # 1) Excel de seguimiento
    if os.path.exists(EXCEL_FILE):
        mtime = str(int(os.path.getmtime(EXCEL_FILE)))
        if estado.get("excel") != mtime:
            log("Excel modificado -> subiendo estados de transferencias")
            if ejecutar("subir_csv_supabase.py"):
                estado["excel"] = mtime
    else:
        log(f"No se encontró el Excel: {EXCEL_FILE}")

    # 2) Documentos (solicitudes, reingresos, padrones)
    firma = firma_documentos()
    if estado.get("documentos") != firma:
        log("Documentos nuevos o modificados -> reindexando links")
        if ejecutar("indexar_documentos.py"):
            estado["documentos"] = firma

    json.dump(estado, open(ESTADO, "w", encoding="utf-8"))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR inesperado: {e}")
