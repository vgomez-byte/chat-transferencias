import datetime
import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv
import base64

def set_bg_from_local(img_path):
    try:
        with open(img_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
        st.markdown(
            f"""
            <style>
            [data-testid="stAppViewContainer"] {{
                background-image: url("data:image/jpg;base64,{encoded}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.warning(f"No se pudo cargar el fondo: {e}")

# Usa ruta absoluta para evitar errores
img_path = os.path.join(os.path.dirname(__file__), "Fondo.jpg")
set_bg_from_local(img_path)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

def consultar_bd(pregunta):
    patente = pregunta.strip().replace(" ", "").upper()

    try:
        respuesta = (
            supabase
            .table("transferencias")
            .select("*")
            .eq("ppu", patente)
            .limit(1)
            .execute()
        )

        if not respuesta.data:
            return []

        fila = respuesta.data[0]

        return [{
            "fecha_subasta": fila.get("fecha_remate"),
            "PPU": fila.get("ppu"),
            "lote": fila.get("lote"),
            "ID_remate": fila.get("id_rte"),
            "estado_lote": fila.get("estado_lote"),
            "estado_transferencia": fila.get("estado_transferencia"),
            "fecha_ingreso_a_proveedor": fila.get("ingreso_proveedor"),
            "fecha_solicitud_transferencia": fila.get("solicitud_transferencia"),
            "fecha_transferencia": fila.get("fecha_transferencia"),
            "comentario": fila.get("observacion"),
            "fecha_observacion": fila.get("fecha_ultima_observacion"),
            "mandante_comercial": fila.get("mandante_comercial"),
            "fecha_rechazo": fila.get("rechazo"),
            "fecha_reingreso": fila.get("reingreso"),
            "fecha_enviado_banco": fila.get("enviado_banco"),
            "fecha_recibido_banco": fila.get("recibido_banco"),
            "fecha_enviado_mandante": fila.get("enviado_mandante"),
            "fecha_recibido_mandante": fila.get("recibido_mandante"),
            "fecha_enviado_notaria": fila.get("enviado_legalizar"),
            "fecha_recibido_notaria": fila.get("recibido_legalizacion"),
        }]

    except Exception as e:
        st.error(f"Error consultando Supabase: {e}")
        return []

st.set_page_config(page_title="Chat Transferencias", page_icon="💬", layout="centered")

# --- ESTILOS ---
# ...existing code...
st.markdown("""
<style>
/* CENTRAR TODO EL CONTENIDO REAL */
section.main > div {
    max-width: 700px;
    margin: auto;
}
/* Quitar fondo blanco */
.main .block-container {
    background: transparent;
    padding-top: 2rem;
}
div[data-testid="stTextInput"] {
    display: flex;
    justify-content: center;
}
div[data-testid="stTextInput"] > div {
    width: 280px;
}
/* INPUT SOLO BORDE NARANJA Y FONDO TRANSPARENTE, TEXTO NEGRO */
div[data-testid="stTextInput"] input {
    border: 2px solid #ff8000 !important;
    border-radius: 10px !important;
    font-size: 0.9em !important;
    padding: 0.4em 0.6em !important;
    height: 34px !important;
    background: transparent !important;
    box-shadow: none !important;
    color: #23272f !important;
    outline: none !important;
    background-clip: padding-box !important;
}
div[data-testid="stHorizontalBlock"] {
    justify-content: center;
}
.stButton > button {
    background-color: #ff8000;
    color: white;
    border-radius: 8px;
    border: none;
    font-weight: bold;
    padding: 0.4em 1.4em;
    font-size: 0.95em;
}
.stButton > button:hover {
    background-color: #ffa94d;
}
.chat-container {
    background: rgba(255,255,255,0.9);
    border-radius: 16px;
    padding: 20px;
    margin-top: 20px;
    box-shadow: 0 6px 20px rgba(255,140,0,0.25);
    border-left: 6px solid #ff8000;
    color: #23272f !important;
}
.row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
}
.chat-label {
    color: #ff8000;
    font-weight: 600;
}
.chat-value {
    color: #23272f !important;
    font-weight: 500;
}
/* Ajusta el espacio entre columnas y el input */
div[data-testid="column"] {
    padding: 0 !important;
}
div[data-testid="stTextInput"] > div {
    width: 240px !important;
}
.stButton > button {
    margin-right: 6px !important;
}
@media (prefers-color-scheme: dark) {
    body, [data-testid="stAppViewContainer"] {
        background: #23272f !important;
    }
    .chat-label {
        color: #ffb347 !important;
    }
    .chat-value {
        color: #fff !important;
    }
    div[data-testid="stTextInput"] input {
        background: #fff !important;      /* Fondo blanco en modo oscuro */
        color: #23272f !important;        /* Texto negro en modo oscuro */
        border: 2px solid #ff8000 !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        outline: none !important;
        background-clip: padding-box !important;
    }
    .stButton > button {
        background-color: #ff8000 !important;
        color: #fff !important;
    }
    .chat-container {
        background: #23272f !important;
        color: #fff !important;
    }
}
</style>
""", unsafe_allow_html=True)
# ...existing code...

st.title("💬 Estado de Transferencias")

col1, col2, col3 = st.columns([2.5,1,1])
with col1:
    pregunta = st.text_input("Escribe tu consulta:", key="consulta_input", label_visibility="visible", placeholder="Ej: ABCD12")
with col2:
    buscar = st.button("Buscar")
with col3:
    limpiar = st.button("Limpiar")

if "historial" not in st.session_state:
    st.session_state.historial = []

if buscar:
    if pregunta:
        st.session_state.historial = []  # Limpiar historial antes de mostrar nueva consulta
        respuesta = consultar_bd(pregunta)
        st.session_state.historial.append(("Consulta", pregunta))
        st.session_state.historial.append(("Sistema", respuesta if respuesta else "Sin resultados"))

if limpiar:
    st.session_state.historial = []

def formatea_fecha(fecha):
    if not fecha or str(fecha).strip() in ["Sin dato", "None"]:
        return "Sin dato"
    if isinstance(fecha, str):
        try:
            fecha = datetime.datetime.strptime(fecha[:10], "%Y-%m-%d")
        except:
            return fecha
    return fecha.strftime("%d-%m-%Y")

for autor, mensaje in st.session_state.historial:
    if autor == "Sistema" and isinstance(mensaje, list) and mensaje and all(isinstance(item, dict) for item in mensaje):
        for item in mensaje:
            tiene_datos = any([
                item.get("fecha_subasta"),
                item.get("PPU"),
                item.get("lote"),
                item.get("ID_remate"),
                item.get("estado_lote"),
                item.get("estado_transferencia"),
                item.get("fecha_ingreso_a_proveedor"),
                item.get("fecha_solicitud_transferencia"),
                item.get("fecha_transferencia"),
                item.get("comentario"),
                item.get("mandante_comercial"),
                item.get("fecha_rechazo"),
                item.get("fecha_reingreso")
            ])
            if not tiene_datos:
                continue

            fecha_transferencia = item.get("fecha_transferencia")
            transferido = fecha_transferencia and str(fecha_transferencia).strip() and fecha_transferencia != "Sin dato"

            # Construir el bloque HTML
            html = '<div class="chat-container">'
            html += f'<span class="chat-label">Fecha Subasta:</span> <span class="chat-value">{formatea_fecha(item.get("fecha_subasta"))}</span><br>'
            html += f'<span class="chat-label">PPU:</span> <span class="chat-value">{item.get("PPU", "Sin dato")}</span><br>'
            html += f'<span class="chat-label">Lote:</span> <span class="chat-value">{item.get("lote", "Sin dato")}</span><br>'
            html += f'<span class="chat-label">ID Remate:</span> <span class="chat-value">{item.get("ID_remate", "Sin dato")}</span><br>'
            html += f'<span class="chat-label">Estado Lote:</span> <span class="chat-value">{item.get("estado_lote", "Sin dato")}</span><br>'
            html += f'<span class="chat-label">Estado Transferencia:</span> <span class="chat-value">{item.get("estado_transferencia", "Sin dato")}</span><br>'

            if transferido:
                html += f'<span class="chat-label">Fecha Transferencia:</span> <span class="chat-value">{formatea_fecha(fecha_transferencia)}</span><br>'
            else:
                fecha_ingreso = formatea_fecha(item.get("fecha_ingreso_a_proveedor"))
                if fecha_ingreso != "Sin dato":
                    html += f'<span class="chat-label">Fecha Ingreso a Proveedor:</span> <span class="chat-value">{fecha_ingreso}</span><br>'

                fecha_solicitud = formatea_fecha(item.get("fecha_solicitud_transferencia"))
                if fecha_solicitud != "Sin dato":
                    html += f'<span class="chat-label">Fecha Solicitud Transferencia:</span> <span class="chat-value">{fecha_solicitud}</span><br>'

                fecha_inicio = item.get("fecha_reingreso") or item.get("fecha_solicitud_transferencia")
                if fecha_inicio and str(fecha_inicio).strip() and fecha_inicio != "Sin dato":
                    try:
                        if isinstance(fecha_inicio, str):
                            fecha_inicio_dt = datetime.datetime.strptime(str(fecha_inicio)[:10], "%Y-%m-%d").date()
                        else:
                            fecha_inicio_dt = fecha_inicio
                        dias_transcurridos = (datetime.date.today() - fecha_inicio_dt).days
                        html += f'<span class="chat-label">Días desde {"reingreso" if item.get("fecha_reingreso") else "solicitud de transferencia"}:</span> <span class="chat-value">{dias_transcurridos} días</span><br>'
                    except Exception:
                        pass

                etapas = [
                    ("Enviado a Banco", "fecha_enviado_banco"),
                    ("Recibido Banco", "fecha_recibido_banco"),
                    ("Enviado a Mandante", "fecha_enviado_mandante"),
                    ("Recibido Mandante", "fecha_recibido_mandante"),
                    ("Enviado a Legalizar", "fecha_enviado_notaria"),
                    ("Recibido Legalizar", "fecha_recibido_notaria"),
                ]
                fechas_etapas = []
                for nombre, campo in etapas:
                    valor = item.get(campo)
                    if valor and str(valor).strip() and valor != "Sin dato":
                        html += f'<span class="chat-label">{nombre}:</span> <span class="chat-value">{formatea_fecha(valor)}</span><br>'
                        fechas_etapas.append((nombre, valor))

                for i in range(1, len(fechas_etapas)):
                    try:
                        f1 = fechas_etapas[i-1][1]
                        f2 = fechas_etapas[i][1]
                        if isinstance(f1, str):
                            f1 = datetime.datetime.strptime(str(f1)[:10], "%Y-%m-%d").date()
                        if isinstance(f2, str):
                            f2 = datetime.datetime.strptime(str(f2)[:10], "%Y-%m-%d").date()
                        dias = (f2 - f1).days
                        html += f'<span class="chat-label">Días entre {fechas_etapas[i-1][0]} y {fechas_etapas[i][0]}:</span> <span class="chat-value">{dias} días</span><br>'
                    except Exception:
                        pass

                if item.get("fecha_rechazo"):
                    html += f'<span class="chat-label">Fecha Rechazo:</span> <span class="chat-value">{formatea_fecha(item.get("fecha_rechazo"))}</span><br>'
                    html += f'<span class="chat-label">Fecha Reingreso:</span> <span class="chat-value">{formatea_fecha(item.get("fecha_reingreso"))}</span><br>'

            comentario = item.get("comentario")
            fecha_observacion = item.get("fecha_observacion")
            if comentario and str(comentario).strip():
                html += f'<span class="chat-label">Comentario:</span> <span class="chat-value">{comentario}</span><br>'
                if fecha_observacion:
                    html += f'<span class="chat-label">Fecha Observación:</span> <span class="chat-value">{formatea_fecha(fecha_observacion)}</span><br>'
            html += f'<span class="chat-label">Mandante Comercial:</span> <span class="chat-value">{item.get("mandante_comercial", "Sin dato")}</span>'
            html += '</div>'

            st.markdown(html, unsafe_allow_html=True)
    else:
        st.write(f"{autor}: {mensaje}")