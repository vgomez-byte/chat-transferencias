import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

# CONFIGURACIÓN
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_URL:
    raise Exception("No existe SUPABASE_URL en .env")
if not SUPABASE_KEY:
    raise Exception("No existe SUPABASE_KEY en .env")
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# ORIGEN DE DATOS
# 1) Excel oficial en GERENCIA DVL (hoja BBDD)  -> ya no hace falta exportar CSV
# 2) Si no se encuentra, usa el CSV de la carpeta "datos" como antes
import datetime
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_FILE = os.getenv(
    "RUTA_EXCEL_TRANSFERENCIAS",
    os.path.join(
        os.path.expanduser("~"), "OneDrive - Macal", "GERENCIA DVL - Documentos",
        "Planillas", "Transferencias", "Seguimiento Transferencias y TAG 2025 2.0.xlsx"
    ),
)
HOJA_EXCEL = "BBDD"
CSV_FILE = os.path.join(
    BASE_DIR,
    "datos",
    "Seguimiento Transferencias y TAG 2025 2.0.csv"
)
print("=" * 60)
print("IMPORTADOR SUPABASE")
print("=" * 60)

if os.path.exists(EXCEL_FILE):
    print(f"Leyendo Excel (hoja {HOJA_EXCEL})...")
    df = pd.read_excel(
        EXCEL_FILE,
        sheet_name=HOJA_EXCEL,
        header=1,          # fila 1: TRANSFERENCIAS / TAG ; fila 2: encabezados
        dtype=object,
        engine="openpyxl",
    )
else:
    print("No se encontró el Excel, leyendo CSV...")
    try:
        df = pd.read_csv(
        CSV_FILE,
        encoding="utf-8-sig",
        sep=";",
        low_memory=False
    )
    except UnicodeDecodeError:
        print("CSV detectado...")
        df = pd.read_csv(
            CSV_FILE,
            encoding="cp1252",
            sep=";",
            header=1,
            low_memory=False
        )
print(f"Registros encontrados: {len(df)}")
df.columns = df.columns.str.strip()

# Eliminar filas sin patente
df = df[df["PPU"].notna()]
df = df[df["PPU"].astype(str).str.strip() != ""]

# Normalizar PPU
df["PPU"] = (
    df["PPU"]
    .astype(str)
    .str.strip()
    .str.upper()
)
df = df[df["PPU"] != ""]

def _orden_fecha(v):
    if isinstance(v, (datetime.datetime, datetime.date)):
        return pd.Timestamp(v)
    return pd.to_datetime(str(v).strip(), format="%d-%m-%Y", errors="coerce")

df["Fecha Remate Orden"] = df["Fecha Remate"].map(_orden_fecha)
df = (
    df.sort_values("Fecha Remate Orden")
      .drop_duplicates(subset=["PPU"], keep="last")
)
df.drop(columns=["Fecha Remate Orden"], inplace=True)
print(f"Registros válidos: {len(df)}")

# FUNCIONES
def texto(valor):
    """
    Convierte valores vacíos en None
    y elimina espacios.
    """
    if pd.isna(valor):
        return None
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    if isinstance(valor, (datetime.datetime, datetime.date)):
        valor = valor.strftime("%d-%m-%Y")
    valor = str(valor).strip()
    if valor == "":
        return None
    return valor
def fecha(valor):
    """
    Convierte fechas del CSV (DD-MM-YYYY) al formato YYYY-MM-DD.
    """
    if pd.isna(valor):
        return None
    # Si ya es Timestamp, devolver directamente
    if isinstance(valor, (pd.Timestamp, datetime.datetime, datetime.date)):
        return valor.strftime("%Y-%m-%d")
    valor = str(valor).strip()
    if valor == "":
        return None
    fecha = pd.to_datetime(
        valor,
        format="%d-%m-%Y",
        errors="coerce"
    )
    if pd.isna(fecha):
        fecha = pd.to_datetime(
            valor,
            format="%Y-%m-%d",
            errors="coerce"
        )
    if pd.isna(fecha):
        return None
    return fecha.strftime("%Y-%m-%d")
print("Preparando registros...")
registros = []

# CONSTRUIR REGISTROS
for _, fila in df.iterrows():
    registro = {
        "id_rte": texto(fila["ID Rte"]),
        "fecha_remate": fecha(fila["Fecha Remate"]),
        "lote": texto(fila["Lote"]),
        "ppu": texto(fila["PPU"]),
        "estado_lote": texto(fila["Estado Lote"]),
        "estado_transferencia": texto(fila["Estado de transferencia"]),
        "mandante_comercial": texto(fila["MANDANTE COMERCIAL"]),
        "observacion": texto(fila["Observación"]),
        "fecha_ultima_observacion": fecha(
            fila["F. última observación"]
        ),
        "ingreso_proveedor": fecha(
            fila["Ingreso Proveedor"]
        ),
        "solicitud_transferencia": fecha(
            fila["Solicitud transferencia"]
        ),
        "rechazo": fecha(
            fila["Rechazo"]
        ),
        "reingreso": fecha(
            fila["Reingreso"]
        ),
        "fecha_transferencia": fecha(
            fila["Transferido"]
        ),
        "enviado_banco": fecha(
            fila["Enviado Banco"]
        ),
        "recibido_banco": fecha(
            fila["Recibido Banco"]
        ),
        "enviado_mandante": fecha(
            fila["Enviado Mandante"]
        ),
        "recibido_mandante": fecha(
            fila["Recibido Mandante"]
        ),
        "enviado_legalizar": fecha(
            fila["Enviado a Legalizar"]
        ),
        "recibido_legalizacion": fecha(
            fila["Recibida Legalización"]
        )
    }
    registros.append(registro)
print(f"Registros preparados: {len(registros)}")


# CARGAR A SUPABASE
print("Subiendo registros a Supabase...")
TAMANO_LOTE = 500
total = len(registros)
print("Limpiando tabla...")

supabase.table("transferencias")\
    .delete()\
    .neq("ppu", "")\
    .execute()
for inicio in range(0, total, TAMANO_LOTE):
    fin = min(inicio + TAMANO_LOTE, total)
    lote = registros[inicio:fin]
    try:
        supabase.table("transferencias").insert(
            lote
        ).execute()
        print(
            f"✔ Registros {inicio + 1} - {fin} cargados."
        )
    except Exception as e:
        print(
            f"❌ Error entre {inicio + 1} y {fin}"
        )
        print(e)
        raise
print()
print("=" * 60)
print("IMPORTACIÓN TERMINADA")
print("=" * 60)
print(f"Total registros : {total}")
print("=" * 60)

if __name__ == "__main__":
    print()

    print("Proceso finalizado correctamente.")