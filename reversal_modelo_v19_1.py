# GrekoTrader v19.1 — Tab Posiciones Unificado (combobox)
# Refactorización: 3 tabs → 1 tab con selector de cartera
# Eliminadas ~1,752 líneas de código duplicado

"""
╔══════════════════════════════════════════════════════════════════╗
║  GREKOTRADER - 100% Automático  - Sin datos en duro  - v13               ║
║                                                                  ║
║  Instalar:  pip install streamlit plotly pandas numpy           ║
║  Ejecutar:  streamlit run reversal_modelo_v5.py                 ║
║                                                                  ║
║  CSV formato (posiciones.csv):                                  ║
║  Ticker,Precio_Compra,Cantidad,Fecha                           ║
║  NBIS,92.00,50,2026-03-10                                      ║
║  RGTI,12.50,200,2026-02-15                                     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import streamlit as st

# v19.1: Lista maestra de ETFs — excluidos del scan de acciones
# Se monitoran en Tab8 Estrategia ETF con lógica propia
_ETF_CRYPTO     = {"IBIT","ETHA","MSTU","GBTC","FBTC","BITB","ARKB","BRRR","BTCO","ETHW"}
_ETF_SECTORIAL  = {"TAN","ARKK","ARKG","ARKF","SMH","SOXX","IBB","XLK","XLF","XLV",
                   "XLE","XLI","XLU","XLB","XLRE","XLC","XLP","XLY","GDX","GDXJ"}
_ETF_INDICE     = {"VOO","SPY","IVV","QQQ","VTI","SCHB","ITOT","VEA","VWO","AGG","BND",
                   "VNQ","DIA","IWM","MDY","ONEQ"}
_ETF_APALANCADO = {"CONL","NVDL","TQQQ","SOXL","LABU","UDOW","DPST","NAIL","WEBL",
                   "MSTU","CURE","DFEN","WANT","RETL","FAS","FAZ","SPXL","SPXS",
                   "TECL","TECS","FNGU","FNGD","BULZ","BERZ"}
_ETF_LATAM      = {"EWZ","EWW","ILF","ARGT","ECH","GXG","EPU"}

# Union de todos — cualquier ticker en esta lista es ETF
_TODOS_ETFS = (_ETF_CRYPTO | _ETF_SECTORIAL | _ETF_INDICE |
               _ETF_APALANCADO | _ETF_LATAM)

def _es_etf(ticker: str) -> bool:
    """v19: True si el ticker es un ETF conocido."""
    return str(ticker).upper().strip() in _TODOS_ETFS



# v19: Silenciar warnings ruidosos de yfinance en consola
import logging as _logging
import warnings as _warnings
_warnings.filterwarnings("ignore", category=FutureWarning)
_warnings.filterwarnings("ignore", category=DeprecationWarning)
_logging.getLogger("yfinance").setLevel(_logging.ERROR)
_logging.getLogger("urllib3").setLevel(_logging.ERROR)
_logging.getLogger("peewee").setLevel(_logging.ERROR)
import warnings as _warnings
_warnings.filterwarnings("ignore", category=UserWarning)  # suprimir 404 yfinance
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import io

st.set_page_config(
    page_title="GrekoTrader v19",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state - inicializar SIEMPRE al inicio ─────────────
if "noticias_cache" not in st.session_state:
    st.session_state["noticias_cache"] = {}
if "noticias_actualizadas" not in st.session_state:
    st.session_state["noticias_actualizadas"] = None

# ─────────────────────────────────────────────────────────────
#  PALETA - LIGHT MODE PROFESIONAL
# ─────────────────────────────────────────────────────────────
BG_APP   = "#F8FAFC"
BG_CARD  = "#FFFFFF"
BG_TABLE = "#FFFFFF"
BG_HEAD  = "#F1F5F9"
BG_ROW2  = "#F8FAFC"
BOR      = "#E2E8F0"
BOR2     = "#CBD5E1"
TXT      = "#1E293B"
TXT_MUT  = "#64748B"
TXT_SOFT = "#94A3B8"

# Colores semánticos light
G      = "#16A34A"; G_BG = "#F0FDF4"; G_BOR = "#BBF7D0"
R      = "#DC2626"; R_BG = "#FEF2F2"; R_BOR = "#FECACA"
A      = "#D97706"; A_BG = "#FFFBEB"; A_BOR = "#FDE68A"
B      = "#2563EB"; B_BG = "#EFF6FF"; B_BOR = "#BFDBFE"
P      = "#7C3AED"; P_BG = "#F5F3FF"; P_BOR = "#DDD6FE"
C      = "#0891B2"; C_BG = "#ECFEFF"; C_BOR = "#A5F3FC"
OR     = "#EA580C"; OR_BG= "#FFF7ED"; OR_BOR= "#FED7AA"

st.markdown(f"""
<style>
/* ── Fondo general ── */
[data-testid="stAppViewContainer"] {{ background:{BG_APP}; }}
[data-testid="stSidebar"]          {{ background:{BG_CARD}; border-right:1px solid {BOR}; box-shadow:2px 0 8px rgba(0,0,0,.04); }}
.main .block-container              {{ padding:0.8rem 1.4rem; max-width:100%; }}

/* ── Métricas ── */
[data-testid="metric-container"]   {{ background:{BG_CARD}; border:1px solid {BOR}; border-radius:12px; padding:12px 16px; box-shadow:0 1px 3px rgba(0,0,0,.05); }}
[data-testid="stMetricLabel"]      {{ color:{TXT_MUT} !important; font-size:11px !important; font-weight:600 !important; }}
[data-testid="stMetricValue"]      {{ color:{TXT} !important; font-size:22px !important; font-weight:700 !important; }}
[data-testid="stMetricDelta"]      {{ font-size:11px !important; }}

/* ── Tabs ── */
div[data-testid="stTabs"] button   {{ font-size:13px; color:{TXT_MUT}; font-weight:500; }}
div[data-testid="stTabs"] button[aria-selected="true"] {{ color:{B}; font-weight:700; border-bottom:2px solid {B}; }}

/* ── Tablas ── */
.tbl-wrap  {{ overflow-x:auto; border-radius:12px; border:1px solid {BOR}; box-shadow:0 1px 4px rgba(0,0,0,.04); margin-bottom:12px; }}
.dtbl      {{ width:100%; border-collapse:collapse; font-size:12.5px; table-layout:auto; background:{BG_TABLE}; }}
.dtbl th   {{ background:{BG_HEAD}; color:{TXT_MUT}; font-size:11px; font-weight:700;
              padding:10px 14px; border-bottom:2px solid {BOR};
              text-transform:uppercase; letter-spacing:.06em; white-space:nowrap; text-align:left; }}
.dtbl td   {{ padding:10px 14px; border-bottom:1px solid {BOR};
              vertical-align:middle; color:{TXT}; white-space:nowrap; }}
.dtbl tr:nth-child(even) td {{ background:{BG_ROW2}; }}
.dtbl tr:hover td {{ background:#EFF6FF; transition:background .1s; }}
.dtbl tr:last-child td {{ border:none; }}

/* ── Badges ── */
.badge {{ display:inline-block; font-size:10.5px; font-weight:700;
          padding:3px 10px; border-radius:6px; white-space:nowrap; letter-spacing:.03em; }}
.bg-g  {{ background:{G_BG};  color:{G};  border:1px solid {G_BOR}; }}
.bg-r  {{ background:{R_BG};  color:{R};  border:1px solid {R_BOR}; }}
.bg-a  {{ background:{A_BG};  color:{A};  border:1px solid {A_BOR}; }}
.bg-b  {{ background:{B_BG};  color:{B};  border:1px solid {B_BOR}; }}
.bg-p  {{ background:{P_BG};  color:{P};  border:1px solid {P_BOR}; }}
.bg-c  {{ background:{C_BG};  color:{C};  border:1px solid {C_BOR}; }}
.bg-or {{ background:{OR_BG}; color:{OR}; border:1px solid {OR_BOR}; }}
.bg-gr {{ background:{BG_HEAD}; color:{TXT_MUT}; border:1px solid {BOR}; }}

/* ── Cards y secciones ── */
.sec-header {{ display:flex; align-items:center; gap:12px; margin:14px 0 10px;
               padding:12px 18px; border-radius:12px; border:1px solid; }}
.pos-card   {{ background:{BG_CARD}; border:1px solid {BOR}; border-radius:14px;
               padding:18px; margin-bottom:14px; box-shadow:0 2px 6px rgba(0,0,0,.05); }}
.info-box   {{ background:{BG_HEAD}; border:1px solid {BOR}; border-radius:10px;
               padding:12px 16px; font-size:12px; color:{TXT_MUT}; line-height:1.7; margin-bottom:12px; }}

footer{{visibility:hidden;}} #MainMenu{{visibility:hidden;}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  COLORES SECTOR
# ─────────────────────────────────────────────────────────────
SECTOR_COLORS = {
    "Tech":"#2563EB","Salud":"#16A34A","Energía":"#D97706",
    "Finanzas":"#7C3AED","Consumo":"#EA580C","Industrial":"#64748B",
    "Cripto/AI":"#0891B2","Quantum":"#7C3AED","Fintech":"#EA580C",
    "AI Infra":"#2563EB","IA y Software":"#2563EB",
}
PT = dict(
    paper_bgcolor=BG_APP, plot_bgcolor=BG_CARD,
    font_color=TXT, font_size=11,
    margin=dict(l=10,r=10,t=36,b=10),
)

# ─────────────────────────────────────────────────────────────
#  UNIVERSO - Actualizado Abril 2026
#  Estado_Patron:
#   "REFERENCIA"  - patrón completado, solo benchmark
#   "ACTIVO"      - patrón en curso, oportunidad real AHORA
#   "FORMANDO"    - fondo formándose, vigilar catalizador
#   "BAJADA"      - bajada activa, acumular en watchlist
# ─────────────────────────────────────────────────────────────
RAW = [
    # ══ REFERENCIA ══════════════════════════════════════════
    ("NBIS","Nebius Group","AI Infra",
     165.0,62,180,+5.0,0.80,3.2,2.71,-38,141,"Oct-25",4,17.47,
     1.2,0.9,2.0,"Contrato","NVIDIA $2B + Meta $27B","Completado",
     ["IREN","APLD","CORZ","CLSK"],"",
     "Patron completado +80% desde fondo. Referencia del modelo.","REFERENCIA"),

    # ══ ACTIVO - oportunidades reales HOY abril 2026 ════════
    ("MSFT","Microsoft Corp","AI Infra",
     371.0,36,145,-14.0,0.40,1.8,1.80,-22,475,"Feb-26",2,5.2,
     0.8,0.6,1.8,"Earnings","Q3 earnings 29 Abr  - Azure growth + AI CapEx","29 Abr 2026",
     ["AMZN","GOOGL","CRM"],"",
     "RSI 36 sobreventa. -22% YTD. Earnings 29 Abr catalizador principal.","ACTIVO"),

    ("AMZN","Amazon.com","AI Infra",
     198.0,34,155,-16.0,0.35,2.0,1.39,-24,261,"Feb-26",2,4.8,
     0.6,0.5,1.5,"Earnings","Q1 earnings 30 Abr  - AWS growth 21-22% + $200B CapEx","30 Abr 2026",
     ["MSFT","GOOGL"],"",
     "RSI 34. -24% YTD. AWS acceleration catalizador. Earnings 30 Abr.","ACTIVO"),

    ("GOOGL","Alphabet Inc","AI Infra",
     155.0,37,138,-13.0,0.30,1.9,1.60,-20,208,"Feb-26",2,4.2,
     0.5,0.4,1.2,"Earnings","Q1 earnings 23 Abr  - Cloud 48% growth","23 Abr 2026",
     ["META","MSFT"],"",
     "RSI 37. Earnings 23 Abr. Cloud +48% YoY. Setup solido.","ACTIVO"),

    ("META","Meta Platforms","AI Infra",
     521.0,40,128,-8.0,0.50,1.5,1.40,-18,636,"Feb-26",2,3.8,
     0.4,0.3,0.8,"Earnings","Q1 earnings 30 Abr  - Llama AI + Reality Labs","30 Abr 2026",
     ["GOOGL","SNAP"],"",
     "RSI 40. Corrigio desde maximos. Earnings 30 Abr.","ACTIVO"),

    ("ZS","Zscaler Inc","Tech",
     175.0,28,220,-22.0,0.60,1.2,2.20,-42,301,"Nov-25",4,18.5,
     0.5,0.4,1.4,"Earnings","FY Q2 record revenue $788M  - MACD girando alcista","May 2026",
     ["CRWD","PANW"],"",
     "RSI 28. Sobreventa >1 mes. MACD alcista. 34 analistas Buy.","ACTIVO"),

    ("NVDA","NVIDIA Corp","AI Infra",
     108.0,38,162,-14.0,0.45,1.8,2.20,-28,153,"Ene-26",2,6.8,
     0.5,0.4,1.2,"Earnings","Q1 FY27 earnings 28 May  - Blackwell demand  - Vera Rubin","28 May 2026",
     ["AMD","SMCI","MRVL","ANET"],"",
     "RSI 38. -28% desde pico. Blackwell demanda. Earnings Mayo.","ACTIVO"),

    # ══ FORMANDO - fondo en construccion ════════════════════
    ("AMD","AMD Corp","AI Infra",
     92.0,35,168,-18.0,0.30,1.5,2.40,-42,159,"Nov-25",4,9.4,
     0.3,0.2,0.5,"Earnings","Q1 earnings 29 Abr  - MI350X GPU demand","29 Abr 2026",
     ["SMCI","ANET","MRVL"],"NVDA",
     "RSI 35. Arrastrada por NVDA. Earnings 29 Abr catalizador.","FORMANDO"),

    ("APLD","Applied Digital","AI Infra",
     26.0,32,185,-22.0,0.45,1.2,7.10,-38,42,"Nov-25",4,12.5,
     0.4,0.3,0.8,"Earnings","CoreWeave lease expansion  - AI infra continua","May 2026",
     ["IREN","CORZ"],"",
     "RSI 32. AI infra continua. Correccion post-earnings absorbida.","FORMANDO"),

    ("IREN","Iris Energy","Cripto/AI",
     38.0,30,195,-24.0,0.35,1.1,4.24,-42,65,"Nov-25",4,11.8,
     0.3,0.2,0.6,"Earnings","BTC >$70K  - Microsoft AI deal activo","May 2026",
     ["CORZ","CLSK","MARA"],"NBIS",
     "RSI 30. BTC correlacion + AI. Fondo formando en soporte.","FORMANDO"),

    ("TSLA","Tesla Inc","Consumo",
     238.0,36,148,-10.0,0.25,1.6,2.80,-45,480,"Dic-24",4,5.2,
     0.4,0.3,0.9,"Earnings","Q1 earnings 22 Abr  - Robotaxi + energia","22 Abr 2026",
     ["RIVN","LCID"],"",
     "RSI 36. Earnings 22 Abr. Robotaxi + Megapack catalizadores.","FORMANDO"),

    ("CRM","Salesforce Inc","IA y Software",
     248.0,33,172,-16.0,0.40,1.4,1.90,-28,348,"Feb-26",2,6.4,
     0.3,0.3,0.8,"Earnings","Agentforce AI momentum  - Q1 FY27 earnings Mayo","Mayo 2026",
     ["ORCL","SNOW"],"MSFT",
     "RSI 33. Agentforce AI traction. Arrastrada por MSFT.","FORMANDO"),

    ("ORCL","Oracle Corp","IA y Software",
     148.0,36,165,-12.0,0.38,1.5,1.80,-22,196,"Feb-26",2,4.8,
     0.3,0.2,0.6,"Contrato","Cloud AI gov contracts  - OpenAI infrastructure deal","Mayo 2026",
     ["CRM","SNOW"],"",
     "RSI 36. Cloud AI gov momentum. Fondo formando.","FORMANDO"),

    # ══ BAJADA - watchlist ═══════════════════════════════════
    ("SMCI","Super Micro Computer","Tech",
     34.0,28,245,-28.0,0.55,0.8,4.20,-72,122,"Mar-25",6,18.4,
     0.2,0.1,0.4,"Pipeline","Server demand AI + Nvidia partnership","Q2 2026",
     ["NVDA","AMD"],"NVDA",
     "RSI 28. DD -72% desde pico. Alta volatilidad. Watchlist.","BAJADA"),

    ("PFE","Pfizer Inc","Salud",
     24.0,27,255,-19.0,0.55,0.6,1.40,-72,85,"2022",36,18.2,
     0.1,0.1,0.2,"Pipeline","Oncology pipeline + cost cuts $4B","Q2 2026",
     ["MRK","ABBV"],"",
     "RSI 27. Capitulacion post-pandemia. Watchlist largo plazo.","BAJADA"),

    ("BA","Boeing Co","Industrial",
     155.0,31,228,-18.0,0.40,1.2,1.90,-48,301,"Nov-25",4,14.6,
     0.2,0.1,0.4,"FAA","737 MAX 10 certif. + Defense contracts","Q2 2026",
     ["GE","SPR"],"",
     "RSI 31. Recuperacion lenta post-crisis. FAA cert catalizador.","BAJADA"),

    ("MRNA","Moderna Inc","Salud",
     48.0,25,280,-24.0,0.55,0.6,1.80,-90,484,"2021",36,14.0,
     0.1,0.1,0.2,"Pipeline","INT melanoma Phase 3 mid-2026 readout","Mid-2026",
     ["BNTX","NVAX"],"",
     "RSI 25. Capitulacion estructural. Watchlist catalizador clinico.","BAJADA"),

    ("HOOD","Robinhood","Fintech",
     62.0,48,132,-4.0,0.40,1.1,2.90,-32,92,"Ene-26",2,8.4,
     0.3,0.2,0.5,"Earnings","Q1 earnings  - usuarios activos plateados","May 2026",
     ["SOFI","COIN"],"",
     "RSI 48. Rally previo absorbido. Pausa tecnica, no senal aun.","BAJADA"),

    ("NKE","Nike Inc","Consumo",
     68.0,31,215,-18.0,0.42,1.0,1.70,-42,121,"Oct-25",5,10.5,
     0.2,0.1,0.3,"Macro","China recovery + nuevo CEO turnaround","Q2 2026",
     ["LULU","SKX"],"",
     "RSI 31. CEO turnaround en curso. DD -42%. Watchlist.","BAJADA"),

    ("OXY","Occidental Pet.","Energía",
     44.0,29,272,-22.0,0.50,0.8,1.90,-35,72,"Nov-25",4,9.1,
     0.2,0.2,0.4,"Petróleo","Buffett 27% float  - oil price recovery","Q2 2026",
     ["XOM","DVN"],"",
     "RSI 29. Buffett acumulando. Oil recovery esperado.","BAJADA"),
]

# ─────────────────────────────────────────────────────────────
#  FILTROS MACRO v16 - Oil Price + Sector Pressure
#  Evita entrar en acciones de Consumo/Industrial cuando
#  el petróleo está caro y los aranceles presionan márgenes
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)  # cache 30 min
def fetch_oil_price() -> dict:
    """Obtiene precio WTI actual. Si > 90 = presión en Consumo/Industrial."""
    try:
        import yfinance as yf
        oil = yf.Ticker("CL=F").history(period="2d")
        if oil.empty:
            raise ValueError("sin datos")
        precio = round(float(oil["Close"].iloc[-1]), 2)
        prev   = round(float(oil["Close"].iloc[-2]), 2) if len(oil) >= 2 else precio
        cambio = round((precio - prev) / prev * 100, 2)

        if precio >= 100:
            nivel = "ALTO"; presion = True
            msg   = f"🛢️ WTI ${precio} - Consumo e Industrial bajo presión máxima"
        elif precio >= 90:
            nivel = "ELEVADO"; presion = True
            msg   = f"🛢️ WTI ${precio} - señales Consumo/Industrial degradadas"
        elif precio >= 75:
            nivel = "NORMAL"; presion = False
            msg   = f"🛢️ WTI ${precio} - sin presión sectorial"
        else:
            nivel = "BAJO"; presion = False
            msg   = f"🛢️ WTI ${precio} - favorable para consumo"

        return {"precio": precio, "cambio": cambio, "nivel": nivel,
                "presion_sectorial": presion, "msg": msg, "_ok": True}
    except Exception:
        return {"precio": 0, "cambio": 0, "nivel": "SIN DATOS",
                "presion_sectorial": False, "msg": "Oil sin datos", "_ok": False}


# Sectores que sufren cuando oil > 90 o hay aranceles
_SECTORES_PRESIONADOS = {"Consumo", "Industrial", "Retail", "Autopartes"}
_SECTORES_BENEFICIADOS = {"Energía", "Minería"}

def evaluar_presion_sectorial(area: str, oil: dict) -> dict:
    """
    Retorna si un ticker está en un sector bajo presión macro.
    Consumo + Industrial con oil > 90 = señal degradada.
    """
    presionado = (
        area in _SECTORES_PRESIONADOS
        and oil.get("presion_sectorial", False)
        and oil.get("_ok", False)
    )
    return {
        "presionado": presionado,
        "area":       area,
        "oil":        oil.get("precio", 0),
        "razon":      (
            f"⚠️ Sector {area} bajo presión - WTI ${oil.get('precio',0):.0f} "
            f"encarece costos y debilita consumo"
        ) if presionado else "",
    }


@st.cache_data(ttl=86400, show_spinner=False)  # cache 24h - guidance no cambia cada hora
def fetch_guidance_flag(ticker: str) -> dict:
    """
    Detecta si la empresa emitió guidance negativo recientemente
    via yfinance earningsHistory - EPS sorpresa negativa reciente.
    Si la empresa tuvo 2+ sorpresas negativas en los últimos 4 trimestres
    o el ratio estimado/real < 0.95, marca como guidance negativo.
    """
    resultado = {"guidance_negativo": False, "razon": "", "score_penalty": 0}
    _BAD_TICKERS = {"MSTU","CRWN","SDNK","VIX","ENTX","AXCM"}  # v17: SNDK removido — era confusión con typo SDNK
    if ticker.upper() in _BAD_TICKERS:
        return resultado
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info or {}

        # Señal 1: Revenue guidance - si revenueGrowth es negativo
        rev_growth = float(info.get("revenueGrowth", 0) or 0)
        # Señal 2: Earnings quarterly growth negativo
        earn_growth = float(info.get("earningsQuarterlyGrowth", 0) or 0)
        # Señal 3: Margen bruto cayendo (grossMargins < 20%)
        gross_margin = float(info.get("grossMargins", 0.5) or 0.5)
        # Señal 4: Recomendación de analistas - si mean > 3.5 = vender/reducir
        analyst_rec = float(info.get("recommendationMean", 2.5) or 2.5)

        # Score de alerta: cuántas señales negativas hay
        alertas = 0
        razones = []

        if rev_growth < -0.05:  # ingresos cayendo > 5%
            alertas += 1
            razones.append(f"Revenue {rev_growth*100:.1f}% YoY")
        if earn_growth < -0.10:  # earnings cayendo > 10%
            alertas += 1
            razones.append(f"Earnings {earn_growth*100:.1f}% YoY")
        if gross_margin < 0.15:  # margen muy bajo
            alertas += 1
            razones.append(f"Margen bruto {gross_margin*100:.1f}%")
        if analyst_rec > 3.5:  # analistas dicen vender
            alertas += 1
            razones.append(f"Analistas: {analyst_rec:.1f}/5 (vender)")

        if alertas >= 2:
            resultado = {
                "guidance_negativo": True,
                "razon": f"⚠️ Señales fundamentales negativas: {'  - '.join(razones)}",
                "score_penalty": min(alertas * 8, 25),  # máx -25 pts al score
            }
    except Exception:
        pass
    return resultado



# ─────────────────────────────────────────────────────────────
#  ACTUALIZACIÓN DE PRECIOS RAW — v17 Fix AMD-F4
#  Los precios en RAW son estáticos y quedan obsoletos
#  Esta función actualiza el precio base de cada ticker
#  usando el precio live de yfinance para calcular DD correcto
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)  # cache 1h
def get_precio_live_batch(tickers: tuple) -> dict:
    """Obtiene precios actuales para una lista de tickers. Cache 1h."""
    result = {}
    _BAD = {"MSTU","CRWN","SDNK","VIX","ENTX","AXCM"}  # v17: SNDK removido — era confusión con typo SDNK
    try:
        import yfinance as yf
        tks_valid = [t for t in tickers if t not in _BAD]
        if not tks_valid:
            return result
        # Batch download es más eficiente
        data = yf.download(tks_valid, period="5d", auto_adjust=True,
                           progress=False, group_by="ticker")
        for tk in tks_valid:
            try:
                if len(tks_valid) == 1:
                    precio = float(data["Close"].iloc[-1])
                else:
                    precio = float(data[tk]["Close"].iloc[-1])
                if precio > 0:
                    result[tk] = round(precio, 2)
            except Exception:
                pass
    except Exception:
        pass
    return result

# Precios live cargados al iniciar (actualizan el pico real de cada ticker)
_TICKERS_RAW = tuple(r[0] for r in RAW if isinstance(r, tuple) and len(r) > 0)
# ─────────────────────────────────────────────────────────────
#  SYMPATHY LOOKUP - v15 fix Bug 2
#  Arrastradas/Lider se perdían en scan_tab y watchlist
#  Este dict los recupera para CUALQUIER tab sin releer RAW
# ─────────────────────────────────────────────────────────────
_SYMPATHY_LOOKUP: dict = {}
for _r in RAW:
    try:
        _tk  = _r[0]
        _arr = _r[27] if len(_r) > 27 and isinstance(_r[27], list) else []
        _lid = _r[28] if len(_r) > 28 and isinstance(_r[28], str)  else ""
        _area_r = _r[2]
        _SYMPATHY_LOOKUP[_tk] = {
            "arrastradas": ", ".join(_arr) if _arr else "-",
            "lider":       _lid if _lid else "-",
            "area":        _area_r,
        }
        for _a in _arr:  # inverso: cada arrastrada conoce su líder
            if _a not in _SYMPATHY_LOOKUP:
                _SYMPATHY_LOOKUP[_a] = {"arrastradas": "-", "lider": _tk, "area": _area_r}
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────
#  DETECTOR DE DILUCIÓN — v18
#  Busca ofertas secundarias recientes (424B5/S-3) en SEC EDGAR
#  Si existe oferta en últimos 90 días → advertencia en Opinión Trader
#  Caso real: VRDN lanzó $150M convertible notes May 2026
#             IONQ lanzó $2B offering → precio cayó post-anuncio
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)  # cache 24h
def detectar_dilucion_reciente(ticker: str, dias: int = 90) -> dict:
    """
    Consulta SEC EDGAR para detectar ofertas secundarias recientes.
    Forms que indican dilución:
      424B5 = Prospecto de oferta secundaria (acción o deuda convertible)
      S-3    = Shelf registration (reserva de acciones para vender)
      424B4 = IPO/Follow-on offering
    
    Si detecta → penaliza score y genera aviso en Opinión Trader.
    """
    resultado = {
        "tiene_dilucion":    False,
        "tipo_oferta":       "",
        "fecha_oferta":      "",
        "dias_desde":        999,
        "badge":             "",
        "accion":            "",
        "penalizacion_score": 0,
    }
    _BAD = {"MSTU","CRWN","SDNK","VIX","ENTX","AXCM"}
    if not ticker or ticker.upper() in _BAD:
        return resultado
    try:
        import urllib.request, json, datetime as _dt
        hoy = _dt.date.today()
        # EDGAR full-text search API
        url = (f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22"
               f"&dateRange=custom&startdt={(hoy - _dt.timedelta(days=dias)).isoformat()}"
               f"&enddt={hoy.isoformat()}"
               f"&forms=424B5,S-3,424B4")
        req = urllib.request.Request(url, headers={"User-Agent":"GrekoTrader research@greko.cl"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
        hits = data.get("hits", {}).get("hits", [])
        if hits:
            hit        = hits[0]["_source"]
            form_type  = hit.get("form_type","")
            filed_at   = hit.get("file_date","")[:10]
            try:
                dias_desde = (hoy - _dt.date.fromisoformat(filed_at)).days
            except Exception:
                dias_desde = dias

            if dias_desde <= 30:
                penalizacion = 25
                urgencia     = "MUY RECIENTE"
                badge_color  = "#DC2626"
            elif dias_desde <= 60:
                penalizacion = 15
                urgencia     = "RECIENTE"
                badge_color  = "#D97706"
            else:
                penalizacion = 8
                urgencia     = "hace ~{dias_desde}d"
                badge_color  = "#7C3AED"

            resultado = {
                "tiene_dilucion":     True,
                "tipo_oferta":        form_type,
                "fecha_oferta":       filed_at,
                "dias_desde":         dias_desde,
                "badge":              f"⚠️ Dilución {urgencia} ({form_type} · {filed_at})",
                "accion":             (
                    f"Oferta secundaria {form_type} detectada ({filed_at}, hace {dias_desde}d). "
                    f"La dilución presiona el precio. Esperar absorción: "
                    f"volumen normal 5+ días + precio estabilizado antes de entrar. "
                    f"Caso típico: IONQ $2B offering, VRDN $150M convertibles."
                ),
                "penalizacion_score": penalizacion,
            }
    except Exception:
        pass
    return resultado


def get_sympathy(ticker: str) -> dict:
    """Retorna arrastradas y lider para un ticker desde RAW. Siempre seguro."""
    return _SYMPATHY_LOOKUP.get(str(ticker).upper(),
           {"arrastradas": "-", "lider": "-", "area": "-"})

# ─────────────────────────────────────────────────────────────
#  FUNDAMENTALES POR TICKER
#  (bpa, dividendo%, margen_bruto%, ingresos_M, vol_diario_K)
#  Aprendizaje: ACN/AXSM/SEI (fundamentales sólidos) vs
#               ENTX/CRWN (sin ingresos, ilíquidas)
# ─────────────────────────────────────────────────────────────
FUND = {
    #  Ticker: (BPA,  Div%,  Margen%, Ingresos_M, VolDiario_K)
    "NBIS":  (0.0,   0.0,   45.0,   280.0,    2800.0),
    "MSFT":  (12.20, 0.82,  68.8,   72110.0,  20000.0),
    "AMZN":  (4.33,  0.0,   47.0,   638000.0, 35000.0),
    "GOOGL": (7.52,  0.0,   56.0,   88000.0,  25000.0),
    "META":  (23.86, 0.52,  81.0,   164000.0, 18000.0),
    "ZS":    (-1.20, 0.0,   77.0,   2370.0,   3500.0),
    "NVDA":  (2.94,  0.04,  73.0,   130500.0, 32000.0),
    "AMD":   (2.61,  0.0,   52.5,   34640.0,  37000.0),
    "APLD":  (-0.74, 0.0,   45.4,   319.0,    24000.0),
    "IREN":  (-0.45, 0.0,   38.0,   210.0,    8000.0),
    "TSLA":  (2.04,  0.0,   17.0,   97690.0,  85000.0),
    "CRM":   (6.20,  0.0,   76.0,   36000.0,  5500.0),
    "ORCL":  (5.60,  1.28,  71.0,   56900.0,  7000.0),
    "SMCI":  (-2.10, 0.0,   14.0,   23000.0,  12000.0),
    "PFE":   (1.41,  6.90,  64.0,   63600.0,  28000.0),
    "BA":    (-5.20, 0.0,   12.0,   66517.0,  6000.0),
    "MRNA":  (-9.60, 0.0,   55.0,   3240.0,   9000.0),
    "HOOD":  (0.42,  0.0,   83.0,   3580.0,   63000.0),
    "NKE":   (3.73,  2.08,  44.0,   51362.0,  7000.0),
    "OXY":   (3.58,  2.40,  51.0,   27263.0,  14000.0),
}
# ─────────────────────────────────────────────────────────────
def calc_score(rsi,vol,ema,macd,sop,dd,pre_move,short_int,pre_vol,post_vol,rsi_tendencia=0):
    sc=0
    if rsi<25:   sc+=18
    elif rsi<30: sc+=16
    elif rsi<35: sc+=12
    elif rsi<42: sc+=6
    sc += rsi_tendencia
    if vol>300: sc+=15
    elif vol>200: sc+=12
    elif vol>150: sc+=8
    elif vol>120: sc+=4
    if pre_move>=10: sc+=18
    elif pre_move>=7: sc+=15
    elif pre_move>=5: sc+=11
    elif pre_move>=3: sc+=6
    elif pre_move>=1: sc+=2
    if pre_vol>=3.0: sc+=12
    elif pre_vol>=2.0: sc+=9
    elif pre_vol>=1.5: sc+=6
    elif pre_vol>=1.2: sc+=3
    if macd>1.5: sc+=12
    elif macd>1: sc+=10
    elif macd>0: sc+=7
    elif macd>-0.5: sc+=2
    if ema<-20: sc+=10
    elif ema<-15: sc+=8
    elif ema<-10: sc+=6
    elif ema<-5: sc+=3
    if sop<0.5: sc+=10
    elif sop<1: sc+=8
    elif sop<2: sc+=6
    elif sop<3: sc+=3
    if dd<-40: sc+=5
    elif dd<-25: sc+=3
    elif dd<-15: sc+=1
    sc=min(sc,100)
    if short_int>=20: sc=min(int(sc*1.30),100)
    elif short_int>=15: sc=min(int(sc*1.20),100)
    elif short_int>=10: sc=min(int(sc*1.10),100)
    return sc

def bonus_fundamentales(bpa: float, dividendo: float, margen_bruto: float,
                         ingresos_m: float, vol_diario_k: float) -> tuple:
    """
    Calcula bonus/penalización por calidad fundamental.
    Retorna (bonus_pts, descripcion)
    Aprendizaje del análisis del día: ACN, AXSM, SEI vs ENTX, CRWN.
    """
    bonus = 0
    razones = []

    # ── BPA positivo ──────────────────────────────────────────
    if bpa > 5:
        bonus += 8; razones.append(f"BPA +${bpa:.2f} ✅")
    elif bpa > 1:
        bonus += 5; razones.append(f"BPA +${bpa:.2f} ✅")
    elif bpa > 0:
        bonus += 3; razones.append(f"BPA +${bpa:.2f} ✅")
    elif bpa < -2:
        bonus -= 5; razones.append(f"BPA -${abs(bpa):.2f} ❌")
    elif bpa < 0:
        bonus -= 2; razones.append(f"BPA negativo ⚠️")

    # ── Dividendo activo ──────────────────────────────────────
    if dividendo >= 3.0:
        bonus += 5; razones.append(f"Dividendo {dividendo:.1f}% 💎")
    elif dividendo >= 1.5:
        bonus += 3; razones.append(f"Dividendo {dividendo:.1f}% ✅")
    elif dividendo > 0:
        bonus += 1; razones.append(f"Dividendo {dividendo:.1f}%")

    # ── Margen bruto ──────────────────────────────────────────
    if margen_bruto >= 70:
        bonus += 4; razones.append(f"Margen {margen_bruto:.0f}% 💎")
    elif margen_bruto >= 40:
        bonus += 2; razones.append(f"Margen {margen_bruto:.0f}% ✅")
    elif margen_bruto > 0:
        bonus += 1

    # ── Ingresos reales ───────────────────────────────────────
    if ingresos_m >= 10000:
        bonus += 3; razones.append(f"Ingresos ${ingresos_m/1000:.0f}B 💎")
    elif ingresos_m >= 500:
        bonus += 2; razones.append(f"Ingresos ${ingresos_m:.0f}M ✅")
    elif ingresos_m >= 100:
        bonus += 1
    elif ingresos_m < 1:
        bonus -= 10; razones.append("Sin ingresos reales ❌")

    # ── Filtro liquidez (no suma, solo excluye) ───────────────
    # vol_diario_k en miles de acciones
    if vol_diario_k < 500:
        bonus -= 20  # penalización que excluye del radar
        razones.append(f"⚠️ ILÍQUIDA vol {vol_diario_k:.0f}K/día")

    bonus = max(-20, min(12, bonus))  # cap: +12 / -20
    desc = "  - ".join(razones) if razones else "Sin datos fundamentales"
    return bonus, desc

# ─────────────────────────────────────────────────────────────
#  VIX - SEMÁFORO DE OPORTUNIDAD DEL MERCADO
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)  # cache 5 min
def fetch_vix() -> dict:
    """
    Descarga el VIX actual via yfinance.
    Retorna dict con valor, nivel, color, mensaje y multiplicador de score.
    """
    try:
        import yfinance as yf
        vix_data = yf.Ticker("^VIX").history(period="2d")
        if vix_data.empty:
            raise ValueError("sin datos VIX")
        vix_val = round(float(vix_data["Close"].iloc[-1]), 2)
        vix_prev = round(float(vix_data["Close"].iloc[-2]), 2) if len(vix_data) >= 2 else vix_val
        cambio = round(vix_val - vix_prev, 2)

        if vix_val >= 35:
            nivel="PÁNICO"; color=G; bg=G_BG; bor=G_BOR
            msg="🟢 Máxima oportunidad - mercado en pánico, buscar fondos"
            mult=1.20  # bonus +20% al score en pánico
        elif vix_val >= 25:
            nivel="MIEDO"; color=A; bg=A_BG; bor=A_BOR
            msg="🟡 Oportunidad moderada - nerviosismo, vigilar fondos"
            mult=1.10
        elif vix_val >= 20:
            nivel="ALERTA"; color=A; bg=A_BG; bor=A_BOR
            msg="🟡 Mercado nervioso - modo normal del modelo"
            mult=1.0
        elif vix_val >= 15:
            nivel="NORMAL"; color=TXT_MUT; bg=BG_HEAD; bor=BOR
            msg="⚪ Mercado tranquilo - exigir más confirmación Pre-Market"
            mult=1.0
        else:
            nivel="COMPLACENCIA"; color=R; bg=R_BG; bor=R_BOR
            msg="🔴 Mercado muy tranquilo - precaución, corrección probable"
            mult=0.95

        return {
            "valor": vix_val, "cambio": cambio, "prev": vix_prev,
            "nivel": nivel, "color": color, "bg": bg, "bor": bor,
            "msg": msg, "mult": mult, "_ok": True
        }
    except Exception:
        return {
            "valor": 0, "cambio": 0, "prev": 0,
            "nivel": "SIN DATOS", "color": TXT_MUT, "bg": BG_HEAD, "bor": BOR,
            "msg": "VIX no disponible - instala yfinance", "mult": 1.0, "_ok": False
        }

# ─────────────────────────────────────────────────────────────
#  FECHAS DE CATALIZADORES - busca earnings desde yfinance
# ─────────────────────────────────────────────────────────────
def fetch_earnings_dates(tickers):
    import yfinance as yf, datetime
    ETF_SIN_EARNINGS = ["VOO","SPY","IVV","QQQ","VTI","SCHB","IBIT","ETHA","GBTC","FBTC","TAN","XBI","IBB","XLF","XLE","XLK","XLV","ARKK","SOXX"]
    # v15: tickers que generan 404 en yfinance - skip silencioso
    TICKERS_MALOS = {"MSTU","CRWN","SDNK","VIX","ENTX","AXCM"}  # v17: SNDK removido — era confusión con typo SDNK
    rows = []
    for tk in tickers:
        if tk.upper() in TICKERS_MALOS:
            rows.append({"Ticker":tk,"Cat_Fecha":"-","Fuente":"No soportado","Nota":f"{tk} - ticker no disponible en yfinance (404)"})
            continue
        if tk in ETF_SIN_EARNINGS:
            rows.append({"Ticker":tk,"Cat_Fecha":"-","Fuente":"ETF - sin earnings","Nota":"ETF - no tiene earnings propios"})
            continue
        try:
            stk = yf.Ticker(tk)
            earn_date = "-"; fuente = "-"
            try:
                cal = stk.calendar
                if cal is not None and "Earnings Date" in cal:
                    hoy = datetime.date.today()
                    fechas = [str(f)[:10] for f in cal["Earnings Date"] if f and str(f)[:10] != "nan"]
                    futuras = [f for f in fechas if datetime.date.fromisoformat(f) >= hoy]
                    if futuras:
                        earn_date = futuras[0]; fuente = "yfinance"
            except Exception:
                pass
            if earn_date == "-":
                info = stk.info or {}
                ed = info.get("earningsDate") or info.get("earningsTimestamp")
                if ed and isinstance(ed, (int,float)):
                    earn_date = datetime.datetime.fromtimestamp(ed).strftime("%Y-%m-%d"); fuente = "yfinance"
            nota = "Earnings confirmados" if earn_date != "-" else "No encontrado - verificar en Nasdaq.com o Investing.com"
            rows.append({"Ticker":tk,"Cat_Fecha":earn_date,"Fuente":fuente,"Nota":nota})
        except Exception:
            rows.append({"Ticker":tk,"Cat_Fecha":"-","Fuente":"Error","Nota":"Error - verificar manualmente"})
    return pd.DataFrame(rows)




# ─────────────────────────────────────────────────────────────
#  EARNINGS IMPACT EN FASES - v15
#  Calcula el efecto de earnings próximos sobre M1/M2/M3
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def get_earnings_single(ticker: str) -> str:
    """Obtiene próxima fecha de earnings para un ticker individual. Cache 1h."""
    ETF_SKIP = {"VOO","SPY","IVV","QQQ","VTI","SCHB","IBIT","ETHA","GBTC","FBTC",
                "TAN","XBI","IBB","XLF","XLE","XLK","XLV","ARKK","SOXX"}
    # v15: misma blacklist que fetch_ticker_data - evita 404 spam
    _BAD = {"MSTU","CRWN","SDNK","VIX","ENTX","AXCM"}  # v17: SNDK removido — era confusión con typo SDNK
    if ticker in ETF_SKIP or ticker.upper() in _BAD:
        return "-"
    try:
        import yfinance as yf, datetime
        stk = yf.Ticker(ticker)
        cal = stk.calendar
        if cal is not None and "Earnings Date" in cal:
            hoy   = datetime.date.today()
            fechas = [str(f)[:10] for f in cal["Earnings Date"] if f and str(f)[:10] != "nan"]
            futuras = [f for f in fechas if datetime.date.fromisoformat(f) >= hoy]
            if futuras:
                return futuras[0]
        info = stk.info or {}
        ed   = info.get("earningsDate") or info.get("earningsTimestamp")
        if ed and isinstance(ed, (int, float)):
            import datetime as _dt
            return _dt.datetime.fromtimestamp(ed).strftime("%Y-%m-%d")
    except Exception:
        pass
    return "-"


def calcular_earnings_impact(cat_fecha: str, fase_actual: str) -> dict:
    """
    Dado un Cat_Fecha y la fase calculada por el modelo,
    retorna el impacto de earnings sobre la fase.

    Zonas NBIS:
      🎯 7-15 días: M2 -> M3  (zona óptima - earnings es el catalizador)
      ⚡ 15-30 días: M1 -> M2  (zona válida  - da convicción adicional)
      ⚠️  3-6 días: fase + badge CAUCIÓN (tarde para entrar)
      🚫  1-2 días: BLOQUEAR entrada (earnings mañana = ruleta)
      ➡️  sin fecha: sin cambio
    """
    import datetime
    resultado = {
        "fase_final":     fase_actual,
        "fase_original":  fase_actual,
        "dias_para_cat":  999,
        "tiene_cat":      False,
        "badge":          "",
        "badge_color":    "",
        "accion_earn":    "",
        "zona":           "sin_earnings",
    }
    if not cat_fecha or cat_fecha in ("-", "", "nan"):
        return resultado

    try:
        fecha_cat = datetime.date.fromisoformat(str(cat_fecha)[:10])
        hoy       = datetime.date.today()
        dias      = (fecha_cat - hoy).days
    except Exception:
        return resultado

    if dias < 0:
        return resultado  # earnings pasado

    resultado["dias_para_cat"] = dias
    resultado["tiene_cat"]     = True

    if dias <= 2:
        # 🚫 BLOQUEO - earnings mañana pasado
        resultado["fase_final"]   = "ESPERAR"
        resultado["zona"]         = "bloqueo"
        resultado["badge"]        = f"🚫 Earnings en {dias}d - NO ENTRAR"
        resultado["badge_color"]  = "#DC2626"
        resultado["accion_earn"]  = f"Earnings en {dias} días. Riesgo binario - esperar resultado antes de entrar."

    elif dias <= 6:
        # ⚠️ CAUCIÓN - fase no cambia pero se avisa
        resultado["fase_final"]   = fase_actual
        resultado["zona"]         = "caucion"
        resultado["badge"]        = f"⚠️ Earnings en {dias}d - Cuidado"
        resultado["badge_color"]  = "#D97706"
        resultado["accion_earn"]  = f"Earnings en {dias} días. Tarde para nueva entrada. Si ya estás dentro, mantener y decidir antes del reporte."

    elif dias <= 15:
        # 🎯 ZONA ÓPTIMA - M2 sube a M3, M1 sube a M2
        if fase_actual in ("M2", "⚡ EN FORMACIÓN M2", "ANTICIPAR"):
            resultado["fase_final"]  = "M3"
            resultado["zona"]        = "optima"
            resultado["badge"]       = f"🎯 Earnings en {dias}d - Zona óptima NBIS"
            resultado["badge_color"] = "#16A34A"
            resultado["accion_earn"] = f"Earnings en {dias} días. Zona ideal NBIS: el catalizador confirma el setup. Entrar con 75% del tamaño."
        elif fase_actual in ("M1", "📡 DETECTADA", "SEGUIR"):
            resultado["fase_final"]  = "M2"
            resultado["zona"]        = "optima"
            resultado["badge"]       = f"🎯 Earnings en {dias}d - Sube a M2"
            resultado["badge_color"] = "#0891B2"
            resultado["accion_earn"] = f"Earnings en {dias} días. El catalizador eleva la convicción. Preparar orden al 50%."
        else:
            resultado["zona"]        = "optima"
            resultado["badge"]       = f"🎯 Earnings en {dias}d"
            resultado["badge_color"] = "#16A34A"
            resultado["accion_earn"] = f"Earnings en {dias} días - catalizador próximo."

    elif dias <= 30:
        # ⚡ ZONA VÁLIDA - M1 sube a M2 con aviso
        if fase_actual in ("M1", "📡 DETECTADA"):
            resultado["fase_final"]  = "M2"
            resultado["zona"]        = "valida"
            resultado["badge"]       = f"⚡ Earnings en {dias}d - Convicción extra"
            resultado["badge_color"] = "#0891B2"
            resultado["accion_earn"] = f"Earnings en {dias} días. Da convicción adicional al setup. Entrar al 50%."
        else:
            resultado["zona"]        = "valida"
            resultado["badge"]       = f"📅 Earnings en {dias}d"
            resultado["badge_color"] = "#2563EB"
            resultado["accion_earn"] = f"Earnings en {dias} días - monitorear acercamiento."

    else:
        resultado["zona"]        = "lejano"
        resultado["badge"]       = f"📅 Earnings en {dias}d"
        resultado["badge_color"] = "#64748B"
        resultado["accion_earn"] = f"Earnings lejanos ({dias}d). Monitorear."

    return resultado

def render_catalysts_section(posiciones_df, key_prefix):
    st.markdown("---")
    st.markdown(
        '<div style="font-size:13px;font-weight:700;margin-bottom:8px">'+
        '📅 Fechas de Earnings - Catalizadores</div>',
        unsafe_allow_html=True)
    st.markdown(
        '<div class="info-box">Busca automáticamente las fechas de earnings desde yfinance. '+
        'Descarga el CSV y agrega las fechas a la columna <strong>Cat_Fecha</strong> '+
        'de tu archivo de posiciones.</div>',
        unsafe_allow_html=True)

    if st.button("📅 Buscar fechas de earnings", use_container_width=True,
                 key=f"btn_earnings_{key_prefix}"):
        tickers = posiciones_df["Ticker"].str.upper().unique().tolist()
        with st.spinner(f"Buscando earnings para {len(tickers)} acciones..."):
            earn_df = fetch_earnings_dates(tickers)
            st.session_state[f"earnings_{key_prefix}"] = earn_df

    earn_result = st.session_state.get(f"earnings_{key_prefix}")
    if earn_result is not None:
        for _, row in earn_result.iterrows():
            has_date = row["Cat_Fecha"] not in ("-","","nan")
            color = G if has_date else TXT_MUT
            bg    = G_BG if has_date else GRIS_CLAR if 'GRIS_CLAR' in dir() else "F8FAFC"
            bor   = G_BOR if has_date else BOR
            icon  = "📅" if has_date else "-"
            st.markdown(
                f'<div style="background:{bg};border:1px solid {bor};border-radius:8px;'
                f'padding:8px 14px;margin-bottom:5px;'
                f'display:flex;justify-content:space-between;align-items:center">'
                f'<div style="display:flex;align-items:center;gap:12px">'
                f'<span style="font-size:14px;font-weight:800;color:{B}">{row["Ticker"]}</span>'
                f'<span style="font-size:12px;font-weight:700;color:{color}">'
                f'{icon} {row["Cat_Fecha"]}</span>'
                f'</div>'
                f'<span style="font-size:10px;color:{TXT_MUT}">{row["Nota"]}</span>'
                f'</div>', unsafe_allow_html=True)

        import datetime as _dt
        earn_csv = df_to_csv_chile(earn_result).encode("utf-8-sig")
        col_dl, col_tip = st.columns([2,3])
        with col_dl:
            st.download_button(
                "⬇️ Descargar fechas CSV",
                data=earn_csv,
                file_name=f"earnings_{_dt.date.today()}.csv",
                mime="text/csv",
                key=f"dl_earn_{key_prefix}",
                use_container_width=True)
        with col_tip:
            st.markdown(
                f'<div style="font-size:10px;color:{TXT_MUT};padding-top:8px">'
                f'Copia <strong>Cat_Fecha</strong> a tu archivo de posiciones '
                f'y vuelve a subirlo al dashboard.</div>',
                unsafe_allow_html=True)


# Cargar VIX y Oil al iniciar (v16: filtros macro)
vix = fetch_vix()
oil = fetch_oil_price()  # v16: filtro sectorial

# v17 Fix AMD-F4: precios live para corregir RAW desactualizado
# AMD tenía $92 en RAW cuando ya valía $196 — todos los DD estaban mal
try:
    _precio_live_cache = get_precio_live_batch(_TICKERS_RAW)
except Exception:
    _precio_live_cache = {}

# ─────────────────────────────────────────────────────────────
#  INDICADORES DE MERCADO - automáticos para el header
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)  # cache 15 min
def fetch_market_indicators() -> dict:
    """
    Descarga indicadores clave de mercado para el header.
    Todos relevantes para el modelo de rebote técnico NBIS.
    """
    result = {}
    try:
        import yfinance as yf

        # S&P 500
        try:
            spx = yf.Ticker("^GSPC").history(period="2d")
            if not spx.empty:
                spx_now  = float(spx["Close"].iloc[-1])
                spx_prev = float(spx["Close"].iloc[-2]) if len(spx)>=2 else spx_now
                result["spx"] = {"val": spx_now, "chg": (spx_now-spx_prev)/spx_prev*100}
        except Exception: pass

        # Nasdaq
        try:
            ndx = yf.Ticker("^IXIC").history(period="2d")
            if not ndx.empty:
                ndx_now  = float(ndx["Close"].iloc[-1])
                ndx_prev = float(ndx["Close"].iloc[-2]) if len(ndx)>=2 else ndx_now
                result["ndx"] = {"val": ndx_now, "chg": (ndx_now-ndx_prev)/ndx_prev*100}
        except Exception: pass

        # Fear & Greed aproximado via VIX (^PCALL no disponible en Yahoo)
        try:
            # Usar VIX como proxy de Fear & Greed
            vix_fg = yf.Ticker("^VIX").history(period="2d")
            if not vix_fg.empty:
                vix_val = float(vix_fg["Close"].iloc[-1])
                if vix_val >= 35:
                    fg_label = "MIEDO EXTREMO 🟢"; fg_score = 15; fg_color = "G"
                elif vix_val >= 25:
                    fg_label = "MIEDO 🟡"; fg_score = 30; fg_color = "A"
                elif vix_val >= 18:
                    fg_label = "NEUTRAL ⚪"; fg_score = 50; fg_color = "TXT_MUT"
                elif vix_val >= 13:
                    fg_label = "CODICIA 🟡"; fg_score = 70; fg_color = "A"
                else:
                    fg_label = "CODICIA EXTREMA 🔴"; fg_score = 85; fg_color = "R"
                result["pcr"] = {"val": round(vix_val,1), "label": fg_label,
                                 "score": fg_score, "color_key": fg_color}
        except Exception:
            pass

        # % acciones S&P500 bajo su EMA50 - proxy via ETF XLK vs SMA
        try:
            # Usar RSI del SPY como proxy de sentimiento
            spy = yf.Ticker("SPY").history(period="3mo")
            if not spy.empty:
                s = spy["Close"]
                delta = s.diff()
                gain  = delta.clip(lower=0).rolling(14).mean()
                loss  = (-delta.clip(upper=0)).rolling(14).mean()
                rsi_spy = round(float(100-100/(1+gain.iloc[-1]/(loss.iloc[-1]+1e-9))), 1)
                ema50_spy = float(s.ewm(span=50).mean().iloc[-1])
                bajo_ema  = "SPY bajo EMA50" if float(s.iloc[-1]) < ema50_spy else "SPY sobre EMA50"
                result["spy"] = {"rsi": rsi_spy, "ema_status": bajo_ema,
                                 "precio": round(float(s.iloc[-1]),2)}
        except Exception: pass

        # Sector más débil - buscar el que tiene más acciones en corrección
        sectores = {
            "Energía":   ["XOM","CVX","OXY","DVN","COP"],
            "Tech":      ["MSFT","GOOGL","META","NVDA","AMD"],
            "Salud":     ["PFE","MRNA","ABBV","MRK","GILD"],
            "Finanzas":  ["JPM","BAC","GS","MS","C"],
            "Consumo":   ["NKE","CROX","SBUX","MCD","TGT"],
            "Industrial":["BA","GE","HON","CAT","DE"],
        }
        sector_scores = {}
        for sector, tickers in sectores.items():
            en_correccion = 0
            for tk in tickers:
                try:
                    import time as _tm_scan
                    _tm_scan.sleep(0.08)  # anti rate-limit
                    h = yf.Ticker(tk).history(period="3mo")
                    if h.empty: continue
                    c2 = h["Close"].values
                    precio = float(c2[-1]); pico = float(c2.max())
                    dd = (precio-pico)/pico*100
                    s2 = __import__("pandas").Series(c2)
                    d2 = s2.diff()
                    g2 = d2.clip(lower=0).rolling(14).mean()
                    l2 = (-d2.clip(upper=0)).rolling(14).mean()
                    rsi2 = float(100-100/(1+g2.iloc[-1]/(l2.iloc[-1]+1e-9)))
                    if rsi2 < 50 and dd < -10:
                        en_correccion += 1
                except Exception: continue
            sector_scores[sector] = en_correccion

        if sector_scores:
            mejor_sector = max(sector_scores, key=sector_scores.get)
            result["sectores"] = {
                "mejor_oportunidad": mejor_sector,
                "acciones_en_correccion": sector_scores[mejor_sector],
                "scores": sector_scores,
            }

    except Exception: pass
    return result


# ─────────────────────────────────────────────────────────────
#  UNIVERSO A ESCANEAR - S&P500 + Nasdaq + Sectores
# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
#  PRE/POST MARKET - datos en tiempo real por ticker
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)  # cache 5 min
def fetch_pre_post(ticker: str) -> dict:
    """
    Obtiene Pre-Market y Post-Market de yfinance.
    Si no hay datos, retorna dict con valores None.
    """
    result = {
        "pre_price":  None, "pre_chg":   None, "pre_vol":  None,
        "post_price": None, "post_chg":  None, "post_vol": None,
        "vol_hoy":    None, "vol_avg20": None, "vol_ratio": None,
        "precio_reg": None,
    }
    try:
        import yfinance as yf
        tk = yf.Ticker(ticker)

        # Fast info - precio regular, pre y post
        try:
            fi = tk.fast_info
            result["precio_reg"] = float(fi.last_price) if fi.last_price else None

            # Pre-Market
            if hasattr(fi, "pre_market_price") and fi.pre_market_price:
                result["pre_price"] = float(fi.pre_market_price)
                if result["precio_reg"]:
                    result["pre_chg"] = round(
                        (result["pre_price"] - result["precio_reg"]) / result["precio_reg"] * 100, 2)

            # Post-Market
            if hasattr(fi, "post_market_price") and fi.post_market_price:
                result["post_price"] = float(fi.post_market_price)
                if result["precio_reg"]:
                    result["post_chg"] = round(
                        (result["post_price"] - result["precio_reg"]) / result["precio_reg"] * 100, 2)
        except Exception:
            pass

        # Volumen hoy vs promedio 20 días
        try:
            hist = tk.history(period="1mo")
            if not hist.empty and len(hist) >= 5:
                import numpy as np
                avg20 = float(np.mean(hist["Volume"].values[-20:]))
                vol_hoy = float(hist["Volume"].values[-1])
                result["vol_hoy"]   = int(vol_hoy)
                result["vol_avg20"] = int(avg20)
                result["vol_ratio"] = round(vol_hoy / avg20 * 100, 0) if avg20 > 0 else None
        except Exception:
            pass

    except Exception:
        pass
    return result

def render_pre_post_bar(ticker: str, precio_actual: float,
                        G: str, A: str, R: str,
                        TXT_MUT: str, TXT_SOFT: str,
                        BG_HEAD: str, BOR: str) -> str:
    """
    v18: Pre/Post Market con interpretación de trader.
    No solo muestra el % — explica qué hacer con el gap.
    """
    d = fetch_pre_post(ticker)

    def vol_semaforo(ratio):
        if ratio is None: return "⚪", TXT_MUT, "Sin datos"
        if ratio >= 200:  return "🟢", G,       f"{ratio:.0f}% — institucional"
        if ratio >= 120:  return "🟡", A,        f"{ratio:.0f}% — normal"
        return "🔴", R, f"{ratio:.0f}% — bajo"

    def chg_semaforo(chg):
        if chg is None:  return "⚪", TXT_MUT, "Sin datos"
        if chg >= 5:     return "🔴", R,       f"+{chg:.1f}% — gap extremo"
        if chg >= 2:     return "🟡", A,        f"+{chg:.1f}% — gap moderado"
        if chg >= 0.5:   return "🟢", G,       f"+{chg:.1f}% — positivo"
        if chg >= -0.5:  return "⚪", TXT_MUT, f"{chg:.1f}% — plano"
        if chg >= -2:    return "🟡", A,        f"{chg:.1f}% — leve baja"
        return "🔴", R, f"{chg:.1f}% — gap negativo"

    # ── Interpretación del gap (la parte nueva v18) ──────────
    def interpretar_gap(chg, vol_ratio) -> tuple:
        """
        Retorna (semaforo, consejo) según el tipo de gap.
        Basado en las 5 reglas del pre-market.
        """
        if chg is None:
            return "⚪", "Sin datos pre-market disponibles"

        abs_chg = abs(chg)

        if abs_chg > 8:
            return ("🚫",
                "Gap extremo (>8%) — tierra de nadie. "
                "Primeros 30 min son muy volátiles. "
                "Esperar que el precio se estabilice antes de entrar. "
                "Caso IREN hoy: abrió +8%, osciló $18 en el día.")
        elif abs_chg > 5:
            return ("⚠️",
                f"Gap {'positivo' if chg>0 else 'negativo'} fuerte ({chg:+.1f}%). "
                "Regla: esperar 15-30 min y ver si MANTIENE el nivel. "
                "Si el precio del primer minuto > precio pre-market → fuerza real. "
                "Si retrocede en los primeros minutos → no perseguir.")
        elif abs_chg > 2:
            return ("🟡",
                f"Gap moderado ({chg:+.1f}%). "
                "Válido si la acción ya estaba en M2/M3 antes del gap. "
                "Confirmar con volumen: si Vol > 150% del promedio → señal real. "
                f"Volumen actual: {vol_ratio:.0f}% del promedio." if vol_ratio else
                f"Gap moderado ({chg:+.1f}%). Confirmar con volumen al abrir.")
        elif chg > 0.3:
            return ("✅",
                f"Gap de continuación ({chg:+.1f}%). "
                "Tipo más seguro para entrar. "
                "Si la acción tiene señal M2/M3 y el gap es pequeño → "
                "puede entrar en apertura o en el primer pull-back.")
        elif chg > -0.3:
            return ("⚪", "Sin gap significativo — acción abre plana.")
        else:
            return ("🔴",
                f"Gap negativo ({chg:+.1f}%). "
                "Señal de debilidad. Si tenías posición → "
                "revisar si el motivo de la baja cambia la tesis.")

    pre_ico,  pre_c,  pre_txt  = chg_semaforo(d["pre_chg"])
    post_ico, post_c, post_txt = chg_semaforo(d["post_chg"])
    vol_ico,  vol_c,  vol_txt  = vol_semaforo(d["vol_ratio"])

    # Gap activo — pre-market si hay datos, sino post-market
    gap_activo = d["pre_chg"] if d["pre_chg"] is not None else d["post_chg"]
    gap_ico, gap_consejo = interpretar_gap(gap_activo, d["vol_ratio"] or 100)
    es_pre = d["pre_chg"] is not None
    gap_label = "PRE-MARKET" if es_pre else "POST-MARKET"

    pre_precio  = f"${d['pre_price']:.2f}"  if d["pre_price"]  else "—"
    post_precio = f"${d['post_price']:.2f}" if d["post_price"] else "—"

    # Color del panel de interpretación
    if gap_ico == "🚫":
        panel_bg, panel_bor, panel_c = "#FEF2F2", "#FCA5A5", "#DC2626"
    elif gap_ico == "⚠️":
        panel_bg, panel_bor, panel_c = "#FFFBEB", "#FCD34D", "#D97706"
    elif gap_ico == "✅":
        panel_bg, panel_bor, panel_c = "#F0FDF4", "#86EFAC", "#16A34A"
    else:
        panel_bg, panel_bor, panel_c = BG_HEAD, BOR, TXT_MUT

    html = (
        f'<div style="margin-top:8px">'
        # Fila superior: Pre / Post / Volumen
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:6px">'
        # Pre-Market
        f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:8px;padding:7px 10px">'
        f'<div style="font-size:9px;color:{TXT_MUT};font-weight:700;margin-bottom:2px">PRE-MARKET</div>'
        f'<div style="font-size:13px;font-weight:700;color:{pre_c}">{pre_ico} {pre_precio}</div>'
        f'<div style="font-size:10px;color:{pre_c}">{pre_txt}</div>'
        f'</div>'
        # Post-Market
        f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:8px;padding:7px 10px">'
        f'<div style="font-size:9px;color:{TXT_MUT};font-weight:700;margin-bottom:2px">POST-MARKET</div>'
        f'<div style="font-size:13px;font-weight:700;color:{post_c}">{post_ico} {post_precio}</div>'
        f'<div style="font-size:10px;color:{post_c}">{post_txt}</div>'
        f'</div>'
        # Volumen
        f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:8px;padding:7px 10px">'
        f'<div style="font-size:9px;color:{TXT_MUT};font-weight:700;margin-bottom:2px">VOL HOY</div>'
        f'<div style="font-size:13px;font-weight:700;color:{vol_c}">{vol_ico} {d["vol_ratio"]:.0f}%</div>'
        f'<div style="font-size:10px;color:{vol_c}">{vol_txt.split(" — ")[1] if " — " in vol_txt else vol_txt}</div>'
        f'</div>'
        f'</div>'
        # Panel de interpretación del trader
        + (
        f'<div style="background:{panel_bg};border:1px solid {panel_bor};'
        f'border-radius:8px;padding:8px 12px">'
        f'<div style="font-size:10px;font-weight:800;color:{panel_c};margin-bottom:3px">'
        f'{gap_ico} {gap_label} — Interpretación del trader</div>'
        f'<div style="font-size:10px;color:#374151;line-height:1.5">{gap_consejo}</div>'
        f'</div>'
        if gap_activo is not None else ""
        )
        + f'</div>'
    )
    return html


# ─────────────────────────────────────────────────────────────
#  PANEL PROBABILIDAD NBIS - para todas las tarjetas del scanner
# ─────────────────────────────────────────────────────────────


@st.cache_data(ttl=600, show_spinner=False)
@st.cache_data(ttl=600, show_spinner=False)
def leer_watchlist_sheets() -> "pd.DataFrame | None":
    """
    v18: Lee GrekoTrader_Watchlist desde Google Sheets.
    Columnas: Ticker | Nombre | Area | Nota
    """
    try:
        svc = _get_sheets_service()
        if not svc:
            st.session_state["_wl_sheets_error"] = "P1_FAIL: sin credenciales gcp_service_account"
            return None

        sheet_id = _get_sheet_id_from_secrets("watchlist_id")
        if not sheet_id:
            st.session_state["_wl_sheets_error"] = "P2_FAIL: watchlist_id no encontrado en st.secrets[sheets]"
            return None

        rows = []
        for _nombre_hoja in ["Hoja 1", "Sheet1", "Watchlist", "Hoja1", "Sheet 1"]:
            try:
                _result = svc.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=f"'{_nombre_hoja}'!A1:Z500"
                ).execute()
                _vals = _result.get("values", [])
                if _vals:
                    rows = _vals
                    st.session_state["_wl_sheets_error"] = ""
                    st.session_state["_wl_sheets_hoja"] = _nombre_hoja
                    break
            except Exception:
                continue

        if not rows:
            try:
                _result = svc.spreadsheets().values().get(
                    spreadsheetId=sheet_id, range="A1:Z500"
                ).execute()
                rows = _result.get("values", [])
                st.session_state["_wl_sheets_hoja"] = "rango genérico"
            except Exception as _e3:
                st.session_state["_wl_sheets_error"] = f"P3_FAIL: {str(_e3)[:100]}"
                return None

        if len(rows) < 2:
            st.session_state["_wl_sheets_error"] = "P4_WARN: Sheet vacío o solo tiene headers — agrega tickers en filas 2+"
            return pd.DataFrame(columns=["Ticker","Nombre","Area","Nota"])

        headers = [h.strip() for h in rows[0]]
        st.session_state["_wl_sheets_error"] = f"P5_OK: {len(rows)-1} filas · headers={headers[:4]}"
        wl_data = []
        for row in rows[1:]:
            if not row: continue
            d = {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
            tk = str(d.get("Ticker", d.get("Ticket", ""))).upper().strip().replace("$","")
            if not tk: continue
            wl_data.append({
                "Ticker": tk,
                "Nombre": str(d.get("Nombre", tk)).strip(),
                "Area":   str(d.get("Area", d.get("Área", d.get("Sector", "-")))).strip(),
                "Nota":   str(d.get("Nota",  d.get("Notas", ""))).strip(),
            })
        return pd.DataFrame(wl_data) if wl_data else pd.DataFrame(columns=["Ticker","Nombre","Area","Nota"])
    except Exception as _e:
        try:
            st.session_state["_wl_sheets_error"] = f"EXCEPTION: {str(_e)[:120]}"
        except Exception:
            pass
        return None


@st.cache_data(ttl=300, show_spinner=False)
def calcular_señal_recompra(
    ticker: str,
    precio_entrada: float,
    pnl_pct: float,
    tipo: str = "Accion",
    cat_fecha: str = "-",     # v19: fecha de earnings para ajustar la lógica
) -> dict:
    """
    v19: Calcula si existe oportunidad de recompra para una posición abierta.
    Ahora considera el contexto de earnings para ajustar la señal.

    Escenario A — Pre-earnings 3-7d + PnL >= 20%:
      → Recompra especulativa pequeña (20% posición)
    Escenario B — Post-earnings precio inflado:
      → NO recomprar (catalizador consumido)
    Escenario C — Post-earnings precio castigado:
      → Mantener lógica normal de recompra
    """
    # ── Contexto de earnings antes de hacer cualquier fetch ─────
    _earn_ctx = {"dias": None, "tipo": "sin_earnings"}
    if cat_fecha and cat_fecha not in ("-","","nan","NaT"):
        try:
            import datetime as _dt_rc
            _dias_rc = (_dt_rc.date.fromisoformat(str(cat_fecha)[:10])
                        - _dt_rc.date.today()).days
            _earn_ctx["dias"] = _dias_rc
            if 3 <= _dias_rc <= 7:
                _earn_ctx["tipo"] = "pre_earnings"
            elif -3 <= _dias_rc <= 0:
                _earn_ctx["tipo"] = "post_earnings"
        except Exception:
            pass
    try:
        import yfinance as _yf_r
        import numpy as _np_r
        import pandas as _pd_r

        hist = _yf_r.Ticker(ticker).history(period="2mo")
        if hist.empty or len(hist) < 14:
            return {"señal": "sin_datos"}

        close = hist["Close"].values
        # v19.1: Divergencia alcista RSI vs precio
        _div_fetch = calcular_divergencia_rsi(close, periodos=14, ventana=20)
        vol   = hist["Volume"].values

        # RSI 14
        s = _pd_r.Series(close)
        delta = s.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rsi   = round(float(100 - 100/(1 + gain.iloc[-1]/(loss.iloc[-1]+1e-9))), 1)

        # RSI hace 3 días (para detectar dirección)
        rsi_3d = round(float(100 - 100/(1 + gain.iloc[-4]/(loss.iloc[-4]+1e-9))), 1)
        rsi_baja = rsi < rsi_3d  # True si RSI bajando

        # EMA20 y precio actual
        ema20 = float(s.ewm(span=20).mean().iloc[-1])
        precio_actual = float(close[-1])
        sobre_ema20 = precio_actual >= ema20 * 0.97  # margen 3%

        # Máximo reciente (últimos 12 días)
        max_rec = float(_np_r.max(close[-12:]))
        dd_max  = round((precio_actual - max_rec) / max_rec * 100, 1)

        # Volumen: bajando en la corrección = sano
        avg_vol  = float(_np_r.mean(vol[-20:]))
        vol_hoy  = float(vol[-1])
        vol_bajo = vol_hoy < avg_vol * 0.9  # vol bajo = pullback sano

        # ── v19.1: Price Target check ANTES de evaluar recompra ────
        # Si el precio está sobre el target de analistas → NO recomprar
        _pt_rec = get_price_targets(ticker)
        _pt_alerta = ""
        _pt_bloquear_recompra = False

        if _pt_rec.get("ok"):
            _tm_rec  = _pt_rec.get("target_mean", 0)
            _tmax_rec = _pt_rec.get("target_max", 0)
            _na_rec  = _pt_rec.get("n_analysts", 0)
            _up_mean_rec = round((_tm_rec - precio_actual) / precio_actual * 100, 1) if _tm_rec > 0 and precio_actual > 0 else 0
            _up_max_rec  = round((_tmax_rec - precio_actual) / precio_actual * 100, 1) if _tmax_rec > 0 and precio_actual > 0 else 0

            if _na_rec >= 3:
                if precio_actual > _tmax_rec > 0:
                    # Precio sobre el target MÁXIMO — bloquear recompra
                    _pt_alerta = (f"🚫 Precio ${precio_actual:.2f} SOBRE target máximo "
                                  f"${_tmax_rec:.0f} de analistas ({_na_rec} analistas) · "
                                  f"Sin upside según consenso")
                    _pt_bloquear_recompra = True

                elif precio_actual > _tm_rec > 0:
                    # Precio sobre target promedio — advertencia
                    _pt_alerta = (f"⚠️ Precio ${precio_actual:.2f} sobre target promedio "
                                  f"${_tm_rec:.0f} ({_up_mean_rec:+.0f}% downside) · "
                                  f"{_na_rec} analistas · Agregar con precaución")

                elif _up_max_rec < 10:
                    # Poco upside incluso al target máximo
                    _pt_alerta = (f"⚠️ Poco upside al target máximo "
                                  f"${_tmax_rec:.0f} (+{_up_max_rec:.0f}%) · "
                                  f"Ratio riesgo/beneficio bajo para recompra")

        if _pt_bloquear_recompra:
            return {
                "señal":    "no_recomprar",
                "razon":    _pt_alerta,
                "rsi":      rsi,
                "dd_max":   dd_max,
                "pt_alerta": _pt_alerta,
            }

        # v19: Días alcistas consecutivos (detectar rebote activo)
        _dias_alcistas = 0
        for _ci in range(len(close)-1, max(0, len(close)-8), -1):
            if close[_ci] > close[_ci-1]:
                _dias_alcistas += 1
            else:
                break

        # Pre-market proxy: comparar último close vs close anterior
        _premia_pct = round((float(close[-1]) - float(close[-2])) / float(close[-2]) * 100, 1)

        # ── Stops según tipo ──────────────────────────────────
        stop_pct = {
            "Accion":        -7.0,
            "ETF_Sectorial": -12.0,
            "ETF_Indice":    -12.0,
            "ETF_Cripto":    -18.0,
        }.get(tipo, -7.0)

        # ── ESCENARIO 2: Posición en PÉRDIDA + rebote activo ─────
        # "Promediar a la baja" cuando el rebote está confirmado
        if pnl_pct < 0 and pnl_pct >= -20:
            _rebote_ok = (
                _dias_alcistas >= 2 and   # rebote iniciado
                48 <= rsi <= 65 and        # RSI válido, no cayendo
                sobre_ema20 and            # tendencia no rota
                not rsi_baja               # RSI subiendo
            )
            if _rebote_ok:
                # Calcular precio promedio si agrega 40%
                _agregar_pct = 0.40
                _precio_prom = round(
                    (precio_entrada + precio_actual * _agregar_pct) /
                    (1 + _agregar_pct), 2)
                _stop_comb   = round(_precio_prom * (1 + stop_pct/100), 2)
                _breakeven   = round(_precio_prom * 1.005, 2)  # casi breakeven
                _target      = round(precio_entrada * 1.05, 2) # recuperar + 5%

                return {
                    "señal":           "promedio_baja",
                    "calidad":         "REBOTE ACTIVO",
                    "emoji_calidad":   "⚡",
                    "precio_actual":   precio_actual,
                    "precio_promedio": _precio_prom,
                    "stop_combinado":  _stop_comb,
                    "breakeven":       _breakeven,
                    "target":          _target,
                    "rsi":             rsi,
                    "dd_max":          dd_max,
                    "dias_alcistas":   _dias_alcistas,
                    "ema_ok":          sobre_ema20,
                    "vol_bajo":        vol_bajo,
                    "descripcion":     (
                        f"{_dias_alcistas} días alcistas consecutivos · "
                        f"RSI {rsi} subiendo · EMA20 respetada. "
                        f"Agregar 40% reduce precio promedio a ${_precio_prom:.2f}. "
                        f"Stop combinado: ${_stop_comb:.2f} · "
                        f"Target recuperación: ${_target:.2f}"
                    ),
                }
            else:
                # Escenario 3: pérdida sin rebote — no actuar
                _razon_no = (
                    f"RSI {rsi} cayendo" if rsi_baja else
                    f"Solo {_dias_alcistas} día(s) alcista(s) — esperar confirmación" if _dias_alcistas < 2 else
                    "EMA20 rota — tendencia comprometida" if not sobre_ema20 else
                    f"RSI {rsi} fuera de zona válida"
                )
                return {
                    "señal":  "no_promediar",
                    "razon":  f"Posición en pérdida {pnl_pct:+.1f}% — {_razon_no}. "
                              f"Esperar {max(0, 2-_dias_alcistas)} día(s) más alcistas antes de agregar.",
                    "rsi":    rsi,
                    "dd_max": dd_max,
                    "dias_alcistas": _dias_alcistas,
                }

        # ── ESCENARIO 3 extremo: pérdida > -20% — nunca promediar ──
        if pnl_pct < -20:
            return {
                "señal":  "no_promediar",
                "razon":  f"Pérdida {pnl_pct:+.1f}% — demasiado profunda para promediar. "
                          f"Evaluar salida y re-entrada cuando el precio estabilice.",
                "rsi":    rsi,
                "dd_max": dd_max,
            }

        # ── Evaluar condiciones ───────────────────────────────
        cond_pnl      = pnl_pct >= 15

        # ── v19: Evaluar contexto de earnings PRIMERO ─────────────
        _earn_tipo = _earn_ctx.get("tipo","sin_earnings")
        _earn_dias = _earn_ctx.get("dias")

        # Escenario A: Pre-earnings 3-7 días
        if _earn_tipo == "pre_earnings" and _earn_dias is not None:
            if pnl_pct >= 20:
                # Colchón suficiente → recompra especulativa pequeña
                return {
                    "señal":           "recompra_pre_earnings",
                    "calidad":         "ESPECULATIVA",
                    "emoji_calidad":   "⚡",
                    "precio_recompra": round(float(close[-1]), 2),
                    "precio_prom":     round((precio_entrada + float(close[-1]))/2, 2),
                    "stop_combinado":  round(float(close[-1]) * 0.95, 2),  # stop -5% estricto
                    "target":          round(float(close[-1]) * 1.12, 2),
                    "rsi":             rsi,
                    "dd_max":          dd_max,
                    "ema_ok":          sobre_ema20,
                    "descripcion":     (
                        f"Earnings en {_earn_dias}d — recompra especulativa. "
                        f"PnL original +{pnl_pct:.1f}% actúa como colchón. "
                        f"Posición máx 20% · Stop -5% sobre recompra. "
                        f"Si earnings positivo → posición total crece. "
                        f"Si earnings negativo → colchón protege la original."
                    ),
                }
            else:
                return {
                    "señal":  "esperar",
                    "razon":  (f"Earnings en {_earn_dias}d — PnL {pnl_pct:+.1f}% "
                               f"insuficiente como colchón. Necesitas ≥20% para "
                               f"asumir el riesgo de un earnings próximo."),
                    "rsi":    rsi,
                    "dd_max": dd_max,
                }

        # Escenario B: Post-earnings precio inflado → NO recomprar
        if _earn_tipo == "post_earnings":
            _gap_post = float(close[-1]) / float(close[-3]) - 1 if len(close) > 3 else 0
            if rsi > 68 or _gap_post > 0.12:
                return {
                    "señal":  "no_recomprar",
                    "razon":  (f"Earnings hace {abs(_earn_dias)}d — precio subió "
                               f"+{_gap_post*100:.0f}% · RSI {rsi:.0f}. "
                               f"Catalizador consumido en el precio. "
                               f"Esperar corrección a RSI 52-58."),
                    "rsi":    rsi,
                    "dd_max": dd_max,
                }
            # Escenario C: Post-earnings precio castigado → lógica normal
            # (el precio bajó post-earnings, es como un pullback sano)
            # → continúa con la lógica normal de recompra abajo
        cond_dd       = -20 <= dd_max <= -5
        cond_rsi      = 48 <= rsi <= 62
        cond_ema      = sobre_ema20
        cond_vol      = vol_bajo
        cond_rsi_baja = rsi_baja  # confirmación pullback

        # Puntaje de calidad de la oportunidad
        puntos = sum([cond_pnl, cond_dd, cond_rsi, cond_ema, cond_vol])

        # ── Determinar señal ─────────────────────────────────
        if not cond_pnl:
            return {
                "señal":      "no_aplica",
                "razon":      f"PnL {pnl_pct:+.1f}% — necesita ≥15% para recomprar con seguridad",
                "rsi":        rsi,
                "dd_max":     dd_max,
                "ema_ok":     sobre_ema20,
            }

        if cond_pnl and cond_dd and cond_rsi and cond_ema:
            # Señal válida — calcular precios
            precio_recompra = round(precio_actual, 2)
            precio_prom = round((precio_entrada + precio_recompra) / 2, 2)
            stop_combinado = round(precio_prom * (1 + stop_pct/100), 2)
            target = round(precio_recompra * 1.15, 2)  # +15% desde recompra

            calidad = "ALTA" if puntos >= 5 else "MEDIA" if puntos >= 4 else "BAJA"
            emoji_cal = "🟢" if calidad == "ALTA" else "🟡" if calidad == "MEDIA" else "🟠"

            return {
                "señal":           "recompra",
                "calidad":         calidad,
                "emoji_calidad":   emoji_cal,
                "precio_recompra": precio_recompra,
                "precio_prom":     precio_prom,
                "stop_combinado":  stop_combinado,
                "target":          target,
                "rsi":             rsi,
                "dd_max":          dd_max,
                "ema_ok":          sobre_ema20,
                "vol_bajo":        vol_bajo,
                "max_rec":         round(max_rec, 2),
                "puntos":          puntos,
                "descripcion":     (
                    f"DD {dd_max:.1f}% desde máximo · RSI {rsi} · "
                    f"EMA20 {'✅' if sobre_ema20 else '❌'} · "
                    f"Vol {'↓ sano' if vol_bajo else '↑ vigilar'}"
                ),
            }

        elif cond_pnl and rsi > 65:
            _razon_ep = (f"RSI {rsi} — precio en máximos, esperar corrección "
                         f"a zona {round(max_rec*0.92,2)}-{round(max_rec*0.95,2)}")
            if _pt_alerta:
                _razon_ep += f" · {_pt_alerta}"
            return {
                "señal":  "esperar_pullback",
                "razon":  _razon_ep,
                "rsi":    rsi,
                "dd_max": dd_max,
                "target_entrada": round(max_rec * 0.93, 2),
                "pt_alerta": _pt_alerta,
            }

        elif cond_pnl and not cond_ema:
            _razon_ema = f"Rompió EMA20 (${ema20:.2f}) — pullback demasiado profundo · RSI {rsi}"
            if _pt_alerta:
                _razon_ema += f" · {_pt_alerta}"
            return {
                "señal":  "no_recomprar",
                "razon":  _razon_ema,
                "rsi":    rsi,
                "dd_max": dd_max,
                "ema20":  round(ema20, 2),
                "pt_alerta": _pt_alerta,
            }

        elif cond_pnl and dd_max < -20:
            _razon_dd = f"DD {dd_max:.1f}% — corrección muy profunda, puede seguir bajando"
            if _pt_alerta:
                _razon_dd += f" · {_pt_alerta}"
            return {
                "señal":  "no_recomprar",
                "razon":  _razon_dd,
                "rsi":    rsi,
                "dd_max": dd_max,
                "pt_alerta": _pt_alerta,
            }

        else:
            _razon_esp = f"PnL {pnl_pct:+.1f}% · RSI {rsi} · DD {dd_max:.1f}% — monitorear"
            if _pt_alerta:
                _razon_esp += f" · {_pt_alerta}"
            return {
                "señal":  "esperar",
                "razon":  _razon_esp,
                "rsi":    rsi,
                "dd_max": dd_max,
                "pt_alerta": _pt_alerta,
            }

    except Exception as _e_r:
        return {"señal": "error", "razon": str(_e_r)[:60]}





def construir_cartera_global() -> dict:
    """
    v19: Lee las 3 carteras (Greko, MVALLE, Amparito) y construye
    un dict global para cruzar con los scans del día.
    
    Retorna:
    {
      "NBIS": {"carteras": ["MVALLE"], "pnl": 72.4, "pc": 129.90},
      "APLD": {"carteras": ["Greko","MVALLE"], "pnl": 73.9, "pc": 26.64},
    }
    Solo incluye posiciones ACTIVAS (sin Fecha_Salida).
    Se cachea en session_state por 10 minutos.
    """
    import datetime as _dtcg
    
    # Cache check — recargar si han pasado >10 min
    _cache = st.session_state.get("_cartera_global_cache", {})
    _ts    = st.session_state.get("_cartera_global_ts")
    if _cache and _ts:
        try:
            _mins = (_dtcg.datetime.now() - _ts).seconds / 60
            if _mins < 10:
                return _cache
        except Exception:
            pass

    _cartera = {}
    
    _SHEETS_CONFIG = [
        (_SHEET_NAME_GREKO,    "Greko"),
        (_SHEET_NAME_MAURI,    "MVALLE"),
        (_SHEET_NAME_AMPARITO, "Amparito"),
    ]

    for _sheet_name, _label in _SHEETS_CONFIG:
        try:
            _df = leer_posiciones_sheets(_sheet_name)
            if _df is None or _df.empty:
                continue
            _df = _normalizar_precios_df(_df)
            
            for _, _row in _df.iterrows():
                _tk  = str(_row.get("Ticker","")).upper().strip()
                _fs  = str(_row.get("Fecha_Salida","-")).strip()
                _pc  = _parse_precio(_row.get("Precio_Compra", 0))
                
                if not _tk or _pc <= 0:
                    continue
                # Solo posiciones abiertas (sin fecha de salida)
                if _fs not in ("-","","nan","NaT","None"):
                    continue
                
                # v19: usar precio del session_state si está disponible
                # evita llamar yfinance × N posiciones al cargar
                _cached_prices = st.session_state.get("_precios_live", {})
                if _tk in _cached_prices:
                    _pa  = _cached_prices[_tk]
                    _pnl = round((_pa - _pc) / _pc * 100, 1)
                else:
                    # Solo llamar yfinance si no tenemos precio en caché
                    try:
                        import yfinance as _yf_cg
                        _pa = float(_yf_cg.Ticker(_tk).history(period="1d")["Close"].iloc[-1])
                        _pnl = round((_pa - _pc) / _pc * 100, 1)
                        # Guardar en caché de precios
                        if "_precios_live" not in st.session_state:
                            st.session_state["_precios_live"] = {}
                        st.session_state["_precios_live"][_tk] = _pa
                    except Exception:
                        _pnl = 0.0
                        _pa  = _pc
                
                if _tk not in _cartera:
                    _cartera[_tk] = {"carteras": [], "pnl": _pnl, "pc": _pc, "pa": _pa}
                if _label not in _cartera[_tk]["carteras"]:
                    _cartera[_tk]["carteras"].append(_label)
                    
        except Exception:
            continue

    st.session_state["_cartera_global_cache"] = _cartera
    st.session_state["_cartera_global_ts"]    = _dtcg.datetime.now()
    return _cartera


def get_badge_cartera(ticker: str, G: str, R: str, A: str) -> str:
    """
    v19: Retorna HTML del badge de cartera para un ticker.
    Vacío si no está en ninguna cartera.
    """
    cartera = st.session_state.get("_cartera_global_cache", {})
    if ticker not in cartera:
        return ""
    
    datos     = cartera[ticker]
    pnl       = datos.get("pnl", 0)
    carteras  = datos.get("carteras", [])
    cart_str  = " y ".join(carteras)
    
    if pnl >= 15:
        color = G
        bg    = "#F0FDF4"
        icono = "📌"
        msg   = f"Ya en {cart_str} ({pnl:+.1f}%) · ver Recompra"
    elif pnl >= 0:
        color = "#D97706"
        bg    = "#FFFBEB"
        icono = "📌"
        msg   = f"Ya en {cart_str} ({pnl:+.1f}%) · posición joven"
    else:
        color = R
        bg    = "#FEF2F2"
        icono = "⚠️"
        msg   = f"En {cart_str} ({pnl:+.1f}%) · NO agregar sin catalizador"

    return (
        f'<div style="background:{bg};border-left:3px solid {color};'
        f'border-radius:0 6px 6px 0;padding:4px 10px;margin-top:3px;'
        f'font-size:10px;font-weight:600;color:{color}">'
        f'{icono} {msg}</div>'
    )

def auto_cargar_noticias(tickers: list, max_tickers: int = 12) -> None:
    """
    v19: Carga noticias automáticamente para una lista de tickers
    sin requerir que el usuario presione "Actualizar noticias".
    Usa el caché existente y solo fetcha los que faltan.
    Máximo max_tickers para no ralentizar.
    """
    cache = st.session_state.get("noticias_cache", {})
    _pendientes = [tk for tk in tickers[:max_tickers]
                   if tk not in cache or not cache[tk].get("noticias")]
    if not _pendientes:
        return  # todos ya en caché
    for _tk in _pendientes:
        try:
            _noticias = fetch_noticias_ticker(_tk)
            if _noticias:
                if "noticias_cache" not in st.session_state:
                    st.session_state["noticias_cache"] = {}
                st.session_state["noticias_cache"][_tk] = {
                    "noticias": _noticias,
                    "ts": __import__("datetime").datetime.now().strftime("%H:%M")
                }
        except Exception:
            pass


def tipo_pullback(dd: float, rsi: float, ema_d: float, 
                  dias_alcistas: int, vol_ratio: float,
                  tiene_posicion_abierta: bool = False,
                  pnl_pct: float = 0.0) -> dict:
    """
    v19: Clasifica el tipo de pullback y genera mensaje claro para el trader.
    
    Pullback 1 — Corrección profunda en tendencia alcista (DD ≤ -20%)
    Pullback 2 — Corrección leve en tendencia activa (DD -8% a -20%)  
    Pullback 3 — Pullback en posición abierta (Recompra)
    """
    if tiene_posicion_abierta and pnl_pct >= 5:
        # Pullback 3: posición abierta con ganancia
        if dd <= -5:
            return {
                "tipo": 3,
                "nombre": "Pullback en posición abierta",
                "emoji": "🔄",
                "color": "#7C3AED",
                "bg": "#F5F3FF",
                "descripcion": (
                    f"Corrección {dd:.1f}% en tu posición ganadora (+{pnl_pct:.1f}%). "
                    f"Oportunidad de recompra si RSI 48-62 y EMA20 se respeta. "
                    f"Máximo agregar 30% de la posición original."
                ),
                "accion": "Ver panel Recompra",
            }
        else:
            return {
                "tipo": 3,
                "nombre": "Pullback en posición abierta",
                "emoji": "⏳",
                "color": "#2563EB",
                "bg": "#EFF6FF",
                "descripcion": (
                    f"Posición con +{pnl_pct:.1f}% de ganancia. "
                    f"Aún no hay corrección suficiente para recompra. "
                    f"Esperar pullback de al menos -5% desde máximo reciente."
                ),
                "accion": "Mantener posición",
            }

    if dd <= -20:
        # Pullback 1: corrección profunda
        if rsi >= 48 and dias_alcistas >= 2:
            return {
                "tipo": 1,
                "nombre": "Pullback profundo — rebote técnico",
                "emoji": "🔥",
                "color": "#16A34A",
                "bg": "#F0FDF4",
                "descripcion": (
                    f"Corrección profunda {dd:.1f}% desde máximo histórico. "
                    f"RSI {rsi:.0f} en zona de entrada (48-65). "
                    f"{'EMA20 respetada — tendencia intacta.' if ema_d >= -15 else 'Precio bajo EMA20 — vigilar.'} "
                    f"Setup M2/M3 clásico del modelo. WR histórico: 65-80%."
                ),
                "accion": "Señal M2 válida — evaluar entrada",
            }
        else:
            return {
                "tipo": 1,
                "nombre": "Pullback profundo — rebote aún no confirmado",
                "emoji": "👀",
                "color": "#D97706",
                "bg": "#FFFBEB",
                "descripcion": (
                    f"Corrección profunda {dd:.1f}% pero rebote no confirmado. "
                    f"RSI {rsi:.0f} {'aún bajo (< 48) — acción sigue débil.' if rsi < 48 else 'subiendo — positivo.'} "
                    f"Necesita {max(0, 2-dias_alcistas)} día(s) más alcistas para confirmar."
                ),
                "accion": "Radar — esperar confirmación",
            }

    elif -20 < dd <= -8:
        # Pullback 2: corrección leve en tendencia activa
        if rsi >= 48 and ema_d >= -10:
            return {
                "tipo": 2,
                "nombre": "Pullback saludable en tendencia activa",
                "emoji": "⚡",
                "color": "#0891B2",
                "bg": "#ECFEFF",
                "descripcion": (
                    f"Corrección leve {dd:.1f}% en tendencia alcista activa. "
                    f"RSI {rsi:.0f} en zona válida. "
                    f"EMA20 respetada — la tendencia sigue intacta. "
                    f"'Buy the dip' clásico. "
                    f"Volumen {'bajo en la corrección ✅ — sano.' if vol_ratio < 80 else 'alto en la corrección ⚠️ — posible distribución.'}"
                ),
                "accion": "Entrada válida con posición reducida (50-60%)",
            }
        else:
            return {
                "tipo": 2,
                "nombre": "Corrección leve — sin confirmación aún",
                "emoji": "📡",
                "color": "#6B7280",
                "bg": "#F9FAFB",
                "descripcion": (
                    f"Corrección {dd:.1f}% desde máximo. "
                    f"{'RSI ' + str(int(rsi)) + ' bajo zona de entrada (< 48).' if rsi < 48 else ''}"
                    f"{'EMA20 rota — tendencia comprometida.' if ema_d < -10 else ''} "
                    f"Esperar RSI sobre 48 y EMA20 respetada."
                ),
                "accion": "Radar — esperar mejor setup",
            }

    return {}  # DD muy pequeño (< -8%) — no es pullback significativo



def calcular_stop_tipo(
    pc: float,              # precio de compra
    tipo: str,              # Accion, ETF_Cripto, ETF_Indice, ETF_Sectorial
    beta: float,            # beta de la acción
    score_entrada: float = 0,
    prob_entrada: float = 0,
    tenia_earnings: bool = False,
    pnl_pct: float = 0,
    pa: float = 0,          # v19 FIX: precio actual para calcular targets reales
) -> dict:
    """
    v19: Calcula el stop loss según 3 tipos:
    
    Stop Normal — señal técnica limpia (score 40-55, prob 30-50%):
      Acción beta < 1.5: -7%
      Acción beta 1.5-2.5: -10%
      Acción beta > 2.5: -12%
      ETF Sectorial: -12%
      ETF Índice: sin stop (mantener siempre)
      ETF Cripto: -20%
      
    Stop Estricto — señal con riesgo adicional:
      Si Score > 55 o Prob > 50% → -5% (señal tardía)
      Si entró con earnings → -5% (riesgo binario)
      Si RSI > 65 al entrar → -5%
      
    Stop Trailing — posición en ganancia:
      Si PnL > 20%: stop = precio_actual × 0.92 (-8% desde precio actual)
      Si PnL > 40%: stop = precio_actual × 0.95 (-5% desde precio actual)
    """
    # ── Determinar tipo de stop ───────────────────────────────
    _es_tardio   = score_entrada > 55 or prob_entrada > 50
    _es_earnings = tenia_earnings
    _stop_estricto = _es_tardio or _es_earnings

    # ── ETFs: reglas fijas ────────────────────────────────────
    # v19 FIX: targets desde precio ACTUAL (pa), no desde precio de compra (pc)
    # Si pa no se pasa, usar pc como fallback
    _pa = pa if pa > 0 else pc
    _stop_activado = pa > 0 and pa < pc * 0.85  # posición en pérdida significativa

    if tipo == "ETF_Indice":
        return {
            "stop_pct":   0,
            "stop_val":   0,
            "tipo_stop":  "Sin stop — mantener siempre",
            "etiqueta":   "📊 ETF Índice — nunca vender",
            "obj1": _pa*1.15, "obj2": _pa*1.25, "obj3": _pa*1.40,
            "razon": "Los ETF de índice no se venden por señal técnica",
            "stop_activado": False,
        }
    elif tipo == "ETF_Cripto":
        pct = -20.0
        _sv = pc*(1+pct/100)
        return {
            "stop_pct": pct, "stop_val": _sv,
            "tipo_stop": "Normal ETF Cripto",
            "etiqueta":  f"🛑 Stop Cripto ({pct:.0f}%)",
            "obj1": _pa*1.20, "obj2": _pa*1.50, "obj3": _pa*2.00,
            "razon": "Alta volatilidad cripto — stop amplio",
            "stop_activado": pa > 0 and pa < _sv,
        }
    elif tipo == "ETF_Sectorial":
        pct = -12.0
        _sv = pc*(1+pct/100)
        return {
            "stop_pct": pct, "stop_val": _sv,
            "tipo_stop": "Normal ETF Sectorial",
            "etiqueta":  f"🛑 Stop ETF ({pct:.0f}%)",
            "obj1": _pa*1.10, "obj2": _pa*1.25, "obj3": _pa*1.50,
            "razon": "ETF sectorial — stop estándar -12%",
            "stop_activado": pa > 0 and pa < _sv,
        }

    # ── Acciones: según contexto ──────────────────────────────
    if _stop_estricto:
        pct = -5.0
        tipo_lbl = "Estricto"
        if _es_tardio:
            razon = f"Señal tardía (Score {score_entrada:.0f} > 55 o Prob {prob_entrada:.0f}% > 50%)"
        else:
            razon = "Entrada con earnings próximos — stop ajustado"
        obj1 = _pa*1.08; obj2 = _pa*1.15; obj3 = _pa*1.25
    elif beta < 1.5:
        pct = -7.0
        tipo_lbl = "Normal beta bajo"
        razon = f"Acción estable (Beta {beta:.1f})"
        obj1 = _pa*1.10; obj2 = _pa*1.20; obj3 = _pa*1.35
    elif beta < 2.5:
        pct = -10.0
        tipo_lbl = "Normal beta medio"
        razon = f"Acción moderada (Beta {beta:.1f})"
        obj1 = _pa*1.12; obj2 = _pa*1.25; obj3 = _pa*1.45
    else:
        pct = -12.0
        tipo_lbl = "Normal beta alto"
        razon = f"Acción volátil (Beta {beta:.1f})"
        obj1 = _pa*1.15; obj2 = _pa*1.30; obj3 = _pa*1.60

    _sv_acc = round(pc * (1 + pct/100), 2)
    return {
        "stop_pct":  pct,
        "stop_val":  _sv_acc,
        "tipo_stop": tipo_lbl,
        "etiqueta":  f"🛑 Stop {'⚠️ Estricto' if _stop_estricto else 'Normal'} ({pct:.0f}%)",
        "razon":     razon,
        "obj1": round(obj1,2), "obj2": round(obj2,2), "obj3": round(obj3,2),
        "stop_activado": pa > 0 and pa < _sv_acc,
    }

def render_pullback_badge(ticker: str, dd: float, rsi: float, ema_d: float,
                          dias_alcistas: int, vol_ratio: float,
                          G: str, R: str, A: str, C: str,
                          TXT_MUT: str,
                          tiene_posicion: bool = False,
                          pnl_pct: float = 0.0) -> str:
    """
    v19: Renderiza badge de tipo pullback para Watchlist, Swing y Posiciones.
    """
    pb = tipo_pullback(dd, rsi, ema_d, dias_alcistas, vol_ratio,
                       tiene_posicion, pnl_pct)
    if not pb:
        return ""

    return (
        f'<div style="background:{pb["bg"]};border-left:3px solid {pb["color"]};'
        f'border-radius:0 8px 8px 0;padding:8px 12px;margin-top:5px">'
        f'<div style="font-size:11px;font-weight:700;color:{pb["color"]};margin-bottom:3px">'
        f'{pb["emoji"]} {pb["nombre"]}</div>'
        f'<div style="font-size:10px;color:#374151;line-height:1.7">'
        f'{pb["descripcion"]}</div>'
        f'<div style="font-size:10px;font-weight:600;color:{pb["color"]};'
        f'margin-top:4px">→ {pb["accion"]}</div>'
        f'</div>'
    )


# v19: Mapa de normalización de sectores
_SECTOR_MAP = {
    "AI Infra":               "AI Infraestructura",
    "AI Infrastructure":      "AI Infraestructura",
    "Infra IA":               "AI Infraestructura",
    "Storage / AI Infra":     "AI Infraestructura",
    "Energía IA":             "AI Infraestructura",
    "Solar":                  "Energía Solar",
    "Energia Solar":          "Energía Solar",
    "Energía renovable":      "Energía Solar",
    "Biotech":                "Biotecnología",
    "BioTech":                "Biotecnología",
    "Biotecnología e investigación médica": "Biotecnología",
    "AI Healthcare":          "Healthcare / AI",
    "Salud":                  "Healthcare / AI",
    "Semiconductores y equipos de semiconductores": "Semiconductores",
    "Semiconductores":        "Semiconductores",
    "Ciberseguridad":         "Ciberseguridad",
    "Software y servicios informáticos": "Software / Cloud",
    "Cloud Networking":       "Software / Cloud",
    "Enterprise AI":          "Software / Cloud",
    "IA Datos":               "Software / Cloud",
    "Networking&Connectivity":"Networking",
    "Comunicaciones y redes": "Networking",
    "Aeroespacial y defensa": "Aeroespacial",
    "Moon Economy":           "Aeroespacial",
    "Space Infra":            "Aeroespacial",
    "Bitcoin ETF":            "Crypto",
    "Bitcoin Mining":         "Crypto",
    "Ethereum ETF":           "Crypto",
    "Crypto Exchange":        "Crypto",
    "Digital Media":          "Digital Media",
    "Digital Ads":            "Digital Media",
    "Storage AI":             "Storage",
    "Almacenamiento & Storage": "Storage",
}

def _normalizar_sector(area: str) -> str:
    """v19: Normaliza nombre de sector a versión estándar."""
    if not area or str(area) in ("-","","nan"):
        return "Sin sector"
    _a = str(area).strip()
    return _SECTOR_MAP.get(_a, _a)


def get_price_targets(ticker: str) -> dict:
    """
    v19: Obtiene Price Targets, P/E ratio, cobertura analistas y 52w high.
    Cachea en session_state para no repetir calls.
    """
    _cache_key = f"_pt_{ticker}"
    if _cache_key in st.session_state:
        return st.session_state[_cache_key]

    result = {"target_max": 0, "target_mean": 0, "target_min": 0,
              "target_median": 0, "n_analysts": 0, "recommendation": "-",
              "precio": 0, "upside_mean": 0, "upside_max": 0,
              "pe_ratio": 0, "high_52w": 0, "ok": False}
    try:
        import yfinance as _yf_pt
        info = _yf_pt.Ticker(ticker).info
        _tmax  = float(info.get("targetHighPrice", 0) or 0)
        _tmean = float(info.get("targetMeanPrice", 0) or 0)
        _tmin  = float(info.get("targetLowPrice", 0) or 0)
        _tmed  = float(info.get("targetMedianPrice", 0) or 0)
        _na    = int(info.get("numberOfAnalystOpinions", 0) or 0)
        _rec   = str(info.get("recommendationKey", "-") or "-")
        _pa    = float(info.get("currentPrice", 0) or info.get("regularMarketPrice", 0) or 0)
        # v19 nuevos filtros
        _pe    = float(info.get("trailingPE", 0) or info.get("forwardPE", 0) or 0)
        _h52   = float(info.get("fiftyTwoWeekHigh", 0) or 0)

        if _tmean > 0 and _pa > 0:
            result = {
                "target_max":   round(_tmax, 2),
                "target_mean":  round(_tmean, 2),
                "target_min":   round(_tmin, 2),
                "target_median":round(_tmed, 2),
                "n_analysts":   _na,
                "recommendation": _rec,
                "precio":       round(_pa, 2),
                "upside_mean":  round((_tmean - _pa) / _pa * 100, 1),
                "upside_max":   round((_tmax - _pa) / _pa * 100, 1),
                "pe_ratio":     round(_pe, 1),
                "high_52w":     round(_h52, 2),
                "ok": True,
            }
    except Exception:
        pass

    st.session_state[_cache_key] = result
    return result


def evaluar_price_target(ticker: str, precio_actual: float = 0) -> dict:
    """
    v19: Evalúa Price Target + P/E burbuja + cobertura analistas + ATH.
    """
    pt = get_price_targets(ticker)
    if not pt["ok"]:
        return {"nivel": "sin_datos", "msg": "", "color": "", "bloquear": False}

    _pa   = precio_actual if precio_actual > 0 else pt["precio"]
    if _pa <= 0:
        return {"nivel": "sin_datos", "msg": "", "color": "", "bloquear": False}

    _up_mean = round((pt["target_mean"] - _pa) / _pa * 100, 1) if pt["target_mean"] > 0 else 0
    _up_max  = round((pt["target_max"]  - _pa) / _pa * 100, 1) if pt["target_max"] > 0 else 0
    _na      = pt["n_analysts"]
    _pe      = pt.get("pe_ratio", 0)
    _h52     = pt.get("high_52w", 0)

    # ── NUEVOS FILTROS v19 ──────────────────────────────────────

    # Filtro A: P/E > 500x → burbuja especulativa
    if _pe > 500:
        return {
            "nivel": "burbuja_pe",
            "msg": f"🚫 P/E {_pe:.0f}x — Burbuja especulativa · Riesgo de short attack · No entrar",
            "color": "#DC2626",
            "bloquear": True,
            "upside_mean": _up_mean, "upside_max": _up_max,
            "pe_ratio": _pe,
        }

    # Filtro B: Solo 1-2 analistas cubriendo → riesgo short attack
    if 0 < _na <= 2:
        return {
            "nivel": "cobertura_minima",
            "msg": f"⚠️ Solo {_na} analista{'s' if _na > 1 else ''} cubren esta acción · Alto riesgo de short attack · Precaución extrema",
            "color": "#D97706",
            "bloquear": True,
            "upside_mean": _up_mean, "upside_max": _up_max,
            "n_analysts": _na,
        }

    # Filtro C: Precio cerca del ATH sin corrección previa
    if _h52 > 0 and _pa > 0:
        _dist_ath = round((_pa - _h52) / _h52 * 100, 1)  # negativo = bajo el ATH
        if _dist_ath >= -5:  # menos del -5% desde ATH → zona de tope
            return {
                "nivel": "en_ath",
                "msg": f"🚫 Precio a {abs(_dist_ath):.1f}% del máximo histórico ${_h52:.2f} · No entrar sin corrección de -15%+",
                "color": "#DC2626",
                "bloquear": True,
                "upside_mean": _up_mean, "upside_max": _up_max,
                "dist_ath": _dist_ath,
            }
        elif _dist_ath >= -15:  # entre -5% y -15% → aún cerca del ATH
            return {
                "nivel": "cerca_ath",
                "msg": f"⚠️ A solo {abs(_dist_ath):.1f}% del máximo histórico ${_h52:.2f} · Corrección insuficiente",
                "color": "#D97706",
                "bloquear": False,
                "upside_mean": _up_mean, "upside_max": _up_max,
                "dist_ath": _dist_ath,
            }

    # ── REGLAS ORIGINALES DE PRICE TARGET ──────────────────────

    # Regla 1: precio encima del target máximo
    if _up_max <= 0:
        return {
            "nivel": "sobre_target",
            "msg": f"Precio SOBRE target máximo (${pt['target_max']:.0f}) · SIN UPSIDE · {_na} analistas",
            "color": "#DC2626",
            "bloquear": True,
            "upside_mean": _up_mean, "upside_max": _up_max,
        }

    # Regla 2: upside < 5% del target máximo
    if _up_max < 5:
        return {
            "nivel": "sin_upside",
            "msg": f"Solo +{_up_max:.0f}% hasta target máximo (${pt['target_max']:.0f}) · Riesgo > Beneficio",
            "color": "#DC2626",
            "bloquear": True,
            "upside_mean": _up_mean, "upside_max": _up_max,
        }

    # Regla 3: upside < 10% del target promedio
    if _up_mean < 10:
        return {
            "nivel": "upside_limitado",
            "msg": f"Upside limitado +{_up_mean:.0f}% al target promedio (${pt['target_mean']:.0f}) · {_na} analistas · Precaución",
            "color": "#D97706",
            "bloquear": False,
            "upside_mean": _up_mean, "upside_max": _up_max,
        }

    # Regla 4: upside > 30% → excelente
    if _up_mean > 30:
        return {
            "nivel": "alto_upside",
            "msg": f"Amplio upside +{_up_mean:.0f}% al target promedio (${pt['target_mean']:.0f}) · Ratio excelente",
            "color": "#16A34A",
            "bloquear": False,
            "upside_mean": _up_mean, "upside_max": _up_max,
        }

    # Normal
    return {
        "nivel": "normal",
        "msg": f"Upside +{_up_mean:.0f}% target promedio · +{_up_max:.0f}% target máximo · {_na} analistas",
        "color": "#2563EB",
        "bloquear": False,
        "upside_mean": _up_mean,
        "upside_max": _up_max,
    }


def render_price_target_badge(ticker: str, precio_actual: float = 0,
                               G: str = "", R: str = "", A: str = "",
                               TXT_MUT: str = "") -> str:
    """
    v19: Renderiza badge HTML de Price Target para cards y tablas.
    """
    pt  = get_price_targets(ticker)
    ev  = evaluar_price_target(ticker, precio_actual)

    if not pt["ok"] or ev["nivel"] == "sin_datos":
        return ""

    _pa = precio_actual if precio_actual > 0 else pt["precio"]
    _rec_emoji = {"buy":"🟢","strong_buy":"🟢🟢","hold":"🟡",
                  "sell":"🔴","strong_sell":"🔴🔴","underperform":"🔴"}.get(
                  pt["recommendation"], "⚪")
    _rec_label = {"buy":"Comprar","strong_buy":"Compra Fuerte","hold":"Mantener",
                  "sell":"Vender","strong_sell":"Venta Fuerte",
                  "underperform":"Bajo Rendimiento"}.get(
                  pt["recommendation"], pt["recommendation"])

    _c    = ev["color"]
    _bg   = "#FEF2F2" if ev["bloquear"] else "#F0FDF4" if ev["nivel"] == "alto_upside" else "#EFF6FF" if ev["nivel"] == "normal" else "#FFFBEB"
    _bor  = "2px" if ev["bloquear"] else "1px"

    # Barra visual de posición del precio
    _range = pt["target_max"] - pt["target_min"] if pt["target_max"] > pt["target_min"] else 1
    _pct_pos = min(100, max(0, (_pa - pt["target_min"]) / _range * 100))

    return (
        f'<div style="background:{_bg};border:{_bor} solid {_c}40;'
        f'border-left:3px solid {_c};border-radius:0 8px 8px 0;'
        f'padding:8px 12px;margin-top:6px">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">'
        f'<span style="font-size:10px;font-weight:700;color:{_c}">'
        f'📊 Price Targets ({pt["n_analysts"]} analistas)</span>'
        f'<span style="font-size:9px">{_rec_emoji} {_rec_label}</span>'
        f'</div>'
        # Barra visual
        f'<div style="background:#E2E8F0;border-radius:4px;height:6px;margin:6px 0;position:relative">'
        f'<div style="background:{_c};width:{_pct_pos:.0f}%;height:100%;border-radius:4px"></div>'
        f'</div>'
        # Targets
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;font-size:9px;margin-bottom:4px">'
        f'<div style="text-align:center"><div style="color:{TXT_MUT}">Mínimo</div>'
        f'<div style="font-weight:700">${pt["target_min"]:.0f}</div></div>'
        f'<div style="text-align:center"><div style="color:{TXT_MUT}">Promedio</div>'
        f'<div style="font-weight:700">${pt["target_mean"]:.0f}</div></div>'
        f'<div style="text-align:center"><div style="color:{TXT_MUT}">Mediana</div>'
        f'<div style="font-weight:700">${pt["target_median"]:.0f}</div></div>'
        f'<div style="text-align:center"><div style="color:{TXT_MUT}">Máximo</div>'
        f'<div style="font-weight:700">${pt["target_max"]:.0f}</div></div>'
        f'</div>'
        # Evaluación
        f'<div style="font-size:10px;font-weight:600;color:{_c};margin-top:2px">'
        f'{"🚫" if ev["bloquear"] else "📈" if ev["nivel"]=="alto_upside" else "ℹ️"} {ev["msg"]}</div>'
        f'</div>'
    )


def get_sma_status(ticker: str) -> dict:
    """
    v19: Calcula SMA 50 y SMA 200 y evalúa posición del precio.
    Cachea en session_state.
    """
    _cache_key = f"_sma_{ticker}"
    if _cache_key in st.session_state:
        return st.session_state[_cache_key]

    result = {"sma50": 0, "sma200": 0, "precio": 0,
              "vs_sma50": 0, "vs_sma200": 0, "ok": False, "nivel": "sin_datos"}
    try:
        import yfinance as _yf_sma
        import datetime as _dt_sma
        _end_sma = dt.date.today()
        _start_sma = _end_sma - dt.timedelta(days=365)
        hist = _yf_sma.Ticker(ticker).history(
            start=_start_sma.strftime("%Y-%m-%d"),
            end=_end_sma.strftime("%Y-%m-%d"))
        if hist.empty or len(hist) < 50:
            st.session_state[_cache_key] = result
            return result

        close = hist["Close"]
        _pa    = float(close.iloc[-1])
        _sma50 = float(close.rolling(50).mean().iloc[-1])
        _sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else 0

        _vs50  = round((_pa - _sma50) / _sma50 * 100, 1) if _sma50 > 0 else 0
        _vs200 = round((_pa - _sma200) / _sma200 * 100, 1) if _sma200 > 0 else 0

        # Clasificar
        if _pa < _sma50 and _pa < _sma200:
            _nivel = "bajo_ambas"  # muy descontado
        elif _pa < _sma50:
            _nivel = "bajo_sma50"  # descontado
        elif _sma200 > 0 and _pa > _sma200 * 1.15:
            _nivel = "sobre_ambas"  # caro
        else:
            _nivel = "entre_smas"  # neutral

        result = {
            "sma50": round(_sma50, 2), "sma200": round(_sma200, 2),
            "precio": round(_pa, 2), "vs_sma50": _vs50, "vs_sma200": _vs200,
            "ok": True, "nivel": _nivel,
        }
    except Exception:
        pass

    st.session_state[_cache_key] = result
    return result


def calcular_divergencia_rsi(close_arr, periodos: int = 14,
                              ventana: int = 20) -> dict:
    """
    v19.1: Detecta divergencia alcista RSI vs Precio.
    Divergencia alcista = precio hace mínimos más bajos PERO RSI hace mínimos más altos.
    Señal: el momentum de caída se está agotando → rebote inminente.

    Returns:
        {"tiene": bool, "tipo": "fuerte"|"moderada"|"none",
         "badge": html_str, "descripcion": str}
    """
    try:
        import numpy as _np_div
        import pandas as _pd_div

        if len(close_arr) < ventana + periodos:
            return {"tiene": False, "tipo": "none", "badge": "", "descripcion": ""}

        # Calcular RSI sobre el array completo
        _s   = _pd_div.Series(close_arr)
        _d   = _s.diff()
        _g   = _d.clip(lower=0).rolling(periodos).mean()
        _l   = (-_d.clip(upper=0)).rolling(periodos).mean()
        _rsi_serie = (100 - 100 / (1 + _g / (_l + 1e-9))).fillna(50)

        # Últimos N períodos para comparar
        _precio_ventana = _np_div.array(close_arr[-ventana:])
        _rsi_ventana    = _np_div.array(_rsi_serie.values[-ventana:])

        # Encontrar los 2 mínimos más recientes en precio
        _min_idx = []
        for i in range(1, len(_precio_ventana)-1):
            if (_precio_ventana[i] < _precio_ventana[i-1] and
                _precio_ventana[i] < _precio_ventana[i+1]):
                _min_idx.append(i)

        if len(_min_idx) < 2:
            return {"tiene": False, "tipo": "none", "badge": "", "descripcion": ""}

        # Tomar los 2 mínimos más recientes
        _m1_idx, _m2_idx = _min_idx[-2], _min_idx[-1]
        _precio_m1 = _precio_ventana[_m1_idx]
        _precio_m2 = _precio_ventana[_m2_idx]
        _rsi_m1    = _rsi_ventana[_m1_idx]
        _rsi_m2    = _rsi_ventana[_m2_idx]

        # Divergencia alcista:
        # Precio m2 < precio m1 (nuevo mínimo de precio)
        # RSI m2 > RSI m1 (mínimo más ALTO de RSI)
        _precio_baja = _precio_m2 < _precio_m1 * 0.99  # al menos -1%
        _rsi_sube    = _rsi_m2 > _rsi_m1 + 2            # al menos +2 puntos

        if not (_precio_baja and _rsi_sube):
            return {"tiene": False, "tipo": "none", "badge": "", "descripcion": ""}

        # Clasificar intensidad
        _diff_rsi    = _rsi_m2 - _rsi_m1
        _diff_precio = (_precio_m1 - _precio_m2) / _precio_m1 * 100

        if _diff_rsi >= 8 and _diff_precio >= 5:
            _tipo = "fuerte"
            _badge = (
                '<span style="background:#FEF3C7;color:#92400E;border:1px solid #FDE68A;'
                'border-radius:4px;padding:1px 7px;font-size:9px;font-weight:800;'
                'margin-left:5px">📈 DIV ALCISTA FUERTE</span>'
            )
            _desc = f"Precio -${_diff_precio:.1f}% · RSI +{_diff_rsi:.0f}pts → momentum bajista agotándose"
        elif _diff_rsi >= 4:
            _tipo = "moderada"
            _badge = (
                '<span style="background:#ECFDF5;color:#065F46;border:1px solid #6EE7B7;'
                'border-radius:4px;padding:1px 7px;font-size:9px;font-weight:700;'
                'margin-left:5px">📈 DIV ALCISTA</span>'
            )
            _desc = f"Precio -${_diff_precio:.1f}% · RSI +{_diff_rsi:.0f}pts → señal de suelo"
        else:
            return {"tiene": False, "tipo": "none", "badge": "", "descripcion": ""}

        return {
            "tiene":       True,
            "tipo":        _tipo,
            "badge":       _badge,
            "descripcion": _desc,
            "diff_rsi":    round(_diff_rsi, 1),
            "diff_precio": round(_diff_precio, 1),
        }

    except Exception:
        return {"tiene": False, "tipo": "none", "badge": "", "descripcion": ""}



# ══ SISTEMA DE VIGENCIA DE SEÑALES v19.2 ══════════════════════════════════

def calcular_vigencia(fecha_entrada_str: str, fecha_cambio_str: str,
                      tipo_senal: str, fase: str, pnl_pct: float) -> dict:
    """
    v19.2: Calcula el estado de vigencia de una posición en Greko.
    Plazos: M2/Momentum=5 días · M3 NBIS=14 días · Runner (P&L>T1)=∞
    """
    import datetime as _dv
    _hoy = _dv.date.today()
    _resultado = {
        "estado": "VIGENTE", "dias": 0, "plazo": 5,
        "dias_restantes": 5, "vencida": False, "badge_html": "",
        "es_runner": False,
    }
    try:
        # Parsear fecha base (cambio de fase si existe, sino entrada)
        _fecha_base = None
        for _fs in [fecha_cambio_str, fecha_entrada_str]:
            if _fs and str(_fs).strip() not in ("-","","nan","None","NaT"):
                for _fmt in ("%d-%m-%Y","%Y-%m-%d","%d/%m/%Y","%Y/%m/%d"):
                    try:
                        _fecha_base = _dv.datetime.strptime(str(_fs)[:10], _fmt).date()
                        break
                    except Exception: pass
            if _fecha_base: break
        if not _fecha_base:
            return _resultado

        _dias = (_hoy - _fecha_base).days
        _resultado["dias"] = _dias

        # T1 runners (no vencen)
        _t1_nbis = 8.0
        _t1_mom  = 15.0
        _es_mom  = "MOMENTUM" in str(tipo_senal).upper()
        _t1      = _t1_mom if _es_mom else _t1_nbis
        if pnl_pct >= _t1:
            _resultado["estado"]     = "RUNNER"
            _resultado["es_runner"]  = True
            _resultado["badge_html"] = (
                f'<span style="background:#EFF6FF;color:#2563EB;border:1px solid #93C5FD;'
                f'border-radius:4px;padding:2px 8px;font-size:9px;font-weight:700;margin-left:5px">'
                f'🚀 Runner +{pnl_pct:.1f}% · sin vencimiento</span>')
            return _resultado

        # Plazo según tipo y fase
        _fase_up = str(fase).upper()
        _es_m3   = any(x in _fase_up for x in ["M3","FASE 3","FASE3","ENTRAR HOY","RUPTURA"])
        if _es_mom:
            _plazo = 5   # Momentum: 5 días (funciona desde día 1)
        elif _es_m3:
            _plazo = 14  # M3 NBIS: 14 días
        else:
            _plazo = 10  # M2 NBIS: 10 días (datos reales: confirma en 6-20 días)

        _resultado["plazo"]          = _plazo
        _resultado["dias_restantes"] = _plazo - _dias
        _resultado["vencida"]        = _dias > _plazo

        if _dias > _plazo:
            _exceso = _dias - _plazo
            _resultado["estado"] = "VENCIDA"
            _resultado["badge_html"] = (
                f'<span style="background:#FEF2F2;color:#DC2626;border:1px solid #FECACA;'
                f'border-radius:4px;padding:2px 8px;font-size:9px;font-weight:800;margin-left:5px">'
                f'🔴 VENCIDA · día {_dias}/{_plazo} · hace {_exceso}d</span>')
        elif _plazo - _dias <= 1:
            _resultado["estado"] = "VENCE_MANANA"
            _resultado["badge_html"] = (
                f'<span style="background:#FFF7ED;color:#EA580C;border:1px solid #FDBA74;'
                f'border-radius:4px;padding:2px 8px;font-size:9px;font-weight:800;margin-left:5px">'
                f'⚠️ Vence MAÑANA · día {_dias}/{_plazo}</span>')
        elif _plazo - _dias <= 2:
            _resultado["estado"] = "VENCE_PRONTO"
            _resultado["badge_html"] = (
                f'<span style="background:#FFFBEB;color:#D97706;border:1px solid #FDE68A;'
                f'border-radius:4px;padding:2px 8px;font-size:9px;font-weight:700;margin-left:5px">'
                f'⚠️ Vence en 2 días · {_dias}/{_plazo}</span>')
        else:
            _resultado["estado"] = "VIGENTE"
            _resultado["badge_html"] = (
                f'<span style="background:#F0FDF4;color:#16A34A;border:1px solid #86EFAC;'
                f'border-radius:4px;padding:2px 8px;font-size:9px;font-weight:600;margin-left:5px">'
                f'📅 Día {_dias}/{_plazo} · {_plazo-_dias}d restantes</span>')
    except Exception:
        pass
    return _resultado


def actualizar_fase_en_sheet(sheet_name: str, ticker: str,
                              nueva_fase: str, fecha_cambio: str) -> tuple:
    """
    v19.3: Escribe directamente columna F (Fase) y AB (Fecha_Cambio_Fase)
    en el Sheet usando batchUpdate por celda exacta.
    Sin silenciar errores — retorna mensaje detallado.
    """
    try:
        svc = _get_sheets_service()
        if not svc:
            return False, "Sin servicio Google Sheets"

        sheet_id = _get_sheet_id_from_secrets("posiciones_greko_id")
        if not sheet_id and sheet_name == _SHEET_NAME_GREKO:
            sheet_id = _get_sheet_id_from_secrets("posiciones_greko_id")
        if not sheet_id:
            sheet_id = _buscar_sheet_id(sheet_name)
        if not sheet_id:
            return False, f"ID no encontrado para '{sheet_name}'"

        # Obtener nombre real de la hoja (Hoja 1 / Sheet1)
        try:
            _meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
            _hoja = _meta["sheets"][0]["properties"]["title"]
        except Exception as _em:
            _hoja = "Hoja 1"

        # Leer columnas A y O para encontrar la fila correcta
        _raw = svc.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{_hoja}'!A:O"
        ).execute()
        _rows = _raw.get("values", [])
        if not _rows:
            return False, "Sheet vacío"

        _headers = [str(h).strip() for h in _rows[0]]

        # Encontrar índices de columnas por nombre
        def _ci(name, default):
            try: return _headers.index(name)
            except ValueError: return default

        _idx_ticker   = _ci("Ticker", 0)
        _idx_f_salida = _ci("Fecha_Salida", 14)
        _idx_f_ent    = _ci("Fecha_Entrada", 3)

        # Buscar fila activa más reciente del ticker
        _tk_upper = ticker.upper().strip()
        _best_row = None
        _best_ent = ""

        for _r_i, _row in enumerate(_rows[1:], 2):
            if len(_row) <= _idx_ticker:
                continue
            if str(_row[_idx_ticker]).upper().strip() != _tk_upper:
                continue
            _fs = str(_row[_idx_f_salida]).strip() if len(_row) > _idx_f_salida else ""
            if _fs and _fs not in ("-","","nan","None","NaT"):
                continue  # cerrada
            _fe = str(_row[_idx_f_ent]).strip() if len(_row) > _idx_f_ent else ""
            if _best_row is None or _fe > _best_ent:
                _best_row = _r_i
                _best_ent = _fe

        if _best_row is None:
            return False, f"No hay posición activa de {ticker}"

        # Columna F = índice 5 (siempre existe)
        # Columna AB = índice 27 (puede no existir)
        _updates = [
            {
                "range": f"'{_hoja}'!F{_best_row}",
                "values": [[nueva_fase]]
            }
        ]

        # Solo escribir AB si el header existe
        if "Fecha_Cambio_Fase" in _headers:
            _updates.append({
                "range": f"'{_hoja}'!AB{_best_row}",
                "values": [[fecha_cambio]]
            })

        _result = svc.spreadsheets().values().batchUpdate(
            spreadsheetId=sheet_id,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": _updates
            }
        ).execute()

        _cells = _result.get("totalUpdatedCells", 0)
        if _cells == 0:
            return False, f"batchUpdate OK pero 0 celdas actualizadas (fila {_best_row})"

        # Limpiar caché
        try: leer_posiciones_sheets.clear()
        except Exception: pass

        return True, f"✅ Fila {_best_row} col F={nueva_fase} ({_cells} celdas)"

    except Exception as _e:
        return False, f"Error: {str(_e)[:80]}"


    except Exception as _e:
        return False, f"Error actualizando fase: {str(_e)[:80]}"


def cerrar_vencidas_greko(sheet_name: str = None) -> tuple:
    """
    v19.2: Cierra todas las posiciones vencidas en Greko (paper).
    - Solo Greko (nunca MVALLE ni Amparito automáticamente)
    - Solo P&L < T1 (no toca runners)
    - Escribe: Precio_Salida, Fecha_Salida, Fue_Correcto, Razon_Salida, Error_Modelo, Notas
    """
    import datetime as _dc
    import yfinance as _yf_cv

    _sheet = sheet_name or _SHEET_NAME_GREKO
    _hoy   = _dc.date.today().strftime("%d-%m-%Y")

    try:
        _df = leer_posiciones_sheets(_sheet)
        if _df is None or _df.empty:
            return False, "Sheet vacío"

        _mask_act = _df.get("Fecha_Salida", pd.Series(dtype=str)).astype(str).apply(
            lambda v: v.strip() in ("-","","nan","None","NaT"))
        _df_act = _df[_mask_act].copy()

        if _df_act.empty:
            return True, "No hay posiciones activas"

        # Obtener precios actuales en batch
        _tickers_cv = [str(r.get("Ticker","")).upper().strip()
                       for _, r in _df_act.iterrows()
                       if str(r.get("Ticker","")).strip()]
        _precios_cv = {}
        try:
            _dl_cv = _yf_cv.download(" ".join(_tickers_cv), period="5d",
                                      auto_adjust=True, progress=False, threads=True)
            _cl_cv = _dl_cv.get("Close", _dl_cv)
            for _tk_cv in _tickers_cv:
                try:
                    _s_cv = (_cl_cv[_tk_cv].dropna()
                             if hasattr(_cl_cv,"columns") and _tk_cv in _cl_cv.columns
                             else _cl_cv.dropna())
                    _precios_cv[_tk_cv] = round(float(_s_cv.iloc[-1]), 2)
                except Exception: pass
        except Exception: pass

        _cerradas = []
        _n_cerradas = 0

        for _idx_cv, _row_cv in _df_act.iterrows():
            _tk_cv   = str(_row_cv.get("Ticker","")).upper().strip()
            _fase_cv = str(_row_cv.get("Fase","-"))
            _tipo_cv = str(_row_cv.get("Tipo_Señal", _row_cv.get("Tipo_Senal","NBIS")))
            _pc_cv   = float(str(_row_cv.get("Precio_Compra","0") or "0").replace(",","."))
            _fe_cv   = str(_row_cv.get("Fecha_Entrada","-"))
            _fch_cv  = str(_row_cv.get("Fecha_Cambio_Fase","-") or "-")

            # Calcular vigencia
            _pa_cv  = _precios_cv.get(_tk_cv, 0)
            _pnl_cv = round((_pa_cv - _pc_cv) / _pc_cv * 100, 2) if _pc_cv > 0 and _pa_cv > 0 else 0
            _vig    = calcular_vigencia(_fe_cv, _fch_cv, _tipo_cv, _fase_cv, _pnl_cv)

            if not _vig["vencida"]:
                continue  # No vencida → no cerrar

            # Construir valores de cierre
            # P: Fue_Correcto (Opción A)
            if _pnl_cv > 3:
                _fue_correcto = f"✅ Ganó (+{_pnl_cv:.1f}%)"
            elif _pnl_cv < -3:
                _fue_correcto = f"❌ Perdió ({_pnl_cv:.1f}%)"
            else:
                _fue_correcto = f"⏱️ Sin movimiento ({_pnl_cv:+.1f}%)"

            # Q: Razon_Salida
            _razon = f"Expiración señal {_fase_cv} · día {_vig['dias']} de {_vig['plazo']}"

            # R: Error_Modelo
            _fase_up_cv = _fase_cv.upper()
            if any(x in _fase_up_cv for x in ["M2","FASE 2"]):
                _error = "M2 no confirmó transición a M3 en plazo"
            elif any(x in _fase_up_cv for x in ["M3","FASE 3","ENTRAR"]):
                _error = "M3 no activó catalizador en 14 días"
            else:
                _error = "Señal no confirmada en plazo"

            # S: Notas
            _notas = f"Cerrada automáticamente · Entrada ${_pc_cv} · Salida ${_pa_cv}"

            # Actualizar el DataFrame
            _df.at[_idx_cv, "Precio_Salida"] = str(_pa_cv) if _pa_cv > 0 else "-"
            _df.at[_idx_cv, "Fecha_Salida"]  = _hoy
            _df.at[_idx_cv, "Fue_Correcto"]  = _fue_correcto
            _df.at[_idx_cv, "Razon_Salida"]  = _razon
            _df.at[_idx_cv, "Error_Modelo"]  = _error
            _df.at[_idx_cv, "Notas"]         = _notas

            _cerradas.append(f"{_tk_cv} ({_pnl_cv:+.1f}%)")
            _n_cerradas += 1

        if _n_cerradas == 0:
            return True, "No hay posiciones vencidas para cerrar"

        # Guardar el DataFrame actualizado
        ok, msg = guardar_posicion_sheets(_sheet, _df)
        if ok:
            _resumen = f"✅ Cerradas {_n_cerradas} posiciones: {', '.join(_cerradas)}"
            return True, _resumen
        return False, msg

    except Exception as _e:
        return False, f"Error: {str(_e)[:80]}"


def badge_recomendacion_momentum(score: int, rsi: float,
                                  n_analistas: int, rev_yoy_str: str,
                                  upside_str: str, macd: str) -> dict:
    """
    v19.2: Badge de recomendación para señales Momentum.
    Clasifica si una señal vale la pena registrar en Greko.
    Returns: {nivel, badge_html, btn_tipo, btn_label}
    """
    try:
        _rev  = float(str(rev_yoy_str).replace("+","").replace("%","") or 0)
        _up   = float(str(upside_str).replace("+","").replace("%","") or 0)
        _rsi  = float(rsi or 0)
        _sc   = int(score or 0)
        _an   = int(n_analistas or 0)
        _macd = str(macd or "-")

        # Criterios óptimos
        _c_score   = _sc >= 70
        _c_rsi     = 65 <= _rsi <= 82
        _c_an      = _an >= 5
        _c_rev     = _rev >= 15
        _c_up      = _up >= 10
        _c_macd    = _macd in ("+","✅")
        _n_cumple  = sum([_c_score, _c_rsi, _c_an, _c_rev, _c_up, _c_macd])

        if _sc >= 70 and _c_rsi and _c_an and _c_rev and _c_up and _c_macd:
            # REGISTRAR — cumple todos los criterios
            return {
                "nivel": "REGISTRAR",
                "badge_html": (
                    '<span style="background:#DCFCE7;color:#15803D;border:1px solid #86EFAC;'
                    'border-radius:4px;padding:2px 8px;font-size:9px;font-weight:800">'
                    '🟢 REGISTRAR</span>'),
                "btn_tipo": "primary",
                "btn_label": "🦅 Registrar señal fuerte",
                "motivo": f"Score {_sc} · RSI {_rsi:.0f} · {_an} analistas · Rev+{_rev:.0f}%",
            }
        elif _sc >= 50 and _n_cumple >= 4:
            # EVALUAR — cumple la mayoría
            _faltan = []
            if not _c_score: _faltan.append(f"Score {_sc}<70")
            if not _c_rsi:   _faltan.append(f"RSI {_rsi:.0f}" + (">82 extendido" if _rsi>82 else "<65"))
            if not _c_an:    _faltan.append(f"Solo {_an} analistas")
            if not _c_rev:   _faltan.append(f"Rev +{_rev:.0f}%<15%")
            if not _c_up:    _faltan.append(f"Upside +{_up:.0f}%<10%")
            if not _c_macd:  _faltan.append("MACD negativo")
            return {
                "nivel": "EVALUAR",
                "badge_html": (
                    '<span style="background:#FEF9C3;color:#854D0E;border:1px solid #FDE68A;'
                    'border-radius:4px;padding:2px 8px;font-size:9px;font-weight:700">'
                    f'🟡 EVALUAR · falta: {", ".join(_faltan[:2])}</span>'),
                "btn_tipo": "secondary",
                "btn_label": "🦅 Registrar con precaución",
                "motivo": f"Cumple {_n_cumple}/6 criterios",
            }
        else:
            # OBSERVAR — señal débil
            return {
                "nivel": "OBSERVAR",
                "badge_html": (
                    '<span style="background:#F8FAFC;color:#64748B;border:1px solid #E2E8F0;'
                    'border-radius:4px;padding:2px 8px;font-size:9px;font-weight:600">'
                    f'⚪ OBSERVAR · {_n_cumple}/6 criterios</span>'),
                "btn_tipo": "secondary",
                "btn_label": "🦅 Registrar (señal débil)",
                "motivo": f"Score {_sc}/100 — {_n_cumple} de 6 criterios",
            }
    except Exception:
        return {"nivel":"EVALUAR","badge_html":"","btn_tipo":"secondary",
                "btn_label":"🦅 Agregar a Greko","motivo":""}



# ══ SISTEMA GTU — GrekoTrader Upside v1.0 ═══════════════════════════════════
# Basado en correlaciones reales de 104 posiciones (27-Abr→29-May-2026)
# Pesos iniciales: w1=0.45 RSI · w2=0.25 Prob · w3=0.15 Momentum · w4=0.10 Score
# Actualización manual cada 2 semanas con nuevos datos

_GTU_LOOKUP = {
    "EXT_82+":   {"p25":14.8, "p50":18.8, "p75":26.1, "wr":95, "n":21,
                  "label":"RSI 82+ · Ext momentum", "color":"#FBBF24"},
    "MOM_DD":    {"p25":13.7, "p50":23.7, "p75":38.9, "wr":100,"n":9,
                  "label":"RSI 65-82 + DD≥15%",      "color":"#10B981"},
    "MOM_CLEAN": {"p25":-0.8, "p50":0.7,  "p75":11.6, "wr":69, "n":13,
                  "label":"RSI 65-82 sin DD",         "color":"#34D399"},
    "TRANS_DD":  {"p25":3.6,  "p50":6.1,  "p75":13.0, "wr":80, "n":10,
                  "label":"RSI 55-65 + DD≥25%",       "color":"#60A5FA"},
    "TRANS":     {"p25":-6.6, "p50":-2.6, "p75":5.6,  "wr":35, "n":17,
                  "label":"RSI 55-65 sin DD",          "color":"#F59E0B"},
    "NBIS":      {"p25":-7.8, "p50":-1.2, "p75":2.4,  "wr":41, "n":17,
                  "label":"RSI 40-55 · NBIS clásico",  "color":"#F87171"},
    "NBIS_PROF": {"p25":-5.3, "p50":-3.6, "p75":-2.1, "wr":15, "n":13,
                  "label":"RSI 40-55 + DD≥30%",        "color":"#EF4444"},
    "OVERSOLD":  {"p25":-14.2,"p50":-9.4, "p75":-3.3, "wr":25, "n":4,
                  "label":"RSI <40 · oversold",        "color":"#DC2626"},
}

_GTU_WEIGHTS = {
    "w1_rsi": 0.45, "w2_prob": 0.25, "w3_momentum": 0.15,
    "w4_score": 0.10, "w5_dd_rsi": 0.03, "w6_earnings": 0.02,
    "version": "1.0", "n_actualizaciones": 0
}


def _gtu_get_perfil(rsi: float, dd_abs: float, prob: float) -> str:
    """Clasifica la señal en perfil histórico para lookup de rango."""
    if rsi >= 82:         return "EXT_82+"
    elif rsi >= 65:
        if dd_abs >= 15:  return "MOM_DD"
        else:             return "MOM_CLEAN"
    elif rsi >= 55:
        if dd_abs >= 25:  return "TRANS_DD"
        else:             return "TRANS"
    elif rsi >= 40:
        if dd_abs >= 30:  return "NBIS_PROF"
        else:             return "NBIS"
    else:                 return "OVERSOLD"


def calcular_gtu(rsi: float, prob_nbis: float, score_mvalle: int,
                 dd_abs: float, earnings_flag: int = 0) -> dict:
    """
    GrekoTrader Upside Formula v1.0
    Basada en correlaciones de 104 posiciones reales.
    Pesos fijos — ajustar manualmente cada 2 semanas.
    
    Returns: dict con gtu_score (0-100), nivel (1-4), perfil, rango, rango_hist, color
    """
    W = _GTU_WEIGHTS

    # ── Componentes ────────────────────────────────────────────
    rsi_pts   = (rsi / 100) * 40                        # 0-40pts
    prob_pts  = (prob_nbis / 100) * 25                  # 0-25pts
    mom_pts   = 15.0 if rsi >= 65 else 0.0              # 0 o 15pts
    sc_pts    = (min(score_mvalle, 20) / 20.0) * 10.0   # 0-10pts
    ddrsi_pts = (dd_abs * min(rsi, 82) / 10000.0) * 5.0 # interaction capped
    earn_pts  = float(earnings_flag) * 5.0              # 0-5pts

    raw = (W["w1_rsi"]      * rsi_pts  +
           W["w2_prob"]     * prob_pts +
           W["w3_momentum"] * mom_pts  +
           W["w4_score"]    * sc_pts   +
           W["w5_dd_rsi"]   * ddrsi_pts+
           W["w6_earnings"] * earn_pts)

    max_posible = (W["w1_rsi"]*40 + W["w2_prob"]*25 + W["w3_momentum"]*15 +
                   W["w4_score"]*10 + W["w5_dd_rsi"]*5 + W["w6_earnings"]*5)
    gtu = round((raw / max_posible) * 100, 1) if max_posible > 0 else 0.0

    # ── Nivel GTU ────────────────────────────────────────────────
    if gtu >= 70:  nivel=4; gtu_rango="+40-80%"; gtu_emoji="🔥"; gtu_color="#FBBF24"
    elif gtu >= 55:nivel=3; gtu_rango="+20-50%"; gtu_emoji="🟢"; gtu_color="#10B981"
    elif gtu >= 40:nivel=2; gtu_rango="+10-25%"; gtu_emoji="🟡"; gtu_color="#F59E0B"
    else:          nivel=1; gtu_rango="+5-15%";  gtu_emoji="⚪"; gtu_color="#94A3B8"

    # ── Rango histórico ────────────────────────────────────────
    perfil    = _gtu_get_perfil(rsi, dd_abs, prob_nbis)
    hist      = _GTU_LOOKUP.get(perfil, {})
    rh_p25    = hist.get("p25", 0)
    rh_p50    = hist.get("p50", 0)
    rh_p75    = hist.get("p75", 0)
    rh_wr     = hist.get("wr",  0)
    rh_n      = hist.get("n",   0)
    rh_label  = hist.get("label", perfil)
    rh_color  = hist.get("color","#64748B")

    if rh_p50 > 20: rh_emoji = "🔥"
    elif rh_p50 > 8: rh_emoji = "🟢"
    elif rh_p50 > 0: rh_emoji = "🟡"
    else:            rh_emoji = "🔴"

    return {
        "gtu":        gtu,
        "nivel":      nivel,
        "rango":      gtu_rango,
        "emoji":      gtu_emoji,
        "color":      gtu_color,
        "componentes": {
            "RSI":      round(rsi_pts * W["w1_rsi"], 1),
            "Prob":     round(prob_pts * W["w2_prob"], 1),
            "Momentum": round(mom_pts * W["w3_momentum"], 1),
            "Score":    round(sc_pts * W["w4_score"], 1),
            "DD_RSI":   round(ddrsi_pts * W["w5_dd_rsi"], 1),
            "Earnings": round(earn_pts * W["w6_earnings"], 1),
        },
        "perfil":     perfil,
        "rh_perfil_label": rh_label,
        "rh_p25":     rh_p25,
        "rh_p50":     rh_p50,
        "rh_p75":     rh_p75,
        "rh_wr":      rh_wr,
        "rh_n":       rh_n,
        "rh_emoji":   rh_emoji,
        "rh_color":   rh_color,
    }



def actualizar_todas_fases_batch(sheet_names: list) -> tuple:
    """
    v19.3 OPCIÓN B — Recorre TODAS las posiciones activas de los Sheets indicados.
    Calcula Fase live para cada ticker con yf.download BATCH (1 sola llamada).
    Escribe F + AB en un solo batchUpdate por Sheet.
    
    NO modifica X (RSI_Accion), Y (MACD_Estado), Z (DD_Pico_Pct) — son historia.
    
    Criterios de Fase live:
      M3:       RSI 48-65 + DD ≤-15% + MACD+
      M2:       RSI 40-65 + DD ≤-10%
      Momentum: RSI > 65
      M1:       resto (señal debilitada)
    
    Retorna: (ok, mensaje_resumen)
    """
    import datetime as _dtb
    import yfinance as _yf_batch_fase

    _hoy_str  = _dtb.date.today().strftime("%d-%m-%Y")
    _resumen  = []
    _total_ok = 0
    _total_err= 0

    for _sn in sheet_names:
        try:
            # ── PASO 1: Leer Sheet completo (1 llamada) ──────────
            svc = _get_sheets_service()
            if not svc:
                _resumen.append(f"❌ {_sn}: Sin servicio Sheets")
                continue

            _secret_key = ("posiciones_greko_id" if "Greko" in _sn
                           else "posiciones_mauri_id" if "Mauri" in _sn
                           else "posiciones_amparito_id")
            sheet_id = _get_sheet_id_from_secrets(_secret_key)
            if not sheet_id:
                sheet_id = _buscar_sheet_id(_sn)
            if not sheet_id:
                _resumen.append(f"❌ {_sn}: ID no encontrado")
                continue

            _meta  = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
            _hoja  = _meta["sheets"][0]["properties"]["title"]
            _raw   = svc.spreadsheets().values().get(
                spreadsheetId=sheet_id, range=f"'{_hoja}'!A:AB").execute()
            _rows  = _raw.get("values", [])
            if not _rows:
                _resumen.append(f"⚠️ {_sn}: Sheet vacío")
                continue

            _headers = [str(h).strip() for h in _rows[0]]
            def _ci(name, default):
                try: return _headers.index(name)
                except ValueError: return default

            _idx_tk  = _ci("Ticker", 0)
            _idx_fs  = _ci("Fecha_Salida", 14)
            _idx_fe  = _ci("Fecha_Entrada", 3)
            _idx_f   = _ci("Fase", 5)          # columna F
            _idx_ab  = _ci("Fecha_Cambio_Fase", 27)  # columna AB

            # ── Recopilar tickers activos ─────────────────────────
            _activos = []  # [(row_number_1based, ticker, fase_actual)]
            for _ri, _row in enumerate(_rows[1:], 2):
                if len(_row) <= _idx_tk: continue
                _tk = str(_row[_idx_tk]).upper().strip()
                if not _tk or _tk in ("-","", "TICKER"): continue
                _fs = str(_row[_idx_fs]).strip() if len(_row) > _idx_fs else ""
                if _fs and _fs not in ("-","","nan","None","NaT"): continue  # cerrada
                _fase_actual = str(_row[_idx_f]).strip() if len(_row) > _idx_f else "-"
                _activos.append((_ri, _tk, _fase_actual))

            if not _activos:
                _resumen.append(f"ℹ️ {_sn}: Sin posiciones activas")
                continue

            # ── PASO 2: yf.download BATCH (1 sola llamada) ───────
            _tks_uniq = list(set([a[1] for a in _activos]))
            _live = {}
            try:
                _dl = _yf_batch_fase.download(
                    " ".join(_tks_uniq), period="3mo",
                    auto_adjust=True, progress=False, threads=True)
                _cl = _dl.get("Close", _dl)
                for _tk_b in _tks_uniq:
                    try:
                        _s = (_cl[_tk_b].dropna()
                              if hasattr(_cl,"columns") and _tk_b in _cl.columns
                              else _cl.dropna())
                        if len(_s) < 20: continue
                        _pa     = float(_s.iloc[-1])
                        _pico   = float(_s.rolling(60, min_periods=1).max().iloc[-1])
                        _dd     = round((_pa-_pico)/_pico*100,1) if _pico>0 else 0
                        _d      = _s.diff()
                        _g      = _d.clip(lower=0).rolling(14).mean()
                        _lo     = (-_d.clip(upper=0)).rolling(14).mean()
                        _rsi    = round(float(100-100/(1+_g.iloc[-1]/(_lo.iloc[-1]+1e-9))),1)
                        _macd   = "+" if _s.ewm(span=12).mean().iloc[-1] > _s.ewm(span=26).mean().iloc[-1] else "-"
                        _live[_tk_b] = {"rsi":_rsi, "macd":_macd, "dd":_dd}
                    except Exception: pass
            except Exception as _edl:
                _resumen.append(f"❌ {_sn}: Error download — {str(_edl)[:40]}")
                continue

            # ── PASO 3: Calcular Fase live para cada posición ────
            _updates_data = []
            _cambios      = 0
            _sin_cambio   = 0

            for _row_n, _tk_a, _fase_ant in _activos:
                _ld = _live.get(_tk_a, {})
                if not _ld:
                    _sin_cambio += 1
                    continue

                _rsi_l  = _ld["rsi"]
                _macd_l = _ld["macd"]
                _dd_l   = _ld["dd"]
                _dd_abs = abs(_dd_l)

                # Criterios de Fase live
                if 48 <= _rsi_l <= 65 and _dd_l <= -15 and _macd_l == "+":
                    _fase_nueva = "M3"
                elif 40 <= _rsi_l <= 65 and _dd_l <= -10:
                    _fase_nueva = "M2"
                elif _rsi_l > 65:
                    _fase_nueva = "Momentum"
                else:
                    _fase_nueva = "M1"

                # Preparar update para columna F (siempre)
                _updates_data.append({
                    "range": f"'{_hoja}'!F{_row_n}",
                    "values": [[_fase_nueva]]
                })

                # Columna AB: solo si cambió la fase
                _fase_ant_up = _fase_ant.upper()
                _fase_nueva_up = _fase_nueva.upper()
                _cambio_detectado = (
                    _fase_ant_up != _fase_nueva_up and
                    not (_fase_ant_up in ("M3","FASE 3","FASE3","ENTRAR") and _fase_nueva_up == "M3") and
                    not (_fase_ant_up in ("M2","FASE 2","FASE2","ENTRADA") and _fase_nueva_up == "M2")
                )
                if _cambio_detectado:
                    _updates_data.append({
                        "range": f"'{_hoja}'!AB{_row_n}",
                        "values": [[_hoy_str]]
                    })
                    _cambios += 1
                else:
                    _sin_cambio += 1

            # ── PASO 4: batchUpdate (1 sola llamada API) ─────────
            if _updates_data:
                _result = svc.spreadsheets().values().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={"valueInputOption":"USER_ENTERED","data":_updates_data}
                ).execute()
                _celdas = _result.get("totalUpdatedCells", 0)
                _resumen.append(
                    f"✅ {_sn}: {len(_activos)} activas · "
                    f"{_cambios} fases cambiaron · {_sin_cambio} sin cambio · "
                    f"{_celdas} celdas escritas"
                )
                _total_ok += 1
            else:
                _resumen.append(f"ℹ️ {_sn}: Sin datos live para actualizar")

            # Limpiar caché
            try: leer_posiciones_sheets.clear()
            except Exception: pass

        except Exception as _e_sheet:
            _resumen.append(f"❌ {_sn}: {str(_e_sheet)[:60]}")
            _total_err += 1

    # Limpiar caché Score MVALLE
    import streamlit as _st_c
    _st_c.session_state.pop("_score_rows_base", None)
    _st_c.session_state.pop("_greko_processed_df", None)
    _st_c.session_state.pop("_mv_processed_df", None)

    _ok_global = _total_err == 0
    _msg = " | ".join(_resumen) if _resumen else "Sin resultados"
    return _ok_global, _msg

def badge_castigada(rsi: float, dd_pico: float,
                    upside: float = 0, revenue_yoy: float = 0) -> str:
    """
    v19.1: Badge visual 'CASTIGADA' — acción sobrevendida vs fundamentos.
    No requiere columnas nuevas en Google Sheets — solo datos ya disponibles.

    Niveles:
      💥 FUERTE: RSI<55 + DD<-25% + upside>30% (o revenue>0)
      ⚠️ MODERADO: RSI<62 + DD<-20%
    """
    try:
        rsi     = float(rsi or 0)
        dd      = float(dd_pico or 0)
        upside  = float(upside or 0)
        rev     = float(revenue_yoy or 0)
    except Exception:
        return ""

    # Sin corrección real → no aplica
    if dd > -10 or rsi <= 0:
        return ""

    # Nivel FUERTE — castigo excesivo vs fundamentos
    if rsi < 55 and dd <= -25 and (upside >= 30 or rev > 0):
        return (
            '<span style="background:#FEF3C7;color:#D97706;border:1px solid #FDE68A;'
            'border-radius:4px;padding:1px 7px;font-size:9px;font-weight:800;'
            'margin-left:5px">💥 CASTIGADA</span>'
        )
    # Nivel MODERADO — corrección técnica profunda
    elif rsi < 62 and dd <= -20:
        return (
            '<span style="background:#FFF7ED;color:#EA580C;border:1px solid #FDBA74;'
            'border-radius:4px;padding:1px 7px;font-size:9px;font-weight:700;'
            'margin-left:5px">⚠️ CASTIGADA</span>'
        )
    return ""


def render_sma_badge(ticker: str, precio_actual: float = 0,
                      TXT_MUT: str = "") -> str:
    """v19: Badge HTML de SMA 50/200."""
    sma = get_sma_status(ticker)
    if not sma["ok"]:
        return ""

    _pa = precio_actual if precio_actual > 0 else sma["precio"]
    _vs50  = round((_pa - sma["sma50"]) / sma["sma50"] * 100, 1) if sma["sma50"] > 0 else 0
    _vs200 = round((_pa - sma["sma200"]) / sma["sma200"] * 100, 1) if sma["sma200"] > 0 else 0

    if sma["nivel"] == "bajo_ambas":
        _c = "#16A34A"; _bg = "#F0FDF4"; _emoji = "📉"
        _msg = f"Bajo SMA50 ({_vs50:+.0f}%) y SMA200 ({_vs200:+.0f}%) · Precio muy descontado"
    elif sma["nivel"] == "bajo_sma50":
        _c = "#2563EB"; _bg = "#EFF6FF"; _emoji = "📊"
        _msg = f"Bajo SMA50 ({_vs50:+.0f}%) · Precio descontado vs promedio 50d"
    elif sma["nivel"] == "sobre_ambas":
        _c = "#D97706"; _bg = "#FFFBEB"; _emoji = "📈"
        _msg = f"Sobre SMA50 ({_vs50:+.0f}%) y SMA200 ({_vs200:+.0f}%) · Precio alto vs promedios"
    else:
        _c = "#64748B"; _bg = "#F8FAFC"; _emoji = "📊"
        _msg = f"SMA50 ({_vs50:+.0f}%) · SMA200 ({_vs200:+.0f}%) · Zona neutral"

    return (
        f'<div style="background:{_bg};border-left:2px solid {_c};'
        f'border-radius:0 6px 6px 0;padding:4px 10px;margin-top:3px;'
        f'font-size:9px;color:{_c};font-weight:600">'
        f'{_emoji} {_msg}</div>'
    )

def get_sector_from_raw(ticker: str) -> str:
    """v19: Obtiene el sector de un ticker desde RAW universe."""
    _tk = str(ticker).upper().strip()
    for _r in RAW:
        if isinstance(_r, tuple) and len(_r) > 2:
            if str(_r[0]).upper().strip() == _tk:
                return _normalizar_sector(str(_r[2]))
    return "Sin sector"

def sector_en_watchlist(ticker: str) -> bool:
    """v19: Verifica si el ticker está en el Watchlist Sheet cargado."""
    try:
        _wl = st.session_state.get("wl_res_df")
        if _wl is not None and not _wl.empty and "Ticker" in _wl.columns:
            return str(ticker).upper() in _wl["Ticker"].str.upper().values
    except Exception:
        pass
    return False

def render_earn_news_card(
    ticker: str,
    cat_fecha: str,
    G: str, R: str, A: str,
    TXT_MUT: str, BOR: str,
) -> str:
    """
    v19: Renderiza earnings próximos + noticia top en un card compacto.
    Usado en Watchlist, Greko, MVALLE y Amparito para uniformidad.
    """
    import datetime as _dt_en
    partes = []

    # ── Earnings badge con ventana pre-earnings v19 ───────────
    if cat_fecha not in ("-","","nan","NaT"):
        try:
            _dias = (_dt_en.date.fromisoformat(str(cat_fecha)[:10])
                     - _dt_en.date.today()).days
            if _dias < 0 and _dias >= -3:
                partes.append(
                    f'<span style="background:#FEF2F2;color:#DC2626;'
                    f'border-radius:4px;padding:2px 8px;font-size:10px;font-weight:700">'
                    f'⚠️ Earnings hace {abs(_dias)}d — catalizador consumido</span>')
            elif 0 <= _dias <= 2:
                partes.append(
                    f'<span style="background:#FEF2F2;color:#DC2626;'
                    f'border-radius:4px;padding:2px 8px;font-size:10px;font-weight:700">'
                    f'🚨 Earnings {"HOY" if _dias == 0 else f"en {_dias}d"} — NO entrar, riesgo binario</span>')
            elif 3 <= _dias <= 5:
                # v19 MEJORA 2: ventana pre-earnings (2-5 días antes)
                partes.append(
                    f'<span style="background:#F0FDF4;color:#16A34A;'
                    f'border-radius:4px;padding:2px 8px;font-size:10px;font-weight:700">'
                    f'⚡ Earnings en {_dias}d — VENTANA PRE-EARNINGS</span>')
                partes.append(
                    f'<span style="font-size:10px;color:#374151;'
                    f'background:#F0FDF4;border-radius:4px;padding:2px 8px">'
                    f'Si RSI 48-62 + Score 40+: entrada especulativa 50% posición · stop -5%</span>')
            elif 6 <= _dias <= 10:
                partes.append(
                    f'<span style="background:#FFFBEB;color:#D97706;'
                    f'border-radius:4px;padding:2px 8px;font-size:10px;font-weight:700">'
                    f'📅 Earnings en {_dias}d — preparar estrategia</span>')
            elif 11 <= _dias <= 21:
                partes.append(
                    f'<span style="background:#EFF6FF;color:#2563EB;'
                    f'border-radius:4px;padding:2px 8px;font-size:10px;font-weight:700">'
                    f'📅 Earnings en {_dias}d</span>')
        except Exception:
            pass

    # ── Noticia top ───────────────────────────────────────────
    _noticia = render_noticia_inline(ticker, G, R, A, TXT_MUT, BOR)
    if _noticia:
        partes.append(_noticia)

    if not partes:
        return ""

    return (
        f'<div style="margin-top:6px;display:flex;flex-direction:column;gap:4px">'
        + "".join(partes)
        + f'</div>'
    )


def render_resumen_sector(posiciones_lista: list, G: str, R: str, A: str,
                           TXT: str, TXT_MUT: str, BOR: str, BG_CARD: str, BG_HEAD: str):
    """
    v19: Tabla resumen por sector.
    Activas: usa precio live. Cerradas: usa Precio_Salida.
    P&L = (pa - pc) × qty_activa
    """
    if not posiciones_lista:
        return

    sectores = {}
    total_ganado = 0
    total_invertido = 0

    for pos in posiciones_lista:
        _tk    = str(pos.get("ticker","")).upper()
        _pc    = float(pos.get("pc", 0) or 0)
        _area  = str(pos.get("area",""))

        # v19 FIX D: cerradas usan Precio_Salida; activas usan precio live
        _ps    = float(pos.get("precio_salida", 0) or 0)
        _pa    = _ps if _ps > 0 else float(pos.get("pa", 0) or _pc)

        # v19 FIX B+C: usar Cantidad_Activa si existe
        _qty_act = float(pos.get("qty_activa", 0) or 0)
        _qty     = _qty_act if _qty_act > 0 else float(pos.get("qty", 1) or 1)

        _pnl_p = (_pa - _pc) / _pc * 100 if _pc > 0 else 0
        _area  = _normalizar_sector(_area) if _area and _area not in ("-","","nan")                  else get_sector_from_raw(_tk)

        # P&L $ = ganancia por acción × acciones activas
        _ganancia_x_acc = _pa - _pc
        _pnl_usd = _ganancia_x_acc * _qty if _pc > 0 and _pa > 0 else 0
        _inv_usd = _pc * _qty if _pc > 0 else 0

        if _area not in sectores:
            sectores[_area] = {"n": 0, "pnl_usd": 0, "inv_usd": 0,
                               "tickers": [], "pnl_pcts": []}
        sectores[_area]["n"]        += 1
        sectores[_area]["pnl_usd"]  += _pnl_usd
        sectores[_area]["inv_usd"]  += _inv_usd
        sectores[_area]["tickers"].append(_tk)
        sectores[_area]["pnl_pcts"].append(_pnl_p)
        total_ganado    += _pnl_usd
        total_invertido += _inv_usd

    if not sectores:
        return

    # Ordenar por P&L descendente
    sectores_sorted = sorted(
        sectores.items(),
        key=lambda x: x[1]["pnl_usd"], reverse=True)

    # Calcular P&L% total del portafolio
    total_pct = (total_ganado / total_invertido * 100) if total_invertido > 0 else 0

    # Renderizar tabla
    filas = ""
    for sec, datos in sectores_sorted:
        _n      = datos["n"]
        _pnl_u  = datos["pnl_usd"]
        _inv_u  = datos["inv_usd"]
        _pnl_p  = (_pnl_u / _inv_u * 100) if _inv_u > 0 else 0
        _tickers_str = ", ".join(datos["tickers"][:3])
        if len(datos["tickers"]) > 3:
            _tickers_str += f" +{len(datos['tickers'])-3}"

        _c = G if _pnl_u > 0 else R if _pnl_u < 0 else TXT_MUT
        _bg = "#F0FDF4" if _pnl_u > 0 else "#FEF2F2" if _pnl_u < 0 else BG_HEAD
        _estado = "🟢" if _pnl_p >= 10 else "🟡" if _pnl_p >= 0 else "🔴"
        _signo_u = "+" if _pnl_u >= 0 else ""
        _signo_p = "+" if _pnl_p >= 0 else ""

        filas += f"""
        <tr style="background:{_bg};border-bottom:1px solid {BOR}">
          <td style="padding:8px 12px;font-size:11px;font-weight:700">{sec}</td>
          <td style="padding:8px 12px;text-align:center;font-size:11px">{_n}</td>
          <td style="padding:8px 12px;font-size:10px;color:{TXT_MUT}">{_tickers_str}</td>
          <td style="padding:8px 12px;text-align:right;font-weight:700;color:{_c};font-size:12px">
            {_signo_u}${_pnl_u:,.0f}</td>
          <td style="padding:8px 12px;text-align:right;font-weight:700;color:{_c};font-size:12px">
            {_signo_p}{_pnl_p:.1f}%</td>
          <td style="padding:8px 12px;text-align:center">{_estado}</td>
        </tr>"""

    _tc = G if total_ganado > 0 else R if total_ganado < 0 else TXT
    _ts = "+" if total_ganado >= 0 else ""
    _tp = "+" if total_pct >= 0 else ""
    _n_total = sum(d["n"] for _, d in sectores_sorted)

    tabla_html = f"""
    <div style="margin-top:20px">
      <div style="font-size:13px;font-weight:800;color:{TXT};margin-bottom:8px">
        📊 Resumen por Sector</div>
      <div style="background:{BG_CARD};border:1px solid {BOR};border-radius:10px;overflow:hidden">
        <table style="width:100%;border-collapse:collapse;font-size:11px">
          <thead>
            <tr style="background:#1E3A5F">
              <th style="padding:8px 12px;text-align:left;color:white;font-size:11px">Sector</th>
              <th style="padding:8px 12px;text-align:center;color:white;font-size:11px">Acc.</th>
              <th style="padding:8px 12px;text-align:left;color:white;font-size:11px">Tickers</th>
              <th style="padding:8px 12px;text-align:right;color:white;font-size:11px">P&L $</th>
              <th style="padding:8px 12px;text-align:right;color:white;font-size:11px">P&L %</th>
              <th style="padding:8px 12px;text-align:center;color:white;font-size:11px">Estado</th>
            </tr>
          </thead>
          <tbody>{filas}</tbody>
          <tfoot>
            <tr style="background:{BG_HEAD};border-top:2px solid #1E3A5F;font-weight:800">
              <td style="padding:8px 12px;font-size:12px">TOTAL</td>
              <td style="padding:8px 12px;text-align:center;font-size:12px">{_n_total}</td>
              <td style="padding:8px 12px;font-size:10px;color:{TXT_MUT}">
                {len(sectores)} sectores</td>
              <td style="padding:8px 12px;text-align:right;font-weight:800;
                         color:{_tc};font-size:13px">{_ts}${total_ganado:,.0f}</td>
              <td style="padding:8px 12px;text-align:right;font-weight:800;
                         color:{_tc};font-size:13px">{_tp}{total_pct:.1f}%</td>
              <td style="padding:8px 12px;text-align:center">
                {"🟢" if total_pct >= 10 else "🟡" if total_pct >= 0 else "🔴"}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>"""

    st.markdown(tabla_html, unsafe_allow_html=True)



def actualizar_salida_sheet(
    sheet_name: str,
    ticker: str,
    precio_salida: float,
    cantidad_vendida: float,
    razon_salida: str = "T1 alcanzado",
    fue_correcto: str = "SÍ",
    error_modelo: str = "-",
    notas_extra: str = "",
    tipo_salida: str = "TOTAL",   # "TOTAL" o "PARCIAL"
) -> tuple:
    """
    v19: Actualiza la fila EXISTENTE con datos de salida.
    TOTAL  → llena Fecha_Salida, Cantidad_Activa=0 (posición cerrada)
    PARCIAL → NO llena Fecha_Salida, actualiza Cantidad_Activa (runner)
    """
    import datetime as _dts
    try:
        svc = _get_sheets_service()
        if not svc:
            return False, "Sheets no configurado"
        sheet_id = _buscar_sheet_id(sheet_name)
        if not sheet_id:
            return False, f"Sheet no encontrado"

        meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
        hoja = meta["sheets"][0]["properties"]["title"]

        resp = svc.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"'{hoja}'!A1:Z1000",
        ).execute()
        valores = resp.get("values", [])
        if not valores:
            return False, "Sheet vacío"

        header = valores[0]
        def _col(name):
            try: return header.index(name)
            except ValueError: return -1

        col_ticker    = _col("Ticker")
        col_pc        = _col("Precio_Compra")
        col_qty       = _col("Cantidad")
        col_p_sal     = _col("Precio_Salida")
        col_f_sal     = _col("Fecha_Salida")
        col_correcto  = _col("Fue_Correcto")
        col_razon     = _col("Razon_Salida")
        col_error     = _col("Error_Modelo")
        col_notas     = _col("Notas")
        col_qty_act   = _col("Cantidad_Activa")
        col_qty_vend  = _col("Cantidad_Vendida")
        col_pnl_real  = _col("PnL_Realizado_Pct")
        col_tramos    = _col("Tramos_Salida")

        if col_ticker < 0:
            return False, "Columna Ticker no encontrada"

        # Buscar fila activa del ticker (sin Fecha_Salida o con Cantidad_Activa > 0)
        fila_idx = -1
        for i in range(len(valores)-1, 0, -1):
            row = valores[i]
            if len(row) <= col_ticker:
                continue
            if str(row[col_ticker]).upper().strip() != str(ticker).upper().strip():
                continue
            _fs = row[col_f_sal] if col_f_sal >= 0 and len(row) > col_f_sal else ""
            _qa = row[col_qty_act] if col_qty_act >= 0 and len(row) > col_qty_act else ""
            # Activa si no tiene fecha de salida O tiene Cantidad_Activa > 0
            _activa = (str(_fs).strip() in ("-","","nan","NaT","None"))
            _runner = False
            try:
                _runner = float(str(_qa).replace(",",".")) > 0 if _qa else False
            except Exception:
                pass
            if _activa or _runner:
                fila_idx = i + 1
                break

        if fila_idx < 0:
            return False, f"No se encontró fila activa de {ticker}"

        row_data = valores[fila_idx - 1]
        hoy = _dts.date.today().strftime("%d-%m-%Y")

        def _get_val(col, default="0"):
            if col < 0 or len(row_data) <= col: return default
            return str(row_data[col]).strip() or default

        def _fmt(v):
            try: return str(round(float(v), 2)).replace(".", ",")
            except: return str(v)

        # Calcular valores actuales
        try:
            _qty_orig  = float(str(_get_val(col_qty, "0")).replace(",","."))
        except: _qty_orig = 0
        try:
            _qty_act   = float(str(_get_val(col_qty_act, str(_qty_orig))).replace(",","."))
            if _qty_act <= 0: _qty_act = _qty_orig
        except: _qty_act = _qty_orig
        try:
            _qty_vend_prev = float(str(_get_val(col_qty_vend, "0")).replace(",","."))
        except: _qty_vend_prev = 0
        try:
            _pc = float(str(_get_val(col_pc, "0")).replace(",","."))
        except: _pc = 0

        # Calcular P&L realizado ponderado
        _pnl_tramo = round((precio_salida - _pc) / _pc * 100, 1) if _pc > 0 else 0
        _qty_vend_total = _qty_vend_prev + cantidad_vendida
        _qty_act_nueva  = max(0, _qty_act - cantidad_vendida)

        # P&L realizado ponderado (promedio de tramos)
        _pnl_prev_str = _get_val(col_pnl_real, "0")
        try:
            _pnl_prev = float(str(_pnl_prev_str).replace(",",".").replace("%",""))
        except: _pnl_prev = 0
        if _qty_vend_prev > 0:
            _pnl_real_nuevo = round(
                (_pnl_prev * _qty_vend_prev + _pnl_tramo * cantidad_vendida) / _qty_vend_total, 1)
        else:
            _pnl_real_nuevo = _pnl_tramo

        # Tramos histórico
        _tramos_prev = _get_val(col_tramos, "")
        _tramo_label = razon_salida.replace(" ","")[:3].upper()
        _tramo_nuevo = f"{_tramo_label}:{cantidad_vendida:.1f}acc@${precio_salida:.2f}({_pnl_tramo:+.1f}%)|{hoy}"
        _tramos_new = f"{_tramos_prev} | {_tramo_nuevo}".strip(" |") if _tramos_prev else _tramo_nuevo

        # Notas actualizadas
        _notas_act = _get_val(col_notas, "")
        _notas_new = f"{_notas_act} | {notas_extra}".strip(" |") if notas_extra else _notas_act

        def _col_letter(idx):
            return chr(ord("A") + idx) if idx < 26 else f"A{chr(ord('A') + idx - 26)}"

        batch = []

        # Siempre actualizar estos campos
        if col_qty_act >= 0:
            batch.append({"range": f"'{hoja}'!{_col_letter(col_qty_act)}{fila_idx}",
                          "values": [[_fmt(_qty_act_nueva)]]})
        if col_qty_vend >= 0:
            batch.append({"range": f"'{hoja}'!{_col_letter(col_qty_vend)}{fila_idx}",
                          "values": [[_fmt(_qty_vend_total)]]})
        if col_pnl_real >= 0:
            batch.append({"range": f"'{hoja}'!{_col_letter(col_pnl_real)}{fila_idx}",
                          "values": [[f"{_pnl_real_nuevo:+.1f}%"]]})
        if col_tramos >= 0:
            batch.append({"range": f"'{hoja}'!{_col_letter(col_tramos)}{fila_idx}",
                          "values": [[_tramos_new]]})
        if col_correcto >= 0:
            batch.append({"range": f"'{hoja}'!{_col_letter(col_correcto)}{fila_idx}",
                          "values": [[fue_correcto]]})
        if col_razon >= 0:
            batch.append({"range": f"'{hoja}'!{_col_letter(col_razon)}{fila_idx}",
                          "values": [[razon_salida]]})
        if col_error >= 0:
            batch.append({"range": f"'{hoja}'!{_col_letter(col_error)}{fila_idx}",
                          "values": [[error_modelo]]})
        if col_notas >= 0:
            batch.append({"range": f"'{hoja}'!{_col_letter(col_notas)}{fila_idx}",
                          "values": [[_notas_new]]})

        # Solo si TOTAL → llenar Precio_Salida y Fecha_Salida
        if tipo_salida == "TOTAL":
            if col_p_sal >= 0:
                batch.append({"range": f"'{hoja}'!{_col_letter(col_p_sal)}{fila_idx}",
                              "values": [[_fmt(precio_salida)]]})
            if col_f_sal >= 0:
                batch.append({"range": f"'{hoja}'!{_col_letter(col_f_sal)}{fila_idx}",
                              "values": [[hoy]]})

        svc.spreadsheets().values().batchUpdate(
            spreadsheetId=sheet_id,
            body={"valueInputOption": "USER_ENTERED", "data": batch}
        ).execute()

        try: limpiar_cache_sheets_only()
        except Exception: pass
        st.session_state.pop("_cartera_global_cache", None)
        st.session_state.pop("_cartera_global_ts", None)

        _label = {_SHEET_NAME_GREKO:"Greko",
                  _SHEET_NAME_MAURI:"MVALLE",
                  _SHEET_NAME_AMPARITO:"Amparito"}.get(sheet_name, sheet_name)

        if tipo_salida == "PARCIAL":
            return True, (f"✅ T1/T2 registrado en {_label} · "
                         f"{cantidad_vendida:.1f} acc vendidas @ ${precio_salida:.2f} "
                         f"({_pnl_tramo:+.1f}%) · Runner: {_qty_act_nueva:.1f} acc activas")
        else:
            return True, (f"✅ Cierre TOTAL {ticker} en {_label} · "
                         f"P&L realizado: {_pnl_real_nuevo:+.1f}%")

    except Exception as e:
        return False, f"❌ Error: {str(e)[:120]}"


def render_botones_salida(
    ticker: str, pc: float, pa: float, pnl_pct: float,
    sheet_name: str, key_prefix: str,
    G: str, R: str, A: str, TXT_MUT: str, BG_HEAD: str, BOR: str,
    idx: int = 0):  # v19 FIX A: índice para keys únicas
    """v19: Renderiza botones de salida con lógica TOTAL vs PARCIAL."""
    _uk = f"{key_prefix}_{ticker}_{idx}"

    # Razones que implican TOTAL (posición cerrada)
    _razones_total = {"T3 alcanzado","Stop loss","Stop loss tardío",
                      "Decisión propia","Earnings próximo",
                      "Cambio de tesis","Otro"}
    _razones_parcial = {"T1 alcanzado","T2 alcanzado"}

    with st.expander(f"🏁 Registrar salida {ticker}", expanded=False):

        # Selector TOTAL / PARCIAL
        _tipo_sal = st.radio(
            "Tipo de salida",
            ["🏁 TOTAL — cerrar posición completa",
             "⚡ PARCIAL — T1/T2 · queda runner activo"],
            key=f"tipo_{_uk}", horizontal=True)
        _es_total = "TOTAL" in _tipo_sal

        _ce1, _ce2 = st.columns(2)
        with _ce1:
            _p_sal = st.number_input(
                "Precio de salida", min_value=0.0, value=float(pa),
                step=0.01, format="%.2f", key=f"psal_{_uk}")

            _razones_list = (
                ["Stop loss","Stop loss tardío","T3 alcanzado",
                 "Decisión propia","Earnings próximo","Cambio de tesis","Otro"]
                if _es_total else
                ["T1 alcanzado","T2 alcanzado"]
            )
            _razon = st.selectbox(
                "Razón", _razones_list, key=f"razon_{_uk}")

            if not _es_total:
                _cant_vend = st.number_input(
                    "Cantidad vendida (acciones)",
                    min_value=0.1, value=1.0, step=0.1, format="%.1f",
                    key=f"cantvend_{_uk}",
                    help="Cuántas acciones vendes en este tramo")
            else:
                _cant_vend = 0.0  # en TOTAL se calcula desde Cantidad

        with _ce2:
            _pnl_real = (_p_sal - pc) / pc * 100 if pc > 0 else 0
            _sugerido = "SÍ" if _pnl_real > 0 else "NO"
            _correcto = st.selectbox(
                "¿Fue correcto?", ["SÍ","NO","PARCIAL"],
                index=["SÍ","NO","PARCIAL"].index(_sugerido),
                key=f"correcto_{_uk}")
            _error = st.text_input(
                "Error del modelo", key=f"error_{_uk}",
                placeholder="ej: stop tardío, dilución no detectada")
            _notas_ext = st.text_input(
                "Notas", key=f"notasal_{_uk}",
                placeholder="ej: vendí en apertura")

        # Preview P&L
        _c = G if _pnl_real > 0 else R
        _cant_label = f"· {_cant_vend:.1f} acc vendidas" if not _es_total else ""
        st.markdown(
            f'<div style="background:{BG_HEAD};border-radius:6px;'
            f'padding:8px 12px;margin:4px 0;border-left:3px solid {_c}">'
            f'<span style="font-size:11px;color:{TXT_MUT}">P&L del tramo: </span>'
            f'<span style="font-size:13px;font-weight:800;color:{_c}">'
            f'{_pnl_real:+.1f}% · ${(_p_sal-pc):+.2f}/acc{_cant_label}</span>'
            f'{"<br><span style=font-size:10px;color:#64748B>Runner activo después de esta venta</span>" if not _es_total else ""}'
            f'</div>',
            unsafe_allow_html=True)

        if st.button(
            f"💾 Confirmar {'cierre total' if _es_total else 'T1/T2 parcial'} {ticker}",
            key=f"btnsal_{_uk}", use_container_width=True, type="primary"):

            # En TOTAL, cantidad vendida = toda la posición activa
            _cant_final = 0.0 if _es_total else float(_cant_vend)

            ok, msg = actualizar_salida_sheet(
                sheet_name=sheet_name,
                ticker=ticker,
                precio_salida=float(_p_sal),
                cantidad_vendida=_cant_final,
                razon_salida=_razon,
                fue_correcto=_correcto,
                error_modelo=_error if _error else "-",
                notas_extra=_notas_ext,
                tipo_salida="TOTAL" if _es_total else "PARCIAL",
            )
            if ok:
                st.success(msg)
                # v19 FIX SPEED: invalidar caché para forzar recarga en próxima apertura
                # No st.rerun() — el checkbox no recarga todo
                st.session_state.pop("_cartera_global_cache", None)
                st.session_state.pop("_cartera_global_ts", None)
                st.session_state.pop("_greko_df_cache", None)
                st.session_state.pop("_greko_batch_cache", None)
                st.session_state.pop("_greko_cache_ts", None)
            else:
                st.error(msg)

def render_panel_recompra(
    recompra: dict,
    tipo: str,
    G: str, R: str, A: str, C: str,
    TXT: str, TXT_MUT: str, BOR: str,
) -> str:
    """
    v19: Renderiza el panel de GESTIÓN/RECOMPRA para una posición.
    Claramente diferenciado de las noticias externas.
    """
    señal = recompra.get("señal", "")

    if señal == "promedio_baja":
        _dias = recompra.get("dias_alcistas", 0)
        return (
            f'<div style="background:#EFF6FF;border:2px solid #93C5FD;'
            f'border-left:4px solid #2563EB;border-radius:10px;'
            f'padding:10px 14px;margin-top:8px">'
            f'<div style="font-size:12px;font-weight:800;color:#2563EB;margin-bottom:6px">'
            f'⚡ PROMEDIAR A LA BAJA — {_dias} días alcistas · rebote confirmado</div>'
            f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:8px">'
            f'<div style="text-align:center">'
            f'<div style="font-size:9px;color:{TXT_MUT}">Precio actual</div>'
            f'<div style="font-size:13px;font-weight:700;color:{TXT}">${recompra.get("precio_actual",0):.2f}</div></div>'
            f'<div style="text-align:center">'
            f'<div style="font-size:9px;color:{TXT_MUT}">Precio prom. nuevo</div>'
            f'<div style="font-size:13px;font-weight:700;color:#2563EB">${recompra.get("precio_promedio",0):.2f}</div></div>'
            f'<div style="text-align:center">'
            f'<div style="font-size:9px;color:{TXT_MUT}">Stop combinado</div>'
            f'<div style="font-size:13px;font-weight:700;color:{R}">${recompra.get("stop_combinado",0):.2f}</div></div>'
            f'<div style="text-align:center">'
            f'<div style="font-size:9px;color:{TXT_MUT}">Target recuperación</div>'
            f'<div style="font-size:13px;font-weight:700;color:{G}">${recompra.get("target",0):.2f}</div></div>'
            f'</div>'
            f'<div style="font-size:10px;color:#374151;line-height:1.7">'
            f'{recompra.get("descripcion","")}</div>'
            f'<div style="font-size:10px;font-weight:600;color:#2563EB;margin-top:4px">'
            f'Agregar máx 40% posición original · '
            f'RSI {recompra.get("rsi",0)} · '
            f'{"Vol ↓ sano" if recompra.get("vol_bajo") else "Vol ↑ vigilar"}'
            f'</div></div>'
        )

    if señal == "no_promediar":
        return (
            f'<div style="background:#FEF3C7;border:1px solid #FCD34D;'
            f'border-left:3px solid #D97706;border-radius:8px;'
            f'padding:8px 12px;margin-top:6px">'
            f'<div style="font-size:11px;font-weight:700;color:#D97706;margin-bottom:3px">'
            f'⏳ No promediar aún</div>'
            f'<div style="font-size:10px;color:#374151">'
            f'{recompra.get("razon","")}</div>'
            f'</div>'
        )

    if señal == "esperar_pullback":
        _rsi_ep  = recompra.get("rsi", 0)
        _dd_ep   = recompra.get("dd_max", 0)
        _tgt_ep  = recompra.get("target_entrada", 0)
        _pt_ep   = recompra.get("pt_alerta", "")
        # Color del borde: naranja si hay alerta PT, azul si no
        _bor_ep  = "#D97706" if _pt_ep else "#2563EB"
        _bg_ep   = "#FFFBEB" if _pt_ep else "#EFF6FF"
        _bor_ep2 = "#FDE68A" if _pt_ep else "#BFDBFE"
        _pt_badge = (
            f'<div style="background:#FEF2F2;border:1px solid #FECACA;'
            f'border-radius:6px;padding:4px 8px;margin-top:6px;font-size:10px;'
            f'color:#DC2626;font-weight:600">⚠️ {_pt_ep}</div>'
        ) if _pt_ep else ""
        return (
            f'<div style="background:{_bg_ep};border:1px solid {_bor_ep2};'
            f'border-left:3px solid {_bor_ep};border-radius:8px;'
            f'padding:8px 12px;margin-top:6px">'
            f'<div style="font-size:11px;font-weight:700;color:{_bor_ep};margin-bottom:3px">'
            f'⏳ Esperando pullback para recompra</div>'
            f'<div style="font-size:10px;color:#374151">'
            f'Posición con ganancia — sin corrección suficiente aún. '
            f'RSI {_rsi_ep} · DD {_dd_ep:.1f}% desde máximo. '
            f'{"Recomprar si precio baja a $" + str(round(_tgt_ep,2)) + " (-8% desde máximo)" if _tgt_ep > 0 else "Esperar corrección de -8% desde máximo reciente."}'
            f'</div>'
            f'{_pt_badge}'
            f'</div>'
        )

    if señal == "esperar":
        return (
            f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
            f'border-left:3px solid #94A3B8;border-radius:8px;'
            f'padding:8px 12px;margin-top:6px">'
            f'<div style="font-size:11px;font-weight:700;color:#64748B;margin-bottom:3px">'
            f'⏳ Esperar</div>'
            f'<div style="font-size:10px;color:#374151">'
            f'{recompra.get("razon","Sin condiciones para recompra en este momento.")}</div>'
            f'</div>'
        )

    if señal == "no_recomprar":
        return (
            f'<div style="background:#FEF2F2;border:1px solid #FECACA;'
            f'border-left:3px solid #DC2626;border-radius:8px;'
            f'padding:8px 12px;margin-top:6px">'
            f'<div style="font-size:11px;font-weight:700;color:#DC2626;margin-bottom:3px">'
            f'🚫 No recomprar</div>'
            f'<div style="font-size:10px;color:#374151">'
            f'{recompra.get("razon","Condiciones desfavorables para agregar posición.")}</div>'
            f'</div>'
        )

    if señal == "no_aplica":
        return (
            f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
            f'border-radius:8px;padding:6px 12px;margin-top:6px">'
            f'<div style="font-size:10px;color:#64748B">'
            f'ℹ️ {recompra.get("razon","Recompra no aplica para este tipo de posición.")}</div>'
            f'</div>'
        )

    if señal in ("sin_datos", "error"):
        return ""

    if señal == "recompra_pre_earnings":
        return (
            f'<div style="background:#F0FDF4;border:2px solid #86EFAC;'
            f'border-left:4px solid #16A34A;border-radius:10px;'
            f'padding:10px 14px;margin-top:8px">'
            f'<div style="font-size:12px;font-weight:800;color:#16A34A;margin-bottom:6px">'
            f'⚡ RECOMPRA ESPECULATIVA — ventana pre-earnings</div>'
            f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:8px">'
            f'<div style="text-align:center">'
            f'<div style="font-size:9px;color:{TXT_MUT}">Precio recompra</div>'
            f'<div style="font-size:13px;font-weight:700;color:{TXT}">${recompra.get("precio_recompra",0):.2f}</div></div>'
            f'<div style="text-align:center">'
            f'<div style="font-size:9px;color:{TXT_MUT}">Stop estricto</div>'
            f'<div style="font-size:13px;font-weight:700;color:{R}">${recompra.get("stop_combinado",0):.2f}</div></div>'
            f'<div style="text-align:center">'
            f'<div style="font-size:9px;color:{TXT_MUT}">Target</div>'
            f'<div style="font-size:13px;font-weight:700;color:{G}">${recompra.get("target",0):.2f}</div></div>'
            f'<div style="text-align:center">'
            f'<div style="font-size:9px;color:{TXT_MUT}">RSI actual</div>'
            f'<div style="font-size:13px;font-weight:700;color:{TXT}">{recompra.get("rsi",0)}</div></div>'
            f'</div>'
            f'<div style="font-size:10px;color:#374151;line-height:1.7">'
            f'{recompra.get("descripcion","")}'
            f'</div>'
            f'<div style="font-size:10px;font-weight:600;color:#D97706;margin-top:4px">'
            f'⚠️ Posición máx 20% de la original · Stop -5% estricto · No ampliar después del earnings</div>'
            f'</div>'
        )

    if señal == "recompra":
        cal   = recompra.get("calidad","MEDIA")
        emoji = recompra.get("emoji_calidad","🟡")
        bg    = "#F0FDF4" if cal == "ALTA" else "#FFFBEB" if cal == "MEDIA" else "#FFF7ED"
        bor   = G if cal == "ALTA" else A if cal == "MEDIA" else "#FB923C"
        max_add = "30%" if tipo == "Accion" else "25%"

        return (
            f'<div style="background:{bg};border:2px solid {bor}40;'
            f'border-left:4px solid {bor};border-radius:10px;'
            f'padding:10px 14px;margin-top:8px">'
            f'<div style="font-size:12px;font-weight:800;color:{bor};margin-bottom:6px">'
            f'{emoji} RECOMPRA {cal} — {recompra["descripcion"]}</div>'
            f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:8px">'
            f'<div style="text-align:center">'
            f'<div style="font-size:9px;color:{TXT_MUT}">Precio recompra</div>'
            f'<div style="font-size:13px;font-weight:700;color:{TXT}">${recompra["precio_recompra"]:.2f}</div></div>'
            f'<div style="text-align:center">'
            f'<div style="font-size:9px;color:{TXT_MUT}">Precio prom.</div>'
            f'<div style="font-size:13px;font-weight:700;color:{TXT}">${recompra["precio_prom"]:.2f}</div></div>'
            f'<div style="text-align:center">'
            f'<div style="font-size:9px;color:{TXT_MUT}">Stop combinado</div>'
            f'<div style="font-size:13px;font-weight:700;color:{R}">${recompra["stop_combinado"]:.2f}</div></div>'
            f'<div style="text-align:center">'
            f'<div style="font-size:9px;color:{TXT_MUT}">Target</div>'
            f'<div style="font-size:13px;font-weight:700;color:{G}">${recompra["target"]:.2f}</div></div>'
            f'</div>'
            f'<div style="font-size:10px;color:{TXT_MUT}">'
            f'Agregar máximo <strong>{max_add}</strong> de la posición original · '
            f'Nunca agregar a posiciones en pérdida'
            f'</div></div>'
        )

    elif señal == "esperar_pullback":
        return (
            f'<div style="background:#EFF6FF;border:1px solid #93C5FD;'
            f'border-left:3px solid #2563EB;border-radius:8px;'
            f'padding:8px 12px;margin-top:8px;font-size:11px">'
            f'<strong style="color:#2563EB">⏳ Esperar pullback</strong><br>'
            f'<span style="color:{TXT_MUT}">{recompra.get("razon","")}</span>'
            f'</div>'
        )

    elif señal == "no_recomprar":
        return (
            f'<div style="background:#FEF2F2;border:1px solid #FCA5A5;'
            f'border-left:3px solid {R};border-radius:8px;'
            f'padding:8px 12px;margin-top:8px;font-size:11px">'
            f'<strong style="color:{R}">🚫 No recomprar</strong><br>'
            f'<span style="color:{TXT_MUT}">{recompra.get("razon","")}</span>'
            f'</div>'
        )

    return ""  # sin_datos, error, no_aplica, esperar → no mostrar nada

@st.cache_data(ttl=1800, show_spinner=False)  # cache 30 min
def get_noticia_top(ticker: str) -> dict:
    """
    v18: Obtiene la noticia más relevante del día para un ticker.
    Retorna dict con titulo, sentimiento, dias, impacto, link.
    Usado inline en cards de Watchlist, Sympathy y Posiciones.
    """
    try:
        noticias = fetch_noticias_ticker(ticker)
        if not noticias:
            return {}
        # La primera noticia es la más reciente
        top = noticias[0]
        return {
            "titulo":      top.get("titulo","")[:90],
            "sentimiento": top.get("sentimiento","neutral"),
            "impacto":     top.get("impacto", 0),
            "dias":        top.get("dias_atras", 0),
            "link":        top.get("link",""),
            "fuente":      top.get("fuente",""),
        }
    except Exception:
        return {}


def render_noticia_inline(ticker: str,
                           G: str, R: str, A: str,
                           TXT_MUT: str, BOR: str) -> str:
    """
    v18: Renderiza el titular más importante como HTML inline.
    Para usar dentro de cards de Watchlist, Sympathy y Posiciones.
    """
    # Primero buscar en caché existente
    cache = st.session_state.get("noticias_cache", {})
    if ticker in cache and cache[ticker].get("noticias"):
        top = cache[ticker]["noticias"][0]
        titulo    = top.get("titulo","")[:85]
        sent      = top.get("sentimiento","neutral")
        impacto   = top.get("impacto", 0)
        dias      = top.get("dias_atras", top.get("dias", 0))
        link      = top.get("link","#")
    else:
        # Fetch directo si no está en caché
        data = get_noticia_top(ticker)
        if not data:
            return ""
        titulo  = data.get("titulo","")[:85]
        sent    = data.get("sentimiento","neutral")
        impacto = data.get("impacto", 0)
        dias    = data.get("dias", 0)
        link    = data.get("link","#")

    if not titulo:
        return ""

    # Color por sentimiento
    if sent == "positivo" or impacto > 3:
        _nc, _nbg = G, "#F0FDF4"
        _icon = "📈"
    elif sent == "negativo" or impacto < -3:
        _nc, _nbg = R, "#FEF2F2"
        _icon = "📉"
    else:
        _nc, _nbg = A, "#FFFBEB"
        _icon = "📰"

    _dias_str = "hoy" if dias == 0 else f"hace {dias}d"
    _imp_str  = f"{impacto:+d}" if impacto != 0 else ""

    return (
        f'<div style="background:{_nbg};border-left:3px solid {_nc};'
        f'border-radius:0 6px 6px 0;padding:5px 10px;margin-top:5px;font-size:10px">'
        f'<span style="font-weight:700;color:{_nc}">{_icon} </span>'
        f'<span style="color:#374151">{titulo}</span>'
        f'<span style="color:{_nc};font-weight:600;margin-left:6px">{_imp_str}</span>'
        f'<span style="color:#9CA3AF;margin-left:6px">{_dias_str}</span>'
        f'</div>'
    )

def render_nbis_panel(prob: float, sim: float,
                      G: str, A: str, R: str, C: str,
                      TXT: str, TXT_MUT: str, TXT_SOFT: str,
                      BG_HEAD: str, BOR: str) -> str:
    """
    v19 FIX E: Solo muestra Prob_NBIS (Sim_NBIS eliminado — no afecta decisiones).
    prob: 0-100 probabilidad de seguir el patrón NBIS
    """
    def nivel_color(val):
        if val >= 70: return G, "Alta"
        if val >= 50: return A, "Moderada"
        if val >= 30: return C, "Baja"
        return TXT_MUT, "Muy baja"

    prob_c, prob_lbl = nivel_color(prob)

    if prob >= 65:
        inter = "🔥 Alta probabilidad de rebote significativo"
        inter_c = G
    elif prob >= 50:
        inter = "⚡ Probabilidad moderada — monitorear catalizador"
        inter_c = A
    elif prob >= 35:
        inter = "👀 Probabilidad baja — esperar más confirmación"
        inter_c = C
    else:
        inter = "📡 Patrón especulativo — entrada de mayor riesgo"
        inter_c = TXT_MUT

    html = (
        f'<div style="background:{BG_HEAD};border:1px solid {BOR};'
        f'border-radius:8px;padding:9px 12px;margin-top:8px">'+
        f'  <div style="font-size:9px;color:{TXT_MUT};font-weight:700;margin-bottom:4px">'+
        f'  ⭐ PROB. PATRÓN NBIS</div>'+
        f'  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">'+
        f'    <span style="font-size:22px;font-weight:800;color:{prob_c}">{prob:.0f}%</span>'+
        f'    <span style="background:{prob_c}22;color:{prob_c};border:1px solid {prob_c}44;'
        f'    border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700">{prob_lbl}</span>'+
        f'  </div>'+
        f'  <div style="background:{BOR};border-radius:3px;height:5px;margin-bottom:4px">'+
        f'    <div style="background:{prob_c};height:5px;border-radius:3px;'
        f'    width:{min(prob,100):.0f}%"></div>'+
        f'  </div>'+
        f'  <div style="font-size:9px;color:{inter_c};font-weight:600">{inter}</div>'+
        f'</div>'
    )
    return html


# ─────────────────────────────────────────────────────────────
#  EXPORTAR SEÑALES DEL DÍA - genera CSV para el tracker
# ─────────────────────────────────────────────────────────────
def exportar_senales_dia(df: pd.DataFrame, tab_nombre: str,
                         fase_col: str = None,
                         es_swing: bool = False) -> bytes:
    """
    Genera CSV en formato del tracker paper trading.
    Listo para pegar en hoja ⚡ Paper Trading del Excel.
    """
    import datetime
    hoy = datetime.date.today().strftime("%d-%b-%Y")

    filas = []
    for _, r in df.iterrows():
        tk     = str(r.get("Ticker",""))
        precio = r.get("Precio", 0)
        rsi    = r.get("RSI", 0)
        vol    = r.get("Volumen", r.get("vol_ratio", 0))
        prob   = r.get("Prob_NBIS", 0)
        # Usar Etapa_v12 si existe - es la fuente de verdad
        # Garantiza coherencia entre lo que se muestra en el tab
        # y lo que se exporta al CSV
        if "Etapa_v12" in r and str(r.get("Etapa_v12","")) not in ("-","","nan"):
            fase = str(r.get("Etapa_v12",""))
        elif "Fase" in r and str(r.get("Fase","")) not in ("-","","nan","M1","M2","M3"):
            fase = str(r.get("Fase",""))
        else:
            # Calcular desde datos disponibles como fallback
            rsi_v  = float(r.get("RSI", 50))
            dd_v   = float(r.get("DD_pico", 0))
            vol_v  = float(r.get("Volumen", 0))
            prob_v = float(r.get("Prob_NBIS", 0))
            mom_v  = float(r.get("Momentum_3d", r.get("MACD", 0)))
            dias_v = int(r.get("Dias_Alcistas", 0))
            if rsi_v <= 35 and mom_v >= 5 and dias_v >= 3 and vol_v >= 60 and prob_v >= 40 and dd_v <= -10:
                fase = "M3 - ENTRAR HOY"
            elif 30 <= rsi_v <= 45 and vol_v >= 50 and prob_v >= 40 and dias_v >= 1 and mom_v >= 1 and dd_v <= -8:
                fase = "M2 - EN FORMACIÓN M2"
            elif 35 <= rsi_v <= 60 and prob_v >= 35 and dd_v <= -8:
                fase = "M1 - DETECTADA - Solo radar"
            else:
                fase = "M1 - DETECTADA - Solo radar"
        lectura= str(r.get("Lectura",""))[:60]

        stop   = round(float(precio) * 0.95, 2) if precio else ""
        target1= round(float(precio) * 1.08, 2) if precio else ""
        target2= round(float(precio) * 1.12, 2) if precio else ""

        # Datos adicionales
        dd_val    = round(float(r.get("DD_pico", r.get("DD", 0))), 1)
        sr_val    = int(r.get("Score_Rebote", r.get("Score", 0)))
        mom_val   = round(float(r.get("Momentum_3d", r.get("MACD", 0))), 1)
        dias_val  = int(r.get("Dias_Alcistas", 0))
        precio_val= round(float(precio), 2)

        filas.append({
            "Fecha_Senal":    hoy,
            "Ticker":         _ascii(tk),
            "Tab_Origen":     _ascii(tab_nombre),
            "Fase_Entrada":   _ascii(str(fase)),
            "VIX_Entrada":    round(float(vix.get("valor", 0)), 1) if vix.get("_ok") else "-",
            "RSI_Entrada":    round(float(rsi), 1),
            "DD_Pico_Pct":    dd_val,
            "Vol_Pct":        round(float(vol), 0),
            "Prob_NBIS_Pct":  round(float(prob), 1),
            "Score_Rebote":   sr_val,
            "Momentum_3d":    mom_val,
            "Dias_Alcistas":  dias_val,
            "Precio_Entrada": precio_val,
            "Stop_7pct":      round(precio_val * 0.93, 2) if precio_val else "-",
            "Target1_8pct":   round(precio_val * 1.08, 2) if precio_val else "-",
            "Target2_12pct":  round(precio_val * 1.12, 2) if precio_val else "-",
            "Precio_Dia5":    "-",
            "T1_Alcanzado":   "-",
            "Precio_Dia10":   "-",
            "T2_Alcanzado":   "-",
            "Stop_Activado":  "-",
            "Resultado_Pct":  "-",
            "SPY_Periodo":    "-",
            "Alpha_vs_SPY":   "-",
            "Modelo_OK":      "-",
            "Notas":          _ascii(lectura),
        })

    return df_to_csv_chile(pd.DataFrame(filas))

def boton_exportar(df: pd.DataFrame, tab_nombre: str,
                   key: str, fase_col: str = None,
                   es_swing: bool = False):
    """Renderiza botón de exportar + instrucción."""
    import datetime
    if df is None or df.empty:
        return
    hoy = datetime.date.today().strftime("%Y-%m-%d")
    # Limpiar nombre para filename
    tab_clean = (tab_nombre.replace(" ","_")
                 .replace("🔥","").replace("⚡","")
                 .replace("📡","").replace("👀","")
                 .replace("🔗","").replace("🔎","").strip())
    fname = f"senales_{tab_clean}_{hoy}.csv"

    # Cache CSV en session_state para evitar MediaFileStorageError
    cache_key = f"csv_cache_{key}"
    if cache_key not in st.session_state or st.session_state.get(f"{cache_key}_tab") != tab_nombre:
        st.session_state[cache_key] = exportar_senales_dia(df, tab_nombre, fase_col, es_swing=es_swing)
        st.session_state[f"{cache_key}_tab"] = tab_nombre

    csv_bytes = st.session_state[cache_key]

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    col_btn, col_info = st.columns([2, 3])
    with col_btn:
        st.download_button(
            label=f"📥 Exportar señales de hoy - {len(df)} acción(es)",
            data=csv_bytes,
            file_name=fname,
            mime="text/csv",
            key=key,
            use_container_width=True,
        )
    with col_info:
        st.markdown(
            f'<div style="font-size:10px;color:#64748B;padding-top:8px;line-height:1.6">'+
            f'📋 Pega este CSV en la hoja <strong>⚡ Paper Trading</strong> del tracker.<br>'+
            f'Stop  - Targets  - VIX  - RSI ya vienen calculados.</div>',
            unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  ETF STRATEGY DASHBOARD
# ─────────────────────────────────────────────────────────────
ETF_UNIVERSE = {
    # Índices principales
    "VOO":  {"nombre":"Vanguard S&P500",      "categoria":"Indice",    "riesgo":"Bajo",    "rend_hist":10.0},
    "QQQ":  {"nombre":"Nasdaq 100",            "categoria":"Indice",    "riesgo":"Medio",   "rend_hist":13.0},
    "SPY":  {"nombre":"S&P500 SPDR",           "categoria":"Indice",    "riesgo":"Bajo",    "rend_hist":10.0},
    "VEA":  {"nombre":"Europa/Asia Dev",       "categoria":"Indice",    "riesgo":"Medio",   "rend_hist":7.0},
    # Renta fija / Parking
    "SGOV": {"nombre":"Treasury 0-3m",         "categoria":"Parking",   "riesgo":"Mínimo",  "rend_hist":5.0},
    "BIL":  {"nombre":"Treasury Bills",        "categoria":"Parking",   "riesgo":"Mínimo",  "rend_hist":5.0},
    # Sectoriales
    "XLK":  {"nombre":"Tech Select",           "categoria":"Sectorial", "riesgo":"Medio",   "rend_hist":12.0},
    "XLV":  {"nombre":"Health Care",           "categoria":"Sectorial", "riesgo":"Bajo",    "rend_hist":9.0},
    "XLE":  {"nombre":"Energy Select",         "categoria":"Sectorial", "riesgo":"Medio",   "rend_hist":8.0},
    # Ya tienes
    "TAN":  {"nombre":"Solar Energy",          "categoria":"Sectorial", "riesgo":"Alto",    "rend_hist":8.0},
    "XBI":  {"nombre":"Biotech",               "categoria":"Sectorial", "riesgo":"Alto",    "rend_hist":9.0},
    # Cripto
    "IBIT": {"nombre":"Bitcoin ETF BlackRock", "categoria":"Cripto",    "riesgo":"MuyAlto", "rend_hist":30.0},
    "ETHA": {"nombre":"Ethereum ETF BlackRock","categoria":"Cripto",    "riesgo":"MuyAlto", "rend_hist":25.0},
}

def fetch_etf_data(ticker: str) -> dict:
    """Obtiene datos técnicos de un ETF desde yfinance."""
    try:
        import yfinance as yf
        import numpy as np
        tk  = yf.Ticker(ticker)
        hist = tk.history(period="6mo")
        if hist.empty or len(hist) < 20:
            return None
        close = hist["Close"].values
        vol   = hist["Volume"].values

        precio  = float(close[-1])
        pico    = float(close.max())
        dd      = round((precio - pico) / pico * 100, 1)

        # RSI 14
        delta  = hist["Close"].diff()
        gain   = delta.clip(lower=0).rolling(14).mean()
        loss   = (-delta.clip(upper=0)).rolling(14).mean()
        rsi    = round(float(100 - 100/(1 + gain.iloc[-1]/(loss.iloc[-1]+1e-9))), 1)

        # Tendencia 20d
        ema20  = float(hist["Close"].ewm(span=20).mean().iloc[-1])
        tend   = "↑" if precio > ema20 * 1.02 else "↓" if precio < ema20 * 0.98 else "->"

        # YTD
        try:
            import datetime as _dt_ytd
            _eytd = _dt_ytd.date.today()
            _sytd = _eytd - _dt_ytd.timedelta(days=365)
            hist_ytd = tk.history(
                start=_sytd.strftime("%Y-%m-%d"),
                end=_eytd.strftime("%Y-%m-%d"))
            ytd_price = float(hist_ytd["Close"].iloc[0]) if not hist_ytd.empty else precio
            ytd_pct   = round((precio - ytd_price) / ytd_price * 100, 1)
        except:
            ytd_pct = 0.0

        # Volumen ratio
        avg_vol   = float(np.mean(vol[-20:]))
        vol_ratio = round(float(vol[-1]) / avg_vol * 100, 0) if avg_vol > 0 else 100

        # Señal de entrada
        if rsi < 35 and dd < -15:
            senal = "🟢 COMPRAR AHORA"
            senal_c = "16A34A"
        elif rsi < 50 and dd < -8:
            senal = "🟡 BUENA ENTRADA"
            senal_c = "D97706"
        elif rsi > 70:
            senal = "🔴 ESPERAR - RSI alto"
            senal_c = "DC2626"
        elif dd > -3:
            senal = "⚪ EN MÁXIMOS"
            senal_c = "64748B"
        else:
            senal = "🔵 NEUTRAL"
            senal_c = "2563EB"

        return {
            "ticker":    ticker,
            "precio":    precio,
            "dd":        dd,
            "rsi":       rsi,
            "tend":      tend,
            "ytd":       ytd_pct,
            "vol_ratio": vol_ratio,
            "senal":     senal,
            "senal_c":   senal_c,
            "ema20":     ema20,
        }
    except Exception:
        return None


def calcular_estrategia(capital: float, plazo: str, perfil: str,
                         etf_data: dict) -> dict:
    """
    Calcula distribución óptima de capital en ETFs
    basada en indicadores actuales + perfil + plazo.
    """
    # Pesos base por perfil y plazo
    if perfil == "Moderado":
        if plazo == "Corto (6-12m)":
            base = {"Parking":0.50, "Indice":0.30, "Sectorial":0.10, "Cripto":0.10}
        elif plazo == "Mediano (2-5a)":
            base = {"Parking":0.20, "Indice":0.50, "Sectorial":0.20, "Cripto":0.10}
        else:  # Largo
            base = {"Parking":0.05, "Indice":0.55, "Sectorial":0.25, "Cripto":0.15}
    elif perfil == "Agresivo":
        if plazo == "Corto (6-12m)":
            base = {"Parking":0.20, "Indice":0.40, "Sectorial":0.25, "Cripto":0.15}
        elif plazo == "Mediano (2-5a)":
            base = {"Parking":0.05, "Indice":0.45, "Sectorial":0.30, "Cripto":0.20}
        else:
            base = {"Parking":0.00, "Indice":0.40, "Sectorial":0.35, "Cripto":0.25}
    else:  # Conservador
        if plazo == "Corto (6-12m)":
            base = {"Parking":0.70, "Indice":0.20, "Sectorial":0.10, "Cripto":0.00}
        elif plazo == "Mediano (2-5a)":
            base = {"Parking":0.40, "Indice":0.40, "Sectorial":0.15, "Cripto":0.05}
        else:
            base = {"Parking":0.20, "Indice":0.50, "Sectorial":0.25, "Cripto":0.05}

    # Ajustar por señales técnicas - sobreponderar ETFs en zona de compra
    allocations = []
    for tk, meta in ETF_UNIVERSE.items():
        d = etf_data.get(tk)
        if d is None:
            continue
        cat = meta["categoria"]
        peso_base = base.get(cat, 0)

        # Ajuste por RSI y DD
        if d["rsi"] < 40 and d["dd"] < -15:
            ajuste = 1.3   # sobreponderar
        elif d["rsi"] > 70:
            ajuste = 0.6   # subponderar
        elif d["dd"] > -3:
            ajuste = 0.8   # en máximos, esperar
        else:
            ajuste = 1.0

        peso_ajustado = peso_base * ajuste
        monto         = round(capital * peso_ajustado, 0)

        allocations.append({
            "ticker":   tk,
            "nombre":   meta["nombre"],
            "categoria":cat,
            "riesgo":   meta["riesgo"],
            "rend_hist":meta["rend_hist"],
            "peso":     round(peso_ajustado * 100, 1),
            "monto":    monto,
            "rsi":      d["rsi"],
            "dd":       d["dd"],
            "senal":    d["senal"],
            "senal_c":  d["senal_c"],
            "tend":     d["tend"],
            "ytd":      d["ytd"],
            "precio":   d["precio"],
        })

    # Normalizar a 100%
    total_peso = sum(a["peso"] for a in allocations)
    if total_peso > 0:
        for a in allocations:
            a["peso"]  = round(a["peso"] / total_peso * 100, 1)
            a["monto"] = round(capital * a["peso"] / 100, 0)

    # DCA - dividir en meses según plazo
    meses_dca = {"Corto (6-12m)": 3, "Mediano (2-5a)": 4, "Largo (5-10a)": 6}
    n_meses   = meses_dca.get(plazo, 4)
    monto_mes = round(capital / n_meses, 0)

    # Proyección
    rend_ponderado = sum(
        (a["monto"] / capital) * ETF_UNIVERSE[a["ticker"]]["rend_hist"]
        for a in allocations if capital > 0
    )
    años = {"Corto (6-12m)": 1, "Mediano (2-5a)": 5, "Largo (5-10a)": 10}
    n_años = años.get(plazo, 5)
    proy_base = round(capital * (1 + rend_ponderado/100) ** n_años, 0)
    proy_opt  = round(capital * (1 + (rend_ponderado+3)/100) ** n_años, 0)
    proy_pes  = round(capital * (1 + max(rend_ponderado-4, 2)/100) ** n_años, 0)

    return {
        "allocations":      sorted(allocations, key=lambda x: -x["monto"]),
        "n_meses":          n_meses,
        "monto_mes":        monto_mes,
        "rend_ponderado":   round(rend_ponderado, 1),
        "proy_base":        proy_base,
        "proy_opt":         proy_opt,
        "proy_pes":         proy_pes,
        "n_años":           n_años,
    }


def _ascii(x) -> str:
    """Convierte cualquier valor a string ASCII compatible con Excel Chile (latin-1)."""
    if not isinstance(x, str):
        x = str(x)
    _MAP = {
        "\u2014":"-", "\u2013":"-", "\u2012":"-",
        "\u2019":"'", "\u2018":"'",
        "\u201c":'"', "\u201d":'"',
        "\u2192":"->","\u2190":"<-","\u2191":"^","\u2193":"v",
        "\u00f1":"n", "\u00d1":"N",
        "\u00e9":"e", "\u00e1":"a", "\u00ed":"i",
        "\u00f3":"o", "\u00fa":"u", "\u00fc":"u",
        "\u00c9":"E", "\u00c1":"A", "\u00cd":"I",
        "\u00d3":"O", "\u00da":"U",
        "\u00bf":"?", "\u00a1":"!",
        "\U0001f525":"FUERTE", "\u26a1":"VALIDA",
        "\U0001f4e1":"M1", "\u2705":"OK",
        "\u26a0":    "ALERTA",
        "\U0001f6d1":"STOP",
        "\U0001f480":"MUERTA",
        "\U0001f504":"TRAILING",
        "\U0001f4b0":"", "\U0001f4ca":"",
        "\U0001f4c8":"", "\U0001f4c9":"",
        "-":"-", "-":"-", "->":"->", "←":"<-",
        "ñ":"n", "Ñ":"N",
        "é":"e", "á":"a", "í":"i", "ó":"o", "ú":"u",
        "É":"E", "Á":"A", "Í":"I", "Ó":"O", "Ú":"U",
        "ü":"u", "ï":"i",
    }
    for k, v in _MAP.items():
        x = x.replace(k, v)
    result = ""
    for ch in x:
        try:
            ch.encode("latin-1")
            result += ch
        except UnicodeEncodeError:
            result += "?"
    return result.strip()


def df_to_csv_chile(df: pd.DataFrame) -> str:
    """Exporta DataFrame en formato CSV Chile: separador ; y decimales con coma"""
    return df.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")


# ─────────────────────────────────────────────────────────────
#  PROB NBIS v12 - Probabilidad real basada en patrón NBIS
#  NBIS referencia: RSI~38, Vol 280%, DD -55%, 3 días alcistas
#  momentum +27%, MACD positivo, catalizador earnings
# ─────────────────────────────────────────────────────────────
NBIS_REF = {
    "rsi":       38.0,
    "vol":       280.0,
    "dd":        -55.0,
    "dias_alc":  3,
    "momentum":  27.0,
    "tiene_cat": True,
}

def calcular_prob_nbis(rsi: float, vol_ratio: float, dd: float,
                        dias_alcistas: int, momentum_3d: float,
                        tiene_catalizador: bool) -> float:
    """
    Probabilidad 0-100% de que la acción repita el patrón NBIS.
    Compara condiciones actuales con el patrón NBIS de referencia.
    NO es similitud exacta - es qué tan cerca está de las condiciones
    que hicieron que NBIS funcionara.
    """
    score = 0.0

    # RSI (25 pts) - NBIS entró con RSI ~38
    if rsi <= 35:
        score += 25
    elif rsi <= 42:
        score += 22
    elif rsi <= 50:
        score += 15
    elif rsi <= 60:
        score += 8
    else:
        score += 0

    # Volumen (25 pts) - NBIS tenía 280%
    if vol_ratio >= 250:
        score += 25
    elif vol_ratio >= 150:
        score += 20
    elif vol_ratio >= 100:
        score += 12
    elif vol_ratio >= 60:
        score += 6
    else:
        score += 0

    # DD (20 pts) - NBIS cayó -55%, buscamos -20% a -50%
    if -50 <= dd <= -20:
        score += 20
    elif -60 <= dd <= -15:
        score += 15
    elif -70 <= dd <= -10:
        score += 8
    else:
        score += 0

    # Días alcistas (15 pts) - NBIS tuvo 3 días
    if dias_alcistas >= 3:
        score += 15
    elif dias_alcistas == 2:
        score += 10
    elif dias_alcistas == 1:
        score += 5
    else:
        score += 0

    # Momentum 3d (10 pts) - NBIS tenía +27% en 3 días
    if momentum_3d >= 15:
        score += 10
    elif momentum_3d >= 8:
        score += 8
    elif momentum_3d >= 4:
        score += 5
    elif momentum_3d >= 0:
        score += 2
    else:
        score += 0

    # Catalizador (5 pts)
    if tiene_catalizador:
        score += 5

    return round(score, 1)


# ─────────────────────────────────────────────────────────────
#  NUEVA LÓGICA M1/M2/M3 v12
# ─────────────────────────────────────────────────────────────
def clasificar_etapa_v12(rsi: float, vol_ratio: float, prob_nbis: float,
                          dias_alcistas: int, momentum_3d: float,
                          score_rebote: int, dd: float = 0.0,
                          cat_fecha: str = "-") -> dict:
    """
    Lógica de escalamiento v15 - incluye earnings como modificador de fase:

    Sin earnings / earnings lejanos (>30d):
      M1: RSI 40-60  - DD <= -8%
      M2: RSI 30-45  - Vol >= 50%  - Mom >= 1%  - 3d↑
      M3: RSI <= 42   - Vol >= 50%  - Mom >= 3%  - 3d↑

    Con earnings próximos (zona NBIS):
      7-15d: M2 -> M3 (zona óptima - catalizador activo)
      15-30d: M1 -> M2 (zona válida - da convicción)
      3-6d:  badge ⚠️  sin ascenso (tarde para entrar)
      1-2d:  BLOQUEO  (riesgo binario)
      Post-earnings caída >8%: M1 especial (setup más limpio)
    """
    import datetime as _dt
    # Calcular días para earnings
    _dias_cat = 999
    _tiene_cat = False
    if cat_fecha and cat_fecha not in ("-","","nan"):
        try:
            _fc = _dt.date.fromisoformat(str(cat_fecha)[:10])
            _dias_cat = (_fc - _dt.date.today()).days
            _tiene_cat = _dias_cat >= 0
        except Exception:
            pass
    # ══ FASES BASE (sin earnings) ══════════════════════════════

    # M3 base - señal completa
    _es_m3 = (rsi <= 42 and momentum_3d >= 3 and dias_alcistas >= 3
              and prob_nbis >= 35 and vol_ratio >= 50 and dd <= -8)

    # M2 base - preparar orden
    _es_m2 = (30 <= rsi <= 45 and vol_ratio >= 50
              and prob_nbis >= 40 and dias_alcistas >= 3
              and momentum_3d >= 1.0 and dd <= -8)

    # M1 base - radar
    _es_m1 = (35 <= rsi <= 60 and prob_nbis >= 35 and dd <= -8)

    # ══ MODIFICADORES DE EARNINGS (v15) ═════════════════════
    # AMD caso real: earning ayer -> +10% hoy. Con este bloque hubiera sido M3.
    _earn_label = ""
    _earn_color = ""

    if _tiene_cat:
        if _dias_cat <= 2:
            # 🚫 BLOQUEO total - earnings en 0-2 días
            return {"etapa": "ESPERAR", "label": "🚫 ESPERAR EARNINGS",
                    "color": "DC2626", "bg": "FEF2F2",
                    "accion": f"Earnings en {_dias_cat}d - riesgo binario. NO entrar. Esperar resultado.",
                    "earn_badge": f"🚫 Earnings en {_dias_cat}d", "earn_dias": _dias_cat}

        elif _dias_cat <= 6:
            # ⚠️ CAUCIÓN - no ascender pero badge de advertencia
            _earn_label = f"⚠️ Earnings en {_dias_cat}d - Tarde para entrar"
            _earn_color = "D97706"

        elif _dias_cat <= 15:
            # 🎯 ZONA ÓPTIMA - ascenso de fase
            # M2 -> M3: catalizador confirmado (caso NBIS real)
            if _es_m2 and not _es_m3:
                _es_m3 = True
                _earn_label = f"🎯 Earnings {_dias_cat}d - M2->M3 catalizador activo"
                _earn_color = "16A34A"
            # M1 -> M2: convicción extra
            elif _es_m1 and not _es_m2 and not _es_m3:
                _es_m2 = True
                _earn_label = f"🎯 Earnings {_dias_cat}d - M1->M2 convicción extra"
                _earn_color = "0891B2"
            else:
                _earn_label = f"🎯 Earnings {_dias_cat}d - zona óptima"
                _earn_color = "16A34A"

        elif _dias_cat <= 30:
            # ⚡ ZONA VÁLIDA - M1 puede subir a M2
            if _es_m1 and not _es_m2 and not _es_m3:
                _es_m2 = True
                _earn_label = f"⚡ Earnings {_dias_cat}d - M1->M2"
                _earn_color = "0891B2"
            else:
                _earn_label = f"📅 Earnings {_dias_cat}d"
                _earn_color = "2563EB"
        else:
            _earn_label = f"📅 Earnings {_dias_cat}d"
            _earn_color = "64748B"

    # ══ RETORNO SEGÚN FASE FINAL ═════════════════════════════
    if _es_m3:
        _accion = "Ejecutar en apertura - señal completa"
        if _earn_label:
            _accion = f"{_earn_label}  - {_accion}"
        return {"etapa": "M3", "label": "🔥 ENTRAR HOY",
                "color": "16A34A", "bg": "F0FDF4",
                "accion": _accion,
                "earn_badge": _earn_label, "earn_color": _earn_color,
                "earn_dias": _dias_cat}

    if _es_m2:
        _accion = "Preparar orden  - Definir stop y targets"
        if _earn_label:
            _accion = f"{_earn_label}  - {_accion}"
        return {"etapa": "M2", "label": "⚡ EN FORMACIÓN M2",
                "color": "D97706", "bg": "FFFBEB",
                "accion": _accion,
                "earn_badge": _earn_label, "earn_color": _earn_color,
                "earn_dias": _dias_cat}

    if _es_m1:
        _accion = "En el radar  - NO entrar aún"
        if _earn_label:
            _accion = f"{_earn_label}  - {_accion}"
        return {"etapa": "M1", "label": "📡 DETECTADA",
                "color": "2563EB", "bg": "EFF6FF",
                "accion": _accion,
                "earn_badge": _earn_label, "earn_color": _earn_color,
                "earn_dias": _dias_cat}

    # ── v15: MODIFICADORES POR EARNINGS ──────────────────────
    # Se aplican DESPUÉS de la clasificación base para ascender/bloquear
    if _tiene_cat:
        if _dias_cat <= 2:
            # 🚫 BLOQUEO - earnings mañana/pasado mañana
            return {"etapa": "ESPERAR", "label": "🚫 ESPERAR EARNINGS",
                    "color": "DC2626", "bg": "FEF2F2",
                    "accion": f"Earnings en {_dias_cat}d - riesgo binario. NO entrar hasta ver resultado.",
                    "earn_badge": f"🚫 Earnings en {_dias_cat}d", "earn_dias": _dias_cat}

        elif _dias_cat <= 6:
            # ⚠️ CAUCIÓN - tarde para entrar, no cambia fase pero añade badge
            pass  # fase calculada arriba se devuelve con badge abajo

        elif _dias_cat <= 15:
            # 🎯 ZONA ÓPTIMA - ascenso de fase
            pass  # ascenso ya aplicado en la lógica de fases abajo

        elif _dias_cat <= 30:
            # ⚡ ZONA VÁLIDA - M1 puede subir a M2
            pass

    # Sin etapa
    return {"etapa": "-", "label": "🔵 OBSERVAR",
            "color": "64748B", "bg": "F8FAFC",
            "accion": "Sin señal"}


# ─────────────────────────────────────────────────────────────
#  SEÑALES DE SALIDA v12
# ─────────────────────────────────────────────────────────────
def calcular_señales_salida_v12(pnl_pct: float, precio_compra: float,
                                  precio_actual: float, precio_max: float,
                                  dias_posicion: int, estrategia: str,
                                  tipo: str) -> dict:
    """
    Nueva lógica de salida v12:
    T1 +8%:  vender 40% -> mover stop a breakeven
    T2 +12%: vender 40% -> 20% queda con trailing stop
    Trailing: stop = precio_max x 0.95 (-5% desde máximo)
    Muerta:   >5 días en ±1% -> señal "Salir y reasignar"
    Stop:     -7% automático sin discreción
    """
    if estrategia == "Largo_Plazo":
        return {"señal": "📊 Largo plazo", "accion": "Mantener sin stop",
                "urgencia": "-", "tramos": [], "color": "2563EB"}

    señales = []
    urgencia = "-"
    color = "64748B"

    # Stop diferenciado por tipo — v18 fix: ETF_Cripto necesita -20% mínimo
    # ETHA puede caer 15% en un día — stop de -10% sería señal falsa
    if tipo == "Accion":
        stop_pct = -7.0
        stop_label = "Stop acción (-7%)"
    elif tipo == "ETF_Indice":
        stop_pct = -12.0
        stop_label = "Stop ETF Índice (-12%)"
    elif tipo == "ETF_Cripto":
        stop_pct = -20.0
        stop_label = "Stop ETF Cripto (-20%) — volatilidad normal en crypto"
    elif tipo == "ETF_Sectorial":
        stop_pct = -12.0
        stop_label = "Stop ETF Sectorial (-12%)"
    elif tipo == "ETF_LatAm":
        stop_pct = -12.0
        stop_label = "Stop ETF LatAm (-12%)"
    else:
        stop_pct = -10.0
        stop_label = "Stop (-10%)"

    # ══════════════════════════════════════════════════════════
    # LÓGICA ETF — completamente distinta a acciones
    # Los ETF no se venden por señales técnicas individuales
    # ══════════════════════════════════════════════════════════

    if tipo == "ETF_Indice":
        # VOO, SPY, QQQ — acumulación de largo plazo
        # NUNCA vender por señal técnica — solo rebalanceo o necesidad de capital
        if pnl_pct <= -12.0:
            return {
                "señal": "⚠️ Corrección ETF Índice (-12%)",
                "accion": "Considerar AGREGAR posición — el S&P500 siempre se recupera históricamente. Solo salir si necesitas el capital.",
                "urgencia": "REVISAR",
                "tramos": [(0,"MANTENER"),(100,"CONSIDERAR AGREGAR")],
                "color": "2563EB",
            }
        if pnl_pct >= 25.0:
            return {
                "señal": "✅ ETF Índice +25% — Rebalanceo opcional",
                "accion": f"Ganancia +{pnl_pct:.0f}%. Puedes vender 20-30% para rebalancear portafolio. Mantener el resto indefinidamente.",
                "urgencia": "OPCIONAL",
                "tramos": [(25,"REBALANCEO OPCIONAL"),(75,"MANTENER LP")],
                "color": "16A34A",
            }
        if pnl_pct >= 15.0:
            return {
                "señal": f"📈 ETF Índice +{pnl_pct:.0f}% — en tendencia",
                "accion": "Mantener. ETF índice no se vende en tendencia alcista. Stop mental en -12% desde precio de compra.",
                "urgencia": "MANTENER",
                "tramos": [(100,"MANTENER LP")],
                "color": "16A34A",
            }
        if pnl_pct >= 0:
            return {
                "señal": f"📊 ETF Índice +{pnl_pct:.0f}%",
                "accion": "Mantener. Horizonte largo plazo. Agregar en correcciones de -5% o más.",
                "urgencia": "MANTENER",
                "tramos": [(100,"MANTENER LP")],
                "color": "2563EB",
            }
        # En pérdida — oportunidad de agregar
        return {
            "señal": f"⚡ ETF Índice {pnl_pct:.0f}% — oportunidad",
            "accion": f"Pérdida temporal {pnl_pct:.0f}%. Considera agregar más VOO/SPY — las correcciones son oportunidades de acumulación. Stop mental -12%.",
            "urgencia": "REVISAR",
            "tramos": [(100,"MANTENER / AGREGAR")],
            "color": "D97706",
        }

    elif tipo == "ETF_Sectorial":
        # TAN, XBI — sector rotation, horizontes medios
        # Stop -12%, targets +20/40/60%
        if pnl_pct <= -12.0:
            return {
                "señal": "🛑 Stop ETF Sectorial (-12%)",
                "accion": f"Stop activado en -12%. El sector cambió de tendencia. Salir y reasignar a sector más fuerte.",
                "urgencia": "HOY",
                "tramos": [(100,"VENDER TODO")],
                "color": "DC2626",
            }
        if pnl_pct >= 60.0:
            return {
                "señal": f"🚀 ETF Sectorial +{pnl_pct:.0f}% — T3 runner",
                "accion": "Objetivo T3 alcanzado. Vender 50%, mantener 50% con stop en +40% (breakeven alto).",
                "urgencia": "HOY",
                "tramos": [(50,"VENDER 50%"),(50,"RUNNER")],
                "color": "16A34A",
            }
        if pnl_pct >= 40.0:
            return {
                "señal": f"✅ ETF Sectorial +{pnl_pct:.0f}% — T2",
                "accion": "T2 alcanzado (+40%). Vender 40%. Mantener 60% con stop en +20%.",
                "urgencia": "ESTA SEMANA",
                "tramos": [(40,"VENDER 40%"),(60,"MANTENER")],
                "color": "16A34A",
            }
        if pnl_pct >= 20.0:
            return {
                "señal": f"✅ ETF Sectorial +{pnl_pct:.0f}% — T1",
                "accion": "T1 alcanzado (+20%). Vender 30%. Mover stop a breakeven (+0%). Dejar correr al T2 (+40%).",
                "urgencia": "ESTA SEMANA",
                "tramos": [(30,"VENDER 30%"),(70,"MANTENER")],
                "color": "16A34A",
            }
        if pnl_pct >= 0:
            return {
                "señal": f"📈 ETF Sectorial +{pnl_pct:.0f}%",
                "accion": f"En camino al T1 (+20%). Mantener. Stop en -12%.",
                "urgencia": "MANTENER",
                "tramos": [(100,"MANTENER")],
                "color": "2563EB",
            }
        falta_stop = pnl_pct - (-12.0)
        return {
            "señal": f"⚠️ ETF Sectorial {pnl_pct:.0f}%",
            "accion": f"Pérdida {pnl_pct:.0f}%. Stop a {abs(falta_stop):.1f}% de activarse (-12%). Revisar si el sector sigue válido.",
            "urgencia": "VIGILAR",
            "tramos": [(100,"MANTENER")],
            "color": "D97706",
        }

    elif tipo == "ETF_Cripto":
        # IBIT, ETHA — alta volatilidad, ciclos crypto
        # Stop -20%, targets +30/60/100%
        if pnl_pct <= -20.0:
            return {
                "señal": "🛑 Stop ETF Cripto (-20%)",
                "accion": "Stop activado en -20%. Salir del ciclo bajista crypto. Reentrar cuando BTC/ETH retome tendencia alcista.",
                "urgencia": "HOY",
                "tramos": [(100,"VENDER TODO")],
                "color": "DC2626",
            }
        if pnl_pct >= 100.0:
            return {
                "señal": f"🚀 ETF Cripto +{pnl_pct:.0f}% — T3 excepcional",
                "accion": "Objetivo máximo superado. Vender 60%, mantener 40% como runner con stop en +60%.",
                "urgencia": "ESTA SEMANA",
                "tramos": [(60,"VENDER 60%"),(40,"RUNNER")],
                "color": "16A34A",
            }
        if pnl_pct >= 60.0:
            return {
                "señal": f"✅ ETF Cripto +{pnl_pct:.0f}% — T2",
                "accion": "T2 alcanzado (+60%). Vender 40%. Mantener 60% con stop en +30%. Ciclo crypto puede continuar.",
                "urgencia": "ESTA SEMANA",
                "tramos": [(40,"VENDER 40%"),(60,"MANTENER")],
                "color": "16A34A",
            }
        if pnl_pct >= 30.0:
            return {
                "señal": f"✅ ETF Cripto +{pnl_pct:.0f}% — T1",
                "accion": "T1 alcanzado (+30%). Vender 30%. Stop a breakeven (+0%). Dejar correr al T2 (+60%).",
                "urgencia": "ESTA SEMANA",
                "tramos": [(30,"VENDER 30%"),(70,"MANTENER")],
                "color": "16A34A",
            }
        if pnl_pct >= 0:
            falta = 30.0 - pnl_pct
            return {
                "señal": f"📈 ETF Cripto +{pnl_pct:.0f}%",
                "accion": f"En camino al T1 (+30%). Faltan +{falta:.0f}%. Stop en -20%. Ciclos crypto son lentos — paciencia.",
                "urgencia": "MANTENER",
                "tramos": [(100,"MANTENER")],
                "color": "2563EB",
            }
        falta_stop = pnl_pct - (-20.0)
        return {
            "señal": f"⚠️ ETF Cripto {pnl_pct:.0f}%",
            "accion": f"Pérdida {pnl_pct:.0f}%. Stop a {abs(falta_stop):.1f}% de activarse (-20%). Crypto puede caer más — stop es amplio por diseño.",
            "urgencia": "VIGILAR",
            "tramos": [(100,"MANTENER")],
            "color": "D97706",
        }

    # ══════════════════════════════════════════════════════════
    # LÓGICA ACCIONES — T1/T2/Trailing original
    # ══════════════════════════════════════════════════════════

    stop_pct = -7.0
    if pnl_pct <= stop_pct:
        return {
            "señal": f"🛑 STOP ACTIVADO ({stop_pct}%)",
            "accion": f"VENDER TODO AHORA — {stop_label}",
            "urgencia": "AHORA",
            "tramos": [(100, "VENDER TODO")],
            "color": "DC2626",
            "stop_pct": stop_pct,
        }

    # Posición muerta (>5 días en ±1%)
    if dias_posicion >= 5 and abs(pnl_pct) <= 1.0:
        return {
            "señal": "💀 Posición muerta",
            "accion": "Salir y reasignar capital a señal M3 activa",
            "urgencia": "HOY",
            "tramos": [(100, "SALIR")],
            "color": "7C3AED",
        }

    # Trailing stop después de T2
    if pnl_pct >= 12.0 and precio_max > precio_compra:
        trailing_stop = precio_max * 0.95
        trailing_pct  = (trailing_stop - precio_compra) / precio_compra * 100
        if precio_actual <= trailing_stop:
            return {
                "señal": "🔄 Trailing stop activado",
                "accion": f"Vender 20% residual - precio cayó bajo trailing ${trailing_stop:.2f}",
                "urgencia": "AHORA",
                "tramos": [(20, "VENDER 20% RESIDUAL")],
                "color": "D97706",
                "trailing_stop": trailing_stop,
            }
        señales.append(f"Trailing stop en ${trailing_stop:.2f} (+{trailing_pct:.1f}%)")
        color = "16A34A"
        urgencia = "Vigilar"

    # T2 +12% -> vender 40% - SIEMPRE, catalizador no bloquea
    if pnl_pct >= 12.0:
        return {
            "señal": "✅ T2 +12% - Vender 40%",
            "accion": "Vender 40% adicional  - 20% queda con trailing stop -5%",
            "urgencia": "HOY",
            "tramos": [(40, "VENDER 40%"), (40, "YA VENDIDO T1"), (20, "RUNNER + TRAILING")],
            "color": "16A34A",
        }

    # T1 +8% -> vender 40% - SIEMPRE, catalizador no bloquea
    if pnl_pct >= 7.9:  # usar 7.9 para capturar exactamente +8%
        return {
            "señal": "✅ T1 +8% - Vender 40%",
            "accion": "Vender 40%  - Stop remanente a breakeven",
            "urgencia": "HOY",
            "tramos": [(40, "VENDER 40%"), (60, "MANTENER + STOP BE")],
            "color": "16A34A",
        }

    # En camino a T1
    if pnl_pct > 0:
        falta_t1 = 8.0 - pnl_pct
        _stop_precio = round(precio_compra * (1 + stop_pct/100), 2)
        return {
            "señal": f"📈 En camino T1 — faltan +{falta_t1:.1f}%",
            "accion": (f"MANTENER · Stop duro ${_stop_precio:.2f} ({stop_pct}%) · "
                      f"Objetivo T1 +8% · T2 +12%"),
            "urgencia": "Mantener",
            "tramos": [(100, "MANTENER")],
            "color": "2563EB",
            "stop_precio": _stop_precio,
        }

    # En pérdida pero sobre el stop — enriquecer con precio de stop y contexto
    falta_stop  = pnl_pct - stop_pct
    _stop_precio = round(precio_compra * (1 + stop_pct/100), 2)
    _pa_actual   = precio_actual if precio_actual > 0 else precio_compra * (1 + pnl_pct/100)

    # Intentar obtener targets de analistas para enriquecer el contexto
    _targets_msg = ""
    try:
        _pt = get_price_targets(ticker)
        if _pt.get("ok") and _pt.get("target_mean", 0) > 0:
            _up_mean = round((_pt["target_mean"] - _pa_actual) / _pa_actual * 100, 1)
            _na      = _pt.get("n_analysts", 0)
            if _up_mean > 10:
                _targets_msg = (f" · Analistas: target ${_pt['target_mean']:.0f} "
                               f"(+{_up_mean:.0f}% upside · {_na} analistas)")
    except Exception:
        pass

    return {
        "señal": f"⚠️ En pérdida {pnl_pct:+.1f}% · stop en {stop_pct}%",
        "accion": (f"MANTENER · Stop duro ${_stop_precio:.2f} — "
                  f"a {abs(falta_stop):.1f}% de activarse"
                  f"{_targets_msg}"),
        "urgencia": "Vigilar",
        "tramos": [(100, "MANTENER")],
        "color": "D97706",
        "stop_precio": _stop_precio,
        "falta_stop": round(falta_stop, 1),
    }


# ─────────────────────────────────────────────────────────────
#  SCORE DE REBOTE v11 - Reemplaza Prob NBIS + Sim NBIS
#  Basado en condiciones del patrón, no en comparación exacta
# ─────────────────────────────────────────────────────────────
def calcular_score_rebote(dd: float, rsi: float, vol_ratio: float,
                           dias_alcistas: int, momentum_3d: float,
                           tiene_catalizador: bool, dias_para_cat: int,
                           beta: float) -> dict:
    """
    Score de rebote 0-100 basado en 4 componentes:
    30% DD (corrección profunda)
    25% RSI girando desde zona baja
    25% Volumen confirmando
    20% Catalizador próximo
    """
    # ── Componente 1: DD (30 pts) ─────────────────────────────
    # Buscamos corrección real pero no destrucción
    if dd <= -40:
        pts_dd = 25    # muy profundo - posible destrucción
    elif dd <= -30:
        pts_dd = 30    # ideal - corrección severa
    elif dd <= -20:
        pts_dd = 28    # muy bueno
    elif dd <= -15:
        pts_dd = 22    # bueno
    elif dd <= -10:
        pts_dd = 15    # moderado
    elif dd <= -5:
        pts_dd = 8     # leve
    else:
        pts_dd = 0     # en máximos - no hay corrección

    # ── Componente 2: RSI girando (25 pts) ────────────────────
    # RSI bajo + subiendo = zona ideal de entrada
    if rsi <= 30:
        pts_rsi = 25   # sobreventa extrema
    elif rsi <= 38:
        pts_rsi = 23   # sobreventa clara
    elif rsi <= 45:
        pts_rsi = 18   # zona baja - buena entrada
    elif rsi <= 55:
        pts_rsi = 12   # zona media - aceptable
    elif rsi <= 65:
        pts_rsi = 5    # zona alta - precaución
    else:
        pts_rsi = 0    # sobrecomprado - no entrar

    # Bonus si momentum positivo (RSI girando hacia arriba)
    if momentum_3d > 0 and dias_alcistas >= 2:
        pts_rsi = min(pts_rsi + 5, 25)

    # ── Componente 3: Volumen (25 pts) ────────────────────────
    # Volumen alto confirma que el movimiento es real
    if vol_ratio >= 300:
        pts_vol = 25   # excepcional - institucional
    elif vol_ratio >= 200:
        pts_vol = 22   # muy alto
    elif vol_ratio >= 150:
        pts_vol = 18   # alto - buena señal
    elif vol_ratio >= 100:
        pts_vol = 12   # normal
    elif vol_ratio >= 70:
        pts_vol = 6    # bajo
    else:
        pts_vol = 0    # muy bajo - señal débil

    # ── Componente 4: Catalizador (20 pts) ────────────────────
    if tiene_catalizador and dias_para_cat <= 7:
        pts_cat = 20   # earnings en menos de 1 semana
    elif tiene_catalizador and dias_para_cat <= 15:
        pts_cat = 16   # earnings en 2 semanas
    elif tiene_catalizador and dias_para_cat <= 30:
        pts_cat = 10   # earnings en el mes
    elif tiene_catalizador:
        pts_cat = 5    # earnings lejanos
    else:
        pts_cat = 0    # sin catalizador identificado

    # ── Score total ───────────────────────────────────────────
    score_total = pts_dd + pts_rsi + pts_vol + pts_cat

    # Penalización por Beta muy alto sin volumen
    if beta > 3.0 and vol_ratio < 100:
        score_total = max(score_total - 10, 0)

    # Clasificación
    if score_total >= 75:
        nivel = "🔥 FUERTE"
        color = "16A34A"
    elif score_total >= 60:
        nivel = "⚡ BUENO"
        color = "D97706"
    elif score_total >= 45:
        nivel = "🟡 MODERADO"
        color = "2563EB"
    else:
        nivel = "🔵 DÉBIL"
        color = "64748B"

    return {
        "score":      score_total,
        "nivel":      nivel,
        "color":      color,
        "pts_dd":     pts_dd,
        "pts_rsi":    pts_rsi,
        "pts_vol":    pts_vol,
        "pts_cat":    pts_cat,
        "detalle":    f"DD:{pts_dd}/30  - RSI:{pts_rsi}/25  - Vol:{pts_vol}/25  - Cat:{pts_cat}/20",
    }


def calcular_atr(ticker: str, periodo: int = 14) -> float:
    """Calcula ATR (Average True Range) real de los últimos N días."""
    try:
        import yfinance as yf, numpy as np
        import time as _tm_bd
        _tm_bd.sleep(0.05)
        hist = yf.Ticker(ticker).history(period="3mo")
        if hist.empty or len(hist) < periodo + 1:
            return 0.0
        high = hist["High"].values
        low  = hist["Low"].values
        close_prev = hist["Close"].values[:-1]
        high_c = high[1:]
        low_c  = low[1:]
        tr = np.maximum(high_c - low_c,
             np.maximum(abs(high_c - close_prev),
                        abs(low_c  - close_prev)))
        atr = float(np.mean(tr[-periodo:]))
        return round(atr, 4)
    except Exception:
        return 0.0


def sizing_por_atr(ticker: str, precio_actual: float,
                   capital_riesgo_usd: float = 500,
                   atr_mult: float = 1.5,
                   score: int = 50,
                   vix_val: float = 20) -> dict:
    """
    Sizing profesional basado en ATR - v16.
    Fórmula: acciones = capital_riesgo / (ATR x atr_mult)

    Ejemplo NBIS: ATR=$8, riesgo=$500, mult=1.5
    -> stop = precio - (8x1.5) = precio - $12
    -> acciones = 500/12 = 41 acciones
    -> riesgo real = 41 x $12 = $492

    Parámetros:
      capital_riesgo_usd: cuánto estás dispuesto a perder en este trade
      atr_mult: multiplicador del ATR para el stop (default 1.5)
      score: score del modelo (ajusta el sizing)
      vix_val: VIX actual (ajusta el sizing en pánico)
    """
    atr = calcular_atr(ticker)

    # Si no hay ATR, usar % fijo del precio como fallback
    if atr <= 0:
        atr = precio_actual * 0.03  # 3% del precio = ATR estimado

    stop_distancia  = round(atr * atr_mult, 2)
    stop_precio     = round(precio_actual - stop_distancia, 2)
    stop_pct        = round(stop_distancia / precio_actual * 100, 1)

    # Cantidad de acciones
    acciones_raw    = capital_riesgo_usd / stop_distancia
    acciones        = max(1, int(acciones_raw))

    # Ajuste por score del modelo
    if score >= 75:
        score_mult = 1.0;   score_label = "Señal fuerte - 100%"
    elif score >= 60:
        score_mult = 0.75;  score_label = "Señal buena - 75%"
    elif score >= 45:
        score_mult = 0.50;  score_label = "Señal moderada - 50%"
    else:
        score_mult = 0.25;  score_label = "Señal débil - 25%"

    # Ajuste por VIX (pánico = oportunidad = más tamaño)
    if vix_val >= 35:
        vix_mult = 1.20;  vix_label = "VIX pánico -> +20%"
    elif vix_val >= 25:
        vix_mult = 1.10;  vix_label = "VIX miedo -> +10%"
    elif vix_val < 15:
        vix_mult = 0.80;  vix_label = "VIX complacencia -> -20%"
    else:
        vix_mult = 1.0;   vix_label = "VIX normal -> sin ajuste"

    acciones_final  = max(1, int(acciones * score_mult * vix_mult))
    capital_total   = round(acciones_final * precio_actual, 2)
    riesgo_real     = round(acciones_final * stop_distancia, 2)

    # Targets basados en ATR
    t1 = round(precio_actual + atr * 2, 2)   # T1: +2 ATR (~60% posición)
    t2 = round(precio_actual + atr * 4, 2)   # T2: +4 ATR (~30% posición)
    t3 = round(precio_actual + atr * 6, 2)   # T3: +6 ATR (runner 10%)

    return {
        "ticker":           ticker,
        "precio":           precio_actual,
        "atr":              round(atr, 2),
        "atr_mult":         atr_mult,
        "stop_distancia":   stop_distancia,
        "stop_precio":      stop_precio,
        "stop_pct":         stop_pct,
        "acciones":         acciones_final,
        "capital_total":    capital_total,
        "riesgo_real":      riesgo_real,
        "score_mult":       score_mult,
        "score_label":      score_label,
        "vix_mult":         vix_mult,
        "vix_label":        vix_label,
        "t1":               t1,
        "t2":               t2,
        "t3":               t3,
        "t1_pct":           round((t1/precio_actual-1)*100, 1),
        "t2_pct":           round((t2/precio_actual-1)*100, 1),
        "t3_pct":           round((t3/precio_actual-1)*100, 1),
        "formula":          f"{acciones_final} acc x ${stop_distancia:.2f} stop = ${riesgo_real:.0f} riesgo real",
        "detalle":          f"ATR ${atr:.2f} x {atr_mult} = stop ${stop_distancia:.2f} ({stop_pct}%)",
    }


def clasificar_sizing(score: int, vix: float) -> dict:
    """Legacy - se mantiene para compatibilidad. Usar sizing_por_atr() en v16."""
    return sizing_por_atr("", 100, score=score, vix_val=vix)


def generar_csv_posiciones_actualizado(posiciones_df: pd.DataFrame,
                                        resultados: list,
                                        nombre_archivo: str) -> bytes:
    """
    Genera CSV actualizado de posiciones aplicando salidas T1/T2.
    Si T1 se activó: reduce cantidad en 40%
    Si T2 se activó: reduce cantidad en 40% adicional
    Si Stop: elimina la posición
    Si Muerta: marca para revisión
    """
    import datetime as _dt
    rows_nuevas = []

    for res in resultados:
        tk      = res.get("ticker","")
        pnl     = res.get("pnl_pct", 0)
        analisis= res.get("analisis_v12",{})
        urgencia= analisis.get("urgencia","-")
        señal   = analisis.get("señal","-")

        # Buscar en posiciones_df
        mask = posiciones_df["Ticker"].str.upper() == tk.upper()
        if not mask.any():
            continue
        row = posiciones_df[mask].iloc[0]
        qty_original = float(row.get("Cantidad", 0))

        # Aplicar salidas
        if "STOP" in señal or urgencia == "AHORA" and "Trailing" not in señal:
            # Stop activado -> no incluir (posición cerrada)
            continue
        elif "T2 +12%" in señal:
            # T2: ya se vendió 40% en T1 + 40% en T2 -> queda 20%
            qty_nueva = round(qty_original * 0.20, 6)
            nota = "20% runner post-T2"
        elif "T1 +8%" in señal:
            # T1: se vendió 40% -> queda 60%
            qty_nueva = round(qty_original * 0.60, 6)
            nota = "60% post-T1  - stop en breakeven"
        elif "muerta" in señal.lower():
            # Posición muerta -> marcar pero mantener
            qty_nueva = qty_original
            nota = "⚠️ Revisar - posición muerta"
        else:
            qty_nueva = qty_original
            nota = ""

        nueva_fila = {
            "Ticker":        row["Ticker"],
            "Fecha":         row["Fecha"],
            "Precio_Compra": row["Precio_Compra"],
            "Cantidad":      qty_nueva,
            "Cat_Fecha":     row.get("Cat_Fecha","-"),
            "Tipo":          row.get("Tipo","Accion"),
            "Estrategia":    row.get("Estrategia","Swing"),
            "Fase_Origen":   row.get("Fase_Origen","-"),
            "Notas_Salida":  nota,
        }
        rows_nuevas.append(nueva_fila)

    if not rows_nuevas:
        return b""

    df_nuevo = pd.DataFrame(rows_nuevas)
    return df_nuevo.to_csv(index=False, sep=";", decimal=",",
                           encoding="utf-8-sig").encode("utf-8-sig")


def calcular_score_gestion(pnl_pct: float, dias_posicion: int,
                             precio_max: float, precio_actual: float,
                             precio_compra: float) -> dict:
    """
    Score de GESTIÓN de posición abierta (diferente al Score de entrada)
    No usa RSI ni indicadores técnicos - usa PnL real
    0-100: mayor score = mantener más tiempo
    """
    score = 50  # neutral base

    # PnL actual
    if pnl_pct >= 12:
        score += 30
    elif pnl_pct >= 8:
        score += 20
    elif pnl_pct >= 4:
        score += 10
    elif pnl_pct >= 0:
        score += 0
    elif pnl_pct >= -4:
        score -= 15
    elif pnl_pct >= -7:
        score -= 30
    else:
        score -= 50

    # Días en posición
    if dias_posicion > 8:
        score -= 20
    elif dias_posicion > 5:
        score -= 10

    # Distancia desde máximo
    if precio_max > 0 and precio_compra > 0:
        caida_max = (precio_actual - precio_max) / precio_max * 100
        if caida_max < -10:
            score -= 15
        elif caida_max < -5:
            score -= 5

    score = max(0, min(100, score))

    if score >= 70:
        return {"score": score, "accion": "Mantener", "color": "16A34A"}
    elif score >= 50:
        return {"score": score, "accion": "Vigilar", "color": "D97706"}
    elif score >= 30:
        return {"score": score, "accion": "Preparar salida", "color": "F97316"}
    else:
        return {"score": score, "accion": "Salir", "color": "DC2626"}


@st.cache_data(ttl=300, show_spinner=False)
def scan_detectadas(rsi_min: float = 35, rsi_max: float = 60,
                    dd_min: float = -8, score_min: int = 15,
                    max_results: int = 100, universo: list = None) -> pd.DataFrame:
    """
    Scanner de Detectadas M1 usando yfinance directo.
    Busca acciones EN CORRECCIÓN (aún bajando) con Prob NBIS >= 20%.
    M1: RSI 35-60  - DD <= -8%  - corrección activa
    """
    import yfinance as yf
    candidatos = []
    _universo = universo if universo else SCAN_UNIVERSE

    try:
        for tk in _universo:
            try:
                _ETF_SKIP = {"XLE","XLI","XLY","XLC","XLB","XLP","XLRE","GLD",
                             "SLV","USO","UNG","JETS","HACK","BOTZ","ROBO",
                             "COPX","ARKG","ARKF","ARKQ","SOXX","IBB","ARKK"}
                if tk in _ETF_SKIP:
                    continue

                hist = yf.Ticker(tk).history(period="3mo")
                if hist.empty or len(hist) < 20:
                    continue

                close = hist["Close"].values
                vol   = hist["Volume"].values
                precio = float(close[-1])

                # v17 Fix AMD-F3: DD medido desde pico de 52 semanas
                # Antes: pico solo desde los últimos 3 meses → subestimaba la corrección
                # Ahora: pico real de 52 semanas para DD correcto
                try:
                    import datetime as _dt_52w
                    _e52 = _dt_52w.date.today()
                    _s52 = _e52 - _dt_52w.timedelta(days=365)
                    hist_52w = yf.Ticker(tk).history(
                        start=_s52.strftime("%Y-%m-%d"),
                        end=_e52.strftime("%Y-%m-%d"))
                    pico = float(hist_52w["Close"].max()) if not hist_52w.empty else float(close.max())
                except Exception:
                    pico = float(close.max())

                dd = round((precio - pico) / pico * 100, 1)

                # Filtro DD - corrección real
                if dd > dd_min:
                    continue

                # RSI
                import pandas as _pd_d
                s = _pd_d.Series(close)
                delta = s.diff()
                gain = delta.clip(lower=0).rolling(14).mean()
                loss = (-delta.clip(upper=0)).rolling(14).mean()
                rsi = round(float(100-100/(1+gain.iloc[-1]/(loss.iloc[-1]+1e-9))), 1)

                if not (rsi_min <= rsi <= rsi_max):
                    continue

                # Volumen
                avg_v = float(import_np().mean(vol[-20:]))
                vol_ratio = int(vol[-1] / avg_v * 100) if avg_v > 0 else 100
                if avg_v < 200_000:
                    continue

                # Momentum 3d
                mom_3d = round((close[-1]/close[-4]-1)*100, 2) if len(close)>=4 else 0

                # Días bajistas (para M1 - aún cayendo)
                dias_bajistas = 0
                for _i in range(1, min(5, len(close))):
                    if close[-_i] < close[-_i-1]:
                        dias_bajistas += 1
                    else:
                        break

                # Score Rebote
                sr = calcular_score_rebote(
                    dd=dd, rsi=rsi, vol_ratio=vol_ratio,
                    dias_alcistas=0, momentum_3d=mom_3d,
                    tiene_catalizador=False, dias_para_cat=999,
                    beta=1.5
                )
                if sr["score"] < score_min:
                    continue

                # Prob NBIS
                prob = calcular_prob_nbis(
                    rsi=rsi, vol_ratio=vol_ratio, dd=dd,
                    dias_alcistas=0, momentum_3d=mom_3d,
                    tiene_catalizador=False
                )
                if prob < 20:
                    continue

                # Etapa v12
                # v16 fix: obtener earnings live + area real desde yfinance info
                try:
                    _info_d1 = yf.Ticker(tk).info or {}
                except Exception:
                    _info_d1 = {}

                # Área real desde sector
                _sector_d1 = _info_d1.get("sector", "-")
                _sector_map_d1 = {
                    "Technology":"Tech","Healthcare":"Salud",
                    "Financial Services":"Finanzas",
                    "Consumer Cyclical":"Consumo",
                    "Consumer Defensive":"Consumo",
                    "Energy":"Energía","Industrials":"Industrial",
                    "Communication Services":"Tech",
                    "Basic Materials":"Materiales",
                    "Real Estate":"Real Estate",
                }
                _area_d1 = _sector_map_d1.get(_sector_d1,
                           _sector_d1[:10] if _sector_d1 and _sector_d1 != "-" else "-")

                # Earnings live — usar get_earnings_single() con cache
                _cat_fecha_d1 = get_earnings_single(tk)

                # Etapa con earnings real
                etapa = clasificar_etapa_v12(
                    rsi=rsi, vol_ratio=vol_ratio, prob_nbis=prob,
                    dias_alcistas=0, momentum_3d=mom_3d,
                    score_rebote=sr["score"], dd=dd,
                    cat_fecha=_cat_fecha_d1
                )

                # Sympathy data
                _symp_d1 = get_sympathy(tk)

                candidatos.append({
                    "Ticker":        tk,
                    "Precio":        round(precio, 2),
                    "DD_pico":       dd,
                    "RSI":           rsi,
                    "Div_RSI":       _div_sw.get("tipo","none"),
                    "Div_Badge":     _div_sw.get("badge",""),
                    "Div_Desc":      _div_sw.get("descripcion",""),
                    "Volumen":       vol_ratio,
                    "Momentum_3d":   mom_3d,
                    "Dias_Bajistas": dias_bajistas,
                    "Score_Rebote":  sr["score"],
                    "Nivel_Rebote":  sr["nivel"],
                    "Detalle_Rebote":sr["detalle"],
                    "Prob_NBIS":     prob,
                    "Etapa_v12":     etapa["label"],
                    "Decision":      "SEGUIR",
                    "Fase":          "M1",
                    "Area":          _area_d1,        # v16 fix: área real
                    "Motivo":        f"Corrección {dd}% · RSI {rsi} · Prob {prob}%",
                    "Lectura":       etapa["accion"],
                    "Score":         sr["score"],
                    "Cat_Fecha":     _cat_fecha_d1,   # v16 fix: earnings live
                    "Cat_Desc":      _info_d1.get("longBusinessSummary","")[:80] if _cat_fecha_d1 != "-" else "-",
                    "Cat_Tipo":      "Earnings" if _cat_fecha_d1 != "-" else "-",
                    "Arrastradas":   _symp_d1["arrastradas"],
                    "Lider":         _symp_d1["lider"],
                    "Color":         "#" + etapa["color"],
                    "Bg":            "#" + etapa["bg"],
                })
            except Exception:
                continue
    except Exception:
        pass

    if not candidatos:
        return pd.DataFrame()

    try:
        df_d = pd.DataFrame(candidatos)
        # Ordenar por DD más profundo primero
        df_d = df_d.sort_values("DD_pico", ascending=True)
        return df_d.head(max_results)
    except Exception:
        return pd.DataFrame()


# ═════════════════════════════════════════════════════════════
#  MÓDULO BACKTESTING v13
#  Soporte/Resistencia + Backtesting 6 meses automático
# ═════════════════════════════════════════════════════════════

def calcular_soporte_resistencia(close: list, high: list, low: list) -> dict:
    """
    Calcula niveles de soporte y resistencia técnicos.
    Usa pivots, EMA200 y rangos de 52 semanas.
    """
    import numpy as np
    close = list(close)
    high  = list(high)
    low   = list(low)
    n     = len(close)

    # EMA200
    ema200 = None
    if n >= 200:
        import pandas as _pd_sr
        ema200 = float(_pd_sr.Series(close).ewm(span=200).mean().iloc[-1])

    # Soporte/Resistencia 52 semanas
    n_año = min(252, n)
    max_año = max(high[-n_año:])
    min_año = min(low[-n_año:])

    # Pivot Points últimos 20 días
    pivots_sup = []
    pivots_inf = []
    for i in range(2, min(20, n-2)):
        idx = -(i+1)
        if high[idx] > high[idx-1] and high[idx] > high[idx+1]:
            pivots_sup.append(high[idx])
        if low[idx] < low[idx-1] and low[idx] < low[idx+1]:
            pivots_inf.append(low[idx])

    precio = close[-1]

    # Soporte más cercano por debajo del precio
    soportes = sorted([x for x in pivots_inf if x < precio], reverse=True)
    soporte_cercano = soportes[0] if soportes else min_año

    # Resistencia más cercana por encima
    resistencias = sorted([x for x in pivots_sup if x > precio])
    resistencia_cercana = resistencias[0] if resistencias else max_año

    # ¿Precio cerca de soporte? (dentro del 3%)
    cerca_soporte = abs(precio - soporte_cercano) / precio < 0.03 if soporte_cercano else False
    cerca_resistencia = abs(precio - resistencia_cercana) / precio < 0.03 if resistencia_cercana else False

    # Sobre o bajo EMA200
    sobre_ema200 = precio > ema200 if ema200 else None

    return {
        "soporte":           round(soporte_cercano, 2),
        "resistencia":       round(resistencia_cercana, 2),
        "min_52s":           round(min_año, 2),
        "max_52s":           round(max_año, 2),
        "ema200":            round(ema200, 2) if ema200 else None,
        "cerca_soporte":     cerca_soporte,
        "cerca_resistencia": cerca_resistencia,
        "sobre_ema200":      sobre_ema200,
        "dist_soporte_pct":  round((precio - soporte_cercano) / precio * 100, 1),
        "dist_resist_pct":   round((resistencia_cercana - precio) / precio * 100, 1),
    }


def backtest_ticker(tk: str, meses: int = 6) -> list:
    """
    Backtesting automático para un ticker.
    Simula señales M2/M3 en los últimos N meses
    y verifica si rebotaron +8% / +12% en 10 días.
    """
    import yfinance as yf
    import pandas as pd
    import numpy as np

    resultados = []
    try:
        hist = yf.Ticker(tk).history(period=f"{meses}mo")
        if hist.empty or len(hist) < 60:
            return []

        close_arr = hist["Close"].values
        vol_arr   = hist["Volume"].values
        high_arr  = hist["High"].values
        low_arr   = hist["Low"].values
        dates     = hist.index.tolist()
        n         = len(close_arr)

        # Necesitamos al menos 20 días de historia + 10 días de resultado
        for i in range(20, n - 10):
            close_h = close_arr[:i+1]
            vol_h   = vol_arr[:i+1]
            high_h  = high_arr[:i+1]
            low_h   = low_arr[:i+1]

            precio  = float(close_h[-1])
            pico    = float(close_h.max())
            dd      = round((precio - pico) / pico * 100, 1)

            if dd > -5:  # sin corrección suficiente
                continue

            # RSI
            s     = pd.Series(close_h)
            delta = s.diff()
            gain  = delta.clip(lower=0).rolling(14).mean()
            loss  = (-delta.clip(upper=0)).rolling(14).mean()
            rsi   = float(100 - 100/(1 + gain.iloc[-1]/(loss.iloc[-1]+1e-9)))

            if not (25 <= rsi <= 65):
                continue

            # Volumen ratio
            avg_v = float(np.mean(vol_h[-20:]))
            vol_r = int(vol_h[-1] / avg_v * 100) if avg_v > 0 else 100

            # Momentum 3d
            mom = round((close_h[-1]/close_h[-4]-1)*100, 2) if len(close_h)>=4 else 0

            # Días alcistas
            dias_alc = 0
            for _j in range(1, min(5, len(close_h))):
                if close_h[-_j] > close_h[-_j-1]:
                    dias_alc += 1
                else:
                    break

            # Prob NBIS
            prob = calcular_prob_nbis(
                rsi=rsi, vol_ratio=vol_r, dd=dd,
                dias_alcistas=dias_alc, momentum_3d=mom,
                tiene_catalizador=False
            )

            # Soporte/Resistencia
            sr = calcular_soporte_resistencia(close_h, high_h, low_h)

            # Clasificar fase
            if rsi <= 35 and dias_alc >= 3 and mom >= 5 and vol_r >= 60:
                fase = "M3"
            elif 30 <= rsi <= 45 and dias_alc >= 1 and mom >= 1 and vol_r >= 50:
                fase = "M2"
            else:
                continue

            # Simular resultado en los 10 días siguientes
            precio_entrada = precio
            max_alcanzado  = precio_entrada
            stop_activado  = False
            t1_alcanzado   = False
            t2_alcanzado   = False
            resultado_dia10 = 0

            for d in range(1, 11):
                if i + d >= n:
                    break
                p_dia = float(close_arr[i + d])
                pnl   = (p_dia - precio_entrada) / precio_entrada * 100
                max_alcanzado = max(max_alcanzado, p_dia)

                if pnl <= -7:
                    stop_activado = True
                    resultado_dia10 = pnl
                    break
                if pnl >= 12:
                    t2_alcanzado = True
                    t1_alcanzado = True
                if pnl >= 8:
                    t1_alcanzado = True

                if d == 10:
                    resultado_dia10 = pnl

            ganadora = t1_alcanzado and not stop_activado

            # v16: ATR real en el punto de entrada + stop real calculado
            try:
                atr_val = float(np.mean(
                    np.maximum(
                        high_h[-14:] - low_h[-14:],
                        np.maximum(
                            abs(high_h[-14:] - close_h[-15:-1]),
                            abs(low_h[-14:]  - close_h[-15:-1])
                        )
                    )
                )) if len(high_h) >= 15 else precio_entrada * 0.03
            except Exception:
                atr_val = precio_entrada * 0.03

            stop_atr    = round(precio_entrada - atr_val * 1.5, 2)
            stop_pct_bt = round(atr_val * 1.5 / precio_entrada * 100, 1)
            precio_max  = round(float(max_alcanzado), 2)
            precio_salida = round(float(close_arr[min(i+10, n-1)]), 2)
            resultado_real = round((precio_salida - precio_entrada)/precio_entrada*100, 2)

            resultados.append({
                "Ticker":          tk,
                "Fecha":           str(dates[i])[:10],
                "Fase":            fase,
                "Precio_Entrada":  round(precio_entrada, 2),
                "Precio_Salida":   precio_salida,
                "Precio_Max":      precio_max,
                "RSI":             round(rsi, 1),
        "Div_RSI":         _div_fetch.get("tipo","none"),
        "Div_Badge":       _div_fetch.get("badge",""),
        "Div_Desc":        _div_fetch.get("descripcion",""),
                "DD":              dd,
                "Vol_Ratio":       vol_r,
                "Momentum_3d":     round(mom, 1),
                "Dias_Alcistas":   dias_alc,
                "Prob_NBIS":       prob,
                "Cerca_Soporte":   sr["cerca_soporte"],
                "Dist_Soporte":    sr["dist_soporte_pct"],
                "ATR_Entrada":     round(atr_val, 2),
                "Stop_ATR":        stop_atr,
                "Stop_Pct":        stop_pct_bt,
                "Resultado_10d":   round(resultado_dia10, 2),
                "Resultado_Real":  resultado_real,
                "T1_Alcanzado":    t1_alcanzado,
                "T2_Alcanzado":    t2_alcanzado,
                "Stop_Activado":   stop_activado,
                "Ganadora":        ganadora,
            })

    except Exception:
        pass

    return resultados



# ─────────────────────────────────────────────────────────────
#  BACKTESTING REAL v16
#  Usa precios históricos reales de entrada y salida
#  Calcula win rate, avg gain, avg loss y ratio R/R verdaderos
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def backtest_real_v16(ticker: str, meses: int = 6,
                      stop_atr_mult: float = 1.5,
                      target1_pct: float = 8.0,
                      target2_pct: float = 15.0,
                      dias_max: int = 15) -> dict:
    """
    Backtesting real v16 - calcula win rate con precios exactos.

    Para cada señal M2/M3 detectada en el período:
    - Precio entrada = Close del día de señal
    - Stop = Close - (ATR x 1.5) calculado en ese momento
    - Target 1 = +8%, Target 2 = +15%
    - Salida = primer evento que ocurra en días_max días

    Retorna estadísticas reales:
    - win_rate, avg_ganancia, avg_perdida, ratio_rr, expectativa
    """
    import yfinance as yf, numpy as np, pandas as pd

    resultado_base = {
        "ticker": ticker, "n_señales": 0, "n_ganadoras": 0,
        "n_perdedoras": 0, "win_rate": 0, "avg_ganancia": 0,
        "avg_perdida": 0, "ratio_rr": 0, "expectativa": 0,
        "max_ganancia": 0, "max_perdida": 0,
        "trades": [], "_ok": False, "error": ""
    }

    try:
        hist = yf.Ticker(ticker).history(period=f"{meses}mo")
        if hist is None or len(hist) < 60:
            resultado_base["error"] = "Insuficientes datos históricos"
            return resultado_base

        close = hist["Close"].values
        high  = hist["High"].values
        low   = hist["Low"].values
        vol   = hist["Volume"].values
        dates = [str(d)[:10] for d in hist.index.tolist()]
        n     = len(close)

        trades = []

        for i in range(20, n - dias_max - 1):
            ch = close[:i+1]
            vh = vol[:i+1]
            hh = high[:i+1]
            lh = low[:i+1]

            precio = float(ch[-1])
            pico   = float(ch.max())
            dd     = round((precio - pico) / pico * 100, 1)
            if dd > -5:
                continue

            # RSI
            s     = pd.Series(ch)
            delta = s.diff()
            gain  = delta.clip(lower=0).rolling(14).mean()
            loss  = (-delta.clip(upper=0)).rolling(14).mean()
            rsi   = float(100 - 100/(1 + gain.iloc[-1]/(loss.iloc[-1]+1e-9)))
            if not (25 <= rsi <= 55):
                continue

            # Volumen
            avg_v = float(np.mean(vh[-20:])) if len(vh) >= 20 else float(vh[-1])
            vol_r = int(vh[-1] / avg_v * 100) if avg_v > 0 else 100
            if vol_r < 50:
                continue

            # Días alcistas
            dias_alc = 0
            for j in range(1, min(5, len(ch))):
                if ch[-j] > ch[-j-1]: dias_alc += 1
                else: break
            if dias_alc < 2:
                continue

            # Momentum
            mom = round((ch[-1]/ch[-4]-1)*100, 2) if len(ch) >= 4 else 0

            # Fase
            if rsi <= 42 and dias_alc >= 3 and mom >= 3 and vol_r >= 50 and dd <= -8:
                fase = "M3"
            elif 30 <= rsi <= 45 and dias_alc >= 2 and mom >= 1 and vol_r >= 50 and dd <= -8:
                fase = "M2"
            else:
                continue

            # ATR real en el momento de la señal
            if i >= 15:
                tr_list = []
                for k in range(i-13, i+1):
                    hl  = float(hh[k]) - float(lh[k])
                    hcp = abs(float(hh[k]) - float(ch[k-1]))
                    lcp = abs(float(lh[k]) - float(ch[k-1]))
                    tr_list.append(max(hl, hcp, lcp))
                atr_actual = float(np.mean(tr_list))
            else:
                atr_actual = precio * 0.025  # fallback 2.5%

            stop_dist   = round(atr_actual * stop_atr_mult, 4)
            stop_precio = round(precio - stop_dist, 2)
            t1_precio   = round(precio * (1 + target1_pct/100), 2)
            t2_precio   = round(precio * (1 + target2_pct/100), 2)

            # Simular resultado real en días siguientes
            precio_salida  = None
            pnl_pct        = 0.0
            razon_salida   = "timeout"
            dia_salida     = dias_max

            for d in range(1, dias_max + 1):
                if i + d >= n:
                    precio_salida = float(close[i + d - 1])
                    razon_salida  = "fin datos"
                    dia_salida    = d
                    break
                p_low  = float(low[i + d])
                p_high = float(high[i + d])
                p_close= float(close[i + d])

                # Stop activado (bajo del día toca stop)
                if p_low <= stop_precio:
                    precio_salida = stop_precio
                    razon_salida  = "stop"
                    dia_salida    = d
                    break
                # Target 2 alcanzado
                if p_high >= t2_precio:
                    precio_salida = t2_precio
                    razon_salida  = "T2 +15%"
                    dia_salida    = d
                    break
                # Target 1 alcanzado
                if p_high >= t1_precio:
                    precio_salida = t1_precio
                    razon_salida  = "T1 +8%"
                    dia_salida    = d
                    break
                # Timeout - salir al cierre del último día
                if d == dias_max:
                    precio_salida = p_close
                    razon_salida  = f"timeout {dias_max}d"
                    dia_salida    = d

            if precio_salida is None:
                precio_salida = float(close[min(i + dias_max, n-1)])

            pnl_pct  = round((precio_salida - precio) / precio * 100, 2)
            ganadora = pnl_pct > 0

            trades.append({
                "Ticker":         ticker,
                "Fecha":          dates[i],
                "Fase":           fase,
                "Precio_Entrada": round(precio, 2),
                "Precio_Salida":  round(precio_salida, 2),
                "PnL_pct":        pnl_pct,
                "Razon_Salida":   razon_salida,
                "Dia_Salida":     dia_salida,
                "ATR":            round(atr_actual, 2),
                "Stop":           stop_precio,
                "T1":             t1_precio,
                "T2":             t2_precio,
                "RSI":            round(rsi, 1),
                "DD":             dd,
                "Vol_Ratio":      vol_r,
                "Ganadora":       ganadora,
            })

        if not trades:
            resultado_base["error"] = "Sin señales detectadas en el período"
            return resultado_base

        # Estadísticas reales
        n_tot  = len(trades)
        n_win  = sum(1 for t in trades if t["Ganadora"])
        n_lose = n_tot - n_win
        ganancias = [t["PnL_pct"] for t in trades if t["Ganadora"]]
        perdidas  = [t["PnL_pct"] for t in trades if not t["Ganadora"]]

        avg_g   = round(float(np.mean(ganancias)), 2) if ganancias else 0
        avg_p   = round(float(np.mean(perdidas)), 2) if perdidas else 0
        max_g   = round(max(ganancias), 2) if ganancias else 0
        max_p   = round(min(perdidas), 2) if perdidas else 0
        win_r   = round(n_win / n_tot * 100, 1)
        ratio   = round(abs(avg_g / avg_p), 2) if avg_p != 0 else 0
        # Expectativa = win% x avg_gain + lose% x avg_loss
        expectativa = round((n_win/n_tot) * avg_g + (n_lose/n_tot) * avg_p, 2) if n_tot > 0 else 0

        return {
            "ticker": ticker, "n_señales": n_tot,
            "n_ganadoras": n_win, "n_perdedoras": n_lose,
            "win_rate": win_r, "avg_ganancia": avg_g,
            "avg_perdida": avg_p, "ratio_rr": ratio,
            "expectativa": expectativa,
            "max_ganancia": max_g, "max_perdida": max_p,
            "trades": trades, "_ok": True, "error": "",
        }

    except Exception as e:
        resultado_base["error"] = str(e)
        return resultado_base

@st.cache_data(ttl=3600, show_spinner=False)
def run_backtesting(tickers: tuple, meses: int = 6) -> "pd.DataFrame":
    """Ejecuta backtesting para lista de tickers. Retorna DataFrame con resultados."""
    import pandas as pd
    todos = []
    for tk in tickers:
        todos.extend(backtest_ticker(tk, meses))
    if not todos:
        return pd.DataFrame()
    return pd.DataFrame(todos)


# ─────────────────────────────────────────────────────────────
#  BACKTESTING PATRÓN NBIS EXACTO v13
#  Criterios: RSI <= 35  - Mom >= +7%  - DD <= -15%  - Vol >= 150%
#  Referencia NBIS: RSI 38, Vol 280%, DD -55%, Mom +27%
# ─────────────────────────────────────────────────────────────
NBIS_CRITERIOS = {
    "rsi_max":       35.0,   # RSI <= 35
    "mom_min":        7.0,   # Momentum 3d >= +7%
    "dd_max":       -15.0,   # DD <= -15%
    "vol_min":      150.0,   # Volumen >= 150% del promedio
    "dias_alc_min":   2,     # Mínimo 2 días alcistas
    "stop":          -7.0,   # Stop -7%
    "t1":             8.0,   # Target 1 +8%
    "t2":            12.0,   # Target 2 +12%
    "dias_max":      10,     # Máximo 10 días
}

@st.cache_data(ttl=7200, show_spinner=False)
def run_backtesting_nbis(tickers: tuple, meses: int = 6) -> "pd.DataFrame":
    """
    Backtesting con criterios exactos del patrón NBIS.
    Más estricto que el backtesting general.
    """
    import yfinance as yf
    import pandas as pd
    import numpy as np

    todos = []
    cr    = NBIS_CRITERIOS

    for tk in tickers:
        try:
            hist = yf.Ticker(tk).history(period=f"{meses}mo")
            if hist.empty or len(hist) < 60:
                continue

            close = hist["Close"].values
            vol   = hist["Volume"].values
            high  = hist["High"].values
            low   = hist["Low"].values
            dates = hist.index.tolist()
            n     = len(close)

            for i in range(20, n - 10):
                cl_h  = close[:i+1]
                vol_h = vol[:i+1]

                # DD
                precio = float(cl_h[-1])
                pico   = float(cl_h.max())
                dd     = round((precio - pico) / pico * 100, 1)
                if dd > cr["dd_max"]:
                    continue

                # RSI
                import pandas as _pd
                s     = _pd.Series(cl_h)
                delta = s.diff()
                gain  = delta.clip(lower=0).rolling(14).mean()
                loss  = (-delta.clip(upper=0)).rolling(14).mean()
                rsi   = float(100-100/(1+gain.iloc[-1]/(loss.iloc[-1]+1e-9)))
                if rsi > cr["rsi_max"]:
                    continue

                # Momentum 3d
                mom = round((cl_h[-1]/cl_h[-4]-1)*100, 2) if len(cl_h)>=4 else 0
                if mom < cr["mom_min"]:
                    continue

                # Volumen
                avg_v = float(np.mean(vol_h[-20:]))
                vol_r = int(vol_h[-1]/avg_v*100) if avg_v > 0 else 0
                if vol_r < cr["vol_min"]:
                    continue

                # Días alcistas
                dias_alc = 0
                for _j in range(1, min(5, len(cl_h))):
                    if cl_h[-_j] > cl_h[-_j-1]:
                        dias_alc += 1
                    else:
                        break
                if dias_alc < cr["dias_alc_min"]:
                    continue

                # Prob NBIS
                prob = calcular_prob_nbis(
                    rsi=rsi, vol_ratio=vol_r, dd=dd,
                    dias_alcistas=dias_alc, momentum_3d=mom,
                    tiene_catalizador=False
                )

                # Soporte/Resistencia
                sr_data = calcular_soporte_resistencia(cl_h, high[:i+1], low[:i+1])

                # Simular resultado 10 días
                precio_e   = precio
                stop_act   = False
                t1_act     = False
                t2_act     = False
                res_10d    = 0
                precio_max = precio_e

                for d in range(1, 11):
                    if i+d >= n:
                        break
                    p_d = float(close[i+d])
                    pnl = (p_d - precio_e) / precio_e * 100
                    precio_max = max(precio_max, p_d)

                    if pnl <= cr["stop"]:
                        stop_act = True
                        res_10d  = pnl
                        break
                    if pnl >= cr["t2"]:
                        t2_act = True
                        t1_act = True
                    if pnl >= cr["t1"]:
                        t1_act = True
                    if d == 10:
                        res_10d = pnl

                ganadora = t1_act and not stop_act

                todos.append({
                    "Ticker":          tk,
                    "Fecha":           str(dates[i])[:10],
                    "RSI":             round(rsi, 1),
                    "DD":              dd,
                    "Momentum_3d":     round(mom, 1),
                    "Vol_Ratio":       vol_r,
                    "Dias_Alcistas":   dias_alc,
                    "Prob_NBIS":       prob,
                    "Precio_Entrada":  round(precio_e, 2),
                    "Cerca_Soporte":   sr_data["cerca_soporte"],
                    "EMA200":          sr_data["ema200"],
                    "Sobre_EMA200":    sr_data["sobre_ema200"],
                    "Resultado_10d":   round(res_10d, 2),
                    "T1_Alcanzado":    t1_act,
                    "T2_Alcanzado":    t2_act,
                    "Stop_Activado":   stop_act,
                    "Ganadora":        ganadora,
                    "Max_Alcanzado_Pct": round((precio_max-precio_e)/precio_e*100, 1),
                })
        except Exception:
            continue

    if not todos:
        return pd.DataFrame()
    return pd.DataFrame(todos)

def render_noticias_mini(tickers: list, titulo: str = "📰 Noticias del mercado"):
    """
    Panel compacto de noticias para Swing Activo y Mis Posiciones.
    Muestra las últimas 2-3 noticias por acción con su sentimiento.
    """
    news_cache = st.session_state.get("noticias_cache", {})
    if not news_cache:
        st.markdown(
            f'<div style="background:#1E3A5F;border-radius:8px 8px 0 0;padding:8px 14px">'
            f'<span style="font-size:12px;font-weight:700;color:white">📰 NOTICIAS DEL MERCADO</span>'
            f'</div>'
            f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:0 0 8px 8px;'
            f'padding:10px 14px;font-size:11px;color:{TXT_MUT}">'
            f'Sin noticias — presiona "🔄 Actualizar noticias" en el sidebar</div>',
            unsafe_allow_html=True)
        return

    _ts_news = st.session_state.get("noticias_actualizadas", "-")
    st.markdown(
        f'<div style="background:#1E3A5F;border-radius:8px 8px 0 0;'
        f'padding:8px 14px;display:flex;justify-content:space-between;'
        f'align-items:center">'
        f'<div style="font-size:12px;font-weight:700;color:white">'
        f'📰 NOTICIAS DEL MERCADO</div>'
        f'<div style="font-size:10px;color:#93C5FD">Última actualización: {_ts_news}</div>'
        f'</div>',
        unsafe_allow_html=True)

    tickers_con_noticias = [tk for tk in tickers if tk in news_cache and news_cache[tk]["noticias"]]

    if not tickers_con_noticias:
        st.markdown(
            f'<div style="font-size:10px;color:{TXT_MUT}">Sin noticias disponibles para estas acciones</div>',
            unsafe_allow_html=True)
        return

    for tk in tickers_con_noticias[:8]:  # máximo 8 acciones
        data     = news_cache[tk]
        noticias = data["noticias"][:3]   # máximo 3 noticias por acción
        bonus    = data.get("bonus", 0)
        if not noticias:
            continue

        bonus_c = G if bonus > 5 else R if bonus < -5 else TXT_MUT
        bonus_s = f"+{bonus}" if bonus > 0 else str(bonus)

        st.markdown(
            f'<div style="background:{BG_CARD};border:1px solid {BOR};'+
            f'border-left:3px solid {bonus_c};border-radius:8px;'+
            f'padding:8px 12px;margin-bottom:6px">'+
            f'<div style="display:flex;justify-content:space-between;margin-bottom:4px">'+
            f'<span style="font-size:12px;font-weight:800;color:{B}">{tk}</span>'+
            f'<span style="font-size:10px;font-weight:700;color:{bonus_c}">'+
            f'Sentimiento: {bonus_s}</span>'+
            f'</div>',
            unsafe_allow_html=True)

        for noticia in noticias:
            titulo_n = _ascii(str(noticia.get("titulo", "")))[:80]
            fuente_n = _ascii(str(noticia.get("fuente","Yahoo")))
            sent_c   = G if noticia.get("sentimiento","") == "positivo" else \
                       R if noticia.get("sentimiento","") == "negativo" else TXT_MUT
            sent_s   = "▲" if noticia.get("sentimiento","") == "positivo" else \
                       "▼" if noticia.get("sentimiento","") == "negativo" else "●"
            link     = noticia.get("link","#")
            if titulo_n:
                st.markdown(
                    f'<div style="font-size:10px;color:{TXT};margin:2px 0;padding-left:8px">'+
                    f'<span style="color:{sent_c};font-weight:700">{sent_s}</span> '+
                    f'<a href="{link}" target="_blank" style="color:{TXT};text-decoration:none">'+
                    f'{titulo_n}</a>'+
                    f'<span style="color:{TXT_MUT};font-size:9px">  - {fuente_n}</span>'+
                    f'</div>',
                    unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  UNIVERSO DINÁMICO - S&P500 + Nasdaq100 + Portfolio personal
#  Se descarga automáticamente desde Wikipedia al iniciar
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=86400)  # cache 24 horas
def cargar_universo_dinamico() -> list:
    """
    Descarga componentes S&P500 + Nasdaq100 via múltiples fuentes.
    Fallback progresivo si alguna fuente falla.
    """
    import yfinance as yf

    portfolio_personal = [
        "NBIS","MRNA","CROX","APLD","ASTS","NVDA","CNC","CLOV",
        "NKE","XBI","TAN","VOO","IBIT","ETHA","SPY","IBRX",
    ]
    tickers = set(portfolio_personal)

    # Fuente 1: yfinance - componentes S&P500 via ETF holdings
    try:
        import pandas as pd
        # Descargar desde GitHub (fuente pública confiable)
        url_sp500 = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
        sp500 = pd.read_csv(url_sp500)
        tickers.update(sp500["Symbol"].tolist())
    except Exception:
        pass

    # Fuente 2: Wikipedia con timeout corto
    try:
        import pandas as pd
        sp500_wiki = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            storage_options={"timeout": 5}
        )[0]
        tickers.update(sp500_wiki["Symbol"].str.replace(".","-").tolist())
    except Exception:
        pass

    # Fuente 3: yfinance screener - top 500 por market cap
    try:
        screener = yf.screen("most_actives", count=500)
        if screener and "quotes" in screener:
            for q in screener["quotes"]:
                if "symbol" in q:
                    tickers.add(q["symbol"])
    except Exception:
        pass

    # Siempre ampliar con universo curado de alta calidad
    universo_curado = [
        # Mega Cap
        "MSFT","GOOGL","META","AMZN","AAPL","NVDA","TSLA","ORCL","CRM","SNOW",
        "PLTR","ADBE","INTU","NOW","WDAY","DDOG","NET","CRWD","PANW","ZS","MDB",
        "AMD","AVGO","MRVL","ANET","SMCI","APP","RDDT","DOMO","AI","HOOD","SOFI",
        # Fintech
        "COIN","AFRM","XYZ","PYPL","V","MA","AXP","JPM","BAC","GS","MS","C",
        "WFC","BLK","SCHW","ICE","CME","MELI","NU","PAGS","UPST","LC","OPEN",
        # Biotech
        "IBRX","CELH","HIMS","RXRX","PCVX","PFE","ABBV","MRK","BMY","GILD",
        "AMGN","REGN","VRTX","BIIB","ILMN","ZTS","ISRG","SYK","BSX","EW",
        "DXCM","HOLX","AXSM","TVTX","MRNA","BNTX","ARWR","BEAM","CRSP","EDIT",
        "NVCR","RCUS","MRUS","KROS","FOLD","VRNA","IMVT","XENE","PRAX","ACAD",
        # Cripto/AI
        "MARA","RIOT","CORZ","CLSK","HUT","BTBT","IONQ","RGTI","QBTS","MSTR",
        "IREN","WULF","BITF","CIFR","BTDR","SMLR","HIVE","DMGI",
        # LatAm/Global
        "BABA","PDD","SE","GRAB","GLOB","ARCO","VTEX","DESP",
        # Consumo
        "LULU","SBUX","MCD","CMG","TGT","COST","HD","BURL","CHWY","W","RH",
        "RVLV","ONON","DECK","SKX","CROX","BOOT","ANF","AEO","URBN",
        # Energía/Solar
        "OXY","DVN","XOM","CVX","COP","SLB","HAL","FCX","NEM","FANG",
        "AR","EQT","RRC","ENPH","SEDG","RUN","ARRY","NOVA","FSLR","TAN",
        # Industrial/Defensa
        "BA","GE","HON","LMT","RTX","GD","DE","CAT","UPS","FDX",
        "NOC","AXON","KTOS","RCAT","JOBY","ACHR",
        # ETFs
        "ARKK","ARKG","ARKF","SOXX","XBI","IBB","XLK","XLF","XLV",
        "XLE","XLI","XLY","JETS","HACK","BOTZ",
        # Small/Mid Alta Beta
        "STAA","ACN","OPEN","RGTI","APLD","ASTS","CLOV","NKE",
    ]
    tickers.update(universo_curado)

    result = sorted(list(tickers))
    return result


# Cargar universo al iniciar
SCAN_UNIVERSE = cargar_universo_dinamico()


def detectar_recuperacion_rapida(ticker: str, rsi: float, dd: float,
                                  macd: float, close_arr) -> dict:
    """
    v17 Fix AMD-F5: detecta el patrón de recuperación rápida.
    AMD bajó -11% en 5 días con RSI<42 — MACD negativo pero oportunidad válida.
    Criterios: RSI<45 + DD<-8% + MACD<0 + rebote >2% en 2 días.
    """
    resultado = {"es_rapida": False, "badge": "", "accion": ""}
    try:
        if len(close_arr) < 4:
            return resultado
        rebote_2d = (close_arr[-1] / close_arr[-3] - 1) * 100
        if rsi < 45 and dd < -8 and macd < 0 and rebote_2d > 2:
            resultado = {
                "es_rapida": True,
                "badge":     "⚡ Recuperación Rápida",
                "accion":    (f"RSI {rsi:.0f} en zona baja + rebote {rebote_2d:.1f}% "
                              f"aunque MACD negativo. "
                              f"Entrar 50% ahora, +50% cuando MACD cruce cero "
                              f"(típicamente 2-3 días). Caso AMD 29-Mar → 05-Abr."),
                "rebote_2d": round(rebote_2d, 1),
            }
    except Exception:
        pass
    return resultado


@st.cache_data(ttl=1800, show_spinner=False)

def get_vol_umbral(ticker: str, vol_ratio: float) -> tuple:
    """
    v17 Fix AMD-F2: umbral de volumen diferenciado por market cap.
    Large caps tienen volumen base alto — el 84% de AMD es normal para AMD.
    
    Returns: (pasa_filtro: bool, categoria: str)
    """
    _FUND = FUND.get(ticker, None)
    if _FUND:
        vol_diario_k = _FUND[4] if len(_FUND) > 4 else 0
        ingresos_m   = _FUND[3] if len(_FUND) > 3 else 0
        # Large cap: vol diario > 5M o ingresos > $5B
        if vol_diario_k > 5000 or ingresos_m > 5000:
            umbral = 80    # Large cap — AMD, NVDA, etc.
            cat    = "Large cap"
        elif vol_diario_k > 1000 or ingresos_m > 500:
            umbral = 100   # Mid cap
            cat    = "Mid cap"
        else:
            umbral = 120   # Small cap
            cat    = "Small cap"
    else:
        umbral = 100       # Sin datos = umbral medio
        cat    = "Sin datos"
    return vol_ratio >= umbral, cat, umbral

def scan_tab(rsi_max: float, dd_min: float,
             score_min: int = 25, decisions: list = None,
             vol_min_k: float = 200,
             max_results: int = 100,
             universo: list = None,
             prob_nbis_min: float = 0.0) -> pd.DataFrame:
    """
    Escanea el universo y retorna candidatos para el tab específico.
    rsi_max, dd_min: filtros técnicos del tab
    decision_filter: ["ENTRAR"] | ["ANTICIPAR"] | ["SEGUIR"] etc.
    score_min: score mínimo para aparecer en este tab
    """
    candidatos = []
    try:
        import yfinance as yf
        _universo = universo if universo else SCAN_UNIVERSE
        for tk in _universo:
            try:
                stk  = yf.Ticker(tk)
                # Usar 3mo para velocidad - suficiente para DD y RSI
                try:
                    hist = stk.history(period="3mo")
                except Exception:
                    continue
                if hist.empty or len(hist) < 20:
                    continue

                close = hist["Close"].values
                vol   = hist["Volume"].values
                precio = float(close[-1])
                pico   = float(close.max())
                dd     = round((precio - pico) / pico * 100, 1)
                if dd > dd_min:
                    continue

                s     = pd.Series(close)
                delta = s.diff()
                gain  = delta.clip(lower=0).rolling(14).mean()
                loss  = (-delta.clip(upper=0)).rolling(14).mean()
                rsi   = round(float(100-100/(1+gain.iloc[-1]/(loss.iloc[-1]+1e-9))), 1)
                if rsi > rsi_max:
                    continue

                avg_v  = float(np.mean(vol[-20:]))
                vol_k  = avg_v / 1000
                if vol_k < vol_min_k:
                    continue

                vol_r  = int(vol[-1] / avg_v * 100)
                ema50  = float(s.ewm(span=50).mean().iloc[-1])
                ema_d  = round((precio - ema50) / ema50 * 100, 1)
                ema12  = s.ewm(span=12).mean()
                ema26  = s.ewm(span=26).mean()
                macd_h = round(float((ema12-ema26-(ema12-ema26).ewm(9).mean()).iloc[-1]), 3)
                low30  = float(np.min(close[-30:]))
                sop    = round((precio - low30) / low30 * 100, 1)
                rsi_5d = float((100-100/(1+gain/(loss+1e-9))).iloc[-6]) if len(close)>=6 else rsi
                rsi_t  = 5 if (rsi-rsi_5d)>3 else -3 if (rsi-rsi_5d)<-3 else 0

                try:
                    info    = stk.info or {}
                except Exception:
                    info = {}
                beta_v  = float(info.get("beta", 1.5) or 1.5)
                nombre  = info.get("shortName", tk)
                sector  = info.get("sector", "-")
                ingresos= float(info.get("totalRevenue", 0) or 0) / 1e6
                bpa_v   = float(info.get("trailingEps", 0) or 0)
                div_v   = float(info.get("dividendYield", 0) or 0) * 100
                mar_v   = float(info.get("grossMargins", 0) or 0) * 100
                si_v    = float(info.get("shortPercentOfFloat", 0) or 0) * 100

                try:
                    cal  = stk.calendar
                    earn = str(cal["Earnings Date"][0])[:10] if (cal is not None and "Earnings Date" in cal) else "-"
                except Exception:
                    earn = "-"

                sector_map = {
                    "Technology":"Tech","Healthcare":"Salud",
                    "Financial Services":"Finanzas",
                    "Consumer Cyclical":"Consumo",
                    "Consumer Defensive":"Consumo",
                    "Energy":"Energía","Industrials":"Industrial",
                    "Communication Services":"Tech",
                }
                area = sector_map.get(sector, sector[:10] if sector and sector!="-" else "-")

                bonus_f, desc_f = bonus_fundamentales(bpa_v, div_v, mar_v, ingresos, vol_k)
                sc_base = calc_score(rsi, vol_r, ema_d, macd_h, sop, dd, 0, si_v, 1.0, 1.0, rsi_t)
                sc = min(100, sc_base + bonus_f)

                # ── FILTRO MACRO v16: Sector bajo presión oil ────────────
                # ANF/APTV/AOS el 20-Abr: Consumo+Industrial con oil alto
                # hubieran sido bloqueadas aquí
                _presion_s = evaluar_presion_sectorial(area, oil)
                if _presion_s["presionado"]:
                    sc = max(0, sc - 15)        # penalizar -15 pts
                    if sc_base < 50:
                        continue                 # score base débil + sector presionado = skip

                # ── FILTRO FUNDAMENTAL v16: Guidance negativo ────────────
                _guid_s = fetch_guidance_flag(tk)
                if _guid_s["guidance_negativo"]:
                    sc = max(0, sc - _guid_s["score_penalty"])
                    if sc < 40:
                        continue

                # ── FILTRO DILUCIÓN v18: Oferta secundaria reciente ──────
                # VRDN $150M convertibles, IONQ $2B offering = trampa técnica
                # El RSI bajo puede ser dilución, no oportunidad real
                _dil_s = detectar_dilucion_reciente(tk)
                if _dil_s["tiene_dilucion"]:
                    sc = max(0, sc - _dil_s["penalizacion_score"])
                    if sc < 35:
                        continue  # dilución muy reciente + score bajo = skip

                vix_mult = vix.get("mult", 1.0) if vix.get("_ok") else 1.0
                if vix_mult > 1.0:
                    sc = min(100, int(sc * vix_mult))
                if sc < score_min:
                    continue
                # v18: Score máximo 55 — señal tardía si score > 55
                # Excepción: si score_min ya es 40+ el rango 40-55 es el objetivo
                # Para Tab3 (score_min=40): filtrar score > 55
                # Para otros tabs con score_min=55: el techo no aplica
                _score_max = 55 if score_min <= 45 else 999
                if sc > _score_max:
                    continue
                # v12: calcular Prob NBIS con datos reales del yfinance loop
                _mom_s     = round((close[-1]/close[-4]-1)*100, 2) if len(close)>=4 else 0
                _tiene_c_s = str(earn) not in ("-","","nan") if 'earn' in dir() else False
                # Días alcistas consecutivos desde precio histórico
                _dias_alc_s = 0
                for _i in range(1, min(5, len(close))):
                    if close[-_i] > close[-_i-1]:
                        _dias_alc_s += 1
                    else:
                        break
                _prob_nbis  = calcular_prob_nbis(
                    rsi=rsi, vol_ratio=vol, dd=dd,
                    dias_alcistas=_dias_alc_s,
                    momentum_3d=_mom_s,
                    tiene_catalizador=_tiene_c_s
                )
                if prob_nbis_min > 0 and _prob_nbis < prob_nbis_min:
                    continue

                dec, fase, trig, col, bg = get_decision(sc, 0, 1.0, macd_h, rsi, "-",
                                                         prob_nbis=_prob_nbis,
                                                         vol_ratio=vol, ema_d=ema_d,
                                                         mercado_sobrecomprado=_spy_sobrecomprado,
                                                         ticker=tk)  # v19: filtros PE/ATH
                if decisions and dec not in decisions:
                    continue

                pat = clasificar_patron(beta_v, si_v, 0, 3, dd)
                rsi_dir, _, rsi_dir_desc = rsi_direccion(rsi, rsi_t, dd, macd_h)
                earn_txt = f"Earnings {earn}" if earn != "-" else "Sin catalizador detectado"
                lectura  = (f"RSI {rsi:.0f} {'↑' if rsi_t>0 else '↓' if rsi_t<0 else '->'}  - "
                           f"DD {dd:.0f}%  - {earn_txt}  - Vol {vol_r}% promedio")

                candidatos.append({
                    "Ticker":tk,"Nombre":nombre,"Area":area,
                    "Precio":round(precio,2),"RSI":rsi,"RSI_Tend":rsi_t,
                    "Volumen":vol_r,"EMA50":ema_d,"MACD":macd_h,
                    "Soporte":sop,"Beta":round(beta_v,2),"DD_pico":dd,
                    "Pico_P":round(pico,2),"Pico_F":"-","Meses":3,
                    "Short_Int":round(si_v,1),
                    "Pre_Vol":1.0,"Post_Vol":1.0,"Pre_Move":0.0,
                    "Cat_Tipo":"Earnings" if earn!="-" else "-",
                    "Cat_Desc":earn_txt,"Cat_Fecha":earn,
                    # v15 fix: recuperar Arrastradas/Lider desde RAW
                    "Arrastradas": get_sympathy(tk)["arrastradas"],
                    "Lider":       get_sympathy(tk)["lider"],
                    "Score":sc,"Score_Base":sc_base,"Bonus_Fund":bonus_f,
                    "Fund_Desc":desc_f,
                    "BPA":round(bpa_v,2),"Dividendo":round(div_v,1),
                    "Margen":round(mar_v,1),"Ingresos_M":round(ingresos,0),
                    "Vol_Diario_K":round(vol_k,0),
                    "Es_Iliquida":vol_k<500,
                    "Decision":dec,"Fase":fase,"Trigger":trig,
                    "Color":col,"Bg":bg,
                    "Prob_NBIS":prob_nbis(sc,1.0,si_v,dd,3),
                    "Sim_NBIS":sim_nbis(rsi,vol_r,ema_d,macd_h,sop,dd),
                    "Motivo":motivo("Earnings" if earn!="-" else "-",0,"-"),
                    "Lectura":lectura,"Estado":"ACTIVO",
                    "Patron_Tipo":pat[0],"Patron_Emoji":pat[1],
                    "Patron_Desc":pat[2],"Patron_Dias":pat[3],
                    "RSI_Dir":rsi_dir,"RSI_Dir_Desc":rsi_dir_desc,
                    "_source":"screener","_precio_live":True,
                })
            except Exception:
                continue
    except Exception:
        pass

    return pd.DataFrame(
        sorted(candidatos, key=lambda x: -x["Score"])[:max_results]
    )


# Session state para resultados de cada tab
for _tab_key in ["scan_entrar","scan_swing","scan_detectadas","scan_sympathy"]:
    if _tab_key not in st.session_state:
        st.session_state[_tab_key] = None

def _count(key):
    d = st.session_state.get(key)
    return len(d) if d is not None and not d.empty else 0

def _count_list(key):
    """Cuenta items en una lista guardada en session_state (para Momentum)."""
    d = st.session_state.get(key)
    if d is None: return 0
    return len(d) if isinstance(d, list) else 0



def get_decision(score, pre_move, pre_vol, macd, rsi, lider, prob_nbis=0,
                  vol_ratio=100, ema_d=0.0, mercado_sobrecomprado=False,
                  ticker: str = ""):  # v19: ticker para filtros PE/ATH/analistas
    """
    v19: Guards RSI, volumen, EMA50, SPY, PE, ATH y cobertura analistas.
    """
    try:
        _prob_val = float(prob_nbis) if not callable(prob_nbis) else 0.0
    except Exception:
        _prob_val = 0.0
    _prob_ok_entrar    = 30 <= _prob_val <= 50
    _prob_ok_anticipar = _prob_val >= 30
    _prob_optima       = 30 <= _prob_val <= 45

    _rsi_valido   = rsi >= 35
    _vol_valido   = vol_ratio >= 50
    _ema_valido   = ema_d >= -30.0
    _puede_entrar = _rsi_valido and _vol_valido and _ema_valido

    # ── v19 NUEVOS FILTROS: PE / ATH / Analistas ───────────────
    # Se evalúan solo si tenemos el ticker y hay datos disponibles
    if ticker and _puede_entrar:
        try:
            _ev = evaluar_price_target(ticker)
            if _ev.get("bloquear"):
                _nivel = _ev.get("nivel","")
                if _nivel == "burbuja_pe":
                    return "VIGILAR","Fase 1", _ev["msg"], A, A_BG
                elif _nivel == "cobertura_minima":
                    return "VIGILAR","Fase 2", _ev["msg"], A, A_BG
                elif _nivel == "en_ath":
                    return "VIGILAR","Fase 1", _ev["msg"], A, A_BG
                elif _nivel in ("sobre_target","sin_upside"):
                    return "VIGILAR","Fase 1", _ev["msg"], A, A_BG
            elif _ev.get("nivel") == "cerca_ath":
                # Cerca del ATH pero no bloqueante: máximo ANTICIPAR
                _puede_entrar = False  # no puede ser ENTRAR pleno
        except Exception:
            pass  # si falla el fetch, continuar sin este filtro

    # ── Prioridad 1: mercado sobrecomprado ──────────────────────
    if mercado_sobrecomprado:
        # SPY RSI > 68 → máximos históricos → máximo ANTICIPAR con posición reducida
        if score>=55 and pre_move>=3 and pre_vol>=1.3 and macd>0 and _prob_ok_entrar and _puede_entrar:
            return "ANTICIPAR","M3-A","⚠️ SPY SOBRECOMPRADO · Posición 40% · esperar corrección mercado",C,C_BG
        elif score>=42 and macd>0 and _puede_entrar:
            return "SEGUIR","Fase 2","⚠️ SPY RSI>68 · Mercado en máximos · alto riesgo de corrección",A,A_BG
        else:
            return "OBSERVAR","Fase 1","⚠️ SPY SOBRECOMPRADO · No entrar hasta corrección del mercado",TXT_MUT,BG

    # ── v19: RSI máximo 65 para ENTRAR (regla dura) ─────────────
    # Evidencia: entradas con RSI>65 → WR 33%, avg return -5%
    # WOLF RSI 87→-16%, LUNR RSI 76→-8%, TSEM RSI 75→-6%
    # ENPH RSI 56→+37%, APLD RSI 54→+73%, IONQ RSI 58→+24%
    if rsi > 75 and _puede_entrar:
        return "VIGILAR","Fase 1",f"⚠️ RSI {rsi:.0f} · ZONA DE VENTA — no entrar",A,A_BG
    elif rsi > 70 and _puede_entrar:
        return "SEGUIR","Fase 2",f"⚠️ RSI {rsi:.0f} · Sobrecomprado — esperar corrección a RSI 55-60",A,A_BG
    elif rsi > 65 and _puede_entrar:
        # RSI 65-70: máximo ANTICIPAR con posición reducida, nunca ENTRAR
        if score>=42 and macd>0 and _prob_ok_anticipar:
            return "ANTICIPAR","M3-A",f"⚠️ RSI {rsi:.0f}>65 · Posición reducida 40% · esperar pullback",C,C_BG
        else:
            return "SEGUIR","Fase 2",f"⚠️ RSI {rsi:.0f}>65 · Setup parcial pero RSI alto",A,A_BG

    # ── ENTRAR - señal M3 confirmada (RSI ≤ 65 garantizado) ──
    if score>=55 and pre_move>=3 and pre_vol>=1.3 and macd>0 and _prob_ok_entrar and _puede_entrar:
        return "ENTRAR","M3","RUPTURA ACTIVA",G,G_BG
    # ── ANTICIPAR - pre-señal activa ──────────────────────────
    elif score>=42 and pre_move>=1.5 and macd>0 and _prob_ok_anticipar and _puede_entrar:
        return "ANTICIPAR","M3-A","PRE-SEÑAL ACTIVA",C,C_BG
    # ── Score ok pero Prob fuera del rango → señal técnica ────
    elif score>=42 and pre_move>=1.5 and macd>0 and not _prob_ok_anticipar and _puede_entrar:
        return "SEGUIR","Fase 2","SEÑAL TÉCNICA · Prob NBIS baja",A,A_BG
    # ── Guards activados → degradar a Fase 1 con razón ───────
    elif score>=42 and not _puede_entrar:
        _razon = (
            "RSI CAÍDA LIBRE" if not _rsi_valido else
            "VOLUMEN INACTIVO" if not _vol_valido else
            "TENDENCIA ROTA"
        )
        return "SEGUIR","Fase 1",f"RADAR · {_razon}",A,A_BG
    # ── SEGUIR Fase 2 - radar, fondo formando ─────────────────
    elif score>=40:
        return "SEGUIR","Fase 2","FONDO FORMANDO",A,A_BG
    # ── v17 Fix AMD-F1: M1 en BAJADA ACTIVA
    elif score>=20 and rsi < 50 and macd > -3:
        return "SEGUIR","Fase 1","CORRECCIÓN - VIGILAR",A,A_BG
    elif score>=20:
        return "SEGUIR","Fase 1","EN BAJADA",R,R_BG
    else:
        return "OBSERVAR","Fase 0","SIN SEÑAL",TXT_MUT,BG_HEAD

def clasificar_patron(beta: float, short_int: float, pre_move: float,
                      meses: int, dd: float) -> tuple:
    """
    Clasifica el tipo de patrón esperado.
    Aprendizaje del análisis: NBIS (explosivo) vs SEI (gradual) vs TVTX (cíclico).
    Retorna (tipo, emoji, descripcion, dias_objetivo)
    """
    # Patrón EXPLOSIVO - alta velocidad, alto riesgo
    if beta >= 2.5 or short_int >= 15 or pre_move >= 7:
        return ("EXPLOSIVO", "🚀",
                "Rebote rápido 1-3 semanas  - Beta alto o short squeeze",
                "7-21 días")
    # Patrón CÍCLICO - múltiples fondos visibles
    if meses <= 2 and dd >= -35 and beta >= 1.5:
        return ("CÍCLICO", "🔄",
                "Ciclos repetidos  - Entrar solo en fondo del ciclo",
                "3-8 semanas por ciclo")
    # Patrón GRADUAL - fundamentales sólidos, movimiento sostenido
    return ("GRADUAL", "📈",
            "Rebote sostenido 2-4 meses  - Fundamentales sólidos",
            "8-16 semanas")

def rsi_direccion(rsi_actual: float, rsi_tend: int, precio_dd: float,
                   macd: float) -> tuple:
    """
    Evalúa la dirección del RSI en contexto del precio.
    Aprendizaje: ENTX (RSI 48 bajando = trampa) vs STAA (RSI 28 subiendo = oportunidad)
    Retorna (señal, color, descripcion)
    """
    # RSI bajo + subiendo = rebote confirmado ✅
    if rsi_actual < 40 and rsi_tend > 0 and macd > 0:
        return ("RSI REBOTANDO", "G",
                f"RSI {rsi_actual:.0f} subiendo con MACD positivo - señal fuerte")
    # RSI bajo + lateral = base formando 🟡
    if rsi_actual < 40 and rsi_tend == 0:
        return ("RSI BASE", "A",
                f"RSI {rsi_actual:.0f} lateral - base formando, esperar dirección")
    # RSI bajo + bajando = trampa ❌
    if rsi_actual < 45 and rsi_tend < 0:
        return ("RSI CAYENDO", "R",
                f"RSI {rsi_actual:.0f} aún bajando - NO entrar, esperar capitulación")
    # RSI medio + bajando = tendencia bajista activa
    if rsi_actual >= 45 and precio_dd < -15:
        return ("TRAMPA DD", "R",
                f"RSI {rsi_actual:.0f} con DD {precio_dd:.0f}% - bajada sin capitulación")
    # RSI neutro normal
    return ("RSI NEUTRO", "TXT_MUT",
            f"RSI {rsi_actual:.0f} - zona neutral")


def prob_nbis(score,pre_vol,short_int,dd,meses):
    b=score*0.65+min(pre_vol*8,20)+min(short_int*0.8,15)
    if dd<-30: b+=8
    if meses>=3: b+=7
    return round(min(b,99),1)

def sim_nbis(rsi,vol,ema,macd,sop,dd):
    s=100-abs(rsi-29)*1.5-abs(vol-310)*0.04-abs(ema+12)*1.2-abs(macd-1.80)*8-abs(sop-0.8)*4-abs(dd+38)*0.3
    return round(max(0,min(s,99)),1)

def motivo(ct,pm,lider):
    if lider: return "Sympathy play" if pm>=3 else "Narrativa sectorial"
    if ct in ["Earnings","Clinical"]: return "Catalizador directo"
    if ct in ["Contrato","FDA"]: return "Catalizador fundamental"
    if ct=="Sector": return "Narrativa sectorial"
    if pm>=5: return "Catalizador general"
    return "Acumulación técnica"

@st.cache_data
def build_curated() -> pd.DataFrame:
    """
    Construye el DataFrame con SOLO los datos curados del RAW:
    catalizador, área, acciones arrastradas, estado, lectura, Pre-Market.
    Los indicadores técnicos se reemplazarán con datos reales de yfinance.
    """
    rows=[]
    for r in RAW:
        (t,n,area,p,rsi,vol,ema,macd,sop,beta,
         dd,pp,pf,mes,si,pv,postv,pm,ct,cd,cf,
         arr,lider,lect,estado)=r
        # v19: excluir ETFs del universo de acciones
        if _es_etf(str(t)):
            continue
        rows.append({
            # ── Datos curados (no reemplazables por yfinance) ──
            "Ticker":t,"Nombre":n,"Area":area,
            "Cat_Tipo":ct,"Cat_Desc":cd,"Cat_Fecha":cf,
            "Arrastradas":", ".join(arr) if arr else "-",
            "Lider":lider if lider else "-",
            "Estado":estado,"Lectura":lect,
            "Meses":mes,                     # meses en corrección (curado)
            "Short_Int":si,                  # short interest (curado, FINRA bi-mensual)
            "Pre_Vol":pv,"Post_Vol":postv,   # vol Pre/Post Market (curado)
            "Pre_Move":pm,                   # movimiento Pre-Market % (curado)
            # ── Indicadores técnicos: valores RAW como fallback ──
            "Precio":p,"RSI":rsi,"Volumen":vol,"EMA50":ema,
            "MACD":macd,"Soporte":sop,"Beta":beta,
            "DD_pico":dd,"Pico_P":pp,"Pico_F":pf,
            "_source":"curado",
        })
    return pd.DataFrame(rows)

# ─────────────────────────────────────────────────────────────
#  OPCIÓN C - TODOS LOS INDICADORES EN TIEMPO REAL
#  Cache 20 min para no saturar yfinance en cada recarga
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=1200, show_spinner=False)
def fetch_all_indicators(tickers: tuple) -> dict:
    """
    Descarga 6 meses de historia para cada ticker y calcula:
    Precio, RSI, RSI_Tend, MACD, EMA50 dist, Volumen ratio,
    DD desde pico, Soporte dist, Beta.
    Retorna dict {ticker: {campo: valor, ...}}
    """
    resultado = {}
    try:
        import yfinance as yf

        # Descarga batch de todos los tickers de una vez (más rápido)
        raw = yf.download(
            list(tickers),
            period="6mo",
            interval="1d",
            progress=False,
            auto_adjust=True,
            group_by="ticker",
        )

        for tk in tickers:
            try:
                # Extraer OHLCV para este ticker
                if len(tickers) == 1:
                    hist_close = raw["Close"].dropna()
                    hist_vol   = raw["Volume"].dropna()
                else:
                    hist_close = raw[tk]["Close"].dropna()
                    hist_vol   = raw[tk]["Volume"].dropna()

                if len(hist_close) < 20:
                    continue

                close = hist_close.values
                vol   = hist_vol.values

                # ── RSI (14) ──────────────────────────────
                s = pd.Series(close)
                delta = s.diff()
                gain  = delta.clip(lower=0).rolling(14).mean()
                loss  = (-delta.clip(upper=0)).rolling(14).mean()
                rs    = gain / (loss + 1e-9)
                rsi_series = 100 - 100 / (1 + rs)
                rsi   = round(float(rsi_series.iloc[-1]), 1)

                # Tendencia RSI (vs 5 días atrás)
                rsi_5d = float(rsi_series.iloc[-6]) if len(rsi_series) >= 6 else rsi
                rsi_tend = 5 if (rsi - rsi_5d) > 3 else -3 if (rsi - rsi_5d) < -3 else 0

                # ── MACD (12/26/9) ────────────────────────
                ema12 = s.ewm(span=12, adjust=False).mean()
                ema26 = s.ewm(span=26, adjust=False).mean()
                macd_line   = ema12 - ema26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                macd_hist   = round(float((macd_line - signal_line).iloc[-1]), 3)

                # ── EMA50 distancia % ─────────────────────
                ema50 = float(s.ewm(span=50, adjust=False).mean().iloc[-1])
                precio_actual = float(close[-1])
                ema_dist = round((precio_actual - ema50) / ema50 * 100, 1)

                # ── Volumen ratio (último vs media 20d) ───
                avg_v = float(np.mean(vol[-20:])) if len(vol) >= 20 else float(np.mean(vol))
                vol_ratio = int(vol[-1] / avg_v * 100) if avg_v > 0 else 100

                # ── DD desde pico (6 meses) ───────────────
                pico = float(np.max(close))
                dd   = round((precio_actual - pico) / pico * 100, 1)

                # ── Soporte (distancia al mínimo 30d) ─────
                low30 = float(np.min(close[-30:])) if len(close) >= 30 else float(np.min(close))
                sop   = round((precio_actual - low30) / low30 * 100, 1)

                # ── Beta (desde fast_info, no bloquea) ────
                try:
                    info = yf.Ticker(tk).fast_info
                    beta = float(getattr(info, "beta", 1.5) or 1.5)
                except Exception:
                    beta = 1.5

                resultado[tk] = {
                    "Precio": round(precio_actual, 2),
                    "RSI": rsi,
                    "RSI_Tend": rsi_tend,
                    "MACD": macd_hist,
                    "EMA50": ema_dist,
                    "Volumen": vol_ratio,
                    "DD_pico": dd,
                    "Pico_P": round(pico, 2),
                    "Soporte": sop,
                    "Beta": round(beta, 2),
                    "_source": "live",
                }
            except Exception:
                continue  # si falla un ticker, seguimos con los demás

    except Exception:
        pass  # sin yfinance o sin internet - retorna vacío

    return resultado

def build_df():
    """
    Combina datos curados del RAW con indicadores de yfinance.
    Si yfinance no está disponible o falla, usa los datos del RAW directamente.
    Siempre retorna (DataFrame, n_live) sin excepciones.
    """
    df_cur = build_curated()
    tickers = tuple(df_cur["Ticker"].tolist())

    # Intentar obtener indicadores reales
    try:
        live = fetch_all_indicators(tickers)
    except Exception:
        live = {}
    n_live = len(live)

    rows = []
    for _, row in df_cur.iterrows():
        tk     = row["Ticker"]
        ind    = live.get(tk, {})
        estado = row["Estado"]

        # ── Indicadores: precio/RSI/EMA/Vol de yfinance ──────
        # MACD y Soporte: SIEMPRE del RAW curado.
        # El MACD real en mercados bajistas es negativo -> rompe el score.
        # El dato curado representa la tendencia esperada del catalizador.
        rsi    = float(ind.get("RSI",     row["RSI"]))
        rsi_t  = int(ind.get("RSI_Tend", 5 if float(row["MACD"])>0 and rsi<42 else 0))
        macd   = float(row["MACD"])          # <- siempre del RAW curado
        ema    = float(ind.get("EMA50",  row["EMA50"]))
        vol    = int(ind.get("Volumen",  row["Volumen"]))
        dd     = float(ind.get("DD_pico",row["DD_pico"]))
        pico_p = float(ind.get("Pico_P", row["Pico_P"]))
        sop    = float(row["Soporte"])       # <- siempre del RAW curado
        beta   = float(ind.get("Beta",   row["Beta"]))
        precio = float(ind.get("Precio", row["Precio"]))
        src    = ind.get("_source", "curado")

        # ── Datos curados (siempre del RAW) ─────────────────
        pm  = float(row["Pre_Move"])
        pv  = float(row["Pre_Vol"])
        si  = float(row["Short_Int"])
        mes = int(row["Meses"])
        lider  = row["Lider"]

        # ── Fundamentales del diccionario FUND ───────────────
        fund = FUND.get(tk, (0.0, 0.0, 0.0, 0.0, 999.0))
        bpa_v, div_v, mar_v, ing_v, vol_k = fund
        bonus_fund, desc_fund = bonus_fundamentales(bpa_v, div_v, mar_v, ing_v, vol_k)

        # ── Score base + bonus fundamentales ─────────────────
        sc_base = calc_score(rsi, vol, ema, macd, sop, dd, pm, si, pv,
                             float(row["Post_Vol"]), rsi_t)
        sc = min(100, sc_base + bonus_fund)

        # ── Multiplicador VIX (ya cargado globalmente) ────────
        # Solo aplica cuando VIX > 25 (mercado en miedo/pánico)
        vix_mult = vix.get("mult", 1.0) if vix.get("_ok") else 1.0
        if vix_mult > 1.0:
            sc = min(100, int(sc * vix_mult))

        # ── Filtro liquidez: acciones ilíquidas no pasan F2 ──
        # vol_k < 500K -> penalización ya está en bonus_fund (-20)
        # pero además limitamos la decisión
        es_iliquida = vol_k < 500

        _spy_info_bdf = get_spy_filtro()
        dec, fase, trig, col, bg = get_decision(sc, pm, pv, macd, rsi, lider, prob_nbis=0,
                                               vol_ratio=vol_r, ema_d=ema_d,
                                               mercado_sobrecomprado=_spy_info_bdf.get("mercado_sobrecomprado", False),
                                               ticker=ticker)  # v19: filtros PE/ATH
        # prob_nbis se calcula después — get_decision usa 0 por defecto aquí
        # El valor real se aplica cuando se recalcula abajo si aplica

        # Ilíquidas no pueden pasar de Bajada F1
        if es_iliquida and dec in ["ENTRAR","ANTICIPAR","SEGUIR"]:
            if dec != "SEGUIR" or sc >= 40:
                dec="SEGUIR"; fase="Fase 1"; trig="ILÍQUIDA"; col=R; bg=R_BG

        if estado == "REFERENCIA":
            dec="REFERENCIA"; fase="Completado"
            trig="PATRÓN COMPLETO"; col=TXT_MUT; bg=BG_HEAD

        prob = prob_nbis(sc, pv, si, dd, mes)
        sim  = sim_nbis(rsi, vol, ema, macd, sop, dd)
        mot  = motivo(row["Cat_Tipo"], pm, lider)

        # v18: recalcular decisión con prob real ahora que está disponible
        dec, fase, trig, col, bg = get_decision(sc, pm, pv, macd, rsi, lider,
                                                 prob_nbis=float(prob),
                                                 vol_ratio=vol_r, ema_d=ema_d,
                                                 ticker=ticker)  # v19: PE/ATH filters

        # v15: earnings live - si Cat_Fecha es "-", buscar en yfinance
        _cat_fecha_row = str(row.get("Cat_Fecha", "-"))
        if _cat_fecha_row in ("-","","nan"):
            _cat_fecha_row = get_earnings_single(tk)
        row = dict(row)  # asegurar que es mutable
        row["Cat_Fecha"] = _cat_fecha_row

        # v19: Reglas de earnings sobre la DECISIÓN (no solo el badge visual)
        if _cat_fecha_row not in ("-","","nan"):
            try:
                import datetime as _dt_bd
                _dias_earn_bd = (_dt_bd.date.fromisoformat(_cat_fecha_row[:10])
                                 - _dt_bd.date.today()).days

                # ── REGLA 1: Post-earnings precio inflado → BLOQUEAR ──────
                # Si earnings fue hace 0-3 días Y precio subió > +15%
                # → catalizador ya consumido en el precio
                if -3 <= _dias_earn_bd <= 0:
                    _gap_post = float(pm) if pm else 0  # pre_move como proxy del gap
                    if _gap_post > 15 or rsi > 68:
                        dec  = "SEGUIR"
                        fase = "Fase 1"
                        trig = (f"🚨 Post-earnings +{_gap_post:.0f}% · RSI {rsi:.0f} — "
                                f"catalizador consumido · esperar RSI 48-58")
                    else:
                        # precio castigado post-earnings → válido (como ENPH)
                        trig = f"⚠️ Post-earnings hace {abs(_dias_earn_bd)}d · {trig}"

                # ── REGLA 2: Pre-earnings 3-5 días → ANTICIPAR, no ENTRAR ──
                # Reducir a posición parcial — no apostar completo al resultado
                elif 3 <= _dias_earn_bd <= 5:
                    trig = f"⚡ PRE-EARNINGS {_dias_earn_bd}d · {trig}"
                    # Degradar ENTRAR → ANTICIPAR (posición 40%, stop -5%)
                    if dec == "ENTRAR":
                        dec  = "ANTICIPAR"
                        fase = "Fase 3"
                        trig = f"⚡ PRE-EARNINGS {_dias_earn_bd}d · posición 40% · stop -5%"

                # ── REGLA 3: Earnings muy próximo → NO entrar ─────────────
                elif 0 <= _dias_earn_bd <= 2:
                    trig = f"🚨 EARNINGS {'HOY' if _dias_earn_bd==0 else f'en {_dias_earn_bd}d'} — NO entrar"
                    dec  = "VIGILAR"
                    fase = "Fase 1"

            except Exception:
                pass

        rows.append({
            "Ticker":tk, "Nombre":row["Nombre"], "Area":row["Area"],
            "Precio":precio, "RSI":rsi, "RSI_Tend":rsi_t,
            "Volumen":vol, "EMA50":ema, "MACD":macd,
            "Soporte":sop, "Beta":beta, "DD_pico":dd,
            "Pico_P":pico_p, "Pico_F":row["Pico_F"],
            "Meses":mes, "Short_Int":si,
            "Pre_Vol":pv, "Post_Vol":float(row["Post_Vol"]), "Pre_Move":pm,
            "Cat_Tipo":row["Cat_Tipo"], "Cat_Desc":row["Cat_Desc"],
            "Cat_Fecha":row["Cat_Fecha"],
            "Arrastradas":row["Arrastradas"], "Lider":lider,
            # Score enriquecido
            "Score":sc, "Score_Base":sc_base, "Bonus_Fund":bonus_fund,
            "Fund_Desc":desc_fund,
            "BPA":bpa_v, "Dividendo":div_v, "Margen":mar_v,
            "Ingresos_M":ing_v, "Vol_Diario_K":vol_k,
            "Es_Iliquida":es_iliquida,
            "Decision":dec, "Fase":fase, "Trigger":trig,
            "Color":col, "Bg":bg, "Prob_NBIS":prob, "Sim_NBIS":sim,
            "Motivo":mot, "Lectura":row["Lectura"], "Estado":estado,
            # v6: tipo patrón + RSI direccional
            "Patron_Tipo": clasificar_patron(beta, si, pm, mes, dd)[0],
            "Patron_Emoji": clasificar_patron(beta, si, pm, mes, dd)[1],
            "Patron_Desc": clasificar_patron(beta, si, pm, mes, dd)[2],
            "Patron_Dias": clasificar_patron(beta, si, pm, mes, dd)[3],
            "RSI_Dir": rsi_direccion(rsi, rsi_t, dd, macd)[0],
            "RSI_Dir_Desc": rsi_direccion(rsi, rsi_t, dd, macd)[2],
            "_source":src, "_precio_live": src=="live",
            # v11: Score Rebote
            **{k: v for k, v in calcular_score_rebote(
                dd=dd, rsi=rsi, vol_ratio=vol,
                dias_alcistas=0, momentum_3d=float(macd),
                tiene_catalizador=row["Cat_Fecha"] not in ("-","","nan"),
                dias_para_cat=(
                    max(0, (pd.to_datetime(row["Cat_Fecha"], errors="coerce").date()
                    - __import__("datetime").date.today()).days)
                    if row["Cat_Fecha"] not in ("-","","nan") else 999
                ),
                beta=beta
            ).items() if k in ("score","nivel","detalle","pts_dd","pts_rsi","pts_vol","pts_cat")},
            "Score_Rebote": calcular_score_rebote(dd=dd,rsi=rsi,vol_ratio=vol,dias_alcistas=0,momentum_3d=float(macd),tiene_catalizador=row["Cat_Fecha"] not in ("-","","nan"),dias_para_cat=999,beta=beta)["score"],
            "Nivel_Rebote": calcular_score_rebote(dd=dd,rsi=rsi,vol_ratio=vol,dias_alcistas=0,momentum_3d=float(macd),tiene_catalizador=row["Cat_Fecha"] not in ("-","","nan"),dias_para_cat=999,beta=beta)["nivel"],
            "Detalle_Rebote": calcular_score_rebote(dd=dd,rsi=rsi,vol_ratio=vol,dias_alcistas=0,momentum_3d=float(macd),tiene_catalizador=row["Cat_Fecha"] not in ("-","","nan"),dias_para_cat=999,beta=beta)["detalle"],
        })

    return pd.DataFrame(rows), n_live

# ── Cargar con spinner visible al usuario ─────────────────────
# v8: sin carga automática - cada tab escanea a pedido
df_all = pd.DataFrame()  # vacío al inicio
_n_live = 0

# ─────────────────────────────────────────────────────────────
#  LOOKUP DINÁMICO - cualquier ticker del CSV
#  Intenta yfinance primero; si falla, estima desde precio
# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
#  Helper: fila vacía segura cuando un ticker no está disponible
# ─────────────────────────────────────────────────────────────
def _fetch_fallback_row(ticker: str, precio_compra: float, razon: str = "Sin datos") -> dict:
    """Retorna una fila neutra para tickers que yfinance no puede resolver."""
    sc = 0
    dec, fase, trig, col, bg = "OBSERVAR","Fase 0","SIN DATOS",        "#64748B","#F8FAFC"
    symp = get_sympathy(ticker)
    return {
        "Ticker":ticker,"Nombre":ticker,"Area":"-",
        "Precio":round(precio_compra,2) if precio_compra>0 else 0.0,
        "RSI":50.0,"RSI_Tend":0,"Volumen":100,"EMA50":0.0,"MACD":0.0,
        "Soporte":0.0,"Beta":1.0,"DD_pico":0.0,
        "Pico_P":precio_compra,"Pico_F":"-","Meses":1,
        "Short_Int":0.0,"Pre_Vol":1.0,"Post_Vol":1.0,"Pre_Move":0.0,
        "RSI_Tend":0,
        "Cat_Tipo":"-","Cat_Desc":razon,"Cat_Fecha":"-",
        "Arrastradas":symp["arrastradas"],"Lider":symp["lider"],
        "Score":0,"Score_Base":0,"Bonus_Fund":0,"Fund_Desc":"-",
        "BPA":0.0,"Dividendo":0.0,"Margen":0.0,"Ingresos_M":0,"Vol_Diario_K":0,
        "Es_Iliquida":True,
        "Decision":dec,"Fase":fase,"Trigger":trig,"Color":col,"Bg":bg,
        "Prob_NBIS":0.0,"Sim_NBIS":0.0,
        "Motivo":razon,"Lectura":f"{ticker} - {razon}",
        "Estado":"-",
        "Patron_Tipo":"-","Patron_Emoji":"❓","Patron_Desc":"-","Patron_Dias":"-",
        "RSI_Dir":"-","RSI_Dir_Desc":"-",
        "Score_Rebote":0,"Nivel_Rebote":"🔵 SIN DATOS","Detalle_Rebote":"-",
        "_source":"error","_precio_live":False,
        "Etapa_v12":"-",
    }

@st.cache_data(ttl=300, show_spinner=False)  # FIX v13.1: 5 min (antes 3600=1h -> fase no actualizaba)
def fetch_ticker_data(ticker: str, precio_compra: float) -> dict:
    """Retorna dict con los mismos campos que df_all para un ticker arbitrario."""
    # Silenciar warnings de yfinance para este ticker
    import logging as _log_ftd
    _log_ftd.getLogger("yfinance").setLevel(_log_ftd.CRITICAL)
    # v15 fix: tickers conocidos como inválidos en yfinance - evita spam de 404
    _TICKER_BLACKLIST = {
        "MSTU",   # ETF apalancado sin fundamentals en Yahoo
        "CRWN",   # Ilíquida / sin datos
        "SDNK",   # Typo — el ticker correcto es SNDK (SanDisk, válido en yfinance)
        "VIX",    # Debe ser ^VIX - sin ^ falla
        "ENTX",   # Delisted
    }
    if ticker.upper() in _TICKER_BLACKLIST:
        # Retornar fila vacía sin llamar a yfinance
        return _fetch_fallback_row(ticker, precio_compra, razon="Ticker no soportado en yfinance")

    try:
        import yfinance as yf
        import warnings
        warnings.filterwarnings("ignore")   # suprimir warnings de yfinance
        stk  = yf.Ticker(ticker)
        hist = stk.history(period="6mo")
        if hist.empty:
            raise ValueError("sin datos")

        close = hist["Close"].values
        vol   = hist["Volume"].values

        # RSI
        delta = pd.Series(close).diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rsi   = float(100 - 100/(1 + gain.iloc[-1]/(loss.iloc[-1]+1e-9)))

        # MACD
        ema12 = pd.Series(close).ewm(span=12).mean()
        ema26 = pd.Series(close).ewm(span=26).mean()
        macd_hist = float((ema12 - ema26 - (ema12-ema26).ewm(span=9).mean()).iloc[-1])

        # EMA50
        ema50  = float(pd.Series(close).ewm(span=50).mean().iloc[-1])
        ema_d  = round((close[-1]-ema50)/ema50*100, 1)

        # Volumen ratio
        avg_v  = float(np.mean(vol[-20:])) if len(vol)>=20 else float(np.mean(vol))
        vol_r  = int(vol[-1]/avg_v*100) if avg_v>0 else 100

        # DD desde pico (6 meses)
        peak  = float(np.max(close))
        dd    = round((close[-1]-peak)/peak*100, 1)

        # Soporte (mínimo 30d)
        low30 = float(np.min(close[-30:])) if len(close)>=30 else float(np.min(close))
        sop   = round((close[-1]-low30)/low30*100, 1)

        info  = stk.fast_info
        beta  = float(getattr(info,"beta",1.5) or 1.5)
        nombre= ticker
        area  = "-"

        precio_actual = float(close[-1])

        # Tendencia RSI - comparar RSI actual vs hace 5 días
        rsi_series = pd.Series(close)
        delta_all  = rsi_series.diff()
        gain_all   = delta_all.clip(lower=0).rolling(14).mean()
        loss_all   = (-delta_all.clip(upper=0)).rolling(14).mean()
        rsi_full   = 100 - 100/(1 + gain_all/(loss_all+1e-9))
        rsi_5d_ago = float(rsi_full.iloc[-6]) if len(rsi_full)>=6 else rsi
        rsi_tend   = 5 if (rsi - rsi_5d_ago) > 3 else -3 if (rsi - rsi_5d_ago) < -3 else 0

        # ── Pre_Move real: momentum 5 días (mínimo->actual) ──────
        # FIX v13.1: antes siempre era 0.0 -> nunca llegaba a Fase 2/3
        min_5d        = float(np.min(close[-5:]))  if len(close) >= 5  else float(close[-1])
        pre_move_calc = round((close[-1] - min_5d) / min_5d * 100, 1) if min_5d > 0 else 0.0
        pre_vol_calc  = round(vol_r / 100.0, 2)   # vol_r (%) -> ratio (x)

        sc = calc_score(rsi, vol_r, ema_d, macd_hist, sop, dd,
                        pre_move_calc, 0.0, max(pre_vol_calc, 1.0), 1.0, rsi_tend)
        # v18 fix: calcular el VALOR de prob_nbis antes de get_decision
        # prob_nbis es una función — necesitamos llamarla primero
        try:
            _prob_val = float(prob_nbis(sc, max(pre_vol_calc,1.0), 0.0, dd, 3))
        except Exception as _ep:
            # Guardar el error para diagnóstico
            try:
                st.session_state["_prob_debug"] = f"{ticker}: sc={sc} pre_vol={pre_vol_calc} dd={dd} err={str(_ep)[:60]}"
            except Exception:
                pass
            _prob_val = 0.0
        _spy_info_ftd = get_spy_filtro()
        dec,fase,trig,col,bg = get_decision(sc, pre_move_calc,
                                            max(pre_vol_calc, 1.0), macd_hist, rsi, "",
                                            prob_nbis=_prob_val,
                                            ticker=ticker,  # v19: pasar ticker para filtros PE/ATH
                                            vol_ratio=vol_r, ema_d=ema_d,
                                            mercado_sobrecomprado=_spy_info_ftd.get("mercado_sobrecomprado", False))

        # v19: aplicar reglas de earnings sobre la decisión
        try:
            _cat_ftd = get_earnings_single(ticker)
            if _cat_ftd and _cat_ftd not in ("-","","nan"):
                import datetime as _dt_ftd
                _dias_ftd = (_dt_ftd.date.fromisoformat(_cat_ftd[:10])
                             - _dt_ftd.date.today()).days
                # Post-earnings precio inflado → bloquear
                if -3 <= _dias_ftd <= 0 and (rsi > 68 or pre_move_calc > 15):
                    dec  = "SEGUIR"; fase = "Fase 1"
                    trig = f"🚨 Post-earnings RSI {rsi:.0f} — catalizador consumido"
                # Pre-earnings → degradar ENTRAR a ANTICIPAR
                elif 3 <= _dias_ftd <= 5 and dec == "ENTRAR":
                    dec  = "ANTICIPAR"
                    trig = f"⚡ PRE-EARNINGS {_dias_ftd}d · posición 40% · stop -5%"
                # Earnings hoy o mañana → bloquear
                elif 0 <= _dias_ftd <= 2:
                    dec  = "VIGILAR"; fase = "Fase 1"
                    trig = f"🚨 EARNINGS {'HOY' if _dias_ftd==0 else f'en {_dias_ftd}d'} — NO entrar"
        except Exception:
            pass

        return {
            "Ticker":ticker,"Nombre":nombre,"Area":area,
            "Precio":round(precio_actual,2),
            "RSI":round(rsi,1),"Volumen":vol_r,"EMA50":ema_d,
            "MACD":round(macd_hist,2),"Soporte":round(sop,1),
            "Beta":round(beta,2),"DD_pico":dd,
            "Pico_P":round(peak,2),"Pico_F":"-","Meses":3,
            "Short_Int":0.0,"Pre_Vol":round(max(pre_vol_calc,1.0),2),"Post_Vol":1.0,"Pre_Move":pre_move_calc,
            "RSI_Tend":rsi_tend,
            "Cat_Tipo":"-","Cat_Desc":"Sin catalizador identificado","Cat_Fecha":"-",
            "Arrastradas": get_sympathy(ticker)["arrastradas"],"Lider": get_sympathy(ticker)["lider"],
            "Score":sc,"Decision":dec,"Fase":fase,"Trigger":trig,
            "Color":col,"Bg":bg,
            "Prob_NBIS":round(_prob_val, 1),
            "Sim_NBIS":round(sim_nbis(rsi,vol_r,ema_d,macd_hist,sop,dd),1),
            "Motivo":"Datos en tiempo real","Lectura":"Calculado desde yfinance.",
            "_source":"yfinance",
        }
    except Exception:
        # Sin internet o ticker inválido - estimación desde precio de compra
        precio_actual = precio_compra   # no sabemos el precio actual
        rsi_est  = 45.0
        ema_est  = -5.0
        macd_est = 0.0
        vol_est  = 100
        dd_est   = -10.0
        sop_est  = 2.0
        sc = calc_score(rsi_est,vol_est,ema_est,macd_est,sop_est,dd_est,0.0,0.0,1.0,1.0,0)
        dec,fase,trig,col,bg = get_decision(sc,0.0,1.0,macd_est,rsi_est,"",
                                            prob_nbis=30,
                                            vol_ratio=100, ema_d=-5.0,
                                            ticker=ticker)
        return {
            "Ticker":ticker,"Nombre":ticker,"Area":"-",
            "Precio":precio_compra,
            "RSI":rsi_est,"Volumen":vol_est,"EMA50":ema_est,
            "MACD":macd_est,"Soporte":sop_est,
            "Beta":1.5,"DD_pico":dd_est,
            "Pico_P":precio_compra,"Pico_F":"-","Meses":1,
            "Short_Int":0.0,"Pre_Vol":1.0,"Post_Vol":1.0,"Pre_Move":0.0,
            "RSI_Tend":0,
            "Cat_Tipo":"-","Cat_Desc":"Sin datos disponibles","Cat_Fecha":"-",
            "Arrastradas": get_sympathy(ticker)["arrastradas"],"Lider": get_sympathy(ticker)["lider"],
            "Score":sc,"Decision":dec,"Fase":fase,"Trigger":trig,
            "Color":col,"Bg":bg,
            "Prob_NBIS":20.0,"Sim_NBIS":10.0,
            "Motivo":"Estimación (sin datos)","Lectura":"Instala yfinance para datos reales.",
            "_source":"estimado",
        }

def get_row_for_ticker(ticker: str, precio_compra: float) -> dict:
    """Busca en el universo local primero; si no existe, llama a fetch_ticker_data."""
    rdata = pd.DataFrame()  # v8: sin universo fijo
    if not rdata.empty:
        return rdata.iloc[0].to_dict()
    return fetch_ticker_data(ticker, precio_compra)



# ─────────────────────────────────────────────────────────────
#  POST-EARNINGS DETECTOR - v15
#  Detecta si el earning fue positivo o negativo via gap de precio
#  y genera la decisión de trading correspondiente
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)  # cache 15 min
def detect_post_earning_gap(ticker: str, cat_fecha: str) -> dict:
    """
    Analiza si el earning ya ocurrió y cuál fue el resultado.
    Retorna gap%, clasificación y decisión de trading.

    Situaciones:
      Gap > +5%  -> Positivo fuerte -> Si tienes: MANTENER/AGREGAR
      Gap +1/+5% -> Positivo moderado -> Si tienes: MANTENER
      Gap -1/+1% -> Neutral -> Esperar confirmación
      Gap -5/-1% -> Negativo moderado -> Evaluar salida parcial
      Gap < -5%  -> Negativo fuerte -> ZONA RECOMPRA NBIS si fundamentals OK
    """
    import datetime, numpy as np
    resultado = {
        "ocurrio":       False,
        "gap_pct":       0.0,
        "clasificacion": "sin_datos",
        "color":         "#64748B",
        "emoji":         "📅",
        "decision_tiene": "-",
        "decision_notiene": "-",
        "accion_rapida":  "-",
        "recompra_activa": False,
        "vol_ratio":     1.0,
    }
    if not cat_fecha or cat_fecha in ("-","","nan"):
        return resultado
    try:
        fecha_earn = datetime.date.fromisoformat(str(cat_fecha)[:10])
        hoy        = datetime.date.today()
        dias_desde = (hoy - fecha_earn).days
        # Earning ocurrió si hace 0-3 días (puede reportar after-hours)
        if not (0 <= dias_desde <= 3):
            return resultado
    except Exception:
        return resultado

    try:
        import yfinance as yf
        hist = yf.Ticker(ticker).history(period="5d")
        if hist is None or len(hist) < 2:
            return resultado

        cierre_ayer = float(hist["Close"].values[-2])
        apertura_hoy = float(hist["Open"].values[-1])
        cierre_hoy  = float(hist["Close"].values[-1])
        vol_hoy     = float(hist["Volume"].values[-1])
        vol_avg     = float(np.mean(hist["Volume"].values[:-1])) if len(hist) > 1 else vol_hoy
        vol_ratio   = round(vol_hoy / vol_avg, 1) if vol_avg > 0 else 1.0

        # Gap = diferencia entre apertura hoy vs cierre ayer
        gap = round((apertura_hoy - cierre_ayer) / cierre_ayer * 100, 2)
        # Movimiento intraday adicional
        move_total = round((cierre_hoy - cierre_ayer) / cierre_ayer * 100, 2)

        resultado["ocurrio"]   = True
        resultado["gap_pct"]   = gap
        resultado["vol_ratio"] = vol_ratio

        if gap >= 8:
            resultado.update({
                "clasificacion":     "positivo_fuerte",
                "color":             "#16A34A",
                "emoji":             "🚀",
                "decision_tiene":    f"MANTENER 100% - Earning fuerte +{gap:.1f}%. No vender en el pico de euforia. Dejar correr el runner.",
                "decision_notiene":  f"NO PERSEGUIR - Gap +{gap:.1f}% ya fue. Esperar pullback a zona de soporte (+3-5d).",
                "accion_rapida":     "🟢 MANTENER - momentum confirmado",
                "recompra_activa":   False,
            })
        elif gap >= 3:
            resultado.update({
                "clasificacion":     "positivo_moderado",
                "color":             "#22C55E",
                "emoji":             "📈",
                "decision_tiene":    f"MANTENER - Earning positivo +{gap:.1f}%. Si llegaste a T1, vender 30% y dejar runner.",
                "decision_notiene":  f"Esperar consolidación 2-3 días. Si RSI no supera 65, puede ser entrada tardía válida.",
                "accion_rapida":     "🟢 MANTENER - revisar targets",
                "recompra_activa":   False,
            })
        elif gap >= -2:
            resultado.update({
                "clasificacion":     "neutral",
                "color":             "#D97706",
                "emoji":             "➡️",
                "decision_tiene":    f"MANTENER con stop ajustado. Earning neutral ({gap:+.1f}%). El mercado esperaba más.",
                "decision_notiene":  f"Esperar dirección clara. 2-3 días de consolidación antes de entrar.",
                "accion_rapida":     "⚠️ NEUTRAL - esperar confirmación",
                "recompra_activa":   False,
            })
        elif gap >= -8:
            resultado.update({
                "clasificacion":     "negativo_moderado",
                "color":             "#EF4444",
                "emoji":             "📉",
                "decision_tiene":    f"REDUCIR 40-50% - Earning decepcionó ({gap:.1f}%). Proteger capital. Evaluar si el tesis sigue válida.",
                "decision_notiene":  f"Monitorear 2-3 días. Si RSI baja a 35-40 y hay soporte, puede ser zona NBIS.",
                "accion_rapida":     "🔴 REDUCIR - earning debajo de expectativas",
                "recompra_activa":   False,
            })
        else:  # gap < -8
            resultado.update({
                "clasificacion":     "negativo_fuerte",
                "color":             "#DC2626",
                "emoji":             "🎯",
                "decision_tiene":    f"STOP o REDUCIR 60% - Caída severa {gap:.1f}%. Evaluar si es error del mercado o problema real.",
                "decision_notiene":  f"🎯 ZONA RECOMPRA NBIS - Caída {gap:.1f}% post-earning. Esperar 2-3 días para confirmar piso. RSI y volumen.",
                "accion_rapida":     "🎯 RECOMPRA POTENCIAL - esperar piso (2-3 días)",
                "recompra_activa":   True,
            })

        resultado["move_total"] = move_total
    except Exception:
        pass

    return resultado

def analizar_posicion(precio_compra, precio_actual, rsi, macd,
                      ema_dist, score, pnl_pct, prob_nbis_v, sim_nbis_v, beta,
                      cat_fecha="-", dias_posicion=0, tipo="Accion", estrategia="Swing"):
    """
    Retorna un dict con:
      - tramos: lista de (pct, etiqueta, color) - los 3 tramos de gestión
      - señal: texto resumen
      - razon: explicación
      - color: color principal
      - urgencia: etiqueta de urgencia

    Lógica de 3 tramos NBIS:
      Tramo 1 (30%) -> +20% -> VENDER 30% para asegurar ganancia
      Tramo 2 (40%) -> +40% -> VENDER 40% momentum confirmado
      Tramo 3 (30%) -> +60% -> RUNNER dejar correr
    """
    import datetime
    # ── Categoría según Tipo + Beta ──────────────────────────
    if tipo == "ETF_Cripto":
        categoria = "VOLATIL 🔴 Cripto"
        stop_pct  = 0.80; t1_pct=0.30; t2_pct=0.60; t3_pct=1.00
        cat_label = f"ETF Cripto (Beta {beta:.1f})  - Stop -20%  - Targets +30/60/100%"
    elif tipo == "ETF_Indice":
        categoria = "CONSERVADOR 🔵 Índice"
        stop_pct  = 0.88; t1_pct=0.15; t2_pct=0.25; t3_pct=0.40
        cat_label = f"ETF Índice (Beta {beta:.1f})  - Acumulación LP  - Stop -12%  - Targets +15/25/40%"
    elif tipo == "ETF_Sectorial":
        categoria = "NORMAL 🟡 Sectorial"
        stop_pct  = 0.90; t1_pct=0.20; t2_pct=0.40; t3_pct=0.60
        cat_label = f"ETF Sectorial (Beta {beta:.1f})  - Patrón NBIS estándar"
    elif beta >= 2.5:
        categoria = "VOLATIL 🔴 Alta Beta"
        stop_pct  = 0.82; t1_pct=0.25; t2_pct=0.50; t3_pct=0.80
        cat_label = f"Acción alta volatilidad (Beta {beta:.1f})  - Stop -18%  - Targets +25/50/80%"
    elif beta < 1.5:
        categoria = "CONSERVADOR 🔵 Baja Beta"
        stop_pct  = 0.88; t1_pct=0.15; t2_pct=0.25; t3_pct=0.40
        cat_label = f"Acción baja volatilidad (Beta {beta:.1f})  - Stop -12%  - Targets +15/25/40%"
    else:
        categoria = "NORMAL 🟡 Estándar"
        stop_pct  = 0.90; t1_pct=0.20; t2_pct=0.40; t3_pct=0.60
        cat_label = f"Acción estándar (Beta {beta:.1f})  - Patrón NBIS  - Stop -10%  - Targets +20/40/60%"

    stop = precio_compra * stop_pct
    t1   = precio_compra * (1 + t1_pct)
    t2   = precio_compra * (1 + t2_pct)
    t3   = precio_compra * (1 + t3_pct)

    # ── Verificar si hay catalizador próximo (earnings, etc.) ──
    dias_para_cat = 999
    try:
        if cat_fecha and cat_fecha not in ("-","","Sin catalizador identificado","nan"):
            fecha_cat = pd.to_datetime(cat_fecha, errors="coerce")
            if fecha_cat and not pd.isna(fecha_cat):
                dias_para_cat = (fecha_cat.date() - datetime.date.today()).days
    except Exception:
        pass
    tiene_cat_proximo = 0 <= dias_para_cat <= 15  # earnings en próximos 15 días

    # ── v18: Earnings CONSUMIDOS (0-3 días PASADOS) ──────────────
    # Si el earning ya ocurrió, el catalizador está consumido
    # El movimiento actual ya refleja la reacción post-earnings
    try:
        if cat_fecha and cat_fecha not in ("-","","nan","NaT"):
            _cat_date = pd.to_datetime(cat_fecha, errors="coerce")
            if _cat_date and not pd.isna(_cat_date):
                _dias_desde_earn = (datetime.date.today() - _cat_date.date()).days
                if 0 <= _dias_desde_earn <= 3 and dias_posicion <= 5:
                    _earn_msg = (
                        "Momentum post-earnings es efímero — considerar tomar ganancias."
                        if pnl_pct > 5 else
                        "Si es sympathy play, revisar estado del líder antes de salir."
                        if pnl_pct < -5 else
                        "Mantener y monitorear 2-3 días más."
                    )
                    return {
                        "señal": f"📅 Post-Earnings ({_dias_desde_earn}d) — catalizador consumido",
                        "accion": (
                            f"El earning fue hace {_dias_desde_earn} día(s). "
                            f"El movimiento actual ({pnl_pct:+.1f}%) refleja la reacción. "
                            f"{_earn_msg}"
                        ),
                        "urgencia": "VIGILAR",
                        "tramos": [(100, "MONITOREAR")],
                        "color": "D97706",
                        "piramidar": None,
                    }
    except Exception:
        pass

    # ── v18: PIRAMIDACIÓN — agregar a posiciones ganadoras ───────
    # Detecta 3 zonas donde tiene sentido agregar más acciones:
    # Zona 1: primer pullback desde ganancia +8-20%
    # Zona 2: antes de catalizador próximo con ganancia positiva
    # Zona 3: ruptura de nuevos máximos con volumen institucional
    piramidar = None

    # Zona 2 — Catalizador próximo con posición ganadora (NBIS 13 Mayo, caso exacto)
    if pnl_pct > 3 and tiene_cat_proximo and 1 <= dias_para_cat <= 15:
        piramidar = {
            "accion":  f"🎯 AGREGAR {min(30, max(20, int(pnl_pct))):.0f}% antes del catalizador",
            "razon":   (f"Tienes ganancia +{pnl_pct:.0f}% Y earnings en {dias_para_cat}d. "
                        f"Zona óptima NBIS — agregar 20-30% antes del reporte. "
                        f"Si el catalizador es positivo, maximizas. "
                        f"Stop del agregado en precio actual −ATR×1.5."),
            "urgencia": "⚡ ANTES DEL CATALIZADOR",
            "color":    "#16A34A",
        }
    # Zona 1 — Primer pullback sano (+5-20% ganancia + 2-3 días bajistas = oportunidad de agregar)
    elif 5 < pnl_pct < 20 and dias_posicion >= 5 and macd > 0:
        piramidar = {
            "accion":  "📈 AGREGAR 25% en próximo pullback de -5%",
            "razon":   (f"Ganancia +{pnl_pct:.0f}% con tendencia activa (MACD positivo). "
                        f"Si el precio retrocede -5% desde el máximo sin romper la tendencia, "
                        f"es oportunidad de agregar 25% más. "
                        f"Stop del agregado = tu precio de entrada original ${precio_compra:.2f}."),
            "urgencia": "📡 MONITOREAR",
            "color":    "#0891B2",
        }
    # Zona 3 — Ganancia fuerte >20% con momentum (no agregar, mantener y ajustar stop)
    elif pnl_pct >= 20 and macd > 0:
        piramidar = {
            "accion":  "🚀 MANTENER — stop a breakeven garantizado",
            "razon":   (f"Ganancia excelente +{pnl_pct:.0f}%. "
                        f"Subir stop al precio de compra ${precio_compra:.2f} (breakeven). "
                        f"Con stop en breakeven, el trade no puede terminar en pérdida. "
                        f"Dejar correr el runner."),
            "urgencia": "✅ AJUSTAR STOP",
            "color":    "#7C3AED",
        }

    # ── Escenarios basados en PnL real (no RSI) ──────────────
    # El RSI alto en posición abierta no es señal de salida
    # La señal de salida la determina el PnL vs los 3 tramos NBIS

    # -2. Earnings con posición negativa -> cerrar antes del reporte
    if pnl_pct < -3 and tiene_cat_proximo and dias_para_cat <= 3 and estrategia != "Largo_Plazo":
        tramos = [(100,"VENDER",R),(0,"MANTENER",G),(0,"RUNNER",G)]
        return {"tramos":tramos,
                "señal":"⚠️ Earnings en 3 días con pérdida - CERRAR",
                "razon":"Posición en pérdida con earnings próximos. "
                        "Riesgo asimétrico - cerrar antes del reporte.",
                "color":R,"urgencia":"HOY"}

    # -0.5: Alerta día 7 — ventana óptima de salida (dato semana 27abr-08may)
    # IONQ día 9 +24.9%, RUN día 8 +26.5%, PANW día 9 +16.3%
    # Después del día 9 el momentum se agota — alerta para revisar
    if 7 <= dias_posicion < 10 and estrategia != "Largo_Plazo":
        if pnl_pct >= 8:
            return {
                "señal": f"⚡ Día {dias_posicion} — ventana óptima",
                "accion": (f"Estás en la VENTANA ÓPTIMA de salida (días 7-9). "
                           f"Considera vender 50-60% HOY para asegurar ganancia. "
                           f"Mantén 40% como runner si RSI < 68 y tendencia activa."),
                "urgencia": "ESTA SEMANA",
                "tramos": [(55,"VENDER 55%"),(45,"RUNNER")],
                "color": "D97706",
                "piramidar": None,
            }
        elif 0 < pnl_pct < 8:
            return {
                "señal": f"📡 Día {dias_posicion} — sin T1 aún",
                "accion": (f"Día {dias_posicion} sin llegar a T1 (+8%). "
                           f"Si no supera T1 antes del día 9 → salir. "
                           f"El modelo tiene WR bajo después del día 9 sin T1."),
                "urgencia": "VIGILAR",
                "tramos": [(100,"MANTENER")],
                "color": "2563EB",
                "piramidar": None,
            }

    # -1. Verificar día 10 con excepción por catalizador
    if dias_posicion >= 10 and estrategia != "Largo_Plazo":
        if tiene_cat_proximo and dias_para_cat <= 5:
            # Excepción: catalizador en próximos 5 días -> extender
            pass  # continuar con análisis normal
        elif pnl_pct > 0:
            tramos = [(60,"VENDER",R),(40,"MANTENER",A),(0,"RUNNER",G)]
            return {"tramos":tramos,"señal":"Día 10 - Vender 60%  - Revisar",
                    "razon":f"Día {dias_posicion} en posición. Swing venció. Vender 60% hoy. "
                            f"Sin catalizador próximo - no extender.","color":R,"urgencia":"HOY"}
        else:
            tramos = [(100,"VENDER",R),(0,"MANTENER",G),(0,"RUNNER",G)]
            return {"tramos":tramos,"señal":"Día 10 - Salida obligatoria",
                    "razon":f"Día {dias_posicion} en posición. Swing venció sin ganancia. "
                            f"Salir hoy - liberar capital para nueva oportunidad.","color":R,"urgencia":"HOY"}

    # 0. Largo plazo - sin stop, solo monitorear
    if estrategia == "Largo_Plazo":
        if pnl_pct >= t1_pct*100:
            tramos = [(30,"VENDER",OR),(40,"MANTENER",A),(30,"RUNNER",G)]
            return {"tramos":tramos,"señal":f"Vender 30%  - Mantener 70%",
                    "razon":f"Largo plazo  - {cat_label}. Target 1 alcanzado (+{pnl_pct:.0f}%). Vender 30%, mantener 70%.","color":G,"urgencia":"ESTA SEMANA"}
        elif pnl_pct < -30:
            tramos = [(0,"VENDER",TXT_SOFT),(50,"MANTENER",B),(50,"RUNNER",G)]
            return {"tramos":tramos,"señal":"Mantener - estrategia largo plazo",
                    "razon":f"Largo plazo  - {cat_label}. Pérdida {pnl_pct:.0f}% - en cripto es volatilidad normal. Mantener si tienes convicción en BTC/ETH.","color":B,"urgencia":"MONITOR"}
        else:
            tramos = [(0,"VENDER",TXT_SOFT),(60,"MANTENER",B),(40,"RUNNER",G)]
            return {"tramos":tramos,"señal":"Mantener - acumulación",
                    "razon":f"Largo plazo  - {cat_label}. P&L {pnl_pct:+.0f}%. Sin stop. Acumular en caídas si tienes convicción.","color":B,"urgencia":"MONITOR"}

    # 0b. Stop loss - prioridad absoluta (solo para Swing)
    if pnl_pct < -12:
        tramos = [(100,"VENDER",R),(0,"MANTENER",TXT_SOFT),(0,"RUNNER",TXT_SOFT)]
        return {"tramos":tramos,"señal":"SALIR - Stop loss activado",
                "razon":f"Pérdida {pnl_pct:.0f}%. Stop loss activado. Salir hoy sin excepción.","color":R,"urgencia":"STOP LOSS"}

    # 1. Pérdida leve - revisar catalizador
    if pnl_pct < -5:
        tramos = [(0,"VENDER",TXT_SOFT),(80,"MANTENER",B),(20,"RUNNER",G)]
        return {"tramos":tramos,"señal":"Mantener - revisar catalizador",
                "razon":f"Pérdida leve {pnl_pct:.0f}%. Verificar que el catalizador sigue válido. Si no hay catalizador -> evaluar salida.","color":B,"urgencia":"VIGILAR"}

    # 2. Break even / pérdida mínima
    if pnl_pct < 5:
        tramos = [(0,"VENDER",TXT_SOFT),(70,"MANTENER",B),(30,"RUNNER",G)]
        return {"tramos":tramos,"señal":"Mantener - esperar movimiento",
                "razon":f"{cat_label}. Break even ({pnl_pct:+.0f}%). Confirmar catalizador activo. Stop en ${stop:.2f}.",
                "color":B,"urgencia":"MONITOR","piramidar":piramidar}

    # 3. En camino - no llegó al Tramo 1 aún
    if pnl_pct < t1_pct * 100:
        if tiene_cat_proximo:
            razon_cat = f"Earnings en {dias_para_cat}d - mantener hasta el catalizador."
            urgencia_cat = "MONITOR"
        else:
            razon_cat = "Sin catalizador próximo. Vigilar RSI y stop."
            urgencia_cat = "AJUSTAR STOP"
        tramos = [(0,"VENDER",TXT_SOFT),(65,"MANTENER",A),(35,"RUNNER",G)]
        return {"tramos":tramos,"señal":"Mantener - en camino al Tramo 1",
                "razon":f"Ganancia {pnl_pct:+.0f}% - falta {20-pnl_pct:.0f}% para Tramo 1 (+20%). {razon_cat}",
                "color":A,"urgencia":urgencia_cat,"piramidar":piramidar}

    # 4. Tramo 1 alcanzado con catalizador próximo
    if pnl_pct >= t1_pct*100 and tiene_cat_proximo:
        tramos = [(30,"VENDER",OR),(45,"MANTENER",A),(25,"RUNNER",G)]
        return {"tramos":tramos,"señal":f"Vender 30%  - Mantener 70%",
                "razon":f"{cat_label}. Tramo 1 alcanzado (+{pnl_pct:.0f}%). Vender 30%. Earnings en {dias_para_cat}d - mantener 70%.",
                "color":A,"urgencia":"ESTA SEMANA","piramidar":piramidar}

    # 5. Tramo 1 alcanzado sin catalizador
    if pnl_pct >= t1_pct*100 and pnl_pct < t2_pct*100:
        tramos = [(30,"VENDER",OR),(45,"MANTENER",A),(25,"RUNNER",G)]
        return {"tramos":tramos,"señal":f"Vender 30%  - Mantener 70%",
                "razon":f"{cat_label}. Tramo 1 (+{t1_pct*100:.0f}%) alcanzado. Vender 30%, mantener 70% con stop en ${stop:.2f}.","color":A,"urgencia":"ESTA SEMANA"}

    # 6. Tramo 2 alcanzado
    if pnl_pct >= t2_pct*100 and pnl_pct < t3_pct*100:
        tramos = [(40,"VENDER",R),(35,"MANTENER",A),(25,"RUNNER",G)]
        return {"tramos":tramos,"señal":f"Vender 40%  - Runner 25%",
                "razon":f"{cat_label}. Tramo 2 (+{t2_pct*100:.0f}%) alcanzado. Vender 40%, dejar runner.","color":G,"urgencia":"HOY"}

    # 7. Tramo 3 alcanzado
    if pnl_pct >= t3_pct*100:
        tramos = [(30,"VENDER",R),(10,"MANTENER",A),(60,"RUNNER",G)]
        return {"tramos":tramos,"señal":f"Vender 30% más  - Runner libre",
                "razon":f"{cat_label}. Tramo 3 (+{t3_pct*100:.0f}%) alcanzado. Dejar runner correr.","color":G,"urgencia":"HOY"}

    # 9. Posición en ganancia moderada, patrón activo
    if pnl_pct > 0 and score > 55:
        tramos = [(0,"VENDER",TXT_SOFT),(60,"MANTENER",B),(40,"RUNNER",G)]
        return {"tramos":tramos,"señal":"0% Vender / 60% Mantener / 40% Runner",
                "razon":f"Ganancia {pnl_pct:.0f}%. Patrón en desarrollo, mantener posición.","color":G,"urgencia":"HOLD"}

    # 10. Default - posición nueva o neutral
    tramos = [(0,"VENDER",TXT_SOFT),(70,"MANTENER",B),(30,"RUNNER",G)]
    return {"tramos":tramos,"señal":"0% Vender / 70% Mantener / 30% Runner",
            "razon":"Posición activa. Monitorear Pre-Market y catalizador.","color":B,"urgencia":"MONITOR"}

# ─────────────────────────────────────────────────────────────
#  HELPERS DE RENDER
# ─────────────────────────────────────────────────────────────
def badge(text,cls="bg-gr"):
    return f'<span class="badge {cls}">{text}</span>'

def c_rsi(v):
    if v<30: return R
    if v<40: return A
    return TXT_MUT

def c_pre(v):
    if v>=8: return G
    if v>=5: return C
    if v>=3: return A
    return TXT_MUT

def c_vol(v):
    if v>=2.5: return G
    if v>=1.5: return A
    return TXT_MUT


# ─────────────────────────────────────────────────────────────
#  OPINIÓN DEL TRADER — v17
#  Sintetiza todos los indicadores en una frase accionable
#  Aparece en Tab1 Detectadas, Tab2 Swing, Tab3 Entrar Hoy, Tab5 Watchlist
# ─────────────────────────────────────────────────────────────
def generar_opinion_trader(
    ticker: str,
    etapa: str,
    rsi: float,
    dd: float,
    vol_ratio: float,
    macd: float,
    dias_alcistas: int,
    momentum_3d: float,
    prob_nbis: float,
    cat_fecha: str,
    arrastradas: str,
    lider: str,
    nivel_rebote: str,
    score: int,
    incluir_dilucion: bool = True,  # v18: buscar oferta SEC
) -> str:
    """
    Genera la opinión del trader en 2-3 líneas.
    v18: incluye advertencia de dilución si hay oferta secundaria reciente.
    VRDN $150M convertibles = el modelo lo detecta y avisa.
    """
    import datetime as _dt
    partes = []

    # ── 0. DILUCIÓN — va PRIMERO si existe (v18) ─────────────
    # Es la advertencia más importante — anula cualquier señal técnica
    if incluir_dilucion and ticker:
        try:
            _dil = detectar_dilucion_reciente(ticker)
            if _dil["tiene_dilucion"]:
                partes.insert(0,
                    f"⚠️ DILUCIÓN {_dil['tipo_oferta']} ({_dil['fecha_oferta']}, "
                    f"hace {_dil['dias_desde']}d) — "
                    f"esperar absorción antes de entrar. "
                    f"RSI bajo puede ser presión vendedora institucional, no oportunidad."
                )
        except Exception:
            pass

    # ── 1. Estado y razón principal ─────────────────────────
    if "M3" in etapa or "ENTRAR HOY" in etapa:
        partes.append(f"Señal M3 completa — patrón NBIS confirmado.")
    elif "SWING HOY" in etapa or "SWING" in etapa:
        partes.append(f"Momentum de swing fuerte — {dias_alcistas} días alcistas consecutivos.")
    elif "ANTICIPAR" in etapa or "PRE" in etapa:
        partes.append(f"Pre-señal activa — falta confirmación de volumen o MACD.")
    elif "M2" in etapa or "EN FORMACIÓN M2" in etapa:
        partes.append(f"En zona de preparación M2 — corrección absorbida, rebote iniciando.")
    elif "M1" in etapa or "DETECTADA" in etapa:
        partes.append(f"Corrección activa detectada — aún no es entrada, vigilar el rebote.")
    elif "CORRECCIÓN" in etapa:
        partes.append(f"Caída en curso — monitorear para entrada cuando gire.")
    else:
        partes.append(f"En radar — sin señal clara aún.")

    # ── 2. RSI ──────────────────────────────────────────────
    if rsi <= 30:
        partes.append(f"RSI {rsi:.0f} en sobreventa extrema — mercado exageró la caída.")
    elif rsi <= 42:
        partes.append(f"RSI {rsi:.0f} en zona de rebote — históricamente punto de entrada NBIS.")
    elif rsi <= 55:
        partes.append(f"RSI {rsi:.0f} neutral — saliendo de zona baja.")
    elif rsi <= 68:
        partes.append(f"RSI {rsi:.0f} en fuerza — momentum activo pero no sobrecomprado.")
    else:
        partes.append(f"RSI {rsi:.0f} elevado — precaución con nuevas entradas.")

    # ── 3. DD y corrección ──────────────────────────────────
    if dd <= -30:
        partes.append(f"Corrección {dd:.0f}% desde pico — severa, potencial rebote fuerte.")
    elif dd <= -15:
        partes.append(f"Corrección {dd:.0f}% — zona clásica del patrón NBIS.")
    elif dd <= -8:
        partes.append(f"Caída {dd:.0f}% — corrección válida para swing.")
    elif dd < 0:
        partes.append(f"Caída leve {dd:.0f}% — poca corrección, señal más débil.")

    # ── 4. Volumen ──────────────────────────────────────────
    if vol_ratio >= 200:
        partes.append(f"Volumen {vol_ratio:.0f}% del promedio — acumulación institucional fuerte.")
    elif vol_ratio >= 150:
        partes.append(f"Volumen {vol_ratio:.0f}% — interés institucional confirmado.")
    elif vol_ratio >= 100:
        partes.append(f"Volumen normal — sin señal de acumulación excepcional.")
    elif vol_ratio >= 80:
        partes.append(f"Volumen bajo {vol_ratio:.0f}% — señal más débil sin confirmación.")
    else:
        partes.append(f"Volumen muy bajo — esperar aumento antes de entrar.")

    # ── 5. MACD ─────────────────────────────────────────────
    if macd > 1.0:
        partes.append("MACD positivo y fuerte — momentum confirmado.")
    elif macd > 0:
        partes.append("MACD recién cruzó a positivo — giro alcista temprano.")
    elif macd > -1:
        partes.append("MACD levemente negativo — aún no confirma, vigilar cruce.")
    else:
        partes.append("MACD negativo — señal en corrección, esperar giro.")

    # ── 6. Catalizador ──────────────────────────────────────
    if cat_fecha and cat_fecha not in ("-","","nan","—"):
        try:
            dias_cat = (_dt.date.fromisoformat(cat_fecha[:10]) - _dt.date.today()).days
            if 1 <= dias_cat <= 7:
                partes.append(f"Earnings en {dias_cat}d — zona óptima NBIS: catalizador activo.")
            elif 1 <= dias_cat <= 15:
                partes.append(f"Earnings en {dias_cat}d — convicción extra para el setup.")
            elif dias_cat > 15:
                partes.append(f"Earnings en {dias_cat}d — monitorear acercamiento.")
            elif dias_cat == 0:
                partes.append("Reporta HOY — esperar resultado antes de entrar.")
        except Exception:
            pass

    # ── 7. Arrastradas / Líder (el tren) ────────────────────
    arr_clean = str(arrastradas) if arrastradas not in ("-","","nan") else ""
    lid_clean = str(lider) if lider not in ("-","","nan") else ""
    if arr_clean and arr_clean != "-":
        partes.append(f"Arrastra a {arr_clean} — si entra, buscar esas en M1/M2.")
    elif lid_clean and lid_clean != "-":
        partes.append(f"Arrastrada por {lid_clean} — verificar si el líder sigue subiendo.")

    # ── 8. Probabilidad NBIS ────────────────────────────────
    if prob_nbis >= 70:
        partes.append(f"Prob NBIS {prob_nbis:.0f}% — alta similitud con el patrón ganador.")
    elif prob_nbis >= 50:
        partes.append(f"Prob NBIS {prob_nbis:.0f}% — similitud moderada con el patrón.")
    elif prob_nbis >= 35:
        partes.append(f"Prob NBIS {prob_nbis:.0f}% — similitud baja, mayor cautela.")

    # Unir todo — máximo 3 frases para no saturar
    # Prioridad: estado + RSI + catalizador/arrastradas
    frases_clave = [partes[0]]  # siempre el estado
    if len(partes) > 1: frases_clave.append(partes[1])  # RSI
    # Catalizador o arrastradas si existen (más relevante que DD/vol)
    for p in partes:
        if "Earnings" in p or "Arrastra" in p or "líder" in p.lower():
            if p not in frases_clave:
                frases_clave.append(p)
                break
    if len(frases_clave) < 3 and len(partes) > 2:
        for p in partes[2:]:
            if p not in frases_clave:
                frases_clave.append(p)
                break

    return " · ".join(frases_clave[:3])


# ─────────────────────────────────────────────────────────────
#  MEMORIA DE TRADES — Google Sheets v18
#  Registra entradas/salidas/candidatos automáticamente
#  Sheet: GrekoTrader_Senales_Modelo (señales) o GrekoTrader_Posiciones_Greko (paper)
# ─────────────────────────────────────────────────────────────

# ID del Google Sheet de memoria (se crea automáticamente la primera vez)
_SHEET_NAME           = "GrekoTrader_Senales_Modelo"  # v18: nombre correcto
_SHEET_NAME_SENALES   = "GrekoTrader_Senales_Modelo"
_SHEET_NAME_TRADES    = "GrekoTrader_Trades_Reales"
_SHEET_NAME_MAURI     = "GrekoTrader_Posiciones_Mauri"
_SHEET_NAME_AMPARITO  = "GrekoTrader_Posiciones_Amparito"
_SHEET_NAME_GREKO     = "GrekoTrader_Posiciones_Greko"  # Tab C — paper trading

# v19.1: Configuración unificada de carteras
CARTERAS = {
    "🦅 Greko":    {
        "sheet":      _SHEET_NAME_GREKO,
        "secret_key": "posiciones_greko_id",
        "color":      "#2563EB",
        "color_bg":   "#EFF6FF",
        "emoji":      "🦅",
        "cache_df":   "_greko_processed_df",
        "cache_batch":"_greko_batch_cache",
        "cache_ts":   "_greko_cache_ts",
    },
    "📈 MVALLE":   {
        "sheet":      _SHEET_NAME_MAURI,
        "secret_key": "posiciones_mauri_id",
        "color":      "#16A34A",
        "color_bg":   "#F0FDF4",
        "emoji":      "📈",
        "cache_df":   "_mv_processed_df",
        "cache_batch":"_mv_batch_cache",
        "cache_ts":   "_mv_cache_ts",
    },
    "💜 Amparito": {
        "sheet":      _SHEET_NAME_AMPARITO,
        "secret_key": "posiciones_amparito_id",
        "color":      "#D97706",
        "color_bg":   "#FFFBEB",
        "emoji":      "💜",
        "cache_df":   "_amp_processed_df",
        "cache_batch":"_amp_batch_cache",
        "cache_ts":   "_amp_cache_ts",
    },
}
_SHEET_NAME_WATCHLIST = "GrekoTrader_Watchlist"           # v18: Watchlist desde Google Sheets
_SHEET_NAME_SYMPATHY  = "GrekoTrader_Sympathy"           # v18: relaciones tren de arrastre

# v18: leer Sheet IDs desde Streamlit secrets si están configurados
def _get_sheet_id_from_secrets(key: str) -> str:
    """Lee Sheet ID desde st.secrets[sheets][key] si existe."""
    try:
        return st.secrets["sheets"][key]
    except Exception:
        return ""

_SHEET_HEADERS = [
    "Fecha_Señal","Ticker","Area","Tipo_Registro","Fase","Precio_Entrada",
    "Cantidad","Score","Prob_NBIS","Cat_Fecha","Arrastradas","Lider",
    "Opinion_Trader","Version_Modelo","SPY_RSI",
    "Fecha_Salida","Precio_Salida","Resultado_Pct","Razon_Salida",
    "Fue_Correcto","Error_Modelo","Notas"
]

def _get_sheets_service():
    """Obtiene el servicio de Google Sheets via MCP."""
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        import json, os
        # Intenta leer credenciales desde secrets de Streamlit
        if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive"]
            )
            return build("sheets", "v4", credentials=creds)
    except Exception:
        pass
    return None

@st.cache_data(ttl=300, show_spinner=False)
def _buscar_sheet_id(nombre: str) -> str:
    """Busca el ID del Google Sheet por nombre."""
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/drive.readonly"]
            )
            drive = build("drive", "v3", credentials=creds)
            res = drive.files().list(
                q=f"name='{nombre}' and mimeType='application/vnd.google-apps.spreadsheet'",
                fields="files(id,name)"
            ).execute()
            files = res.get("files", [])
            return files[0]["id"] if files else ""
    except Exception:
        return ""

def _buscar_sheet_id(nombre: str) -> str:
    """Busca el ID del Google Sheet por nombre en Drive o en secrets."""
    # Primero intentar desde secrets (más rápido, sin llamada a Drive API)
    _secrets_map = {
        _SHEET_NAME_MAURI:    "posiciones_mauri_id",
        _SHEET_NAME_AMPARITO: "posiciones_amparito_id",
        _SHEET_NAME_SENALES:  "senales_modelo_id",
        _SHEET_NAME_TRADES:   "trades_reales_id",
        _SHEET_NAME_GREKO:    "posiciones_greko_id",
        _SHEET_NAME_WATCHLIST:"watchlist_id",             # v18: watchlist sheets
        _SHEET_NAME_SYMPATHY: "sympathy_id",            # v18: tren de arrastre
    }
    if nombre in _secrets_map:
        _id = _get_sheet_id_from_secrets(_secrets_map[nombre])
        if _id:
            return _id
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/drive.readonly"]
            )
            drive = build("drive", "v3", credentials=creds)
            res = drive.files().list(
                q=f"name='{nombre}' and mimeType='application/vnd.google-apps.spreadsheet'",
                fields="files(id,name)"
            ).execute()
            files = res.get("files", [])
            return files[0]["id"] if files else ""
    except Exception:
        return ""
    return ""


@st.cache_data(ttl=60, show_spinner=False)

def _parse_precio(val) -> float:
    """v19: Convierte precio desde Google Sheets — acepta '46,33' o '46.33'"""
    try:
        return float(str(val).strip().replace(",", ".").replace(" ", ""))
    except Exception:
        return 0.0

def _normalizar_precios_df(df: "pd.DataFrame") -> "pd.DataFrame":
    """v19: Normaliza columnas numéricas de posiciones — acepta coma o punto decimal"""
    for col in ["Precio_Compra", "Cantidad", "Precio_Salida", "Score",
                "Prob_NBIS", "SPY_RSI_Dia"]:
        if col in df.columns:
            df[col] = df[col].apply(_parse_precio)
    return df

def leer_posiciones_sheets(nombre_sheet: str) -> "pd.DataFrame | None":
    """
    v18 debug: Lee posiciones con diagnóstico paso a paso en session_state.
    """
    import streamlit as _st

    # Resetear debug log
    _log = []
    _st.session_state["sheets_debug_log"] = _log

    try:
        # PASO 1: secrets configurados?
        has_secrets = hasattr(_st, "secrets")
        has_gcp     = has_secrets and "gcp_service_account" in _st.secrets
        has_sheets  = has_secrets and "sheets" in _st.secrets
        _log.append(f"P1 secrets: has_secrets={has_secrets} has_gcp={has_gcp} has_sheets_section={has_sheets}")

        if not has_gcp:
            _st.session_state["sheets_error"] = "secrets_missing"
            _log.append("FALLO: gcp_service_account no encontrado en secrets")
            return None

        # PASO 2: construir credenciales
        try:
            from googleapiclient.discovery import build
            from google.oauth2 import service_account
            import os

            # v18: SSL workaround para redes con proxy/antivirus (Kaspersky, ESET, etc.)
            os.environ["PYTHONHTTPSVERIFY"] = "0"
            os.environ["CURL_CA_BUNDLE"]    = ""
            os.environ["REQUESTS_CA_BUNDLE"]= ""
            try:
                import urllib3
                urllib3.disable_warnings()
            except Exception:
                pass

            creds_dict = dict(_st.secrets["gcp_service_account"])
            _log.append(f"P2 creds: project={creds_dict.get('project_id','?')} email={creds_dict.get('client_email','?')[:40]}")
            creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
            )
            _log.append("P2 OK: credenciales construidas")
        except Exception as e2:
            _st.session_state["sheets_error"] = f"creds_error:{str(e2)[:80]}"
            _log.append(f"FALLO P2: {e2}")
            return None

        # PASO 3: obtener Sheet ID
        sheet_id = ""
        _id_map = {
            "GrekoTrader_Posiciones_Mauri":    "posiciones_mauri_id",
            "GrekoTrader_Posiciones_Amparito": "posiciones_amparito_id",
            "GrekoTrader_Senales_Modelo":      "senales_modelo_id",
            "GrekoTrader_Trades_Reales":       "trades_reales_id",
            "GrekoTrader_Posiciones_Greko":    "posiciones_greko_id",
        }
        secrets_key = _id_map.get(nombre_sheet, "")
        _log.append(f"P3 buscando: sheet='{nombre_sheet}' secrets_key='{secrets_key}'")

        if has_sheets and secrets_key:
            try:
                sheet_id = str(_st.secrets["sheets"].get(secrets_key, "")).strip()
                _log.append(f"P3 desde secrets: sheet_id='{sheet_id[:20]}...' " if len(sheet_id)>20 else f"P3 desde secrets: sheet_id='{sheet_id}' (vacío={'SÍ' if not sheet_id else 'NO'})")
            except Exception as e3a:
                _log.append(f"P3 secrets error: {e3a}")

        # Si no está en secrets, buscar en Drive
        if not sheet_id:
            _log.append("P3 sheet_id vacío en secrets → buscando en Drive por nombre")
            try:
                drive_svc = build("drive", "v3", credentials=creds)
                res = drive_svc.files().list(
                    q=f"name='{nombre_sheet}' and mimeType='application/vnd.google-apps.spreadsheet'",
                    fields="files(id,name)"
                ).execute()
                files = res.get("files", [])
                _log.append(f"P3 Drive encontró {len(files)} archivo(s) con nombre '{nombre_sheet}'")
                if files:
                    sheet_id = files[0]["id"]
                    _log.append(f"P3 usando: {sheet_id[:20]}...")
                else:
                    _st.session_state["sheets_error"] = f"not_found:{nombre_sheet}"
                    _log.append(f"FALLO P3: Sheet '{nombre_sheet}' no encontrado en Drive")
                    _log.append("SOLUCIÓN: Compartir el Sheet con el email del service account")
                    return None
            except Exception as e3b:
                _st.session_state["sheets_error"] = f"drive_error:{str(e3b)[:80]}"
                _log.append(f"FALLO P3 Drive: {e3b}")
                return None

        # PASO 4: leer datos del Sheet
        _log.append(f"P4 leyendo sheet_id={sheet_id[:20]}...")
        try:
            svc = build("sheets", "v4", credentials=creds)

            # v18 fix: detectar nombre real de la hoja
            # En español Google Sheets crea "Hoja 1" en lugar de "Sheet1"
            meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
            hojas = [s["properties"]["title"] for s in meta.get("sheets", [])]
            _log.append(f"P4 hojas encontradas: {hojas}")

            # Usar la primera hoja disponible
            hoja = hojas[0] if hojas else "Sheet1"
            _log.append(f"P4 usando hoja: '{hoja}'")

            result = svc.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"'{hoja}'!A1:Z1000"
            ).execute()
            values = result.get("values", [])
            _log.append(f"P4 OK: {len(values)} filas leídas (incluyendo header)")
        except Exception as e4:
            # Capturar TODOS los detalles del error
            import traceback
            e4_str     = str(e4)
            e4_type    = type(e4).__name__
            e4_repr    = repr(e4)
            e4_trace   = traceback.format_exc()[-300:]

            _st.session_state["sheets_error"] = f"read_error:{e4_type}:{e4_str[:80]}"
            _log.append(f"FALLO P4 tipo: {e4_type}")
            _log.append(f"FALLO P4 msg: {e4_str[:200] if e4_str else '(vacío)'}")
            _log.append(f"FALLO P4 repr: {e4_repr[:150]}")
            _log.append(f"FALLO P4 trace: {e4_trace[-200:]}")

            # Diagnóstico específico
            full_err = e4_str + e4_repr + e4_trace
            if "SSL" in full_err or "CERTIFICATE" in full_err or "ssl" in full_err:
                _log.append("→ CAUSA: SSL — proxy o antivirus")
            elif "403" in full_err:
                _log.append("→ CAUSA: 403 — Sheet no compartido con service account")
            elif "404" in full_err:
                _log.append("→ CAUSA: 404 — Sheet ID incorrecto")
            elif "API" in full_err and ("not" in full_err or "disabled" in full_err):
                _log.append("→ CAUSA: API no habilitada en Google Cloud")
            elif "quota" in full_err.lower():
                _log.append("→ CAUSA: Cuota de API excedida")
            elif not e4_str:
                _log.append("→ Error vacío — posible problema de red o timeout")
            return None

        if len(values) < 1:
            _st.session_state["sheets_error"] = "empty_sheet"
            _log.append("FALLO: Sheet completamente vacío")
            return None
        if len(values) < 2:
            _st.session_state["sheets_error"] = "no_data_rows"
            _log.append(f"FALLO: Solo headers '{values[0]}', sin filas de datos")
            return None

        # PASO 5: construir DataFrame
        headers   = values[0]
        rows      = values[1:]
        _log.append(f"P5 headers: {headers}")
        _log.append(f"P5 filas de datos: {len(rows)}")

        rows_norm = [r + [""] * (len(headers) - len(r)) for r in rows]
        df = pd.DataFrame(rows_norm, columns=headers)

        # Normalizar columna Fecha
        if "Fecha_Compra" in df.columns and "Fecha" not in df.columns:
            df = df.rename(columns={"Fecha_Compra": "Fecha"})

        if "Ticker" not in df.columns:
            _st.session_state["sheets_error"] = "no_ticker_column"
            _log.append(f"FALLO: No hay columna 'Ticker'. Columnas encontradas: {list(df.columns)}")
            return None

        df["Ticker"] = df["Ticker"].str.upper().str.strip()
        df = df[df["Ticker"] != ""]
        _log.append(f"P5 OK: {len(df)} posiciones cargadas — {list(df['Ticker'])}")

        _st.session_state["sheets_error"] = None
        _st.session_state["sheets_sheet_id"] = sheet_id
        return df if not df.empty else None

    except Exception as e:
        _st.session_state["sheets_error"] = f"exception:{str(e)[:100]}"
        _log.append(f"EXCEPCIÓN GLOBAL: {e}")
        return None


def guardar_posicion_sheets(nombre_sheet: str, df: pd.DataFrame) -> tuple:
    """
    Actualiza las posiciones en Google Sheets reemplazando todo el contenido.
    Se llama cuando el usuario registra una venta o modifica una posición.
    """
    try:
        svc = _get_sheets_service()
        if not svc:
            return False, "Google Sheets no configurado"
        sheet_id = _buscar_sheet_id(nombre_sheet)
        if not sheet_id:
            return False, f"Sheet '{nombre_sheet}' no encontrado"
        values = [list(df.columns)] + df.fillna("").values.tolist()
        # v18: detectar nombre real de hoja (Hoja 1 en español, Sheet1 en inglés)
        try:
            _meta_gps = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
            _hoja_gps = _meta_gps["sheets"][0]["properties"]["title"]
        except Exception:
            _hoja_gps = "Hoja 1"
        svc.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"'{_hoja_gps}'!A1",
            valueInputOption="USER_ENTERED",
            body={"values": values}
        ).execute()
        return True, f"✅ Posiciones actualizadas en Google Sheets"
    except Exception as e:
        return False, f"❌ Error: {str(e)[:60]}"



def limpiar_cache_sheets_only():
    """
    v19: Limpia cache de Google Sheets.
    Usa try/except por si alguna función no tiene @st.cache_data.
    """
    for _fn in [leer_posiciones_sheets, leer_watchlist_sheets,
                leer_sympathy_sheets, _buscar_sheet_id]:
        try:
            _fn.clear()
        except AttributeError:
            pass
    # Invalidar cartera global también
    st.session_state.pop("_cartera_global_cache", None)
    st.session_state.pop("_cartera_global_ts", None)

def escribir_trade_sheets(
    tipo: str,          # "ENTRADA","SALIDA","CANDIDATO","T1","STOP"
    ticker: str,
    fase: str,
    precio_entrada: float,
    cantidad: int = 0,
    score: int = 0,
    prob_nbis: float = 0,
    cat_fecha: str = "-",
    arrastradas: str = "-",
    lider: str = "-",
    opinion: str = "-",
    precio_salida: float = 0,
    razon_salida: str = "-",
    fue_correcto: str = "-",
    error_modelo: str = "-",
    notas: str = "",
    area: str = "",
    rsi_ticker: float = 0,  # v19 B+C: RSI del ticker específico al entrar
) -> tuple:
    """
    Escribe una fila en Google Sheets según el tipo de registro.
    Retorna (ok: bool, mensaje: str)
    """
    import datetime as _dt
    hoy = str(_dt.date.today().isoformat())  # v18: str() fuerza texto, evita serial de Excel
    
    resultado_pct = ""
    if precio_salida > 0 and precio_entrada > 0:
        resultado_pct = round((precio_salida - precio_entrada) / precio_entrada * 100, 2)
    
    # SPY RSI del día — v19 FIX: siempre calcular fresco al registrar
    # El caché mercado_data puede tener horas de antigüedad → valor incorrecto
    spy_rsi = ""
    try:
        import yfinance as _yf_spy2
        import pandas as _pd_spy2
        _spy_h = _yf_spy2.Ticker("SPY").history(period="1mo")
        if not _spy_h.empty:
            _s2 = _pd_spy2.Series(_spy_h["Close"].values)
            _d2 = _s2.diff()
            _g2 = _d2.clip(lower=0).rolling(14).mean()
            _l2 = (-_d2.clip(upper=0)).rolling(14).mean()
            spy_rsi = round(float(100 - 100/(1 + _g2.iloc[-1]/(_l2.iloc[-1]+1e-9))), 1)
            # Actualizar caché con el valor fresco
            st.session_state.setdefault("mercado_data", {}).setdefault("spy", {})["rsi"] = spy_rsi
    except Exception:
        # Fallback al caché si falla yfinance
        try:
            spy_rsi = round(float(st.session_state.get("mercado_data", {}).get("spy", {}).get("rsi", 0)), 1) or ""
        except Exception:
            spy_rsi = ""

    # v19 B: RSI del TICKER específico
    # Si viene el parámetro → usarlo directamente
    # Si no → intentar calcular desde yfinance
    _rsi_tk_final = ""
    try:
        if rsi_ticker and float(rsi_ticker) > 0:
            _rsi_tk_final = round(float(rsi_ticker), 1)
        else:
            # Calcular RSI del ticker desde yfinance
            import yfinance as _yf_rsi_tk
            import pandas as _pd_rsi_tk
            _tk_h = _yf_rsi_tk.Ticker(ticker).history(period="1mo")
            if not _tk_h.empty and len(_tk_h) >= 14:
                _s_tk = _pd_rsi_tk.Series(_tk_h["Close"].values)
                _d_tk = _s_tk.diff()
                _g_tk = _d_tk.clip(lower=0).rolling(14).mean()
                _l_tk = (-_d_tk.clip(upper=0)).rolling(14).mean()
                _rsi_tk_final = round(float(100 - 100/(1 + _g_tk.iloc[-1]/(_l_tk.iloc[-1]+1e-9))), 1)
    except Exception:
        _rsi_tk_final = ""

    # Area del ticker — v19: parámetro > Watchlist session_state > RAW > "-"
    _area_write = area if area and area not in ("-","","nan") else ""
    if not _area_write:
        # Buscar en wl_res_df (Watchlist cargado)
        try:
            _wl_df_ts = st.session_state.get("wl_res_df")
            if _wl_df_ts is not None and "Area" in _wl_df_ts.columns:
                _row_ts = _wl_df_ts[_wl_df_ts["Ticker"].str.upper() == ticker.upper()]
                if not _row_ts.empty:
                    _area_write = str(_row_ts.iloc[0]["Area"]).strip()
        except Exception:
            pass
    if not _area_write:
        # Buscar en RAW (universe estático)
        try:
            for _r in RAW:
                if isinstance(_r, tuple) and len(_r) > 2 and str(_r[0]).upper() == ticker.upper():
                    _area_write = str(_r[2])
                    break
        except Exception:
            pass
    if not _area_write or _area_write in ("-","","nan"):
        _area_write = "-"

    # v19: orden columnas GrekoTrader_Senales_Modelo
    # Fecha_Señal | Ticker | Fase | Precio_Entrada | Score | Prob_NBIS |
    # Cat_Fecha | Arrastradas | Lider | Opinion_Trader | Version_Modelo |
    # SPY_RSI_Dia (= RSI TICKER) | Tipo | Notas | Timestamp | Area | RSI_Mercado
    fila = [
        str(hoy),                               # Fecha_Señal
        ticker,                                 # Ticker
        fase,                                   # Fase
        precio_entrada,                         # Precio_Entrada
        score,                                  # Score
        prob_nbis,                              # Prob_NBIS
        cat_fecha,                              # Cat_Fecha
        arrastradas,                            # Arrastradas
        lider,                                  # Lider
        (opinion[:150] if opinion and opinion not in ("-","","nan") else "-"),  # Opinion_Trader
        "v19",                                  # Version_Modelo
        _rsi_tk_final if _rsi_tk_final else spy_rsi,  # SPY_RSI_Dia → v19: RSI del TICKER
        tipo,                                   # Tipo
        notas,                                  # Notas
        str(hoy),                               # Timestamp
        _area_write,                            # Area
        spy_rsi,                                # RSI_Mercado (SPY RSI del día) ← NUEVA col
    ]

    # v18 fix: usar el Sheet correcto según el tipo de registro
    # CANDIDATO/ENTRADA/SALIDA → Senales_Modelo
    # GREKO_PAPER → Posiciones_Greko
    if hasattr(locals(), 'sheet_name') and sheet_name:
        _sheet_destino = sheet_name
    elif tipo in ("GREKO_PAPER",):
        _sheet_destino = _SHEET_NAME_GREKO
    else:
        _sheet_destino = _SHEET_NAME_SENALES  # antes era _SHEET_NAME (Memoria_Trades)

    # Intentar escribir en Google Sheets
    try:
        svc = _get_sheets_service()
        if svc:
            sheet_id = _buscar_sheet_id(_sheet_destino)
            if not sheet_id:
                return False, f"Sheet '{_sheet_destino}' no encontrado. Verificar secrets."
            # Detectar nombre real de la hoja (Hoja 1 en español, Sheet1 en inglés)
            try:
                _meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
                _hoja = _meta["sheets"][0]["properties"]["title"]
            except Exception:
                _hoja = "Hoja 1"
            svc.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range=f"'{_hoja}'!A1",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": [fila]}
            ).execute()
            return True, f"✅ {tipo} de {ticker} registrado en Google Sheets"
        else:
            # Fallback: guardar en session_state (local, se pierde al cerrar)
            if "memoria_trades_local" not in st.session_state:
                st.session_state["memoria_trades_local"] = []
            st.session_state["memoria_trades_local"].append(dict(zip(_SHEET_HEADERS, fila)))
            return True, f"✅ {tipo} de {ticker} guardado localmente (configura Google Sheets para persistir)"
    except Exception as e:
        return False, f"❌ Error al guardar: {str(e)[:60]}"




def escribir_posicion_sheets(
    sheet_name: str,
    ticker: str,
    precio_compra: float,
    fase: str,
    score: int,
    prob_nbis: float,
    area: str,
    tipo: str,
    fuente: str,
    arrastradas: str = "-",
    opinion: str = "-",
    cantidad: float = 0,
    notas: str = "",
    rsi_ticker: float = 0.0,
    # v19.1: nuevas columnas X,Y,Z,AA
    rsi_accion: float = 0.0,
    macd_estado: str = "-",
    dd_pico_pct: float = 0.0,
    tipo_senal: str = "-",
) -> tuple:
    """
    v19.1: Función genérica — escribe en Greko, MVALLE o Amparito
    con 23 campos homologados (+ RSI_Accion, MACD_Estado, DD_Pico_Pct, Tipo_Señal).
    """
    import datetime as _dtp
    hoy = _dtp.date.today().strftime("%d-%m-%Y")

    def _fmt(v):
        try: return str(round(float(v), 2)).replace(".", ",")
        except: return str(v)

    # v19 FIX B: si rsi_ticker es 0, intentar desde session_state
    _rsi_tk_raw = float(rsi_ticker) if rsi_ticker else 0
    if _rsi_tk_raw <= 0:
        _rsi_tk_raw = float(st.session_state.get(f"_rsi_{ticker}", 0))
    spy_rsi_valor = round(_rsi_tk_raw, 1) if _rsi_tk_raw > 0 else "-"

    _spy_ctx = ""
    try:
        _mkt_p = st.session_state.get("mercado_data", {})
        _spy_r  = _mkt_p.get("spy", {}).get("rsi", 0)
        if _spy_r and float(_spy_r) > 0:
            _spy_ctx = f" | SPY RSI: {round(float(_spy_r),1)}"
    except Exception:
        pass
    notas_final = (notas + _spy_ctx).strip(" |")

    fila = [
        ticker,                                          # Ticker
        _fmt(precio_compra),                             # Precio_Compra
        str(round(float(cantidad), 1)).replace(".", ","), # Cantidad (decimal)
        hoy,                                             # Fecha_Entrada
        fuente,                                          # Fuente
        fase,                                            # Fase
        score,                                           # Score
        _fmt(prob_nbis),                                 # Prob_NBIS
        spy_rsi_valor,                                   # SPY_RSI_Dia
        area,                                            # Area
        tipo,                                            # Tipo
        arrastradas,                                     # Arrastradas
        (opinion[:120] if opinion else "-"),             # Opinion_Trader
        "",                                              # Precio_Salida
        "",                                              # Fecha_Salida
        "",                                              # Fue_Correcto
        "",                                              # Razon_Salida
        "",                                              # Error_Modelo
        notas_final,                                     # Notas
    ]

    try:
        svc = _get_sheets_service()
        if not svc:
            return False, "Google Sheets no configurado"
        sheet_id = _buscar_sheet_id(sheet_name)
        if not sheet_id:
            return False, f"Sheet '{sheet_name}' no encontrado"
        meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
        hoja = meta["sheets"][0]["properties"]["title"]
        svc.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"'{hoja}'!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [fila]}
        ).execute()
        # Invalidar caché
        limpiar_cache_sheets_only()
        st.session_state.pop("_cartera_global_cache", None)
        st.session_state.pop("_cartera_global_ts", None)

        _label = {
            _SHEET_NAME_GREKO:    "Posiciones Greko",
            _SHEET_NAME_MAURI:    "Posiciones MVALLE",
            _SHEET_NAME_AMPARITO: "Posiciones Amparito",
        }.get(sheet_name, sheet_name)
        return True, f"✅ {ticker} agregado a {_label}"
    except Exception as e:
        return False, f"❌ Error: {str(e)[:80]}"

def escribir_greko_sheets(
    ticker: str,
    precio_compra: float,
    fase: str,
    score: int,
    prob_nbis: float,
    area: str,
    tipo: str,
    fuente: str,
    arrastradas: str = "-",
    opinion: str = "-",
    cantidad: float = 0,
    notas: str = "",
    rsi_ticker: float = 0.0,
    rsi_accion: float = 0.0,
    macd_estado: str = "-",
    dd_pico_pct: float = 0.0,
    tipo_senal: str = "-",
) -> tuple:
    """
    v19: Wrapper para GrekoTrader_Posiciones_Greko
    Usa escribir_posicion_sheets() con 19 campos homologados.
    """
    return escribir_posicion_sheets(
        sheet_name=_SHEET_NAME_GREKO,
        ticker=ticker, precio_compra=precio_compra,
        fase=fase, score=score, prob_nbis=prob_nbis,
        area=area, tipo=tipo, fuente=fuente,
        arrastradas=arrastradas, opinion=opinion,
        cantidad=cantidad, notas=notas, rsi_ticker=rsi_ticker,
        rsi_accion=rsi_accion, macd_estado=macd_estado,
        dd_pico_pct=dd_pico_pct, tipo_senal=tipo_senal)

def escribir_greko_sheets_LEGACY(
    ticker: str, precio_compra: float, fase: str, score: int,
    prob_nbis: float, area: str, tipo: str, fuente: str,
    arrastradas: str = "-", opinion: str = "-",
    cantidad: float = 0, notas: str = "",
    rsi_ticker: float = 0.0,
) -> tuple:
    """LEGACY — mantener por compatibilidad, no usar directamente"""
    import datetime as _dtg
    # v19: fecha en formato DD-MM-AAAA para el Sheet
    hoy = _dtg.date.today().strftime("%d-%m-%Y")

    # v19 FIX: SPY_RSI_Dia = RSI real del SPY (contexto mercado)
    # rsi_ticker = RSI de la acción (va en Notas para trazabilidad)
    _spy_rsi_real = 0
    try:
        _mkt_g = st.session_state.get("mercado_data", {})
        _spy_rsi_real = float(_mkt_g.get("spy", {}).get("rsi", 0) or 0)
        if _spy_rsi_real <= 0:
            # Calcular fresco si no está en caché
            import yfinance as _yf_spy_pos
            _hspy = _yf_spy_pos.Ticker("SPY").history(period="1mo")
            if not _hspy.empty:
                _d = _hspy["Close"].diff()
                _g = _d.clip(lower=0).rolling(14).mean()
                _l = (-_d.clip(upper=0)).rolling(14).mean()
                _spy_rsi_real = round(float(100-100/(1+_g.iloc[-1]/(_l.iloc[-1]+1e-9))),1)
                st.session_state.setdefault("mercado_data",{}).setdefault("spy",{})["rsi"] = _spy_rsi_real
    except Exception:
        pass

    spy_rsi_valor = round(_spy_rsi_real, 1) if _spy_rsi_real > 0 else "-"

    # RSI de la acción en notas para trazabilidad
    _rsi_accion = round(float(rsi_ticker), 1) if rsi_ticker and float(rsi_ticker) > 0 else 0
    _ticker_rsi_nota = f" | RSI {_rsi_accion}" if _rsi_accion > 0 else ""
    notas_final = (notas + _ticker_rsi_nota).strip(" |")

    # Precio Max y Min histórico desde hoy (al entrar son iguales al precio)
    # v19: formatear números con coma decimal para Google Sheets (formato Chile)
    def _fmt_num(v):
        """Convierte float a string con coma decimal: 46.33 → '46,33'"""
        try:
            return str(round(float(v), 2)).replace(".", ",")
        except Exception:
            return str(v)

    fila_greko = [
        ticker,                    # Ticker
        _fmt_num(precio_compra),   # Precio_Compra — con coma decimal
        _fmt_num(cantidad),        # Cantidad
        hoy,                       # Fecha_Entrada — DD-MM-AAAA
        fuente,                    # Fuente
        fase,                      # Fase
        score,                     # Score
        _fmt_num(prob_nbis),       # Prob_NBIS
        spy_rsi_valor,             # SPY_RSI_Dia
        area,                      # Area
        tipo,                      # Tipo
        arrastradas,               # Arrastradas
        opinion[:120] if opinion else "-",  # Opinion_Trader
        "",                        # Precio_Salida
        "",                        # Fecha_Salida
        "",                        # Fue_Correcto
        "",                        # Razon_Salida
        "",                        # Error_Modelo
        notas_final,               # Notas
        "",                        # Cantidad_Activa (T)
        "",                        # Cantidad_Vendida (U)
        "",                        # PnL_Realizado_Pct (V)
        "",                        # Tramos_Salida (W)
        round(float(rsi_accion),1) if rsi_accion else "-",   # RSI_Accion (X)
        macd_estado if macd_estado else "-",                  # MACD_Estado (Y)
        round(float(dd_pico_pct),1) if dd_pico_pct else "-", # DD_Pico_Pct (Z)
        tipo_senal if tipo_senal else "-",                    # Tipo_Señal (AA)
    ]

    try:
        svc = _get_sheets_service()
        if not svc:
            return False, "Google Sheets no configurado"
        sheet_id = _buscar_sheet_id(_SHEET_NAME_GREKO)
        if not sheet_id:
            return False, f"Sheet '{_SHEET_NAME_GREKO}' no encontrado"
        meta_g = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
        hoja_g = meta_g["sheets"][0]["properties"]["title"]
        svc.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"'{hoja_g}'!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [fila_greko]}
        ).execute()
        limpiar_cache_sheets_only()
        return True, f"✅ {ticker} agregado a Posiciones Greko"
    except Exception as e:
        return False, f"❌ Error: {str(e)[:80]}"


@st.cache_data(ttl=600, show_spinner=False)
def leer_sympathy_sheets() -> dict:
    """
    v18: Lee GrekoTrader_Sympathy directamente por ID desde secrets.
    Intenta primero "Hoja 1", luego "Sheet1", luego via metadata.
    """
    _diag = []
    try:
        # PASO 1: Servicio
        svc = _get_sheets_service()
        if not svc:
            _diag.append("P1_FAIL: sin credenciales gcp_service_account")
            st.session_state["_sympathy_error"] = " | ".join(_diag)
            return {}
        _diag.append("P1_OK: Sheets service conectado")

        # PASO 2: Sheet ID
        sheet_id = _get_sheet_id_from_secrets("sympathy_id")
        if not sheet_id:
            _diag.append("P2_FAIL: sympathy_id no encontrado en st.secrets[sheets]")
            st.session_state["_sympathy_error"] = " | ".join(_diag)
            return {}
        _diag.append(f"P2_OK: sheet_id={sheet_id[:12]}...")

        # PASO 3: Intentar leer directamente con nombres comunes
        # Evita el metadata que puede fallar por permisos
        rows = []
        _hoja_usada = ""
        for _nombre_hoja in ["Hoja 1", "Sheet1", "Hoja1", "Sheet 1", "Sympathy"]:
            try:
                _result = svc.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=f"'{_nombre_hoja}'!A1:Z500"
                ).execute()
                _vals = _result.get("values", [])
                if _vals:
                    rows = _vals
                    _hoja_usada = _nombre_hoja
                    _diag.append(f"P3_OK: hoja='{_nombre_hoja}' → {len(rows)} filas")
                    break
            except Exception:
                continue

        # Si ninguno funcionó, intentar sin nombre de hoja
        if not rows:
            try:
                _result = svc.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range="A1:Z500"
                ).execute()
                rows = _result.get("values", [])
                _hoja_usada = "sin nombre"
                _diag.append(f"P3_OK: rango genérico → {len(rows)} filas")
            except Exception as _e3:
                _diag.append(f"P3_FAIL: {str(_e3)[:100]}")
                st.session_state["_sympathy_error"] = " | ".join(_diag)
                return {}

        if len(rows) < 2:
            _diag.append(f"P3_WARN: Sheet '{_hoja_usada}' vacío o solo headers — agrega datos en filas 2+")
            st.session_state["_sympathy_error"] = " | ".join(_diag)
            return {}

        # PASO 4: Parsear
        headers = [h.strip() for h in rows[0]]
        _diag.append(f"P4_OK: headers={headers[:5]}")
        sympathy = {}
        for row in rows[1:]:
            if not row: continue
            d = {headers[i]: row[i] if i < len(row) else ""
                 for i in range(len(headers))}
            tk = str(d.get("Ticker", "")).upper().strip()
            if not tk: continue
            sympathy[tk] = {
                "lider":       str(d.get("Lider", "-")).upper().strip(),
                "arrastradas": str(d.get("Arrastradas", "-")).strip(),
                "sector":      str(d.get("Sector", "-")).strip(),
                "correlacion": str(d.get("Correlacion", "-")).strip(),
                "tipo":        str(d.get("Tipo_Relacion", "-")).strip(),
                "notas":       str(d.get("Notas", "")).strip(),
            }
        _diag.append(f"P4_OK: {len(sympathy)} tickers parseados")
        st.session_state["_sympathy_error"] = ""
        st.session_state["_sympathy_diag"] = " | ".join(_diag)
        return sympathy

    except Exception as _e_symp:
        _diag.append(f"EXCEPTION: {str(_e_symp)[:150]}")
        try:
            st.session_state["_sympathy_error"] = " | ".join(_diag)
        except Exception:
            pass
        return {}


def get_sympathy_v18(ticker: str) -> dict:
    """
    v18: Obtiene relaciones de arrastre desde Google Sheet primero,
    luego fallback al RAW hardcodeado.
    """
    _default = {"lider": "-", "arrastradas": "-", "sector": "-",
                "correlacion": "-", "tipo": "-", "notas": ""}
    # Intentar desde Sheet primero
    try:
        _sheet_symp = leer_sympathy_sheets()
        if _sheet_symp and ticker.upper() in _sheet_symp:
            return _sheet_symp[ticker.upper()]
    except Exception:
        pass
    # Fallback al RAW
    _raw_symp = _SYMPATHY_LOOKUP.get(ticker.upper(), {})
    if _raw_symp:
        return {
            "lider":        _raw_symp.get("lider", "-"),
            "arrastradas":  _raw_symp.get("arrastradas", "-"),
            "sector":       _raw_symp.get("area", "-"),
            "correlacion":  "-",
            "tipo":         "peer",
            "notas":        "",
        }
    return _default


def get_lider_status(lider_ticker: str) -> dict:
    """
    v18: Obtiene el estado actual del ticker líder para evaluar si el tren sigue activo.
    Retorna precio, RSI, EMA20>EMA50, tendencia.
    """
    if not lider_ticker or lider_ticker in ("-", "", "nan"):
        return {"activo": False, "precio": 0, "rsi": 0, "tendencia": "-"}
    try:
        import yfinance as _yf_lid
        import pandas as _pd_lid
        import numpy as _np_lid
        hist = _yf_lid.Ticker(lider_ticker).history(period="3mo")
        if hist.empty or len(hist) < 20:
            return {"activo": False, "precio": 0, "rsi": 0, "tendencia": "-"}
        close = hist["Close"].values
        s = _pd_lid.Series(close)
        delta = s.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rsi   = round(float(100-100/(1+gain.iloc[-1]/(loss.iloc[-1]+1e-9))), 1)
        ema20 = float(s.ewm(span=20).mean().iloc[-1])
        ema50 = float(s.ewm(span=50).mean().iloc[-1])
        precio = round(float(close[-1]), 2)
        mom3  = round((close[-1]/close[-4]-1)*100, 1) if len(close)>=4 else 0
        tendencia_ok = ema20 > ema50 and rsi > 50
        return {
            "activo":    tendencia_ok,
            "precio":    precio,
            "rsi":       rsi,
            "ema20":     round(ema20, 2),
            "ema50":     round(ema50, 2),
            "ema_ok":    ema20 > ema50,
            "mom3":      mom3,
            "tendencia": "✅ Alcista" if tendencia_ok else "⚠️ Debilitando",
        }
    except Exception:
        return {"activo": False, "precio": 0, "rsi": 0, "tendencia": "Sin datos"}


def render_sympathy_panel(ticker: str, pc: float, pa: float,
                          pnl_pct: float,
                          G: str, A: str, R: str,
                          TXT_MUT: str, BOR: str) -> str:
    """
    v18: Renderiza el panel de Sympathy Play en la card de posición.
    Muestra estado del líder y recomendación basada en su tendencia.
    """
    symp = get_sympathy_v18(ticker)
    lider = symp["lider"]
    if lider in ("-", "", "nan"):
        return ""  # No es sympathy play

    # v19 FIX: si el líder es la misma acción → no hay tren real
    if str(lider).upper().strip() == str(ticker).upper().strip():
        return ""  # Líder indefinido, señal inválida

    lider_st = get_lider_status(lider)
    lider_color = "#16A34A" if lider_st["activo"] else "#D97706"
    rsi_l  = lider_st.get("rsi", 0)
    mom_l  = lider_st.get("mom3", 0)
    ema_ok = lider_st.get("ema_ok", False)

    # Recomendación basada en estado del líder
    if lider_st["activo"] and rsi_l >= 50:
        rec_color = "#16A34A"
        rec_text  = f"MANTENER — {lider} sigue alcista. Esperar recuperación de {ticker}."
        rec_icon  = "✅"
    elif rsi_l >= 45 and ema_ok:
        rec_color = "#D97706"
        rec_text  = f"VIGILAR — {lider} desacelerando. Monitorear 1-2 días más."
        rec_icon  = "⚠️"
    else:
        rec_color = "#DC2626"
        rec_text  = f"SALIR — {lider} perdió tendencia. El tren de arrastre se interrumpió."
        rec_icon  = "🛑"

    corr = symp.get("correlacion", "-")
    tipo = symp.get("tipo", "-")

    _corr_html = f'<span style="font-size:10px;color:#6B7280">Corr {corr}</span>' if corr != "-" else ""
    return (
        f'<div style="background:#F5F3FF;border:1px solid #C4B5FD;'
        f'border-radius:8px;padding:8px 12px;margin-top:6px">'
        f'<div style="font-size:10px;font-weight:700;color:#7C3AED;margin-bottom:4px">'
        f'🔗 SYMPATHY PLAY — depende de {lider}</div>'
        f'<div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap">'
        f'<span style="font-size:11px"><strong style="color:{lider_color}">{lider}</strong>'
        f' ${lider_st["precio"]:.2f} · RSI {rsi_l} · {lider_st["tendencia"]}</span>'
        f'<span style="font-size:10px;color:#6B7280">EMA20{">"if ema_ok else "<"}EMA50'
        f' · Mom3d {mom_l:+.1f}%</span>'
        f'{_corr_html}'
        f'</div>'
        f'<div style="margin-top:4px;font-size:11px;font-weight:700;color:{rec_color}">'
        f'{rec_icon} {rec_text}</div>'
        f'</div>'
    )



@st.cache_data(ttl=600, show_spinner=False)
def get_lider_estado(lider_tk: str) -> dict:
    """
    v18: Obtiene estado actual del ticker líder (ej: NBIS)
    para evaluar si el tren de arrastre sigue activo.
    """
    if not lider_tk or lider_tk in ("-","","nan"):
        return {}
    try:
        import yfinance as _yf_lid
        import pandas as _pd_lid
        hist = _yf_lid.Ticker(lider_tk).history(period="1mo")
        if hist.empty:
            return {}
        close = hist["Close"].values
        vol   = hist["Volume"].values
        s = _pd_lid.Series(close)
        delta = s.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rsi   = round(float(100-100/(1+gain.iloc[-1]/(loss.iloc[-1]+1e-9))), 1)
        ema20 = float(s.ewm(span=20).mean().iloc[-1])
        ema50 = float(s.ewm(span=50).mean().iloc[-1]) if len(close) >= 50 else ema20
        precio = float(close[-1])
        pico   = float(close.max())
        dd     = round((precio-pico)/pico*100, 1)
        mom3   = round((close[-1]/close[-4]-1)*100, 2) if len(close) >= 4 else 0
        avg_v  = float(__import__("numpy").mean(vol[-20:]))
        vol_r  = int(float(vol[-1])/avg_v*100) if avg_v > 0 else 100
        ema12  = float(s.ewm(span=12).mean().iloc[-1])
        ema26  = float(s.ewm(span=26).mean().iloc[-1]) if len(close) >= 26 else ema12
        macd   = round(ema12-ema26, 2)

        # Estado del tren
        tren_activo = (
            precio >= ema20 * 0.97 and  # precio cerca o sobre EMA20
            rsi >= 48 and               # RSI sin debilidad
            mom3 > -3 and               # sin momentum negativo fuerte
            macd > -0.5                  # MACD no colapsado
        )
        return {
            "precio":      round(precio, 2),
            "rsi":         rsi,
            "ema20":       round(ema20, 2),
            "ema50":       round(ema50, 2),
            "dd":          dd,
            "mom3":        mom3,
            "vol_ratio":   vol_r,
            "macd":        macd,
            "tren_activo": tren_activo,
            "sobre_ema20": precio >= ema20,
        }
    except Exception:
        return {}


def render_boton_registro(
    ticker: str, fase: str, precio: float, score: int,
    prob_nbis: float, cat_fecha: str, arrastradas: str,
    lider: str, opinion: str, key_prefix: str,
    tipo: str = "ENTRADA",
    area: str = "",
    rsi_ticker: float = 0,
):
    """
    v19: Botón de registro con destino seleccionable.
    Escribe en GrekoTrader_Senales_Modelo (señal) y
    opcionalmente también en Posiciones Greko/MVALLE/Amparito.
    """
    _icon = {"ENTRADA":"💾","CANDIDATO":"📌","SALIDA":"🏁","T1":"✂️","STOP":"🛑"}.get(tipo,"💾")
    _label = {"ENTRADA":f"💾 Registrar entrada {ticker}",
              "CANDIDATO":f"📌 Guardar como candidato",
              "SALIDA":f"🏁 Registrar salida",
              "T1":f"✂️ Registrar T1 (venta parcial)",
              "STOP":f"🛑 Registrar stop loss"}.get(tipo, "💾 Registrar")

    with st.expander(f"{_icon} {_label}", expanded=False):
        _c1, _c2 = st.columns(2)
        with _c1:
            _qty = st.number_input("Cantidad acciones", min_value=0.0,
                                    value=0.0, step=0.1, format="%.1f",
                                    key=f"qty_{key_prefix}_{ticker}",
                                    help="Acepta decimales: ej. 23.5 acciones")
            _notas = st.text_input("Notas (opcional)", key=f"notas_{key_prefix}_{ticker}",
                                    placeholder="ej: entré por earnings próximos")
        with _c2:
            if tipo in ("SALIDA","T1","STOP"):
                _p_sal = st.number_input("Precio salida",
                    min_value=0.0, value=float(precio), step=0.01,
                    key=f"psal_{key_prefix}_{ticker}")
                _razon = st.selectbox("Razón salida",
                    ["T1 alcanzado","T2 alcanzado","Stop loss","Decisión propia","Earnings","Otro"],
                    key=f"razon_{key_prefix}_{ticker}")
                _correcto = st.selectbox("¿Fue correcto?", ["SÍ","NO","PARCIAL"],
                    key=f"correcto_{key_prefix}_{ticker}")
                _error = st.text_input("Error del modelo (si aplica)",
                    key=f"error_{key_prefix}_{ticker}",
                    placeholder="ej: no detectó dilución")
            else:
                _p_sal = 0.0; _razon = "-"; _correcto = "-"; _error = "-"

            # v19: selector de cartera destino
            if tipo in ("ENTRADA","CANDIDATO"):
                _destino = st.selectbox(
                    "Guardar también en:",
                    ["Solo Señales Modelo","+ Posiciones Greko","+ Posiciones MVALLE","+ Posiciones Amparito"],
                    key=f"dest_{key_prefix}_{ticker}",
                    help="Registra la señal y opcionalmente agrega a tu cartera")
            else:
                _destino = "Solo Señales Modelo"

        if st.button(f"{_icon} Confirmar registro", key=f"btn_reg_{key_prefix}_{ticker}",
                     use_container_width=True, type="primary"):
            # Siempre escribir en Señales Modelo
            ok, msg = escribir_trade_sheets(
                tipo=tipo, ticker=ticker, fase=fase,
                precio_entrada=float(precio), cantidad=float(_qty),
                score=score, prob_nbis=prob_nbis,
                cat_fecha=cat_fecha, arrastradas=arrastradas,
                lider=lider, opinion=opinion,
                precio_salida=_p_sal, razon_salida=_razon,
                fue_correcto=_correcto, error_modelo=_error,
                notas=_notas, area=area,
                rsi_ticker=float(rsi_ticker) if rsi_ticker else 0,
            )
            if ok:
                st.success(msg)
            else:
                st.error(msg)

            # v19: también escribir en la cartera seleccionada
            if tipo in ("ENTRADA","CANDIDATO") and _destino != "Solo Señales Modelo":
                _sheet_map = {
                    "+ Posiciones Greko":    _SHEET_NAME_GREKO,
                    "+ Posiciones MVALLE":   _SHEET_NAME_MAURI,
                    "+ Posiciones Amparito": _SHEET_NAME_AMPARITO,
                }
                _target_sheet = _sheet_map.get(_destino)
                if _target_sheet:
                    _area_final = area if area and area not in ("-","","nan") else get_sector_from_raw(ticker)
                    ok2, msg2 = escribir_posicion_sheets(
                        sheet_name=_target_sheet,
                        ticker=ticker, precio_compra=float(precio),
                        fase=fase, score=score, prob_nbis=prob_nbis,
                        area=_area_final, tipo="Accion",
                        fuente={"tab2":"Swing Activo","tab3":"Entrar Hoy","tab5":"Mi Watchlist"}.get(key_prefix, key_prefix),
                        arrastradas=arrastradas,
                        opinion=opinion, cantidad=float(_qty),
                        notas=_notas, rsi_ticker=float(rsi_ticker) if rsi_ticker else 0,
                    )
                    if ok2:
                        st.success(msg2)
                        st.session_state.pop("_cartera_global_cache", None)
                        st.session_state.pop("_cartera_global_ts", None)
                    else:
                        st.error(msg2)

def render_table(df_sub, show_cols, tab_key="tabla"):
    if df_sub.empty:
        st.markdown(f'<div style="padding:16px;color:{TXT_MUT};font-size:12px;text-align:center;background:{BG_HEAD};border-radius:10px;border:1px solid {BOR}">- sin resultados -</div>',unsafe_allow_html=True)
        return

    # v11: calcular Score_Rebote si no existe en el DataFrame
    df_sub = df_sub.copy()

    # v17: calcular Opinion_Trader si no está en el DataFrame
    if "Opinion_Trader" not in df_sub.columns:
        def _make_opinion(r):
            try:
                return generar_opinion_trader(
                    ticker=str(r.get("Ticker","")),
                    etapa=str(r.get("Etapa_v12", r.get("Fase",""))),
                    rsi=float(r.get("RSI",50)), dd=float(r.get("DD_pico",0)),
                    vol_ratio=float(r.get("Volumen",100)),
                    macd=float(r.get("MACD",0)),
                    dias_alcistas=int(r.get("Dias_Alcistas",0)),
                    momentum_3d=float(r.get("Momentum_3d",0)),
                    prob_nbis=float(r.get("Prob_NBIS",0)),
                    cat_fecha=str(r.get("Cat_Fecha","-")),
                    arrastradas=str(r.get("Arrastradas","-")),
                    lider=str(r.get("Lider","-")),
                    nivel_rebote=str(r.get("Nivel_Rebote","-")),
                    score=int(r.get("Score", r.get("Score_Rebote",0))),
                    incluir_dilucion=True,  # v18: busca SEC EDGAR
                )
            except Exception:
                return "-"
        df_sub["Opinion_Trader"] = df_sub.apply(_make_opinion, axis=1)
    if "Score_Rebote" not in df_sub.columns or df_sub["Score_Rebote"].isna().all() or (df_sub["Score_Rebote"] == "").all():
        def _calc_sr(row):
            try:
                sr = calcular_score_rebote(
                    dd=float(row.get("DD_pico", 0)),
                    rsi=float(row.get("RSI", 50)),
                    vol_ratio=float(row.get("Volumen", 100)),
                    dias_alcistas=int(row.get("Dias_Alcistas", 0)),
                    momentum_3d=float(row.get("MACD", 0)),
                    tiene_catalizador=str(row.get("Cat_Fecha","-")) not in ("-","","nan"),
                    dias_para_cat=999,
                    beta=float(row.get("Beta", 1.5))
                )
                return sr["score"], sr["nivel"], sr["detalle"]
            except Exception:
                return 0, "🔵 DÉBIL", "-"
        _scores = df_sub.apply(_calc_sr, axis=1)
        df_sub["Score_Rebote"]   = [s[0] for s in _scores]
        df_sub["Nivel_Rebote"]   = [s[1] for s in _scores]
        df_sub["Detalle_Rebote"] = [s[2] for s in _scores]

    # ── Paginación ────────────────────────────────────────────
    PAGE_SIZE = 25
    total     = len(df_sub)
    n_pages   = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    _pk       = f"_page_{tab_key}"

    if n_pages > 1:
        pc1, pc2, pc3 = st.columns([1, 3, 1])
        with pc1:
            if st.button("◀ Anterior", key=f"prev_{tab_key}",
                         disabled=st.session_state.get(_pk, 0) == 0):
                st.session_state[_pk] = max(0, st.session_state.get(_pk, 0) - 1)
                st.rerun()
        with pc2:
            _pg = st.session_state.get(_pk, 0)
            _ini = _pg * PAGE_SIZE + 1
            _fin = min((_pg + 1) * PAGE_SIZE, total)
            st.markdown(
                f'<div style="text-align:center;font-size:11px;color:{TXT_MUT};padding-top:6px">'
                f'Página {_pg+1} de {n_pages}  - '
                f'Mostrando {_ini}-{_fin} de {total} acciones</div>',
                unsafe_allow_html=True)
        with pc3:
            if st.button("Siguiente ▶", key=f"next_{tab_key}",
                         disabled=st.session_state.get(_pk, 0) >= n_pages - 1):
                st.session_state[_pk] = min(n_pages - 1, st.session_state.get(_pk, 0) + 1)
                st.rerun()

        page = st.session_state.get(_pk, 0)
        df_sub = df_sub.iloc[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
    else:
        st.markdown(
            f'<div style="font-size:10px;color:{TXT_MUT};margin-bottom:6px">'
            f'{total} acciones encontradas</div>',
            unsafe_allow_html=True)
    rows_html=""
    for _,r in df_sub.iterrows():
        row_html="<tr>"
        for col in show_cols:
            val=r.get(col,"")
            cell=""
            if col=="Ticker":
                _tk_val = str(val)
                # v19: Badge de cartera
                _badge_cart = get_badge_cartera(_tk_val, G, R, A)
                # v19 FIX A: Badge de sector desde RAW
                _sector_val = str(r.get("Area", "")) if "Area" in r else ""
                if not _sector_val or _sector_val in ("-","","nan"):
                    _sector_val = get_sector_from_raw(_tk_val)
                else:
                    _sector_val = _normalizar_sector(_sector_val)
                # Badge en Watchlist
                _en_wl = sector_en_watchlist(_tk_val)
                _wl_badge = (
                    f'<span style="background:#DCFCE7;color:#16A34A;'
                    f'border-radius:4px;padding:1px 6px;font-size:9px;'
                    f'font-weight:600;margin-left:4px">✅ En Watchlist</span>'
                    if _en_wl else
                    f'<span style="background:#F1F5F9;color:#64748B;'
                    f'border-radius:4px;padding:1px 6px;font-size:9px;'
                    f'cursor:pointer">+ WL</span>'
                )
                _sector_badge = (
                    f'<div style="font-size:9px;color:#6366F1;'
                    f'margin-top:2px;font-weight:500">'
                    f'🏷️ {_sector_val}</div>'
                ) if _sector_val and _sector_val != "Sin sector" else ""
                # v19: Price Target badge
                _pt_eval = evaluar_price_target(_tk_val)
                _pt_warning = ""
                if _pt_eval.get("bloquear"):
                    _pt_warning = (
                        f'<div style="background:#FEF2F2;border-left:2px solid #DC2626;'
                        f'border-radius:0 4px 4px 0;padding:2px 6px;margin-top:2px;'
                        f'font-size:9px;font-weight:600;color:#DC2626">'
                        f'🚫 {_pt_eval.get("msg","")[:60]}</div>')
                elif _pt_eval.get("nivel") == "upside_limitado":
                    _pt_warning = (
                        f'<div style="background:#FFFBEB;border-left:2px solid #D97706;'
                        f'border-radius:0 4px 4px 0;padding:2px 6px;margin-top:2px;'
                        f'font-size:9px;font-weight:500;color:#D97706">'
                        f'⚠️ {_pt_eval.get("msg","")[:60]}</div>')
                elif _pt_eval.get("nivel") == "alto_upside":
                    _pt_warning = (
                        f'<div style="background:#F0FDF4;border-left:2px solid #16A34A;'
                        f'border-radius:0 4px 4px 0;padding:2px 6px;margin-top:2px;'
                        f'font-size:9px;font-weight:500;color:#16A34A">'
                        f'📈 {_pt_eval.get("msg","")[:60]}</div>')
                # v19: SMA badge
                _sma_badge = render_sma_badge(_tk_val, 0, TXT_MUT)
                cell = (
                    f'<strong style="color:{B};font-size:13px">{val}</strong>'
                    + _wl_badge
                    + _sector_badge
                    + _pt_warning
                    + (_sma_badge if _sma_badge else "")
                    + (_badge_cart if _badge_cart else "")
                )
            elif col=="Area":
                c2=SECTOR_COLORS.get(str(r.get("Area","")),TXT_MUT)
                _av = str(r.get("Area",""))
                _oil_badge = (
                    f'<span style="background:#FEF2F2;color:#DC2626;border-radius:3px;'
                    f'padding:0px 4px;font-size:9px;font-weight:700;margin-left:3px"'
                    f' title="Sector bajo presión - WTI ${oil.get(chr(34)+"precio"+chr(34),0):.0f}">⚠️</span>'
                    if _av in ("Consumo","Industrial","Retail") and oil.get("presion_sectorial") and oil.get("_ok")
                    else ""
                )
                cell=f'<span style="color:{c2};font-size:11px;font-weight:600">{val}</span>{_oil_badge}'
            elif col=="Decision":
                m={"ENTRAR":"bg-g","ANTICIPAR":"bg-c","SEGUIR":"bg-a",
                   "OBSERVAR":"bg-gr","REFERENCIA":"bg-p"}
                cell=badge(val,m.get(val,"bg-gr"))
            elif col=="Fase":
                cell=f'<span style="color:{TXT_MUT};font-size:11px">{val}</span>'
            elif col=="Trigger":
                v_str = str(val)
                if any(x in v_str for x in ["RUPTURA","REBOTE EN CURSO"]):
                    c2 = "bg-g"
                elif any(x in v_str for x in ["PRE-SEÑAL","MACD ALCISTA"]):
                    c2 = "bg-c"
                elif "FONDO" in v_str:
                    c2 = "bg-a"
                else:
                    c2 = "bg-r"
                cell=badge(val,c2)
            elif col=="Precio":
                es_live = r.get("_precio_live", False)
                live_badge = (f'<span style="background:{G_BG};color:{G};border:1px solid {G_BOR};'
                              f'border-radius:3px;padding:0px 4px;font-size:9px;font-weight:700;'
                              f'margin-left:4px">● live</span>') if es_live else (
                             f'<span style="background:{A_BG};color:{A};border:1px solid {A_BOR};'
                             f'border-radius:3px;padding:0px 4px;font-size:9px;'
                             f'margin-left:4px">estático</span>')
                cell=f'<span style="font-weight:700;color:{TXT}">${val:.2f}</span>{live_badge}'
            elif col=="Prob_NBIS":
                c2=G if val>=75 else A if val>=55 else TXT_MUT
                cell=f'<span style="color:{c2};font-weight:700">{val}</span>'
            elif col=="Sim_NBIS":
                c2=G if val>=60 else A if val>=45 else TXT_MUT
                cell=f'<span style="color:{c2};font-weight:700">{val:.1f}</span>'
            elif col=="Motivo":
                cell=f'<span style="color:{TXT_MUT};font-size:11px">{val}</span>'
            elif col=="Opinion_Trader":
                v2 = str(val) if val and str(val) not in ("-","","nan") else ""
                if v2:
                    _oc = G if any(x in v2 for x in ["M3","ENTRAR","confirmado","institucional"]) else \
                          C if any(x in v2 for x in ["Pre-señal","preparación","recién"]) else \
                          A if any(x in v2 for x in ["M2","M1","vigilar","esperar"]) else TXT_MUT
                    # v18 fix: word-wrap + max-width contenida para no solaparse con Lectura
                    _txt_short = v2[:120] + ("…" if len(v2) > 120 else "")
                    cell = (f'<div style="background:{BG_HEAD};border-left:3px solid {_oc};'
                            f'border-radius:0 6px 6px 0;padding:4px 8px;'
                            f'width:200px;max-width:200px;'
                            f'word-wrap:break-word;overflow-wrap:break-word;'
                            f'white-space:normal;overflow:hidden">'
                            f'<span style="color:{_oc};font-size:10px;line-height:1.4">'
                            f'🦅 {_txt_short}</span></div>')
                else:
                    cell = f'<span style="color:{TXT_SOFT};font-size:10px">—</span>'
            elif col=="Lectura":
                v2=str(val)
                # v18 fix: Lectura también contenida para no solaparse con Opinion_Trader
                _lect_short = v2[:60] + ("…" if len(v2) > 60 else "")
                cell = (f'<div style="width:160px;max-width:160px;'
                        f'word-wrap:break-word;overflow-wrap:break-word;'
                        f'white-space:normal">'
                        f'<span style="color:{TXT_MUT};font-size:10px">{_lect_short}</span></div>')
            elif col=="Arrastradas":
                if val and str(val) not in ("-","","nan"):
                    # v15: chips con tooltip "arrastra a X"
                    chips = " ".join([
                        f'<span style="background:{C_BG};color:{C};border-radius:5px;'
                        f'padding:2px 7px;font-size:10px;font-weight:700;'
                        f'border:1px solid {C_BOR};margin:1px" title="Arrastrada: aún no subió">'
                        f'🔗 {tk.strip()}</span>'
                        for tk in str(val).split(",") if tk.strip()
                    ])
                    cell = chips if chips else f'<span style="color:{TXT_SOFT}">-</span>'
                else:
                    cell = f'<span style="color:{TXT_SOFT}">-</span>'
            elif col=="Lider":
                if val and str(val) not in ("-","","nan"):
                    cell = (f'<span style="background:{P_BG};color:{P};border-radius:5px;'
                            f'padding:2px 8px;font-size:10px;font-weight:700;'
                            f'border:1px solid {P_BOR}" title="Líder del movimiento">'
                            f'🏆 {val}</span>')
                else:
                    cell = f'<span style="color:{TXT_SOFT}">-</span>'
            elif col=="Score":
                c2=G if val>=75 else A if val>=55 else R
                bonus_f = r.get("Bonus_Fund", 0)
                bonus_str = (f'<span style="color:{G};font-size:9px"> +{bonus_f}F</span>'
                             if bonus_f > 0 else
                             f'<span style="color:{R};font-size:9px"> {bonus_f}F</span>'
                             if bonus_f < 0 else "")
                cell=f'<span style="color:{c2};font-weight:700;font-size:13px">{val}</span>{bonus_str}'
            elif col=="RSI":
                tend = r.get("RSI_Tend", 0)
                flecha = " ↑" if tend>0 else " ↓" if tend<0 else ""
                cell=f'<span style="color:{c_rsi(val)};font-weight:700">{val}{flecha}</span>'
            elif col=="Pre_Move":
                _pmv = float(val) if val else 0
                cell=f'<span style="color:{G if _pmv>0 else R};font-weight:700">{_pmv:+.1f}%</span>' if _pmv else "-"
            elif col=="Post_Move":
                _pov = float(val) if val else 0
                cell=f'<span style="color:{G if _pov>0 else R};font-weight:700">{_pov:+.1f}%</span>' if _pov else "-"
            elif col=="Pre_Vol":
                cell=f'<span style="color:{c_vol(val)};font-weight:700">{val:.1f}x</span>'
            elif col=="Post_Vol":
                cell=f'<span style="color:{c_vol(val)};font-weight:700">{val:.1f}x</span>'
            elif col=="Short_Int":
                c2=R if val>=20 else A if val>=12 else TXT_MUT
                cell=f'<span style="color:{c2};font-weight:700">{val:.1f}%</span>'
            elif col=="DD_pico":
                cell=f'<span style="color:{R};font-weight:700">{val:.0f}%</span>'
            elif col=="Patron_Tipo":
                emoji = r.get("Patron_Emoji","📈")
                desc  = r.get("Patron_Dias","-")
                tipo_colors = {"EXPLOSIVO":R,"GRADUAL":G,"CÍCLICO":C}
                tc = tipo_colors.get(str(val), TXT_MUT)
                cell = (f'<span style="color:{tc};font-weight:700;font-size:11px">{emoji} {val}</span>'
                        f'<br><span style="color:{TXT_SOFT};font-size:9px">{desc}</span>')
            elif col=="RSI_Dir":
                dir_colors = {"RSI REBOTANDO":G,"RSI BASE":A,"RSI CAYENDO":R,
                              "TRAMPA DD":R,"RSI NEUTRO":TXT_MUT}
                dc = dir_colors.get(str(val), TXT_MUT)
                desc2 = str(r.get("RSI_Dir_Desc",""))[:35]
                cell = (f'<span style="color:{dc};font-weight:600;font-size:10px">{val}</span>'
                        f'<br><span style="color:{TXT_SOFT};font-size:9px">{desc2}</span>')
            elif col=="Cat_Fecha":
                # v15: colores por urgencia de earnings en TODOS los tabs
                import datetime as _dtt
                _cf = str(val)
                if _cf in ("-","","nan"):
                    cell = f'<span style="color:{TXT_SOFT};font-size:11px">-</span>'
                else:
                    try:
                        _fc2   = _dtt.date.fromisoformat(_cf[:10])
                        _dias2 = (_fc2 - _dtt.date.today()).days
                        if _dias2 < 0:
                            cell = f'<span style="color:{TXT_SOFT};font-size:11px">✅ {_cf[:10]}</span>'
                        elif _dias2 <= 2:
                            cell = (f'<span style="background:#FEF2F2;color:#DC2626;border:1px solid #FCA5A5;'
                                    f'border-radius:6px;padding:2px 7px;font-size:10px;font-weight:800">'
                                    f'🚫 {_dias2}d - NO ENTRAR</span>')
                        elif _dias2 <= 6:
                            cell = (f'<span style="background:#FFFBEB;color:#D97706;border:1px solid #FCD34D;'
                                    f'border-radius:6px;padding:2px 7px;font-size:10px;font-weight:700">'
                                    f'⚠️ {_dias2}d - Cuidado</span>')
                        elif _dias2 <= 15:
                            cell = (f'<span style="background:#F0FDF4;color:#16A34A;border:1px solid #86EFAC;'
                                    f'border-radius:6px;padding:2px 7px;font-size:10px;font-weight:700">'
                                    f'🎯 {_dias2}d - Zona NBIS</span>')
                        elif _dias2 <= 30:
                            cell = (f'<span style="background:#EFF6FF;color:#2563EB;border:1px solid #BFDBFE;'
                                    f'border-radius:6px;padding:2px 7px;font-size:10px;font-weight:700">'
                                    f'📅 {_dias2}d - Monitorear</span>')
                        else:
                            cell = f'<span style="color:{TXT_MUT};font-size:11px">📅 {_cf[:10]}</span>'
                    except Exception:
                        cell = f'<span style="color:{TXT_MUT};font-size:11px">{_cf[:10]}</span>'
            else:
                cell=f'<span style="color:{TXT}">{val}</span>'
            row_html+=f"<td>{cell}</td>"
        row_html+="</tr>"
        rows_html+=row_html
    hdr={"Ticker":"Ticker","Area":"Área","Decision":"Decisión","Fase":"Fase","Trigger":"Trigger",
         "Precio":"Precio","Score_Rebote":"Score Rebote","Nivel_Rebote":"Nivel","Detalle_Rebote":"Detalle Score",
         "Prob_NBIS":"Score Rebote","Sim_NBIS":"Nivel","Motivo":"Motivo",
         "Opinion_Trader":"🦅 Opinión Trader","Lectura":"Lectura Trader","Arrastradas":"Arrastradas","Patron_Tipo":"Tipo Patrón","RSI_Dir":"RSI Dir","Lider":"Líder",
         "Score":"Score","RSI":"RSI","Pre_Move":"Pre-Mkt %","Post_Move":"Post-Mkt %","Pre_Vol":"Vol Pre",
         "Post_Vol":"Vol Post","Short_Int":"Short %","DD_pico":"DD Caída","Cat_Fecha":"Catalizador"}
    ths="".join([f"<th>{hdr.get(c,c)}</th>" for c in show_cols])
    st.markdown(f'<div class="tbl-wrap"><table class="dtbl"><thead><tr>{ths}</tr></thead><tbody>{rows_html}</tbody></table></div>',unsafe_allow_html=True)

    # ── Paneles expandibles de noticias por ticker ──────────
    news_cache = st.session_state.get("noticias_cache", {})
    if news_cache:
        st.markdown(f'<div style="font-size:11px;color:{TXT_MUT};margin:10px 0 6px">📰 Noticias - click en el ticker para expandir</div>', unsafe_allow_html=True)
        for _, r in df_sub.iterrows():
            tk = r["Ticker"]
            tk_data = news_cache.get(tk, {})
            noticias = tk_data.get("noticias", [])
            bonus    = tk_data.get("bonus", 0)
            bonus_str = f"+{bonus}" if bonus > 0 else str(bonus)
            bonus_color = G if bonus > 0 else R if bonus < 0 else TXT_MUT
            n_alc = sum(1 for n in noticias if n["sentimiento"]=="Alcista")
            n_baj = sum(1 for n in noticias if n["sentimiento"]=="Bajista")
            label = (f"📰 {tk} - {len(noticias)} noticias  - "
                     f"🟢{n_alc} alcistas  - 🔴{n_baj} bajistas  - "
                     f"Impacto score: {bonus_str} pts")
            with st.expander(label, expanded=False):
                render_noticias_panel(tk, noticias, bonus)
    else:
        st.markdown(
            f'<div style="background:{A_BG};border:1px solid {A_BOR};border-radius:8px;'
            f'padding:8px 12px;font-size:11px;color:{A};margin-top:8px">'
            f'💡 Presiona "Actualizar noticias" en el sidebar para ver análisis automático</div>',
            unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
KEYWORDS_ALCISTA = [
    "beat","beats","upgrade","upgraded","buy","outperform","contract","contracts",
    "approval","approved","growth","record","partnership","acquisition","bullish",
    "raised","raises","target","expands","wins","awarded","launches","strong",
    "exceeds","accelerat","positive","rally","rebound","surges","breakthrough",
    "dividend","buyback","investment","deal","agreement","milestone"
]
KEYWORDS_BAJISTA = [
    "miss","misses","downgrade","downgraded","sell","underperform","layoff","layoffs",
    "recall","investigation","loss","losses","bearish","cut","cuts","warning","warns",
    "decline","fell","drops","disappoints","weak","concern","risk","below","fraud",
    "lawsuit","probe","fine","penalty","delay","withdrawal","reject","rejected"
]

def analizar_sentimiento_noticia(titulo: str) -> tuple:
    """
    Analiza el sentimiento de un titular de noticia.
    Retorna (sentimiento, impacto, keywords_encontradas)
    """
    titulo_lower = titulo.lower()
    score_alc = sum(1 for k in KEYWORDS_ALCISTA if k in titulo_lower)
    score_baj = sum(1 for k in KEYWORDS_BAJISTA if k in titulo_lower)

    if score_alc > score_baj:
        impacto = min(score_alc * 2, 8)
        return "Alcista", impacto, [k for k in KEYWORDS_ALCISTA if k in titulo_lower]
    elif score_baj > score_alc:
        impacto = -min(score_baj * 2, 8)
        return "Bajista", impacto, [k for k in KEYWORDS_BAJISTA if k in titulo_lower]
    else:
        return "Neutro", 0, []

def clasificar_tipo_noticia(titulo: str) -> str:
    """Clasifica el tipo de noticia según el titular."""
    t = titulo.lower()
    if any(k in t for k in ["earnings","results","revenue","eps","quarterly","q1","q2","q3","q4"]): return "Earnings"
    if any(k in t for k in ["fda","approval","trial","clinical","drug","therapy"]): return "FDA/Clínico"
    if any(k in t for k in ["contract","deal","agreement","partnership","awarded"]): return "Contrato"
    if any(k in t for k in ["upgrade","downgrade","target","analyst","rating","price target"]): return "Analyst"
    if any(k in t for k in ["insider","ceo","cfo","bought","purchased","sold shares"]): return "Insider"
    if any(k in t for k in ["buyback","dividend","acquisition","merger"]): return "Corporativo"
    return "Macro/Sector"

@st.cache_data(ttl=21600, show_spinner=False)  # cache 6 horas
def fetch_noticias_ticker(ticker: str) -> list:
    """
    Descarga y analiza las últimas noticias de un ticker via yfinance.
    Compatible con todas las versiones de yfinance. Max 5s por ticker.
    """
    noticias = []
    try:
        import yfinance as yf
        stk = yf.Ticker(ticker)
        try:
            raw_news = stk.news or []
        except Exception:
            raw_news = []
        if not raw_news:
            return []

        for item in raw_news[:8]:
            try:
                titulo, link, ts, fuente = "", "", 0, "Yahoo Finance"

                if isinstance(item, dict):
                    # Formato nuevo: content anidado
                    content = item.get("content", {})
                    if isinstance(content, dict):
                        titulo = content.get("title","") or content.get("headline","")
                        cl = content.get("clickThroughUrl", {})
                        link = cl.get("url","") if isinstance(cl, dict) else str(cl)
                        prov = content.get("provider",{})
                        fuente = prov.get("displayName","Yahoo Finance") if isinstance(prov,dict) else "Yahoo Finance"
                        ts = content.get("pubDate", 0)
                    # Formato antiguo: campos directos
                    if not titulo:
                        titulo = item.get("title","") or item.get("headline","")
                        link   = item.get("link","") or item.get("url","")
                        ts     = item.get("providerPublishTime",0)
                        fuente = item.get("publisher","Yahoo Finance")
                else:
                    titulo = getattr(item,"title","") or getattr(item,"headline","")
                    link   = getattr(item,"link","") or getattr(item,"url","")
                    ts     = getattr(item,"providerPublishTime",0)
                    fuente = getattr(item,"publisher","Yahoo Finance")

                if not titulo or not link:
                    continue

                # v18: filtrar noticias genéricas de yfinance (eventos corporativos)
                _titulo_lower = titulo.lower()
                _es_generico = any(x in _titulo_lower for x in [
                    "equity investor", "common stock", "class a shares",
                    "form 8-k", "form 10-", "proxy statement", "sec filing",
                    "annual report", "quarterly report", "ex-dividend",
                    "stock split", "dividend payment", "rights offering",
                ])
                if _es_generico:
                    continue

                # Calcular antigüedad
                fecha_dt = datetime.datetime.fromtimestamp(ts) if ts else datetime.datetime.now()
                dias_atras = (datetime.datetime.now() - fecha_dt).days
                fecha_str  = fecha_dt.strftime("%d %b %Y")

                # Noticias > 14 días pesan la mitad
                sentimiento, impacto_base, keywords = analizar_sentimiento_noticia(titulo)
                impacto = impacto_base // 2 if dias_atras > 14 else impacto_base
                tipo = clasificar_tipo_noticia(titulo)

                # Filtrar títulos muy cortos (< 20 chars = no es noticia real)
                if len(titulo.strip()) < 20:
                    continue

                noticias.append({
                    "titulo":      titulo,
                    "link":        link,
                    "fecha":       fecha_str,
                    "dias":        dias_atras,
                    "fuente":      fuente,
                    "tipo":        tipo,
                    "sentimiento": sentimiento,
                    "impacto":     impacto,
                    "keywords":    keywords,
                })
            except Exception:
                continue

    except Exception:
        pass

    return noticias

def calcular_bonus_noticias(noticias: list) -> int:
    """Suma el impacto total de las noticias con límite de +12/-8 pts."""
    if not noticias:
        return 0
    total = sum(n["impacto"] for n in noticias)
    return max(-8, min(12, total))  # cap: +12 alcista, -8 bajista

def render_noticias_panel(ticker: str, noticias: list, bonus: int):
    """Renderiza el panel expandible de noticias para un ticker."""
    if not noticias:
        st.markdown(
            f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:8px;'
            f'padding:10px 14px;font-size:11px;color:{TXT_MUT}">Sin noticias recientes</div>',
            unsafe_allow_html=True)
        return

    bonus_color = G if bonus > 0 else R if bonus < 0 else TXT_MUT
    bonus_txt   = f"+{bonus}" if bonus > 0 else str(bonus)

    st.markdown(
        f'<div style="font-size:11px;color:{TXT_MUT};margin-bottom:6px">'
        f'Impacto total noticias: <strong style="color:{bonus_color}">{bonus_txt} pts al score</strong>'
        f'  - {len(noticias)} noticias analizadas</div>',
        unsafe_allow_html=True)

    for n in noticias:
        # Color por sentimiento
        if n["sentimiento"] == "Alcista":
            s_color = G; s_bg = G_BG; s_bor = G_BOR
            imp_txt = f'+{n["impacto"]} pts'
        elif n["sentimiento"] == "Bajista":
            s_color = R; s_bg = R_BG; s_bor = R_BOR
            imp_txt = f'{n["impacto"]} pts'
        else:
            s_color = TXT_MUT; s_bg = BG_HEAD; s_bor = BOR
            imp_txt = "0 pts"

        # Color tipo noticia
        tipo_colors = {
            "Earnings": B, "FDA/Clínico": P, "Contrato": G,
            "Analyst": A, "Insider": C, "Corporativo": B, "Macro/Sector": TXT_MUT
        }
        t_color = tipo_colors.get(n["tipo"], TXT_MUT)

        # Antigüedad
        dias_str = "hoy" if n["dias"]==0 else f"hace {n['dias']}d"

        titulo_short = n["titulo"][:90] + "..." if len(n["titulo"]) > 90 else n["titulo"]

        st.markdown(
            f'<div style="background:{s_bg};border:1px solid {s_bor};border-left:3px solid {s_color};'
            f'border-radius:8px;padding:8px 12px;margin-bottom:6px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">'
            f'<span style="background:{BG_HEAD};color:{t_color};border:1px solid {BOR};'
            f'border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700">{n["tipo"]}</span>'
            f'<span style="font-size:10px;color:{TXT_SOFT}">{dias_str}  - {n["fuente"]}</span>'
            f'<span style="color:{s_color};font-size:10px;font-weight:700">{imp_txt}</span>'
            f'</div>'
            f'<a href="{n["link"]}" target="_blank" style="color:{TXT};font-size:11px;'
            f'text-decoration:none;line-height:1.4">{titulo_short}</a>'
            f'</div>',
            unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
#  SWING ACTIVO - detecta acciones que giraron alcista 2-3 días
#  Patrón: estaban cayendo -> llevan 2-3 días subiendo con vol
#  Filtros: precio subiendo 3 días + volumen creciente + RSI girando
# ─────────────────────────────────────────────────────────────
# ══ FILTRO SPY DÍA ANTERIOR v14 ════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def get_spy_filtro() -> dict:
    """
    Retorna si el mercado está en modo positivo para habilitar señales M2.
    Regla: SPY cierre ayer > SPY cierre anteayer -> mercado_positivo = True
    Si mercado_positivo = False -> NO mostrar señales M2 (evita entrar en días rojos)
    """
    try:
        import yfinance as yf
        spy = yf.Ticker("SPY").history(period="5d")
        if spy.empty or len(spy) < 2:
            return {"mercado_positivo": True, "spy_ayer": 0.0,
                    "spy_antes": 0.0, "cambio_pct": 0.0, "fuente": "sin_datos"}
        close = spy["Close"].values
        spy_ayer   = float(close[-1])
        spy_antes  = float(close[-2])
        cambio_pct = round((spy_ayer - spy_antes) / spy_antes * 100, 2)
        # v18 fix: umbral -0.5% en lugar de 0%
        # Un -0.31% es ruido normal — no debe bloquear señales
        # El filtro original era demasiado sensible: -0.01% bloqueaba igual que -2%
        # Nuevo criterio:
        #   > -0.5%  → mercado OK (ruido normal, no bloquear)
        #   -0.5% a -1.5% → advertencia + bloqueo parcial (solo M3 pasa)
        #   < -1.5%  → bloqueo total (día realmente negativo como 21-25 Abr)
        if cambio_pct >= -0.5:
            mercado_positivo = True   # ruido normal — no bloquear
            nivel = "ok"
        elif cambio_pct >= -1.5:
            mercado_positivo = False  # debilidad moderada — bloquear M2
            nivel = "moderado"
        else:
            mercado_positivo = False  # día negativo real — bloqueo total
            nivel = "negativo"
        # v19: calcular RSI de SPY y contexto alcista
        import pandas as _pd_spy
        s = _pd_spy.Series(close)
        delta = s.diff()
        gain  = delta.clip(lower=0).rolling(min(14,len(close))).mean()
        loss  = (-delta.clip(upper=0)).rolling(min(14,len(close))).mean()
        spy_rsi = round(float(100 - 100/(1 + gain.iloc[-1]/(loss.iloc[-1]+1e-9))), 1)

        # v19: DD mínimo adaptativo según fase del mercado
        # SPY RSI > 60 → mercado alcista → correciones van -10-15%, no -20%
        # SPY RSI 45-60 → mercado neutro → umbral normal -15 a -20%
        # SPY RSI < 45 → mercado débil → umbral -20% correcto
        if spy_rsi > 60:
            dd_min_adaptativo = -12.0   # alcista: correcciones más leves
        elif spy_rsi >= 45:
            dd_min_adaptativo = -15.0   # neutro: umbral intermedio
        else:
            dd_min_adaptativo = -20.0   # bajista: umbral original

        # v19 Prioridad 1: bloqueo cuando mercado sobrecomprado
        # SPY RSI > 68 → máximos históricos → NO generar señales ENTRAR
        mercado_sobrecomprado = spy_rsi > 68

        return {
            "mercado_positivo":      mercado_positivo,
            "mercado_sobrecomprado": mercado_sobrecomprado,
            "spy_ayer":              round(spy_ayer, 2),
            "spy_antes":             round(spy_antes, 2),
            "cambio_pct":            cambio_pct,
            "nivel":                 nivel,
            "spy_rsi":               spy_rsi,
            "dd_min_adaptativo":     dd_min_adaptativo,
            "fuente":                "yfinance"
        }
    except Exception:
        return {"mercado_positivo": True, "mercado_sobrecomprado": False,
                "spy_ayer": 0.0, "spy_antes": 0.0, "cambio_pct": 0.0,
                "spy_rsi": 55.0, "dd_min_adaptativo": -15.0,
                "fuente": "error"}


@st.cache_data(ttl=1800, show_spinner=False)
def scan_swing(vol_min_k: float = 200, max_results: int = 100, universo: list = None) -> pd.DataFrame:
    """
    Detecta acciones en rebote de swing 5-10 días.
    Criterios:
    - Venían en corrección (DD > -8% desde pico)
    - Llevan 2-3 días consecutivos subiendo
    - Volumen creciente en los días alcistas
    - RSI girando hacia arriba desde zona baja-media
    - No en sobrecompra (RSI < 65)
    """
    candidatos = []
    try:
        import yfinance as yf
        _universo_sw = universo if universo else SCAN_UNIVERSE
        for tk in _universo_sw:
            # v19: usar lista maestra de ETFs en lugar de set manual
            if _es_etf(tk):
                continue
            try:
                try:
                    hist = yf.Ticker(tk).history(period="3mo")
                except Exception:
                    continue
                if hist.empty or len(hist) < 20:
                    continue

                close = hist["Close"].values
                vol   = hist["Volume"].values

                # Necesitamos últimos 5 días
                if len(close) < 5:
                    continue

                precio   = float(close[-1])
                pico     = float(close.max())
                dd       = round((precio - pico) / pico * 100, 1)

                # v18 mejora: DD mínimo -20% (dato semana 27abr-08may)
                # DD -5% a -20% tiene WR 33-40% — ruido, no rebote real
                # v19: DD mínimo ADAPTATIVO según contexto SPY
                # SPY alcista (RSI>60): -12% (institucionales entran antes)
                # SPY neutro  (RSI 45-60): -15% umbral intermedio
                # SPY bajista (RSI<45): -20% umbral original
                _spy_dd = get_spy_filtro()
                _dd_min_ctx = _spy_dd.get("dd_min_adaptativo", -15.0)
                _spy_sobrecomprado = _spy_dd.get("mercado_sobrecomprado", False)
                if dd > _dd_min_ctx:
                    continue

                # Detectar días consecutivos alcistas (últimos 3)
                dias_alcistas = 0
                for i in range(1, 4):
                    if close[-i] > close[-i-1]:
                        dias_alcistas += 1
                    else:
                        break

                if dias_alcistas < 3:
                    continue  # v14: necesita mínimo 3 días alcistas (antes 2 -> bull trap)

                # Calcular variables necesarias para Prob NBIS antes de usarlas
                avg_v_pre = float(import_np().mean(vol[-20:])) if len(vol) >= 20 else float(vol[-1])
                vol_hoy_pre = float(vol[-1])
                vol_ratio_pre = int(vol_hoy_pre / avg_v_pre * 100) if avg_v_pre > 0 else 100

                import pandas as _pd_sw
                s_pre = _pd_sw.Series(close)
                delta_pre = s_pre.diff()
                gain_pre = delta_pre.clip(lower=0).rolling(14).mean()
                loss_pre = (-delta_pre.clip(upper=0)).rolling(14).mean()
                rsi_pre = round(float(100-100/(1+gain_pre.iloc[-1]/(loss_pre.iloc[-1]+1e-9))), 1)
                # v19.1: Divergencia alcista RSI vs Precio
                _div_sw = calcular_divergencia_rsi(close, periodos=14, ventana=20)
                mom_pre = round((close[-1]/close[-4]-1)*100, 2) if len(close)>=4 else 0

                # v12: Prob NBIS obligatorio en Swing
                _prob_sw = calcular_prob_nbis(
                    rsi=rsi_pre, vol_ratio=vol_ratio_pre, dd=dd,
                    dias_alcistas=dias_alcistas,
                    momentum_3d=mom_pre, tiene_catalizador=False
                )
                if _prob_sw < 25:  # mínimo 25% para aparecer en Swing
                    continue

                # v18 mejora: Score máximo 55
                # Score > 55 = acción ya se movió, llegaste tarde (WR 25% vs 70% en 40-55)
                # Se calcula aquí usando _prob_sw como proxy del score
                # El score real se calcula más abajo — aplicar filtro allí también

                # Volumen creciente en días alcistas
                avg_v = float(import_np().mean(vol[-20:]))
                vol_k = avg_v / 1000
                if vol_k < vol_min_k:
                    continue

                # Volumen de hoy vs promedio
                vol_hoy = float(vol[-1])
                vol_ratio = int(vol_hoy / avg_v * 100)

                # RSI actual y tendencia
                import pandas as pd
                s = pd.Series(close)
                delta = s.diff()
                gain  = delta.clip(lower=0).rolling(14).mean()
                loss  = (-delta.clip(upper=0)).rolling(14).mean()
                rsi   = round(float(100-100/(1+gain.iloc[-1]/(loss.iloc[-1]+1e-9))), 1)

                # v18 mejora: RSI zona válida 48-65
                # RSI < 48: acción aún débil, rebote no confirmado (WR cae a 33%)
                # RSI > 65: sobrecomprada, llegaste tarde
                # Zona óptima 48-65: WR 91% (semana 27abr-08may)
                if rsi > 65 or rsi < 48:
                    continue

                # RSI debe estar girando (hoy > hace 3 días)
                rsi_3d = float(100-100/(1+gain.iloc[-4]/(loss.iloc[-4]+1e-9))) if len(close)>=4 else rsi
                rsi_tend = rsi - rsi_3d
                if rsi_tend < 1:  # RSI debe estar subiendo
                    continue

                # Momentum: ganancia en últimos 3 días
                momentum_3d = round((close[-1] / close[-4] - 1) * 100, 2) if len(close)>=4 else 0
                if momentum_3d <= 0:
                    continue

                # Ganancia de hoy
                gain_hoy = round((close[-1] / close[-2] - 1) * 100, 2)

                # Fundamentales básicos
                info    = yf.Ticker(tk).info or {}
                beta_v  = float(info.get("beta", 1.5) or 1.5)
                nombre  = info.get("shortName", tk)
                sector  = info.get("sector", "-")
                ingresos= float(info.get("totalRevenue", 0) or 0) / 1e6

                sector_map = {
                    "Technology":"Tech","Healthcare":"Salud",
                    "Financial Services":"Finanzas",
                    "Consumer Cyclical":"Consumo",
                    "Consumer Defensive":"Consumo",
                    "Energy":"Energía","Industrials":"Industrial",
                    "Communication Services":"Tech",
                }
                area = sector_map.get(sector, sector[:10] if sector and sector!="-" else "-")

                # Stop para swing: -5% desde precio actual
                stop_swing = round(precio * 0.95, 2)
                # Target: +8-12% en 5-10 días
                target1 = round(precio * 1.08, 2)
                target2 = round(precio * 1.12, 2)

                lectura = (f"↑{dias_alcistas} días alcistas consecutivos  - "
                          f"Momentum +{momentum_3d:.1f}% (3d)  - "
                          f"RSI {rsi:.0f} girando ↑  - "
                          f"DD {dd:.0f}% desde pico")

                # v17 Fix AMD-F5: detectar patrón recuperación rápida
                _rapid_sw = detectar_recuperacion_rapida(
                    tk, rsi, dd,
                    macd_val if "macd_val" in dir() else 0.0,
                    close
                )
                if _rapid_sw["es_rapida"]:
                    lectura += f" · {_rapid_sw['badge']}: {_rapid_sw['accion']}"

                candidatos.append({
                    "Ticker": tk, "Nombre": nombre, "Area": area,
                    "Precio": round(precio, 2),
                    "RSI": rsi, "RSI_Tend": round(rsi_tend, 1),
                    "Volumen": vol_ratio, "DD_pico": dd,
                    "Beta": round(beta_v, 2),
                    "Dias_Alcistas": dias_alcistas,
                    "Momentum_3d": momentum_3d,
                    "Gain_Hoy": gain_hoy,
                    "Stop_Swing": stop_swing,
                    "Target_1": target1,
                    "Target_2": target2,
                    "Ingresos_M": round(ingresos, 0),
                    "Vol_Diario_K": round(vol_k, 0),
                    "Lectura": lectura,
                    "_source": "screener",
                    # v19: Prob_NBIS para registro en Sheets
                    "Prob_NBIS": calcular_prob_nbis(
                        rsi=rsi, vol_ratio=vol_ratio, dd=dd,
                        dias_alcistas=dias_alcistas, momentum_3d=momentum_3d,
                        tiene_catalizador=False),
                    # v19: Pre y Post Market
                    "Pre_Move": round(gain_hoy, 1) if gain_hoy else 0,
                    "Post_Move": 0,  # Post-market se calcula aparte si disponible
                    # Score Rebote v11 para Swing
                    "Score_Rebote": calcular_score_rebote(
                        dd=dd, rsi=rsi, vol_ratio=vol_ratio,
                        dias_alcistas=dias_alcistas, momentum_3d=momentum_3d,
                        tiene_catalizador=False, dias_para_cat=999,
                        beta=beta_v
                    )["score"],
                    "Nivel_Rebote": calcular_score_rebote(
                        dd=dd, rsi=rsi, vol_ratio=vol_ratio,
                        dias_alcistas=dias_alcistas, momentum_3d=momentum_3d,
                        tiene_catalizador=False, dias_para_cat=999,
                        beta=beta_v
                    )["nivel"],
                    "Detalle_Rebote": calcular_score_rebote(
                        dd=dd, rsi=rsi, vol_ratio=vol_ratio,
                        dias_alcistas=dias_alcistas, momentum_3d=momentum_3d,
                        tiene_catalizador=False, dias_para_cat=999,
                        beta=beta_v
                    )["detalle"],
                })
            except Exception:
                continue
    except Exception:
        pass

    # ── FILTRO 1 v14: SPY día anterior ─────────────────────────
    # Si el mercado cayó ayer -> no mostrar señales M2 (evita bull traps)
    spy_info = get_spy_filtro()
    if not spy_info["mercado_positivo"]:
        df_warn = pd.DataFrame()
        df_warn.attrs["spy_filtro_activo"] = True
        df_warn.attrs["spy_cambio_pct"]    = spy_info["cambio_pct"]
        df_warn.attrs["spy_ayer"]          = spy_info["spy_ayer"]
        return df_warn

    # ── FILTRO 3 v14: Máximo 8 señales simultáneas ─────────────
    # Si hay > 8 candidatos -> probable rebote falso del mercado
    # Mostrar solo las 5 mejores por Score_Rebote
    LIMITE_M2 = 8
    MAX_MOSTRAR = 5
    filtro_limite_activo = len(candidatos) > LIMITE_M2
    if filtro_limite_activo:
        candidatos = sorted(candidatos,
                            key=lambda x: float(x.get("Score_Rebote", 0)),
                            reverse=True)[:MAX_MOSTRAR]

    # Ordenar por momentum 3d descendente
    if not candidatos:
        return pd.DataFrame()
    try:
        sorted_c = sorted(candidatos, key=lambda x: float(x.get("Momentum_3d", 0)))[::-1][:max_results]
        df_sw = pd.DataFrame(sorted_c)
        # Asegurar columnas mínimas
        for col, default in [
            ("Prob_NBIS", 0.0), ("Sim_NBIS", 0.0),
            ("Score_Rebote", 0), ("Nivel_Rebote", "-"),
            ("Detalle_Rebote", "-"), ("Etapa_v12", "-"),
            ("Decision", "SEGUIR"), ("Fase", "M2"),
            ("Score", 0), ("Cat_Fecha", "-"),
            ("Cat_Desc", "-"), ("Cat_Tipo", "-"),
            ("Motivo", "-"), ("Lectura", "-"),
            ("Arrastradas", "-"), ("Lider", "-"),
            ("Color", "#64748B"), ("Bg", "#F8FAFC"),
        ]:
            if col not in df_sw.columns:
                df_sw[col] = default
        # Guardar metadatos de filtros v14 en attrs
        df_sw.attrs["filtro_limite_activo"] = filtro_limite_activo
        df_sw.attrs["spy_cambio_pct"] = spy_info.get("cambio_pct", 0.0)
        return df_sw
    except Exception:
        return pd.DataFrame()

def import_np():
    import numpy as np
    return np


with st.sidebar:
    st.markdown(f'<div style="font-size:22px;font-weight:800;color:{B}">🦅 GrekoTrader</div>'
            f'<div style="font-size:10px;color:{TXT_MUT};margin-top:2px">'
            f'v19  - Mayo 2026  - ATR Sizing + Backtesting Real + Dashboard Rendimiento  - '
            f'{len(SCAN_UNIVERSE)} tickers</div>'+
            f'</div>',unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:11px;color:{TXT_MUT};margin-bottom:6px">{datetime.date.today():%d %b %Y}  - Modelo 3 Momentos</div>',unsafe_allow_html=True)

    # ── Parámetros del modelo v18 (semana 27abr-08may) ─────────
    # v19: construir cartera global para cruzar con scans
    if "construir_cartera_global" in dir():
        try:
            construir_cartera_global()
        except Exception:
            pass

    # v19: mostrar alerta SPY en sidebar si sobrecomprado
    _spy_sb = st.session_state.get("_cartera_global_cache", {})  # reutilizar cache
    _spy_sb_info = get_spy_filtro()
    if _spy_sb_info.get("mercado_sobrecomprado", False):
        st.sidebar.markdown(
            f'<div style="background:#FEF2F2;border:1px solid #FCA5A5;'
            f'border-radius:8px;padding:6px 10px;margin-bottom:8px;font-size:10px">'
            f'🚨 <strong style="color:#DC2626">SPY RSI {_spy_sb_info.get("spy_rsi",0):.0f}</strong> — '
            f'Mercado sobrecomprado · Señales degradadas</div>',
            unsafe_allow_html=True)

    with st.expander("📊 Umbrales activos del modelo", expanded=False):
        # Debug Prob_NBIS si hay error
        _pd = st.session_state.get("_prob_debug","")
        if _pd:
            st.markdown(f"⚠️ **Debug Prob_NBIS:** `{_pd}`")
        st.markdown("""
**Basados en análisis semana 27 Abr — 08 May:**

| Variable | Umbral | WR sin filtro | WR con filtro |
|----------|--------|--------------|--------------|
| M1 Detectadas | Solo radar ❌ entrada | 0% | — |
| DD mínimo | -20% | 33% | 65%+ |
| RSI entrada | 48-65 | 48% | 91% |
| Score | 40-55 | 48% | 70% |
| Ventana salida | Día 7-9 | — | alerta |

**Combo óptimo esta semana:**
DD≤-20% + RSI 48-65 + Score 40-55 + Sector AI/Tech
→ **WR 100%, avg +12.2%** (n=6)
""")

    # ── Estado Google Sheets v18 ─────────────────────────────
    _gs_configured = (hasattr(st, "secrets") and
                      "gcp_service_account" in st.secrets and
                      "sheets" in st.secrets)
    if _gs_configured:
        st.markdown(
            f'<div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;'
            f'padding:6px 10px;margin-bottom:6px;font-size:10px;color:#16A34A;font-weight:700">'
            f'🗄️ Google Sheets conectado — datos persisten</div>',
            unsafe_allow_html=True)
    else:
        with st.expander("⚙️ Configurar Google Sheets", expanded=False):
            st.markdown("""
**Para que ventas y registros persistan:**

**Paso 1** — Crear Google Sheet:
`GrekoTrader_Posiciones_Mauri`

**Paso 2** — Compartir con:
`grekotrader-sheets@<proyecto>.iam.gserviceaccount.com`

**Paso 3** — En Streamlit Secrets:
```toml
[gcp_service_account]
type = "service_account"
project_id = "grekotrader"
private_key = "-----BEGIN..."
client_email = "..."

[sheets]
posiciones_mauri_id = "ID_del_sheet"
posiciones_amparito_id = "ID_del_sheet"
senales_modelo_id = "ID_del_sheet"
trades_reales_id = "ID_del_sheet"
```

📄 Ver guía completa adjunta
""")

    # Badge indicadores live
    if _n_live > 0:
        hora = datetime.datetime.now().strftime("%H:%M")
        st.markdown(
            f'<div style="background:{G_BG};border:1px solid {G_BOR};border-radius:8px;'
            f'padding:5px 10px;font-size:11px;color:{G};font-weight:600;margin-bottom:8px">'
            f'● Indicadores live  - {_n_live} tickers  - {hora}  - cache 20min</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="background:{A_BG};border:1px solid {A_BOR};border-radius:8px;'
            f'padding:5px 10px;font-size:11px;color:{A};font-weight:600;margin-bottom:8px">'
            f'⚠ Datos estáticos  - pip install yfinance</div>',
            unsafe_allow_html=True)
    st.markdown("---")
    area_fil  = st.selectbox("Área",["Todas","AI Infra","Tech","Salud","Finanzas","Consumo","Energía","Industrial","Cripto/AI","Quantum"])
    st.markdown("---")
    max_res = st.slider("📊 Máx. resultados por tab", min_value=10, max_value=200, value=100, step=10,
                        help="Cuántas acciones mostrar por tab. Más = escaneo más lento.")
    st.markdown("---")
    # Refresh market data
    if st.button("🔄 Actualizar indicadores de mercado", use_container_width=True):
        st.session_state["mkt_cache"] = {}
        st.rerun()
    if st.button("🗑️ Limpiar cache de precios", use_container_width=True,
                  help="Fuerza descarga de precios frescos — los tabs tardarán 1-2 min en recargar"):
        st.cache_data.clear()
        for key in ["scan_swing","scan_entrar","scan_detectadas","scan_sympathy",
                    "mkt_cache","etf_data","earnings_mis_pos","earnings_amparito"]:
            if key in st.session_state:
                del st.session_state[key]
        st.warning("⚠️ Cache limpiado — los tabs Swing y Entrar Hoy tardarán 1-2 min en recargar. Es normal.")
        st.success("✅ Cache limpiado - datos frescos al escanear")
        st.rerun()
    st.markdown("---")
    # Guía rápida de fases
    st.markdown(f'<div style="font-size:11px;font-weight:700;color:{TXT};margin-bottom:8px">📋 Guía de fases</div>',unsafe_allow_html=True)
    for emoji, label, desc, color in [
        ("📡","M1 Detectada","Cayendo  - Solo observar",TXT_SOFT),
        ("⚡","Swing Activo","Rebotando  - Entrar 5-10d",C),
        ("🔥","M3 Entrar hoy","Confirmado  - Ejecutar",G),
    ]:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;border-bottom:1px solid {BOR}">'
            f'<span style="font-size:14px">{emoji}</span>'
            f'<div><div style="font-size:11px;font-weight:600;color:{color}">{label}</div>'
            f'<div style="font-size:10px;color:{TXT_SOFT}">{desc}</div></div>'
            f'</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f'<div style="font-size:12px;font-weight:700;color:{TXT};margin-bottom:8px">📰 Noticias automáticas</div>', unsafe_allow_html=True)

    if st.button("🔄 Actualizar noticias", use_container_width=True, help="Descarga y analiza las últimas noticias de cada ticker via yfinance"):
        _all_scanned = []

        # Scans (Swing, Entrar Hoy, Detectadas)
        for _k in ["scan_entrar","scan_swing","scan_momentum"]:
            _d = st.session_state.get(_k)
            if _d is not None and not _d.empty:
                _all_scanned.extend(_d["Ticker"].tolist())

        # v19 FIX: también incluir tickers del Watchlist
        try:
            _wl = st.session_state.get("wl_res_df")
            if _wl is not None and not _wl.empty and "Ticker" in _wl.columns:
                _all_scanned.extend(_wl["Ticker"].tolist())
        except Exception:
            pass

        # v19 FIX: tickers de Posiciones Greko
        try:
            _pg = leer_posiciones_sheets(_SHEET_NAME_GREKO)
            if _pg is not None and not _pg.empty and "Ticker" in _pg.columns:
                _activas = _pg[_pg.get("Fecha_Salida", pd.Series(["-"]*len(_pg))).astype(str).isin(["-","","nan","NaT","None"])]
                _all_scanned.extend(_activas["Ticker"].tolist())
        except Exception:
            pass

        # v19 FIX: tickers de Posiciones MVALLE
        try:
            _pm = leer_posiciones_sheets(_SHEET_NAME_MAURI)
            if _pm is not None and not _pm.empty and "Ticker" in _pm.columns:
                _activas = _pm[_pm.get("Fecha_Salida", pd.Series(["-"]*len(_pm))).astype(str).isin(["-","","nan","NaT","None"])]
                _all_scanned.extend(_activas["Ticker"].tolist())
        except Exception:
            pass

        # v19 FIX: tickers de Posiciones Amparito
        try:
            _pa = leer_posiciones_sheets(_SHEET_NAME_AMPARITO)
            if _pa is not None and not _pa.empty and "Ticker" in _pa.columns:
                _activas = _pa[_pa.get("Fecha_Salida", pd.Series(["-"]*len(_pa))).astype(str).isin(["-","","nan","NaT","None"])]
                _all_scanned.extend(_activas["Ticker"].tolist())
        except Exception:
            pass

        # v19 FIX: tickers del Sympathy Sheet activos
        try:
            _symp_all = st.session_state.get("sympathy_data", {})
            for _stk, _sv in _symp_all.items():
                _all_scanned.append(_stk)
                _lider = _sv.get("lider","")
                if _lider and _lider not in ("-","","nan"):
                    _all_scanned.append(_lider)
        except Exception:
            pass

        # Deduplicar y limpiar
        tickers_universo = list(dict.fromkeys(
            [str(t).upper().strip() for t in _all_scanned
             if t and str(t).upper().strip() not in ("-","","NAN")]
        ))

        if not tickers_universo:
            tickers_universo = ["MSFT","NVDA","AAPL","ENPH","IONQ"]

        st.info(f"Cargando noticias para {len(tickers_universo)} tickers...")
        progress    = st.progress(0)
        status_txt  = st.empty()
        cache_nuevo = {}

        # Limitar a 40 tickers máximo para evitar timeouts
        _MAX_TICKERS = 40
        if len(tickers_universo) > _MAX_TICKERS:
            # Priorizar posiciones abiertas sobre watchlist
            tickers_universo = tickers_universo[:_MAX_TICKERS]

        _total = len(tickers_universo)
        _ok = 0; _err = 0

        for i, tk in enumerate(tickers_universo):
            status_txt.markdown(
                f'<div style="font-size:10px;color:#64748B">'
                f'⏳ {i+1}/{_total} — {tk}</div>',
                unsafe_allow_html=True)
            try:
                import signal as _sig
                # Timeout de 5s por ticker en sistemas Unix
                def _timeout_handler(signum, frame):
                    raise TimeoutError()
                try:
                    _sig.signal(_sig.SIGALRM, _timeout_handler)
                    _sig.alarm(5)
                    news  = fetch_noticias_ticker(tk)
                    _sig.alarm(0)
                except Exception:
                    news = []
            except Exception:
                # Windows no tiene SIGALRM — usar try/except directo
                try:
                    news = fetch_noticias_ticker(tk)
                except Exception:
                    news = []
            bonus = calcular_bonus_noticias(news)
            cache_nuevo[tk] = {"noticias": news, "bonus": bonus}
            if news: _ok += 1
            else:    _err += 1
            progress.progress((i+1)/_total)

        st.session_state["noticias_cache"] = cache_nuevo
        st.session_state["noticias_actualizadas"] = datetime.datetime.now().strftime("%H:%M")
        progress.empty()
        status_txt.empty()
        st.success(f"✅ Noticias actualizadas · {_ok} tickers con noticias · {_err} sin datos")

    if st.session_state["noticias_actualizadas"]:
        st.markdown(
            f'<div style="font-size:10px;color:{G}">● Última actualización: {st.session_state["noticias_actualizadas"]}</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size:10px;color:{TXT_SOFT}">Sin actualizar - presiona el botón</div>', unsafe_allow_html=True)

    st.markdown("---")
    resumen = [
        ("ENTRAR",  "🔥", G,  _count("scan_entrar")),
        ("ANTICIPAR","⚡", C,  _count("scan_anticipar")),
        ("RADAR F2", "👀", A,  _count("scan_radar")),
        ("MOMENTUM","⚡", "#D97706", _count_list("scan_momentum")),
    ]
    for dec,emoji,c,cnt in resumen:
        st.markdown(f'<div style="display:flex;justify-content:space-between;padding:5px 0;font-size:12px;color:{TXT_MUT};border-bottom:1px solid {BOR}"><span>{emoji} {dec}</span><span style="color:{c};font-weight:700">{cnt}</span></div>',unsafe_allow_html=True)

# Filtros
# v8: df se construye en cada tab al escanear
df = pd.DataFrame()

# v15 fix: Arrastradas y Lider ahora visibles en todas las tablas
COLS_MAIN=["Ticker","Score_Rebote","Nivel_Rebote","Etapa_v12","Area","Precio","RSI","DD_pico","Pre_Move","Post_Move","Cat_Fecha","Prob_NBIS","Opinion_Trader","Lectura"]
COLS_EXT =["Ticker","Score_Rebote","Nivel_Rebote","Etapa_v12","Area","Decision","Precio","Score","RSI","DD_pico","Cat_Fecha","Prob_NBIS","Detalle_Rebote","Opinion_Trader","Lectura"]


# ─────────────────────────────────────────────────────────────
#  NOTICIAS AUTOMÁTICAS - yfinance + análisis de sentimiento
# ─────────────────────────────────────────────────────────────

# Keywords para análisis de sentimiento

def render_scan_tab(tab_key, titulo, emoji, color, color_bg, color_bor,
                    desc, rsi_max, dd_min, score_min, decisions,
                    cols_show=None, default_sort="Score", prob_nbis_min=0.0):
    """Renderiza un tab con botón de escaneo y resultados."""
    if cols_show is None:
        cols_show = COLS_MAIN

    st.markdown(
        f'<div class="sec-header" style="background:{color_bg};border-color:{color_bor}">'+
        f'<span style="font-size:20px">{emoji}</span>'+
        f'<div><span style="font-size:16px;font-weight:700;color:{color}">{titulo}</span>'+
        f'<span style="font-size:12px;color:{TXT_MUT};margin-left:10px">{desc}</span></div>'+
        f'</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:10px;'+
        f'padding:12px 16px;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center">'+
        f'<div style="font-size:11px;color:{TXT_MUT}">'+
        f'<strong>Filtros automáticos:</strong> RSI <= {rsi_max}  - DD <= {dd_min}%  - Score >= {score_min}  - Vol >= 200K/día'+
        f'</div></div>', unsafe_allow_html=True)

    col_btn, col_info = st.columns([2, 3])
    with col_btn:
        if st.button(f"🔍 Escanear {titulo}", use_container_width=True, key=f"btn_{tab_key}"):
            with st.spinner(f"Escaneando ~{len(SCAN_UNIVERSE)} tickers..."):
                resultado = scan_tab(rsi_max, dd_min, score_min, decisions, universo=SCAN_UNIVERSE[:st.session_state.get("universo_size", len(SCAN_UNIVERSE))], prob_nbis_min=prob_nbis_min)
                st.session_state[tab_key] = resultado
    with col_info:
        if st.session_state.get(tab_key) is not None:
            n = len(st.session_state[tab_key])
            ts = st.session_state.get(f"{tab_key}_ts", "")
            st.markdown(
                f'<div style="font-size:11px;color:{G if n>0 else TXT_MUT};padding-top:8px">'+
                f'● {n} candidatos encontrados {ts}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="font-size:11px;color:{TXT_SOFT};padding-top:8px">'+
                f'Presiona el botón para escanear el mercado ahora</div>', unsafe_allow_html=True)

    resultado_df = st.session_state.get(tab_key)
    if resultado_df is None:
        st.markdown(
            f'<div style="background:{color_bg};border:1px solid {color_bor};border-radius:12px;'+
            f'padding:32px;text-align:center">'+
            f'<div style="font-size:36px;margin-bottom:10px">{emoji}</div>'+
            f'<div style="font-size:14px;font-weight:700;color:{color};margin-bottom:6px">{titulo} - Sin escanear</div>'+
            f'<div style="font-size:12px;color:{TXT_MUT}">Presiona el botón para buscar oportunidades en tiempo real</div>'+
            f'</div>', unsafe_allow_html=True)
        return

    # Aplicar filtro de área si está seleccionado
    if not resultado_df.empty and area_fil != "Todas":
        resultado_df = resultado_df[resultado_df["Area"]==area_fil]

    if resultado_df.empty:
        st.markdown(
            f'<div style="background:{A_BG};border:1px solid {A_BOR};border-radius:10px;'+
            f'padding:20px;text-align:center;color:{A}">'+
            f'🚀 Mercado en rally - ninguna acción cumple los filtros de {titulo} ahora.'+
            f'<br><span style="font-size:11px;color:{TXT_MUT}">'+
            f'Filtros activos: RSI <= {rsi_max}  - DD <= {dd_min}%  - Score >= {score_min}. '+
            f'Esto es información válida - el modelo dice que no hay oportunidades en este nivel hoy.</span></div>',
            unsafe_allow_html=True)
        return

    # ── Orden automático por tab + columna Señal ────────────
    df_show = resultado_df.copy()

    # Agregar columna "Señal" con interpretación correcta según tab
    def generar_senal(row):
        rsi  = float(row.get("RSI", 50))
        dd   = float(row.get("DD_pico", 0))
        vol  = float(row.get("Volumen", 100))
        dec  = str(row.get("Decision",""))

        # Detectadas M1 - solo estados de corrección
        if tab_key == "scan_detectadas":
            if dd < -30 and rsi < 40:
                return "🔴 Corrección profunda - watchlist prioritaria"
            elif dd < -15 and rsi < 50:
                return "👀 En corrección - vigilar"
            elif dd < -8:
                return "📡 Inicio corrección - agregar a watchlist"
            else:
                return "🔵 Corrección leve"

        # Entrar hoy - solo señales fuertes
        elif tab_key == "scan_entrar":
            if dec == "ENTRAR" or (rsi < 35 and dd < -15 and vol > 150):
                return "🔥 Entrar hoy - señal completa"
            elif dec == "ANTICIPAR":
                return "⚡ Anticipar - pre-señal"
            else:
                return "⚡ Candidata"

        # Otros tabs - señal general
        else:
            if dec == "ENTRAR" or (rsi < 35 and dd < -20 and vol > 150):
                return "🔥 Entrar hoy"
            elif dec == "ANTICIPAR" or (rsi < 45 and dd < -15 and vol > 100):
                return "⚡ Entrada válida"
            elif dd < -8 and rsi < 55:
                return "👀 En corrección - vigilar"
            elif rsi > 65:
                return "⛔ RSI alto - esperar"
            else:
                return "🔵 Neutral - observar"

    if not df_show.empty:
        df_show["Señal modelo"] = df_show.apply(generar_senal, axis=1)

    # Orden automático según tab (sin selector)
    if default_sort in df_show.columns:
        asc = (default_sort == "DD_pico")
        df_show = df_show.sort_values(default_sort, ascending=asc)

    # Mostrar columna Señal primero
    cols_con_senal = cols_show.copy() if cols_show else list(df_show.columns)
    if "Señal modelo" not in cols_con_senal:
        cols_con_senal = ["Ticker","Señal modelo"] + [c for c in cols_con_senal if c not in ("Ticker","Señal modelo")]

    # ── BOTONES DE REGISTRO v18 ─────────────────────────────────
    # v18 fix: M1 = solo radar. Botón Greko disponible pero con aviso claro
    if not df_show.empty:
        # Si es Tab M1 Detectadas, mostrar aviso de no entrada
        if tab_key == "scan_detectadas":
            st.markdown(
                f'<div style="background:#FEF3C7;border:1px solid #FCD34D;'
                f'border-radius:8px;padding:8px 14px;margin-bottom:6px;font-size:11px">'
                f'<strong>📡 M1 = Solo Radar</strong> — estas acciones están en corrección. '
                f'NO son señales de entrada. Agrégalas al radar para esperar M2/M3. '
                f'<strong>Win rate M1 como entrada esta semana: 0%</strong>'
                f'</div>', unsafe_allow_html=True)

        _reg_col1, _reg_col2, _reg_col3 = st.columns([2,2,2])
        with _reg_col1:
            _reg_tk = st.selectbox(
                "Seleccionar ticker",
                ["— seleccionar —"] + list(df_show["Ticker"].unique()),
                key=f"reg_sel_{tab_key}",
                label_visibility="collapsed",
            )
        with _reg_col2:
            _reg_cant = st.number_input(
                "Cantidad", min_value=0.0, value=0.0, step=1.0,
                key=f"reg_cant_{tab_key}", label_visibility="collapsed",
                help="Cantidad de acciones (0 = sin especificar)"
            )
        with _reg_col3:
            _reg_nota = st.text_input(
                "Nota", value="", key=f"reg_nota_{tab_key}",
                label_visibility="collapsed", placeholder="nota..."
            )

        if _reg_tk != "— seleccionar —":
            _rr       = df_show[df_show["Ticker"]==_reg_tk].iloc[0]
            _rr_tk    = _reg_tk
            _rr_precio= float(_rr.get("Precio",0))
            _rr_fase  = str(_rr.get("Etapa_v12",_rr.get("Fase","")))
            _rr_score = int(_rr.get("Score",_rr.get("Score_Rebote",0)))
            _rr_prob  = float(_rr.get("Prob_NBIS",0))
            _rr_arr   = str(_rr.get("Arrastradas","-"))
            _rr_op    = str(_rr.get("Opinion_Trader","-"))
            _rr_area  = str(_rr.get("Area","-"))

            # v19.2: verificar si ya está en Greko (evitar duplicados)
            # PERO permitir si la posición está vencida
            _wl_df_ck    = st.session_state.get("wl_res_df")
            _greko_df_ck = st.session_state.get("_greko_rows_cache", [])
            _ya_en_wl    = (_wl_df_ck is not None and not _wl_df_ck.empty and
                            _rr_tk in _wl_df_ck["Ticker"].str.upper().values)
            _ya_en_greko = any(str(r.get("Ticker","")).upper() == _rr_tk
                               for r in _greko_df_ck)

            # Verificar si la posición en Greko está vencida
            _vig_ck = st.session_state.get(
                f"_fase_live_{_SHEET_NAME_GREKO}_vigencias", {}).get(_rr_tk, {})
            _vencida_ck = _vig_ck.get("vencida", False)

            if _ya_en_wl or (_ya_en_greko and not _vencida_ck):
                _donde = "Watchlist" if _ya_en_wl else "Posiciones Greko"
                st.markdown(
                    f'<div style="background:#F0FDF4;border:1px solid #86EFAC;'
                    f'border-radius:8px;padding:6px 12px;font-size:11px;'
                    f'color:#16A34A;font-weight:600">'
                    f'✅ {_rr_tk} ya está en {_donde} — '
                    f'no es necesario agregar de nuevo</div>',
                    unsafe_allow_html=True)
            elif _ya_en_greko and _vencida_ck:
                # Posición vencida → permitir nueva entrada con advertencia
                st.markdown(
                    f'<div style="background:#FFFBEB;border:1px solid #FDE68A;'
                    f'border-radius:8px;padding:6px 12px;font-size:11px;'
                    f'color:#D97706;font-weight:600">'
                    f'⚠️ {_rr_tk} estuvo en Greko pero la señal venció — '
                    f'puedes registrar nueva entrada</div>',
                    unsafe_allow_html=True)
            else:
                # v19.2: Alerta de catalizador para NBIS puro (RSI < 55)
                _rsi_warn = float(_rr.get("RSI", 0) or 0)
                _prob_warn = float(_rr.get("Prob_NBIS", _rr.get("Prob_NBIS", 0)) or 0)
                _dd_warn   = float(_rr.get("DD", _rr.get("Dist_ATH_Pct", 0)) or 0)
                _dec_warn  = str(_rr.get("Decision", "")).upper()

                if _rsi_warn < 55 and _dec_warn not in ("ENTRAR","ANTICIPAR"):
                    # NBIS puro sin confirmación — datos: 32% WR, -5.3% prom
                    st.markdown(
                        f'<div style="background:#1F0A0A;border:1px solid #7F1D1D;'
                        f'border-left:3px solid #F43F5E;border-radius:6px;'
                        f'padding:6px 12px;font-size:10px;color:#FCA5A5;margin-bottom:6px">'
                        f'🚨 <strong>NBIS sin catalizador</strong> · RSI {_rsi_warn:.0f} &lt;55 sin Decision ENTRAR · '
                        f'Datos históricos: WR 32% · promedio −5.3% · '
                        f'Validar Revenue YoY y catalizador antes de registrar'
                        f'</div>', unsafe_allow_html=True)
                elif _rsi_warn < 65 and _rsi_warn > 0 and _dec_warn not in ("ENTRAR","ANTICIPAR"):
                    # NBIS transición — datos: 48% WR
                    st.markdown(
                        f'<div style="background:#1A1000;border:1px solid #78350F;'
                        f'border-left:3px solid #FBBF24;border-radius:6px;'
                        f'padding:6px 12px;font-size:10px;color:#FDE68A;margin-bottom:6px">'
                        f'⚠️ <strong>Zona de confirmación</strong> · RSI {_rsi_warn:.0f} · '
                        f'Datos históricos: WR 48% · Esperar MACD+ y Revenue para mayor convicción'
                        f'</div>', unsafe_allow_html=True)

                _bc1, _bc2 = st.columns(2)
                with _bc1:
                    _ok_g, _msg_g = False, ""
                    if st.button(f"🦅 Agregar a Posiciones Greko",
                                 key=f"btn_greko_{tab_key}_{_rr_tk}",
                                 use_container_width=True, type="primary",
                                 help="Paper trading — registra señal para validar el modelo"):
                        # v19.1: datos técnicos al momento de registrar
                        _rsi_sw   = float(_rr.get("RSI", 0) or 0)
                        _macd_sw  = "+" if float(_rr.get("MACD", 0) or 0) > 0 else "-"
                        _dd_sw    = float(_rr.get("DD", _rr.get("DD_Pico","0")) or 0)
                        _tipo_sw  = "NBIS"  # Swing siempre NBIS

                        _ok_g, _msg_g = escribir_greko_sheets(
                            ticker=_rr_tk, precio_compra=_rr_precio,
                            fase=str(_rr.get("Fase", _rr.get("Etapa_v12", _rr_fase))), score=_rr_score, prob_nbis=_rr_prob,
                            area=_rr_area, tipo="Accion",
                            fuente={"tab2":"Swing Activo","tab3":"Entrar Hoy","tab5":"Mi Watchlist"}.get(tab_key, tab_key),
                            arrastradas=_rr_arr, opinion=_rr_op,
                            cantidad=float(_reg_cant), notas=_reg_nota,
                            rsi_ticker=_rsi_sw,
                            rsi_accion=_rsi_sw, macd_estado=_macd_sw,
                            dd_pico_pct=_dd_sw, tipo_senal=_tipo_sw,
                        )
                    if _ok_g:
                        st.success(_msg_g)
                        st.session_state.pop("_cartera_global_cache", None)
                        st.session_state.pop("_cartera_global_ts", None)
                    elif _msg_g:
                        st.error(_msg_g)
                with _bc2:
                    render_boton_registro(
                        ticker=_rr_tk, fase=_rr_fase, precio=_rr_precio,
                        score=_rr_score, prob_nbis=_rr_prob,
                        cat_fecha=str(_rr.get("Cat_Fecha","-")),
                        arrastradas=_rr_arr, lider=str(_rr.get("Lider","-")),
                        opinion=_rr_op, key_prefix=tab_key, tipo="CANDIDATO",
                    )

    render_table(df_show, cols_con_senal, tab_key=tab_key)

    # ── v19: Panel de Pullback por acción ────────────────────────
    if not df_show.empty:
        st.markdown(
            f'<div style="font-size:12px;font-weight:700;color:{TXT};'
            f'margin:14px 0 8px">🔍 Análisis de Pullback por señal</div>',
            unsafe_allow_html=True)
        for _, _pr in df_show.iterrows():
            _pr_tk   = str(_pr.get("Ticker",""))
            _pr_dd   = float(str(_pr.get("DD_pico",0)).replace(",",".") or 0)
            _pr_rsi  = float(str(_pr.get("RSI",50)).replace(",",".") or 50)
            _pr_ema  = float(str(_pr.get("EMA50",0)).replace(",",".") or 0)
            _pr_dias = int(_pr.get("Dias_Alcistas", _pr.get("dias_alcistas", 0)) or 0)
            _pr_vol  = float(str(_pr.get("Volumen",100)).replace(",",".") or 100)
            _pb_html = render_pullback_badge(
                _pr_tk, _pr_dd, _pr_rsi, _pr_ema, _pr_dias, _pr_vol,
                G, R, A, C, TXT_MUT)
            if _pb_html:
                st.markdown(
                    f'<div style="font-size:11px;font-weight:700;color:{B};'
                    f'margin:8px 0 2px">{_pr_tk}</div>' + _pb_html,
                    unsafe_allow_html=True)

    # ── Mensaje contextual cuando no hay señales ─────────────────
    if df_show.empty:
        _spy_ctx_tab = get_spy_filtro()
        _rsi_tab = _spy_ctx_tab.get("spy_rsi", 55)
        _dd_tab  = _spy_ctx_tab.get("dd_min_adaptativo", -15)
        st.markdown(
            f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
            f'border-radius:10px;padding:16px 20px;margin-top:10px">'
            f'<div style="font-size:12px;font-weight:700;color:#374151;margin-bottom:6px">'
            f'⏳ Sin señales {titulo} ahora</div>'
            f'<div style="font-size:11px;color:#6B7280;line-height:1.8">'
            f'{"📈 Mercado alcista (SPY RSI " + str(int(_rsi_tab)) + ") — pocas correcciones disponibles." if _rsi_tab > 58 else "📊 Mercado neutral — esperando setup."}'
            f' DD mínimo activo: <strong>{_dd_tab:.0f}%</strong><br>'
            f'No forzar trades sin setup. Revisar <strong>Tab Watchlist</strong> para seguimiento.'
            f'</div></div>',
            unsafe_allow_html=True)
    # Muestra el mapa completo: qué arrastra a qué, para entrar escalonado
    if not df_show.empty and "Arrastradas" in df_show.columns:
        _has_arrastre = df_show[
            df_show["Arrastradas"].apply(lambda x: str(x) not in ("-","","nan"))
            | df_show["Lider"].apply(lambda x: str(x) not in ("-","","nan"))
        ]
        if not _has_arrastre.empty:
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#EFF6FF,#F0FDF4);'
                f'border:2px solid #BFDBFE;border-radius:14px;'
                f'padding:16px 20px;margin-top:12px">'
                f'<div style="font-size:13px;font-weight:800;color:#1D4ED8;margin-bottom:12px">'
                f'🚂 Trenes de Arrastre — Estrategia Escalonada</div>'
                f'<div style="font-size:11px;color:#374151;margin-bottom:10px">'
                f'Cuando un líder está en M3, sus arrastradas suelen seguir 3-7 días después. '
                f'Entra al líder primero, luego escala en las arrastradas.</div>',
                unsafe_allow_html=True)

            for _, _tr in _has_arrastre.iterrows():
                _tk_tr   = str(_tr["Ticker"])
                _arr_tr  = str(_tr.get("Arrastradas", "-"))
                _lid_tr  = str(_tr.get("Lider", "-"))
                _fase_tr = str(_tr.get("Etapa_v12", _tr.get("Fase", "")))
                _fase_color = "#16A34A" if "M3" in _fase_tr else "#D97706" if "M2" in _fase_tr else "#2563EB"

                _arr_chips = " ".join([
                    f'<span style="background:#0891B2;color:white;border-radius:6px;'
                    f'padding:3px 10px;font-weight:700;font-size:11px;margin:2px;display:inline-block">'
                    f'🔗 {a.strip()} →</span>'
                    for a in _arr_tr.split(",") if a.strip() and a.strip() != "-"
                ]) if _arr_tr not in ("-","","nan") else ""

                _lid_chip = (
                    f'<span style="background:#7C3AED;color:white;border-radius:6px;'
                    f'padding:3px 10px;font-weight:700;font-size:11px">🏆 {_lid_tr}</span>'
                    if _lid_tr not in ("-","","nan") else ""
                )

                if _arr_chips or _lid_chip:
                    st.markdown(
                        f'<div style="background:white;border:1px solid #BFDBFE;'
                        f'border-radius:10px;padding:10px 14px;margin-bottom:8px">'
                        f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
                        + (f'{_lid_chip} <span style="color:#9CA3AF;font-size:11px">arrastra a</span> ' if _lid_chip else "")
                        + f'<span style="background:{_fase_color};color:white;border-radius:6px;'
                        f'padding:3px 10px;font-weight:800;font-size:12px">{_tk_tr}</span>'
                        + (f' <span style="color:#9CA3AF;font-size:11px">arrastra a</span> {_arr_chips}' if _arr_chips else "")
                        + f'</div>'
                        f'<div style="font-size:10px;color:#6B7280;margin-top:5px">'
                        f'{_tk_tr} en {_fase_tr} · '
                        + (f'Arrastradas: {_arr_tr} — buscarlas en M1/M2 para entrada escalonada.' if _arr_chips else
                           f'Líder {_lid_tr} ya subió — {_tk_tr} puede seguir.')
                        + f'</div></div>',
                        unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    # Exportar señales del día
    boton_exportar(resultado_df, titulo, f"exp_{tab_key}")

    # Pre/Post Market por ticker
    if not resultado_df.empty:
        st.markdown(
            f'<div style="font-size:11px;font-weight:700;color:{TXT};margin:14px 0 6px">'+
            f'📡 Pre-Market  - Post-Market  - Volumen en tiempo real</div>',
            unsafe_allow_html=True)
        for _, r in resultado_df.iterrows():
            st.markdown(
                f'<div style="background:{BG_CARD};border:1px solid {BOR};border-radius:10px;'+
                f'padding:10px 14px;margin-bottom:6px">'+
                f'<div style="font-size:12px;font-weight:700;color:{B};margin-bottom:4px">'+
                f'{r["Ticker"]} - {r.get("Nombre","")[:30]}</div>'+
                render_pre_post_bar(r["Ticker"], r["Precio"], G, A, R, TXT_MUT, TXT_SOFT, BG_HEAD, BOR)+
                render_nbis_panel(r.get('Prob_NBIS',0), r.get('Sim_NBIS',0), G, A, R, C, TXT, TXT_MUT, TXT_SOFT, BG_HEAD, BOR)+
                f'</div>', unsafe_allow_html=True)




# ─────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:4px">'
    f'<span style="font-size:24px;font-weight:800;color:{TXT}">Panel de Monitoreo Diario</span>'
    f'<span style="background:{G_BG};color:{G};border:1px solid {G_BOR};border-radius:8px;padding:3px 12px;font-size:12px;font-weight:700">'
    f'{datetime.date.today():%A %d %b %Y}</span>'
    f'{"<span style=background:" + G_BG + ";color:" + G + ";border:1px solid " + G_BOR + ";border-radius:8px;padding:3px 10px;font-size:11px;font-weight:600>● Precios live</span>" if _n_live>0 else "<span style=background:" + A_BG + ";color:" + A + ";border:1px solid " + A_BOR + ";border-radius:8px;padding:3px 10px;font-size:11px>⚠ Precios estáticos</span>"}'
    f'</div>',unsafe_allow_html=True)
st.markdown(f'<div style="font-size:11px;color:{TXT_MUT};margin-bottom:10px">Modelo Rebote Técnico  - Patrón NBIS  - 3 Momentos  - Pre/Post Market  - {"RSI / MACD / EMA50 / Precio actualizados en tiempo real  - cache 20min" if _n_live>0 else "pip install yfinance para indicadores en tiempo real"}</div>',unsafe_allow_html=True)

# ── Banner Oil v18 - presión sectorial ────────────────────────
if oil.get("_ok") and oil.get("presion_sectorial"):
    # v18: mostrar solo el dato de precio + contexto, sin degradar tickers
    # Los tickers hardcodeados (TSLA, BA, NKE) no son relevantes para Oil
    st.markdown(
        f'<div style="background:#FEF9C3;border:1px solid #FCD34D;border-radius:10px;'
        f'padding:8px 16px;margin-bottom:8px;display:flex;align-items:center;gap:12px">'
        f'<span style="font-size:18px">🛢️</span>'
        f'<div><span style="font-size:12px;font-weight:700;color:#92400E">'
        f'WTI ${oil["precio"]:.1f} — Presión en sectores Oil/Energy</span><br>'
        f'<span style="font-size:11px;color:#78350F">'
        f'Evitar entradas en Oil, Gas y Energy mientras el precio siga débil. '
        f'Sectores Tech, AI y Biotech no están afectados.</span></div>'
        f'</div>', unsafe_allow_html=True)

# ── Estado del mercado (abierto/cerrado/pre/post) ─────────────
def get_market_status() -> dict:
    """
    Detecta si el mercado NYSE está abierto, cerrado, en pre o post market.
    Basado en hora de Nueva York (ET).
    """
    import datetime as _dt
    try:
        import pytz
        ny_tz = pytz.timezone("America/New_York")
        now_ny = _dt.datetime.now(ny_tz)
    except ImportError:
        # Sin pytz — usar UTC-5 como aproximación
        now_ny = _dt.datetime.utcnow() - _dt.timedelta(hours=5)

    hora    = now_ny.hour
    minuto  = now_ny.minute
    weekday = now_ny.weekday()  # 0=Lunes, 6=Domingo
    hora_decimal = hora + minuto/60

    # Fin de semana
    if weekday >= 5:
        return {
            "estado":  "cerrado",
            "label":   "🔴 Mercado Cerrado — Fin de semana",
            "detalle": f"Abre el lunes a las 9:30 AM ET",
            "color":   "#DC2626",
            "bg":      "#FEF2F2",
        }
    # Pre-market: 4:00 AM - 9:30 AM ET
    if 4.0 <= hora_decimal < 9.5:
        mins_para_open = int((9.5 - hora_decimal) * 60)
        return {
            "estado":  "pre_market",
            "label":   "🟡 Pre-Market",
            "detalle": f"Mercado abre en {mins_para_open} min (9:30 AM ET) — precios orientativos",
            "color":   "#D97706",
            "bg":      "#FFFBEB",
        }
    # Mercado abierto: 9:30 AM - 4:00 PM ET
    if 9.5 <= hora_decimal < 16.0:
        mins_para_close = int((16.0 - hora_decimal) * 60)
        return {
            "estado":  "abierto",
            "label":   "🟢 Mercado Abierto",
            "detalle": f"Cierra en {mins_para_close} min (4:00 PM ET)",
            "color":   "#16A34A",
            "bg":      "#F0FDF4",
        }
    # Post-market: 4:00 PM - 8:00 PM ET
    if 16.0 <= hora_decimal < 20.0:
        return {
            "estado":  "post_market",
            "label":   "🔵 Post-Market",
            "detalle": "Mercado cerrado — solo trading extendido hasta 8:00 PM ET",
            "color":   "#2563EB",
            "bg":      "#EFF6FF",
        }
    # Noche / madrugada
    return {
        "estado":  "cerrado",
        "label":   "🔴 Mercado Cerrado",
        "detalle": "Pre-market abre a las 4:00 AM ET",
        "color":   "#DC2626",
        "bg":      "#FEF2F2",
    }

_mkt_status = get_market_status()

# ── Banner de estado del mercado ───────────────────────────────
st.markdown(
    f'<div style="background:{_mkt_status["bg"]};border:1px solid {_mkt_status["color"]}40;'
    f'border-radius:8px;padding:6px 14px;margin-bottom:8px;'
    f'display:flex;align-items:center;gap:12px">'
    f'<span style="font-size:13px;font-weight:800;color:{_mkt_status["color"]}">'
    f'{_mkt_status["label"]}</span>'
    f'<span style="font-size:11px;color:#6B7280">{_mkt_status["detalle"]}</span>'
    + (f'<span style="font-size:10px;color:#9CA3AF;margin-left:auto">'
       f'Los precios y señales son orientativos fuera del horario de mercado</span>'
       if _mkt_status["estado"] != "abierto" else "")
    + f'</div>',
    unsafe_allow_html=True)

# ── Semáforo VIX ──────────────────────────────────────────────
if not vix["_ok"]:
    st.markdown(
        f'<div style="background:{BG_HEAD};border:1px solid {BOR};'
        f'border-radius:12px;padding:10px 18px;margin-bottom:12px">'
        f'<div style="display:flex;align-items:center;gap:16px">'
        f'<div>'
        f'  <span style="font-size:10px;color:{TXT_MUT};font-weight:600">VIX - Índice de Volatilidad</span><br>'
        f'  <span style="font-size:22px;font-weight:800;color:{TXT_MUT}">-</span>'
        f'  <span style="font-size:11px;color:{TXT_MUT};margin-left:8px">Sin datos  - Mercado cerrado</span>'
        f'</div></div></div>',
        unsafe_allow_html=True)
elif vix["_ok"]:
    cambio_sym = f'+{vix["cambio"]:.2f}' if vix["cambio"] >= 0 else f'{vix["cambio"]:.2f}'
    cambio_col = R if vix["cambio"] > 0 else G
    vix_v = vix["valor"]

    # Etapa VIX + ETF sugerido
    if vix_v >= 35:
        vix_etapa = "🔥 ENTRAR - Pánico máximo"
        vix_etf   = "ETF: SPY  - VOO  - QQQ"
        vix_accion= "Comprar índices ahora  - Máxima oportunidad histórica"
    elif vix_v >= 25:
        vix_etapa = "⚡ SWING - Miedo elevado"
        vix_etf   = "ETF: SPY  - IVV  - TQQQ"
        vix_accion= "Buscar swings en índices  - Oportunidad moderada"
    elif vix_v >= 18:
        vix_etapa = "📡 VIGILAR - Nerviosismo"
        vix_etf   = "ETF: SPY  - QQQ  - XLF"
        vix_accion= "Monitorear  - No entrar índices aún"
    elif vix_v >= 13:
        vix_etapa = "⚪ NORMAL - Mercado tranquilo"
        vix_etf   = "-"
        vix_accion= "Exigir Pre-Market confirmado antes de entrar"
    else:
        vix_etapa = "🔴 PRECAUCIÓN - Complacencia"
        vix_etf   = "Considerar UVXY  - VIXY (corto)"
        vix_accion= "Mercado muy tranquilo - corrección probable próxima"

    st.markdown(
        f'<div style="background:{vix["bg"]};border:1px solid {vix["bor"]};'
        f'border-radius:12px;padding:12px 18px;margin-bottom:12px">'
        f'<div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap">'
        f'<div>'
        f'  <span style="font-size:10px;color:{TXT_MUT};font-weight:600">VIX - Índice de Volatilidad</span><br>'
        f'  <span style="font-size:26px;font-weight:800;color:{vix["color"]}">{vix_v}</span>'
        f'  <span style="font-size:12px;color:{cambio_col};margin-left:6px">{cambio_sym}</span>'
        f'  <span style="background:{vix["bg"]};color:{vix["color"]};border:1px solid {vix["bor"]};'
        f'  border-radius:6px;padding:2px 10px;font-size:11px;font-weight:700;margin-left:8px">'
        f'  {vix["nivel"]}</span>'
        f'</div>'
        f'<div style="flex:1">'
        f'  <div style="font-size:12px;font-weight:700;color:{vix["color"]}">{vix_etapa}</div>'
        f'  <div style="font-size:11px;color:{TXT_MUT};margin-top:2px">{vix_accion}</div>'
        f'  <div style="font-size:10px;color:{TXT_SOFT};margin-top:4px">'
        f'  {"🎯 " + vix_etf if vix_etf != "-" else ""}</div>'
        f'</div>'
        f'{"<div style=font-size:11px;color:" + G + ";font-weight:600;white-space:nowrap>● Score x" + str(vix["mult"]) + " activo</div>" if vix["mult"] > 1.0 else ""}'
        f'</div></div>',
        unsafe_allow_html=True)

# ── Cargar indicadores de mercado (cache 15min - no bloquea) ──
if "mkt_cache" not in st.session_state:
    st.session_state["mkt_cache"] = {}
mkt = st.session_state.get("mkt_cache", {})
if not mkt:
    with st.spinner("Cargando indicadores de mercado..."):
        mkt = fetch_market_indicators()
        st.session_state["mkt_cache"] = mkt

# ── Fila 1: S&P500  - Nasdaq  - SPY RSI  - Sector  - Señal ───────
col_spx, col_ndx, col_spy, col_sector, col_signal = st.columns(5)

with col_spx:
    if "spx" in mkt:
        sc = G if mkt["spx"]["chg"] >= 0 else R
        chg = mkt["spx"]["chg"]
        # Etapa S&P500
        spy_rsi_hdr = mkt.get("spy", {}).get("rsi", 50)
        if spy_rsi_hdr < 35:
            spx_etapa = "🔥 M3 - Pánico"; spx_etf = "Entrar SPY/VOO - crash = oportunidad"
            spx_c = G; spx_bg = G_BG; spx_bor = G_BOR
        elif spy_rsi_hdr < 45:
            spx_etapa = "⚡ Corrección - Swing"; spx_etf = "Considerar SPY/TQQQ"
            spx_c = C; spx_bg = C_BG; spx_bor = C_BOR
        elif spy_rsi_hdr < 55:
            spx_etapa = "📡 Lateral - Vigilar"; spx_etf = "Acciones individuales OK"
            spx_c = A; spx_bg = A_BG; spx_bor = A_BOR
        elif spy_rsi_hdr < 68:
            # v16 fix: RSI 55-68 = bull market normal — NO bloquea acciones individuales
            spx_etapa = "📈 Bull normal"; spx_etf = "ETF índice: esperar. Acciones: OK"
            spx_c = G; spx_bg = G_BG; spx_bor = G_BOR
        else:
            # RSI > 68 = sobrecompra real
            spx_etapa = "🔴 Sobrecomprado"; spx_etf = "ETF índice: NO entrar. Acciones: cuidado"
            spx_c = TXT_MUT; spx_bg = BG_CARD; spx_bor = BOR
        st.markdown(
            f'<div style="background:{spx_bg};border:1px solid {spx_bor};border-radius:10px;padding:10px 14px">'
            f'<div style="font-size:10px;color:{TXT_MUT};font-weight:600">S&P 500</div>'
            f'<div style="font-size:18px;font-weight:800;color:{TXT}">{mkt["spx"]["val"]:,.0f}</div>'
            f'<div style="font-size:11px;color:{sc};font-weight:600">{chg:+.2f}%</div>'
            f'<div style="font-size:10px;color:{spx_c};font-weight:700;margin-top:4px">{spx_etapa}</div>'
            f'<div style="font-size:9px;color:{TXT_SOFT}">🎯 {spx_etf}</div>'
            f'</div>', unsafe_allow_html=True)
    else:
        st.metric("S&P 500", "-")

with col_ndx:
    if "ndx" in mkt:
        nc = G if mkt["ndx"]["chg"] >= 0 else R
        chg_n = mkt["ndx"]["chg"]
        # Etapa Nasdaq
        if spy_rsi_hdr < 35:
            ndx_etapa = "🔥 M3 - Pánico"; ndx_etf = "Entrar QQQ/TQQQ - crash = oportunidad"
            ndx_c = G; ndx_bg = G_BG; ndx_bor = G_BOR
        elif spy_rsi_hdr < 45:
            ndx_etapa = "⚡ Corrección - Swing"; ndx_etf = "Considerar QQQ/SQQQ hedge"
            ndx_c = C; ndx_bg = C_BG; ndx_bor = C_BOR
        elif spy_rsi_hdr < 55:
            ndx_etapa = "📡 Lateral - Vigilar"; ndx_etf = "Acciones tech individuales OK"
            ndx_c = A; ndx_bg = A_BG; ndx_bor = A_BOR
        elif spy_rsi_hdr < 68:
            # v16 fix: bull market normal — no bloquea acciones individuales
            ndx_etapa = "📈 Bull normal"; ndx_etf = "ETF Nasdaq: esperar. Tech: OK"
            ndx_c = G; ndx_bg = G_BG; ndx_bor = G_BOR
        else:
            ndx_etapa = "🔴 Sobrecomprado"; ndx_etf = "ETF Nasdaq: NO entrar. Tech: cuidado"
            ndx_c = TXT_MUT; ndx_bg = BG_CARD; ndx_bor = BOR
        st.markdown(
            f'<div style="background:{ndx_bg};border:1px solid {ndx_bor};border-radius:10px;padding:10px 14px">'
            f'<div style="font-size:10px;color:{TXT_MUT};font-weight:600">Nasdaq</div>'
            f'<div style="font-size:18px;font-weight:800;color:{TXT}">{mkt["ndx"]["val"]:,.0f}</div>'
            f'<div style="font-size:11px;color:{nc};font-weight:600">{chg_n:+.2f}%</div>'
            f'<div style="font-size:10px;color:{ndx_c};font-weight:700;margin-top:4px">{ndx_etapa}</div>'
            f'<div style="font-size:9px;color:{TXT_SOFT}">🎯 {ndx_etf}</div>'
            f'</div>', unsafe_allow_html=True)
    else:
        st.metric("Nasdaq", "-")

with col_spy:
    if "spy" in mkt:
        spy_d = mkt["spy"]
        _rsi_spy = spy_d["rsi"]
        # v18 fix: umbrales calibrados al comportamiento real del S&P500
        # RSI 65-75 es NORMAL en bull market — no es señal de precaución
        if _rsi_spy < 35:
            rc       = R
            spy_desc = "🔥 Pánico — oportunidad ETF"
            spy_tip  = "Crash o corrección severa. Momento ideal para entrar a ETF índice."
        elif _rsi_spy < 45:
            rc       = A
            spy_desc = "⚡ Corrección — considerar ETF"
            spy_tip  = "Pull-back de mercado. Buen momento para acumular SPY/VOO."
        elif _rsi_spy < 55:
            rc       = A
            spy_desc = "📡 Neutral — acciones OK"
            spy_tip  = "Mercado lateral. Seguir señales por ticker individual."
        elif _rsi_spy < 68:
            rc       = G
            spy_desc = "📈 Bull normal — acciones OK"
            spy_tip  = "Estado normal de un bull market. Acciones individuales con señal M2/M3: entrar. ETF índice: esperar pullback."
        elif _rsi_spy < 76:
            rc       = A
            spy_desc = "⚡ Bull fuerte — ETF esperar"
            spy_tip  = "Mercado fuerte pero extendido. Para ETF SPY/QQQ esperar pullback. Para acciones con señal M2/M3: OK con cautela."
        else:
            rc       = R
            spy_desc = "🔴 Sobrecompra extrema"
            spy_tip  = "RSI >76 ocurre solo el 5% del tiempo. Reducir exposición nueva en ETF. Acciones individuales: stops ajustados."
        ec = R if "bajo" in spy_d["ema_status"] else G
        st.markdown(
            f'<div style="background:{BG_CARD};border:1px solid {BOR};border-radius:10px;'
            f'padding:10px 14px" title="{spy_tip}">'
            f'<div style="font-size:10px;color:{TXT_MUT};font-weight:600">SPY — S&P500 ETF</div>'
            f'<div style="font-size:18px;font-weight:800;color:{rc}">{_rsi_spy}</div>'
            f'<div style="font-size:10px;color:{rc};font-weight:600">{spy_desc}</div>'
            f'<div style="font-size:9px;color:{ec};margin-top:3px">{spy_d["ema_status"]}</div>'
            f'<div style="font-size:8px;color:{TXT_SOFT};margin-top:2px;line-height:1.4">{spy_tip}</div>'
            f'</div>', unsafe_allow_html=True)
    else:
        st.metric("SPY RSI", "-")

with col_sector:
    if "sectores" in mkt:
        sec = mkt["sectores"]
        # Sugerir ETF del sector
        sector_etf_map = {
            "Energía": "XLE  - OIH", "Tech": "XLK  - SOXX",
            "Salud": "XLV  - XBI", "Finanzas": "XLF  - KRE",
            "Consumo": "XLY  - XLP", "Industrial": "XLI  - ITA",
            "Materiales": "XLB  - GDX",
        }
        etf_sector = sector_etf_map.get(sec["mejor_oportunidad"], "ETF sectorial")
        st.markdown(
            f'<div style="background:{G_BG};border:1px solid {G_BOR};border-radius:10px;padding:10px 14px">'
            f'<div style="font-size:10px;color:{TXT_MUT};font-weight:600">🔍 Sector con oportunidades</div>'
            f'<div style="font-size:16px;font-weight:800;color:{G}">{sec["mejor_oportunidad"]}</div>'
            f'<div style="font-size:11px;color:{G}">{sec["acciones_en_correccion"]} acciones en corrección</div>'
            f'<div style="font-size:9px;color:{TXT_SOFT};margin-top:3px">🎯 ETF: {etf_sector}</div>'
            f'</div>', unsafe_allow_html=True)
    else:
        st.metric("Sector", "-")

with col_signal:
    vix_v2  = vix.get("valor", 18)
    spy_rsi2 = mkt.get("spy", {}).get("rsi", 50)
    if vix_v2 >= 30 and spy_rsi2 < 45:
        sig="🟢 MÁXIMA OPORTUNIDAD"; sig_c=G; sig_bg=G_BG; sig_bor=G_BOR
        sig_etf = "SPY - QQQ - VOO"
        sig_acc = "Activar reserva táctica — entrar en todo"
    elif vix_v2 >= 25 or spy_rsi2 < 40:
        sig="🟡 OPORTUNIDAD MODERADA"; sig_c=A; sig_bg=A_BG; sig_bor=A_BOR
        sig_etf = "SPY - sector ETF"
        sig_acc = "Buscar swings confirmados por ticker"
    elif spy_rsi2 < 55:
        sig="📡 MERCADO NEUTRO"; sig_c=A; sig_bg=A_BG; sig_bor=A_BOR
        sig_etf = "Acciones individuales según señal NBIS"
        sig_acc = "Neutral — seguir señales M2/M3 por ticker"
    elif spy_rsi2 < 68:
        # v16: RSI 55-68 = bull market NORMAL — no bloquea acciones individuales
        # Esto es lo que ves la mayor parte del tiempo en un mercado sano
        sig="📈 BULL MARKET NORMAL"; sig_c=G; sig_bg=G_BG; sig_bor=G_BOR
        sig_etf = "ETF índice: esperar pullback"
        sig_acc = "Acciones individuales: OK si hay señal M2/M3"
    elif vix_v2 < 18 and spy_rsi2 >= 68:
        sig="🔴 SOBRECOMPRADO"; sig_c=R; sig_bg=R_BG; sig_bor=R_BOR
        sig_etf = "ETF índice: NO entrar"
        sig_acc = "Stops ajustados — reducir exposición nueva"
    else:
        sig="⚪ MERCADO NORMAL"; sig_c=TXT_MUT; sig_bg=BG_HEAD; sig_bor=BOR
        sig_etf = "Selectivo por señal"
        sig_acc = "Seguir señales del modelo por ticker"
    st.markdown(
        f'<div style="background:{sig_bg};border:1px solid {sig_bor};border-radius:10px;padding:10px 14px">'
        f'<div style="font-size:10px;color:{TXT_MUT};font-weight:600">Señal del modelo</div>'
        f'<div style="font-size:12px;font-weight:700;color:{sig_c}">{sig}</div>'
        f'<div style="font-size:10px;color:{TXT_MUT};margin-top:3px">{sig_acc}</div>'
        f'<div style="font-size:9px;color:{TXT_SOFT};margin-top:2px">🎯 {sig_etf}</div>'
        f'<div style="font-size:9px;color:{TXT_SOFT}">VIX {vix_v2}  - SPY RSI {spy_rsi2}</div>'
        f'</div>', unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.markdown("---")

tab1,tab2,tab3,tab4,tab5,tab_posiciones,tab8,tab_score,tab9=st.tabs([
    "⚡ Momentum","⚡ Swing Activo","🔥 Entrar hoy",
    "🔗 Sympathy","🔎 Mi Watchlist",
    "💼 Posiciones",                  # v19.1: Tab unificado (Greko/MVALLE/Amparito)
    "💰 Estrategia ETF",
    "🎯 Score MVALLE",                # v19.1: Ranking de candidatos para dinero real
    "📊 Backtesting",
])

# v19.1: Alias para compatibilidad con código que referencia tab_greko/tab6/tab7
tab_greko = tab_posiciones
tab6      = tab_posiciones
tab7      = tab_posiciones




# ══ TAB 1 - MOMENTUM CATALIZADOR (nueva estrategia v19) ════════

def _banner_mercado_macro(spy_rsi: float = 0) -> None:
    """
    v19.2: Muestra banner de contexto macro según RSI del SPY.
    Solo aparece cuando SPY RSI > 65 para no generar ruido innecesario.
    """
    import streamlit as _st
    if spy_rsi <= 0:
        try:
            import yfinance as _yf_bm
            _spy_hist = _yf_bm.download("SPY", period="1mo",
                                         auto_adjust=True, progress=False)
            if not _spy_hist.empty:
                _s_bm = _spy_hist["Close"].dropna()
                _d_bm = _s_bm.diff()
                _g_bm = _d_bm.clip(lower=0).rolling(14).mean()
                _l_bm = (-_d_bm.clip(upper=0)).rolling(14).mean()
                spy_rsi = round(float(100-100/(1+_g_bm.iloc[-1]/(_l_bm.iloc[-1]+1e-9))),1)
        except Exception:
            return

    if spy_rsi >= 75:
        _st.markdown(
            f'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;'
            f'padding:6px 14px;margin-bottom:8px;font-size:11px">'
            f'🚨 <strong>Mercado extendido — SPY RSI {spy_rsi:.0f}</strong> · '
            f'Score mínimo recomendado ≥17 · Solo señales con todos los criterios en verde'
            f'</div>', unsafe_allow_html=True)
    elif spy_rsi >= 68:
        _st.markdown(
            f'<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;'
            f'padding:6px 14px;margin-bottom:8px;font-size:11px">'
            f'⚠️ <strong>Mercado sobrecomprado — SPY RSI {spy_rsi:.0f}</strong> · '
            f'Ser selectivo · Privilegiar defensa y NBIS con DD &lt;-25%'
            f'</div>', unsafe_allow_html=True)
    elif spy_rsi >= 60:
        _st.markdown(
            f'<div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;'
            f'padding:6px 14px;margin-bottom:8px;font-size:11px">'
            f'✅ <strong>Mercado en zona normal — SPY RSI {spy_rsi:.0f}</strong> · '
            f'Condiciones favorables para NBIS y Momentum'
            f'</div>', unsafe_allow_html=True)

with tab1:

    st.markdown(
        f'<div class="sec-header" style="background:#FFFBEB;border-color:#FDE047">'+
        f'<span style="font-size:20px">⚡</span>'+
        f'<div><span style="font-size:16px;font-weight:700;color:#D97706">Momentum Catalizador</span>'+
        f'<span style="font-size:12px;color:{TXT_MUT};margin-left:10px">'+
        f'RSI 65-85 · Catalizador real · Posición 20-30% · Stop -5%'+
        f'</span></div></div>', unsafe_allow_html=True)

    # ── PANEL DE VALIDACIÓN — qué buscamos en Momentum ──────────
    with st.expander("📋 ¿Qué busca este tab? — Reglas de Momentum Catalizador", expanded=False):
        st.markdown(
            "<div style='font-size:11px;line-height:1.8'>"
            "<strong style='color:#D97706'>⚡ Tab Momentum — Lee tu Google Sheet Watchlist</strong><br>"
            "Busca acciones con momentum activo y catalizador fundamental real.<br>"
            "<strong style='color:#EA580C'>🌡️ Banner macro:</strong> muestra SPY RSI al inicio — ajusta tu selectividad según el nivel del mercado.<br><br>"
            "<strong>✅ CRITERIOS v19.2:</strong><br>"
            "🔸 RSI: <strong>65 - 88</strong> · MACD: <strong>positivo</strong> (requerido)<br>"
            "🔸 Analistas: <strong>≥ 3</strong> · Upside: <strong>&gt; 5%</strong><br>"
            "🔸 Revenue YoY: <strong>&gt; 0%</strong> · P/E &lt; 500x<br>"
            "🔸 Score ≥ 35 para aparecer · Score ≥ 70 para 🟢 REGISTRAR<br><br>"
            "<strong>🌡️ Con SPY RSI &gt;68:</strong> solo registrar Score ≥ 70 y RSI ≤ 78<br>"
            "<strong>🌡️ Con SPY RSI &gt;75:</strong> pausar nuevas entradas Momentum<br><br>"
            "<strong>📐 Gestión:</strong> 20-30% · Stop -5% · T1 +15% · T2 +30%<br>"
            "<strong>🎯 Badge REGISTRAR/EVALUAR/OBSERVAR</strong> guía cuál registrar en Greko"
            "Usa <strong>yf.download batch</strong> (rápido) + yf.info por ticker para fundamentales.<br><br>"
            "<strong>✅ CRITERIOS v19.2:</strong><br>"
            "🔸 RSI: <strong>65 - 88</strong> (momentum activo, no extremo)<br>"
            "🔸 MACD: <strong>positivo</strong> (requerido, confirma dirección)<br>"
            "🔸 Analistas: <strong>≥ 3</strong> cubriendo<br>"
            "🔸 Upside al target: <strong>&gt; 5%</strong><br>"
            "🔸 Revenue YoY: <strong>&gt; 0%</strong> (crecimiento positivo)<br>"
            "🔸 P/E: &lt; 500x<br><br>"
            "<strong>❌ NO APARECE SI:</strong><br>"
            "🔸 RSI &lt; 65 → Tab 🔎 Watchlist (NBIS) o ⚡ Swing<br>"
            "🔸 RSI &gt; 88 → momentum extremo, esperar corrección<br>"
            "🔸 MACD negativo → sin confirmación técnica<br>"
            "🔸 Revenue cayendo → sin catalizador fundamental<br><br>"
            "<strong>📐 GESTIÓN:</strong> 20-30% · Stop -5% · T1 +15% · T2 +30%<br><br>"
            "<strong>🎯 Ejemplos reales:</strong><br>"
            "ENPH RSI 84 · Rev +47% · MACD+ → +100% ✅<br>"
            "APLD RSI 72 · Rev +139% · MACD+ → +49% ✅<br>"
            "<span style='color:#DC2626'>MRAM RSI 85 · MACD− → BLOQUEADO ✅</span><br><br>"
            "<strong>💥 BADGE CASTIGADA:</strong> RSI &lt; 55 · DD &lt; -25% + Revenue &gt; 0 = castigo excesivo"
            "</div>", unsafe_allow_html=True)

    st.markdown(
        f'<div style="background:#FFFBEB;border:1px solid #FDE047;border-radius:8px;'
        f'padding:10px 14px;margin-bottom:12px;font-size:11px;color:#92400E">'
        f'<strong>⚡ Estrategia diferente a NBIS:</strong> '
        f'Lee tu Watchlist con lógica de momentum. '
        f'<strong>Tamaño 20-30%</strong> · Stop -5% · T1 +15% · T2 +30% · RSI 65-85'
        f'</div>', unsafe_allow_html=True)

    _banner_mercado_macro()

    if st.button("⚡ Escanear Momentum en Watchlist", use_container_width=True, key="btn_momentum"):
        with st.spinner("Analizando Watchlist con lógica Momentum..."):
            import yfinance as _yf_mom
            _mom_resultados = []

            # Leer Watchlist
            _wl_mom = leer_watchlist_sheets()
            if _wl_mom is None or _wl_mom.empty:
                st.warning("⚠️ No se pudo leer el Watchlist desde Google Sheets")
                st.session_state["scan_momentum"] = []
            else:
                _col_ticker = "Ticket" if "Ticket" in _wl_mom.columns else "Ticker"
                _universo_mom = [str(t).upper().strip()
                                 for t in _wl_mom[_col_ticker].dropna().unique()
                                 if str(t).upper().strip() and not _es_etf(str(t).upper().strip())]

                # v19.2 FIX: yf.download BATCH para RSI/MACD (1 sola llamada rápida)
                _cnt_mom = st.empty()
                _cnt_mom.info(f"⚡ Descargando precios para {len(_universo_mom)} tickers...")
                _dl_mom  = {}
                try:
                    _raw_mom = _yf_mom.download(
                        " ".join(_universo_mom), period="6mo",
                        auto_adjust=True, progress=False, threads=True)
                    _cl_mom = _raw_mom.get("Close", _raw_mom)
                    for _tk_m in _universo_mom:
                        try:
                            _s_m = (_cl_mom[_tk_m].dropna()
                                    if hasattr(_cl_mom,"columns") and _tk_m in _cl_mom.columns
                                    else _cl_mom.dropna())
                            if len(_s_m) < 26: continue
                            _pa_m   = float(_s_m.iloc[-1])
                            _h52_m  = float(_s_m.rolling(252, min_periods=1).max().iloc[-1])
                            # RSI 14
                            _d_m    = _s_m.diff()
                            _g_m    = _d_m.clip(lower=0).rolling(14).mean()
                            _lo_m   = (-_d_m.clip(upper=0)).rolling(14).mean()
                            _rsi_m  = round(float(100-100/(1+_g_m.iloc[-1]/(_lo_m.iloc[-1]+1e-9))),1)
                            # MACD
                            _macd_m = "+" if _s_m.ewm(span=12).mean().iloc[-1] > _s_m.ewm(span=26).mean().iloc[-1] else "-"
                            _dist_ath_m = round((_pa_m-_h52_m)/_h52_m*100,1) if _h52_m>0 else 0
                            _dl_mom[_tk_m] = {
                                "precio":_pa_m,"rsi":_rsi_m,"macd":_macd_m,"dist_ath":_dist_ath_m
                            }
                        except Exception:
                            pass
                except Exception:
                    pass

                # v19.2 FIX: yf.info BATCH para fundamentales
                _cnt_mom.info(f"📊 Cargando fundamentales para {len(_universo_mom)} tickers...")
                for _i_mom, _tk_m in enumerate(_universo_mom):
                    _cnt_mom.info(f"📊 {_i_mom+1} de {len(_universo_mom)}: {_tk_m}")
                    if _tk_m not in _dl_mom:
                        continue
                    try:
                        _info_m  = _yf_mom.Ticker(_tk_m).info or {}
                        _pe_m    = float(_info_m.get("trailingPE", 0) or 0)
                        _na_m    = int(_info_m.get("numberOfAnalystOpinions", 0) or 0)
                        _tm_m    = float(_info_m.get("targetMeanPrice", 0) or 0)
                        _rev_gr  = float(_info_m.get("revenueGrowth", 0) or 0)
                        _pa_m    = _dl_mom[_tk_m]["precio"]
                        _rsi_m   = _dl_mom[_tk_m]["rsi"]
                        _macd_m  = _dl_mom[_tk_m]["macd"]
                        _dist_ath_m = _dl_mom[_tk_m]["dist_ath"]

                        # v19.2 FIX: criterios más realistas
                        # 1. RSI 65-88 (momentum real, no extremo)
                        if not (65 <= _rsi_m <= 88):
                            continue
                        # 2. Al menos 3 analistas (antes era 5)
                        if _na_m < 3:
                            continue
                        # 3. Upside > 5% (antes era 15%)
                        _up_m = (_tm_m-_pa_m)/_pa_m*100 if _tm_m>0 and _pa_m>0 else 0
                        if _up_m < 5:
                            continue
                        # 4. Revenue > 0% (antes era +15%)
                        if _rev_gr < 0:
                            continue
                        # 5. P/E < 500
                        if _pe_m > 500:
                            continue
                        # 6. MACD positivo (confirmación)
                        if _macd_m != "+":
                            continue

                        # Score de momentum
                        _score_m = 0
                        if _rsi_m >= 75:      _score_m += 25
                        elif _rsi_m >= 70:    _score_m += 20
                        elif _rsi_m >= 65:    _score_m += 10
                        if _up_m >= 30:       _score_m += 25
                        elif _up_m >= 20:     _score_m += 18
                        elif _up_m >= 10:     _score_m += 10
                        elif _up_m >= 5:      _score_m += 5
                        if _rev_gr >= 0.30:   _score_m += 25
                        elif _rev_gr >= 0.15: _score_m += 15
                        elif _rev_gr >= 0:    _score_m += 5
                        if _macd_m == "+":    _score_m += 15
                        if _na_m >= 10:       _score_m += 10
                        elif _na_m >= 5:      _score_m += 5

                        # v19.2: score mínimo 35 (antes 50)
                        if _score_m < 35:
                            continue

                        _mom_resultados.append({
                            "Ticker":      _tk_m,
                            "Precio":      round(_pa_m, 2),
                            "RSI":         round(_rsi_m, 1),
                            "Revenue_YoY": f"+{_rev_gr*100:.0f}%",
                            "Upside":      f"+{_up_m:.0f}%",
                            "Target":      f"${_tm_m:.0f}",
                            "Analistas":   _na_m,
                            "MACD":        "✅" if _macd_m == "+" else "❌",
                            "Dist_ATH":    f"{_dist_ath_m:.1f}%",
                            "Score_Mom":   _score_m,
                            "Señal":       "⚡ MOMENTUM",
                            "Tamaño":      "20-30%",
                            "Stop":        f"${round(_pa_m*0.95,2):.2f} (-5%)",
                            "T1":          f"${round(_pa_m*1.15,2):.2f} (+15%)",
                            "T2":          f"${round(_pa_m*1.30,2):.2f} (+30%)",
                        })
                    except Exception:
                        continue

                _cnt_mom.empty()
                _mom_resultados.sort(key=lambda x: x["Score_Mom"], reverse=True)
                st.session_state["scan_momentum"] = _mom_resultados
                st.session_state["scan_momentum_ts"] = datetime.datetime.now().strftime("%H:%M")

    _mom_data = st.session_state.get("scan_momentum")
    _mom_ts   = st.session_state.get("scan_momentum_ts","")

    if _mom_data is not None and len(_mom_data) > 0:
        st.markdown(
            f'<div style="font-size:11px;color:{TXT_MUT};margin-bottom:8px">'+
            f'⚡ {len(_mom_data)} acciones con momentum catalizador · {_mom_ts}'+
            f'</div>', unsafe_allow_html=True)

        for _idx_m, _mr in enumerate(_mom_data[:15]):
            _rsi_c   = "#DC2626" if _mr["RSI"] > 80 else "#D97706" if _mr["RSI"] > 70 else "#16A34A"
            # v19.2: Calcular recomendación de registro
            _rec_mom = badge_recomendacion_momentum(
                score=_mr.get("Score_Mom",0), rsi=_mr.get("RSI",0),
                n_analistas=_mr.get("Analistas",0),
                rev_yoy_str=_mr.get("Revenue_YoY","0"),
                upside_str=_mr.get("Upside","0"),
                macd=_mr.get("MACD","—"))
            _borde_mom = ("#16A34A" if _rec_mom["nivel"]=="REGISTRAR"
                          else "#D97706" if _rec_mom["nivel"]=="EVALUAR"
                          else "#94A3B8")
            st.markdown(
                f'<div style="background:{BG_CARD};border:1px solid {BOR};'+
                f'border-left:4px solid {_borde_mom};border-radius:8px;'+
                f'padding:10px 14px;margin-bottom:4px">'+
                f'<div style="display:flex;justify-content:space-between;align-items:center">'+
                f'  <div>'+
                f'    <span style="font-size:17px;font-weight:800;color:{TXT}">{_mr["Ticker"]}</span>'+
                f'{badge_castigada(float(_mr.get("RSI",0) or 0), float(str(_mr.get("Dist_ATH","0")).replace("%","").replace("+","") or 0))}'+
                f'    <span style="background:#FEF9C3;color:#D97706;border-radius:4px;'+
                f'    padding:1px 6px;font-size:9px;font-weight:700;margin-left:6px">⚡ MOMENTUM</span>'+
                f'    <span style="background:#F1F5F9;color:#64748B;border-radius:4px;'+
                f'    padding:1px 6px;font-size:9px;margin-left:4px">'+
                f'    🎯 {_mr["Tamaño"]}</span>'+
                f'  </div>'+
                f'  <span style="font-size:16px;font-weight:700;color:{TXT}">${_mr["Precio"]}</span>'+
                f'</div>'+
                f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:8px;font-size:10px">'+
                f'  <div><span style="color:{TXT_MUT}">RSI </span><span style="color:{_rsi_c};font-weight:700">{_mr["RSI"]}</span></div>'+
                f'  <div><span style="color:{TXT_MUT}">Revenue </span><span style="color:#16A34A;font-weight:700">{_mr["Revenue_YoY"]}</span></div>'+
                f'  <div><span style="color:{TXT_MUT}">Target </span><span style="color:#2563EB;font-weight:700">{_mr["Target"]} ({_mr["Upside"]})</span></div>'+
                f'  <div><span style="color:{TXT_MUT}">Analistas </span><span style="font-weight:700">{_mr["Analistas"]}</span></div>'+
                f'  <div><span style="color:{TXT_MUT}">MACD </span><span style="font-weight:700">{_mr["MACD"]}</span></div>'+
                f'  <div><span style="color:{TXT_MUT}">vs ATH </span><span style="font-weight:700">{_mr["Dist_ATH"]}</span></div>'+
                f'  <div><span style="color:{TXT_MUT}">Stop </span><span style="color:#DC2626;font-weight:700">{_mr["Stop"]}</span></div>'+
                f'  <div><span style="color:{TXT_MUT}">Score </span><span style="font-weight:700">{_mr["Score_Mom"]}/100</span></div>'+
                f'</div>'+
                f'<div style="display:flex;gap:8px;margin-top:6px;font-size:10px">'+
                f'  <span style="background:#F0FDF4;color:#16A34A;border-radius:4px;padding:2px 6px">T1 {_mr["T1"]}</span>'+
                f'  <span style="background:#EFF6FF;color:#2563EB;border-radius:4px;padding:2px 6px">T2 {_mr["T2"]}</span>'+
                f'</div></div>', unsafe_allow_html=True)

            # v19.2: Badge recomendación visible antes del botón
            if _rec_mom.get("badge_html"):
                st.markdown(_rec_mom["badge_html"], unsafe_allow_html=True)
            if _rec_mom["nivel"] in ("EVALUAR","OBSERVAR"):
                st.markdown(
                    f'<div style="font-size:9px;color:#94A3B8;margin-top:2px">'
                    f'💡 {_rec_mom["motivo"]}</div>', unsafe_allow_html=True)

            if st.button(_rec_mom["btn_label"],
                         key=f"btn_mom_greko_{_mr['Ticker']}_{_idx_m}",
                         type=_rec_mom["btn_tipo"],
                         help=f"Registrar · {_rec_mom['motivo']}"):
                _rsi_mom  = float(str(_mr.get("RSI",0)).replace("+","") or 0)
                _macd_mom = "+" if str(_mr.get("MACD","—")) in ("+","✅") else "-"
                _dd_mom   = float(str(_mr.get("Dist_ATH","0")).replace("%","").replace("+","") or 0)
                try:
                    _pc_mom = float(str(_mr.get("Precio",0)) or 0)
                except Exception:
                    _pc_mom = 0
                _ok_m, _msg_m = escribir_greko_sheets(
                    ticker=_mr["Ticker"],
                    precio_compra=_pc_mom,
                    fase="M3",
                    score=int(_mr.get("Score_Mom",50)),
                    prob_nbis=float(str(_mr.get("Score_Mom",0) or 0)),  # Score como proxy de probabilidad
                    area=_mr.get("Sector","-"),
                    tipo="Accion",
                    fuente="Momentum",
                    arrastradas="-",
                    opinion=f"Momentum · Rev{_mr.get('Revenue_YoY','')} · Up{_mr.get('Upside','')} · {_mr.get('Analistas',0)}analistas",
                    cantidad=0,
                    notas=f"Score {_mr.get('Score_Mom',0)}/100 · T1:{_mr.get('T1','')} · T2:{_mr.get('T2','')} · RSI:{_rsi_mom}",
                    rsi_ticker=_rsi_mom,
                    rsi_accion=_rsi_mom,
                    macd_estado=_macd_mom,
                    dd_pico_pct=_dd_mom,
                    tipo_senal="Momentum",
                )
                if _ok_m:
                    st.success(f"✅ {_mr['Ticker']} registrado en Greko como Momentum")
                    st.session_state.pop("_cartera_global_cache", None)
                    st.session_state.pop("_greko_processed_df", None)
                    st.session_state.pop("_score_rows_base", None)
                else:
                    st.error(_msg_m)

    elif _mom_data is not None and len(_mom_data) == 0:
        st.markdown(
            f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:10px;'+
            f'padding:20px;text-align:center;color:{TXT_MUT}">'+
            f'⚡ Sin acciones con momentum catalizador hoy.<br>'+
            f'<span style="font-size:11px">RSI 65-85 · ≥5 analistas · upside >15% · revenue >15% YoY</span>'+
            f'</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="background:{BG_HEAD};border:1px solid {BOR};border-radius:10px;'+
            f'padding:24px;text-align:center;color:{TXT_MUT}">'+
            f'<div style="font-size:28px;margin-bottom:8px">⚡</div>'+
            f'Presiona Escanear para encontrar acciones con momentum real</div>',
            unsafe_allow_html=True)

# ══ TAB 2 - SWING ACTIVO (M2 - rebote confirmado) ══════════════
# ══ TAB 4 - SWING ACTIVO ═════════════════════════════════════
with tab2:
    st.markdown(
        f'<div class="sec-header" style="background:{C_BG};border-color:{C_BOR}">'
        f'<span style="font-size:20px">⚡</span>'
        f'<div><span style="font-size:16px;font-weight:700;color:{C}">Swing Activo — M2 Rebote Técnico</span>'
        f'<div style="font-size:11px;color:{TXT_MUT};margin-top:3px">'
        f'DD ≤ -20% · RSI 48-65 · Score 40-55 · Prob_NBIS 30-45% · Ventana óptima 7-9 días</div>'
        f'</div></div>', unsafe_allow_html=True)
    with st.expander("📋 ¿Qué busca este tab? — Reglas Swing Activo (M2)", expanded=False):
        st.markdown(
            "<div style='font-size:11px;line-height:1.8'>"
            "<strong style='color:#7C3AED'>⚡ Tab Swing Activo — NBIS M2/M3 Confirmado</strong><br>"
            "Detecta rebotes desde correcciones profundas. Patrón ENPH/APLD/RCAT.<br>"
            "<strong style='color:#EA580C'>🌡️ Banner macro:</strong> muestra SPY RSI al inicio — "
            "con mercado sobrecomprado, exigir DD &lt;-25% y Score MVALLE ≥17.<br><br>"
            "<strong>✅ CRITERIOS DE ENTRADA:</strong><br>"
            "🔸 RSI: <strong>48 - 65</strong> (zona de recuperación)<br>"
            "🔸 DD desde pico: <strong>-20% o más</strong> (corrección real)<br>"
            "🔸 Score técnico: <strong>40 - 55</strong><br>"
            "🔸 Prob_NBIS: <strong>30% - 45%</strong> (zona óptima del patrón)<br>"
            "🔸 Volumen: activándose · EMA50: precio no más de -30% bajo la media<br><br>"
            "<strong>❌ BLOQUEADO SI:</strong><br>"
            "🔸 RSI &gt; 65 → ver Tab ⚡ Momentum<br>"
            "🔸 P/E &gt; 500x · Solo 1-2 analistas · Precio en ATH ±5%<br>"
            "🔸 SPY RSI &gt; 68 → señales degradadas<br><br>"
            "<strong>📐 GESTIÓN:</strong> Tamaño 40-60% · Stop -7% · T1 +8% · T2 +12%<br><br>"
            "<strong>🔄 Diferencia con Entrar Hoy:</strong><br>"
            "Swing M2 = patrón formándose (entrar parcial) · Entrar Hoy M3 = confirmado (entrar completo)<br><br>"
            "<br><br><strong style='color:#7C3AED'>💥 BADGE CASTIGADA:</strong><br>"
            "<strong style='color:#EA580C'>⚠️ ALERTA CATALIZADOR (v19.2 — datos reales):</strong><br>"
            "RSI &lt;55 sin Decision ENTRAR → badge 🚨 rojo · WR histórico 32% · prom −5.3%<br>"
            "RSI 55-65 sin ENTRAR → badge ⚠️ naranja · WR 48% · esperar confirmación<br>"
            "<strong>Vigencia M2 NBIS: 10 días</strong> (actualizado de 5d) · datos: zona ganadora 6-20d<br><br>"

            "<span style='color:#D97706'>💥 CASTIGADA</span>: RSI &lt; 55 + DD &lt; -25% → castigo excesivo, rebote más probable<br>"
            "<span style='color:#EA580C'>⚠️ CASTIGADA</span>: RSI &lt; 62 + DD &lt; -20% → corrección técnica profunda<br>"
            "Cuando un M2 tiene badge CASTIGADA = mayor convicción de rebote"
            "<strong>💥 BADGE CASTIGADA en Swing:</strong><br>"
            "🔸 💥 CASTIGADA (naranja fuerte): RSI &lt; 55 + DD &lt; -25%<br>"
            "🔸 ⚠️ CASTIGADA (naranja suave): RSI &lt; 62 + DD &lt; -20%<br>"
            "Indica que el mercado vendió en exceso → mayor probabilidad de rebote<br><br>"
            "<strong style='color:#7C3AED'>📈 DIVERGENCIA RSI (v19.1):</strong><br>"
            "Precio hace mínimos más bajos · RSI hace mínimos más ALTOS → momentum bajista agotado<br>"
            "<span style='color:#065F46'>📈 DIV ALCISTA FUERTE</span>: precio -5%+ · RSI +8pts → máxima convicción<br>"
            "<span style='color:#065F46'>📈 DIV ALCISTA</span>: suelo formándose → el rebote puede ser el M3<br>"
            "ENPH Feb 2026: divergencia fuerte a $32 → 4 meses después +100% ✅"
            "</div>", unsafe_allow_html=True)

    # v19 Prioridad 1: banner si mercado sobrecomprado
    _spy_tab2 = get_spy_filtro()
    _spy_rsi_t2 = _spy_tab2.get("spy_rsi", 55)
    if _spy_tab2.get("mercado_sobrecomprado", False):
        st.markdown(
            f'<div style="background:#FEF2F2;border:2px solid #FCA5A5;'
            f'border-radius:10px;padding:12px 18px;margin-bottom:10px">'
            f'<div style="font-size:13px;font-weight:800;color:#DC2626;margin-bottom:4px">'
            f'🚨 MERCADO SOBRECOMPRADO — SPY RSI {_spy_rsi_t2:.0f}</div>'
            f'<div style="font-size:11px;color:#374151;line-height:1.8">'
            f'El S&P 500 está en zona de máximos históricos (RSI > 68). '
            f'Las entradas nuevas tienen WR < 40% en este contexto.<br>'
            f'<strong>El modelo degradó ENTRAR → ANTICIPAR (40% posición)</strong> '
            f'para todas las señales. Solo entrar con catalizador muy específico y convicción alta.'
            f'</div></div>',
            unsafe_allow_html=True)

    st.markdown(
        f'<div class="info-box">'
        f'<strong>📊 Criterios v19 (datos semana 27abr-08may):</strong> '
        f'<span style="color:{R}">DD ≤ -20%</span> (WR 65% vs 33% con DD leve) · '
        f'<span style="color:{C}">RSI 48-65</span> (WR 91% en esa zona) · '
        f'<span style="color:{G}">Score 40-55</span> (WR 70% vs 25% si Score>55) · '
        f'<span style="color:#7C3AED">Prob_NBIS 30-45%</span> (zona óptima 65-70% WR · <25% débil · >45% tardía)<br>'
        f'🏷️ Badge <strong style="color:{G}">✅ APTA</strong> = cumple los 4 criterios (WR histórico 80%+) · '
        f'🛑 Stop -7% · 🎯 T1 +8% vender 55% · 🎯 T2 +15% runner · ⚠️ Alerta día 7'
        f'</div>',
        unsafe_allow_html=True)

    col_btn_sw, col_info_sw = st.columns([2, 3])
    with col_btn_sw:
        _banner_mercado_macro()

    if st.button("⚡ Escanear Swing Activo", use_container_width=True, key="btn_swing"):
            with st.spinner("Detectando rebotes activos en ~{} tickers...".format(len(SCAN_UNIVERSE))):
                resultado_sw = scan_swing(max_results=max_res, universo=SCAN_UNIVERSE[:st.session_state.get("universo_size", len(SCAN_UNIVERSE))])
                st.session_state["scan_swing"] = resultado_sw
                st.session_state["scan_swing_ts"] = datetime.datetime.now().strftime("%H:%M")
    with col_info_sw:
        if st.session_state.get("scan_swing") is not None:
            n_sw = len(st.session_state["scan_swing"])
            ts_sw = st.session_state.get("scan_swing_ts","")
            st.markdown(
                f'<div style="font-size:11px;color:{G if n_sw>0 else TXT_MUT};padding-top:8px">'+
                f'● {n_sw} swings activos encontrados  - {ts_sw}</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="font-size:11px;color:{TXT_SOFT};padding-top:8px">'+
                f'Presiona el botón para detectar swings en tiempo real</div>',
                unsafe_allow_html=True)

    sw_result = st.session_state.get("scan_swing")

    # ══ FILTRO SPY DÍA ANTERIOR v14 ════════════════════════════
    # get_spy_filtro() estaba definida pero NUNCA se llamaba - fix v14
    _spy      = get_spy_filtro()
    _mkt_ok   = _spy["mercado_positivo"]
    _spy_chg  = _spy["cambio_pct"]
    _spy_src  = _spy["fuente"]

    if _spy_src not in ("sin_datos", "error"):
        _spy_nivel = _spy.get("nivel", "ok")
        if _spy_nivel == "negativo":
            # SPY < -1.5% — bloqueo total justificado (como 21-25 Abr)
            st.markdown(
                f'<div style="background:#FEF2F2;border:2px solid #EF4444;border-radius:12px;'
                f'padding:16px 20px;margin-bottom:12px">'
                f'<div style="font-size:14px;font-weight:800;color:#DC2626">'
                f'🚫 FILTRO SPY — Mercado Negativo ({_spy_chg:+.2f}%)</div>'
                f'<div style="font-size:12px;color:#7F1D1D;margin-top:4px">'
                f'SPY cayó {_spy_chg:.1f}% ayer — caída real. Señales M2 bloqueadas. '
                f'Solo M3 confirmadas pasan. Espera un día verde antes de entrar.</div>'
                f'<div style="font-size:11px;color:#991B1B;margin-top:4px">'
                f'Este nivel (-1.5%) es comparable al 21-25 Abr. Bloqueo justificado.</div>'
                f'</div>', unsafe_allow_html=True)
        elif _spy_nivel == "moderado":
            # SPY -0.5% a -1.5% — advertencia pero no catastrófico
            st.markdown(
                f'<div style="background:#FFFBEB;border:2px solid #FCD34D;border-radius:12px;'
                f'padding:14px 18px;margin-bottom:12px">'
                f'<div style="font-size:13px;font-weight:800;color:#D97706">'
                f'⚠️ SPY débil ayer ({_spy_chg:+.2f}%) — señales M2 con precaución</div>'
                f'<div style="font-size:12px;color:#92400E;margin-top:4px">'
                f'Debilidad moderada. Las señales M2 se muestran pero considera '
                f'reducir el tamaño de posición al 50%. M3 confirmadas: sin restricción.</div>'
                f'</div>', unsafe_allow_html=True)
        else:
            # SPY > -0.5% — OK (incluye -0.31% de hoy)
            _color_ok = "#16A34A" if _spy_chg >= 0 else "#D97706"
            _icon_ok  = "✅" if _spy_chg >= 0 else "🟡"
            st.markdown(
                f'<div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;'
                f'padding:10px 16px;margin-bottom:10px">'
                f'<span style="font-size:12px;font-weight:700;color:{_color_ok}">'
                f'{_icon_ok} SPY {_spy_chg:+.2f}% ayer — mercado OK · Señales M2 habilitadas</span>'
                f'<span style="font-size:10px;color:#6B7280;margin-left:8px">'
                f'(variaciones entre -0.5% y +∞ son ruido normal, no bloquean)</span>'
                f'</div>', unsafe_allow_html=True)

    # v18 fix: filtrar M2 solo si mercado REALMENTE negativo (<-1.5%)
    # Antes: -0.31% bloqueaba igual que -2% → demasiado sensible
    _spy_nivel_sw = _spy.get("nivel","ok")
    if sw_result is not None and _spy_nivel_sw == "negativo" and not sw_result.empty:
        # Bloqueo total: solo M3 (4+ días alcistas)
        sw_result_display = sw_result[sw_result["Dias_Alcistas"] >= 4].copy()
    elif sw_result is not None and _spy_nivel_sw == "moderado" and not sw_result.empty:
        # Bloqueo parcial: M2 débiles se filtran (score > 50 pasa)
        sw_result_display = sw_result[sw_result.get("Score_Rebote", 0) >= 45].copy()                             if "Score_Rebote" in sw_result.columns else sw_result
    else:
        # OK o ruido normal: sin filtro
        sw_result_display = sw_result

    # ── v18: Marcar señales que cumplen criterios óptimos (no filtrar) ──
    # Los filtros DD -20%, RSI 48-65, Score 40-55 se muestran como badges
    # pero NO eliminan señales — el trader decide basado en la info
    if sw_result_display is not None and not sw_result_display.empty:
        _cols_sw = sw_result_display.columns.tolist()
        # Calcular qué señales cumplen los 3 criterios óptimos
        _dd_ok = pd.to_numeric(sw_result_display.get("DD_pico", pd.Series()), errors="coerce") <= -20
        _rsi_ok = (pd.to_numeric(sw_result_display.get("RSI", pd.Series()), errors="coerce").between(48,65))
        _sc_ok  = (pd.to_numeric(sw_result_display.get("Score_Rebote", pd.Series()), errors="coerce").between(40,55))
        try:
            _aptas = sw_result_display[_dd_ok & _rsi_ok & _sc_ok]
            _n_aptas = len(_aptas)
            _n_total = len(sw_result_display)
            if _n_aptas > 0:
                _tickers_aptos_sw = " · ".join(_aptas["Ticker"].tolist()[:8])
                st.markdown(
                    f'<div style="background:#F0FDF4;border:1px solid #86EFAC;'
                    f'border-radius:8px;padding:6px 14px;margin-bottom:8px;font-size:11px">'
                    f'<strong style="color:#16A34A">✅ {_n_aptas} de {_n_total} cumplen criterios v18</strong> '
                    f'(DD≤-20% · RSI 48-65 · Score 40-55) WR 80%+ → '
                    f'<strong>{_tickers_aptos_sw}</strong>'
                    f'</div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="background:#FFFBEB;border:1px solid #FCD34D;'
                    f'border-radius:8px;padding:6px 14px;margin-bottom:8px;font-size:11px">'
                    f'<strong style="color:#D97706">⚠️ Hoy ninguna cumple los 3 criterios óptimos</strong> '
                    f'(DD≤-20% · RSI 48-65 · Score 40-55) — '
                    f'Se muestran TODAS las señales del scanner para análisis.'
                    f'</div>',
                    unsafe_allow_html=True)
        except Exception:
            pass

    if sw_result is None:
        st.markdown(
            f'<div style="background:{C_BG};border:1px solid {C_BOR};border-radius:12px;'+
            f'padding:32px;text-align:center">'+
            f'<div style="font-size:36px;margin-bottom:10px">⚡</div>'+
            f'<div style="font-size:14px;font-weight:700;color:{C};margin-bottom:6px">Swing Activo - Sin escanear</div>'+
            f'<div style="font-size:12px;color:{TXT_MUT}">'+
            f'Detecta acciones con 3+ días consecutivos alcistas tras corrección.'+
            f'<br>Oportunidades de 8-15% en 5-10 días.</div>'+
            f'</div>', unsafe_allow_html=True)
    elif sw_result.empty and sw_result.attrs.get("spy_filtro_activo"):
        # ── Banner: filtro SPY activo (mercado cayó ayer) ────
        cambio_spy = sw_result.attrs.get("spy_cambio_pct", 0.0)
        st.markdown(
            f'<div style="background:{R_BG};border:2px solid {R_BOR};border-radius:12px;'+
            f'padding:20px 24px;margin-bottom:12px">'+
            f'<div style="font-size:15px;font-weight:800;color:{R};margin-bottom:6px">'+
            f'🛑 FILTRO SPY ACTIVO - Señales M2 bloqueadas</div>'+
            f'<div style="font-size:13px;color:{TXT}">'+
            f'SPY cerró <strong>{cambio_spy:+.2f}%</strong> ayer - mercado en rojo.'+
            f'<br>El modelo bloquea señales M2 cuando el mercado bajó el día anterior.</div>'+
            f'<div style="font-size:11px;color:{TXT_MUT};margin-top:8px">'+
            f'📖 Regla v14: SPY ayer < SPY anteayer -> no entrar en swings. '+
            f'Las señales volverán cuando el mercado recupere dirección.</div>'+
            f'</div>', unsafe_allow_html=True)
    elif sw_result.empty:
        # v19: mensaje contextual con contexto SPY
        _spy_ctx2 = get_spy_filtro()
        _spy_rsi2 = _spy_ctx2.get("spy_rsi", 55)
        _spy_pct2 = _spy_ctx2.get("cambio_pct", 0)
        _dd_ctx2  = _spy_ctx2.get("dd_min_adaptativo", -15)
        _fase_msg = (
            "📈 Mercado en fase **alcista** — correcciones menos profundas de lo normal."
            if _spy_rsi2 > 58 else
            "📊 Mercado en fase **neutral** — esperando corrección suficiente."
        )
        st.markdown(
            f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
            f'border-radius:12px;padding:20px 24px;margin-bottom:12px">'
            f'<div style="font-size:14px;font-weight:700;color:#374151;margin-bottom:10px">'
            f'⏳ Sin señales de Swing Activo</div>'
            f'<div style="font-size:12px;color:#374151;line-height:2;margin-bottom:10px">'
            f'{_fase_msg}<br>'
            f'El modelo busca correcciones de <strong>{_dd_ctx2:.0f}%</strong> o más. '
            f'Hoy ninguna acción del universo cumple ese criterio.<br>'
            f'<span style="color:#16A34A">💡 Esto es correcto</span> — '
            f'no forzar trades cuando no hay setup es parte de la disciplina del modelo.'
            f'</div>'
            f'<div style="background:#EFF6FF;border-radius:8px;padding:10px 14px;'
            f'font-size:11px;color:#2563EB">'
            f'<strong>¿Qué hacer ahora?</strong> Revisar <strong>Tab Watchlist</strong> '
            f'para acciones en seguimiento. Cuando el mercado consolide o algún sector '
            f'corrija, las señales Swing aparecerán automáticamente.'
            f'</div>'
            f'<div style="margin-top:8px;font-size:10px;color:#9CA3AF">'
            f'SPY RSI {_spy_rsi2:.0f} · Cambio ayer {_spy_pct2:+.1f}% · '
            f'DD mínimo activo: {_dd_ctx2:.0f}%'
            f'</div></div>',
            unsafe_allow_html=True)
    else:
        # ── Banner: filtro de límite activo (> 8 señales) ───
        if sw_result.attrs.get("filtro_limite_activo"):
            st.markdown(
                f'<div style="background:{A_BG};border:1px solid {A_BOR};border-radius:10px;'+
                f'padding:14px 18px;margin-bottom:14px">'+
                f'<div style="font-size:13px;font-weight:700;color:{A}">'+
                f'⚠️ Filtro de límite activo - mostrando solo las 5 mejores señales</div>'+
                f'<div style="font-size:11px;color:{TXT_MUT};margin-top:4px">'+
                f'El modelo detectó más de 8 candidatos simultáneos. '+
                f'Esto indica un rebote general de mercado, no señales individuales sólidas. '+
                f'Se muestran las 5 con mayor Score Rebote.</div>'+
                f'</div>', unsafe_allow_html=True)
        # ── SPY badge positivo ───────────────────────────────
        spy_delta = sw_result.attrs.get("spy_cambio_pct", 0.0)
        st.markdown(
            f'<div style="font-size:11px;color:{G};margin-bottom:10px;font-weight:600">'+
            f'✅ Filtro SPY: mercado positivo ({spy_delta:+.2f}% ayer)  - '+
            f'Señales M2 habilitadas  - v14</div>',
            unsafe_allow_html=True)

        # ── Cambio 3 v14: Límite máx 8 señales -> top 5 por Score Rebote ─
        _display = sw_result_display if sw_result_display is not None else sw_result
        if _display is not None and len(_display) > 8:
            _display = _display.sort_values("Score_Rebote", ascending=False).head(5)
            st.markdown(
                f'<div style="background:{A_BG};border:1px solid {A_BOR};border-radius:10px;'
                f'padding:12px 16px;margin-bottom:12px">'
                f'<div style="font-size:13px;font-weight:700;color:{A}">'
                f'⚠️ Más de 8 señales detectadas -> mostrando top 5 por Score Rebote</div>'
                f'<div style="font-size:11px;color:{TXT_MUT};margin-top:4px">'
                f'Muchas señales simultáneas = rebote de mercado, no oportunidades individuales. '
                f'Semana 21-25 Abr: 15 señales -> con este filtro habrían sido 5.</div>'
                f'</div>', unsafe_allow_html=True)

        # Render swing cards
        for _, r in (_display if _display is not None else pd.DataFrame()).iterrows():
            dias_c = G if r["Dias_Alcistas"] >= 3 else A
            mom_c  = G if r["Momentum_3d"] >= 5 else A if r["Momentum_3d"] >= 2 else TXT_MUT
            rsi_c  = G if r["RSI"] < 45 else A if r["RSI"] < 55 else TXT_MUT

            # ── FASE DE ENTRADA + EARNINGS v15 ──────────────
            vol_r     = r.get("Volumen", 100)
            cat_fecha_card = str(r.get("Cat_Fecha","-"))
            _ei = calcular_earnings_impact(cat_fecha_card, "M2")
            _earn_dias_card = _ei["dias_para_cat"]
            _earn_badge_card = _ei["badge"]
            _earn_badge_color = _ei.get("badge_color","#64748B")

            # Bloqueo total si earnings en 1-2 días
            _bloqueado_earn = _earn_dias_card <= 2 and _ei["tiene_cat"]

            # v17 Fix TAB-F1/F2/F3: Sincronizar criterios con Tab3 Entrar Hoy
            # ANTES: "ENTRAR HOY" con solo 3 condiciones simples → confusión con Tab3
            # AHORA: distinguir SWING HOY (criterios swing) vs ENTRAR HOY (criterios M3)
            _rsi_card  = float(r.get("RSI", 50))
            _dd_card   = float(r.get("DD_pico", 0))

            # Criterios M3 reales (sincronizados con Tab3 Entrar Hoy)
            _es_m3_real = (not _bloqueado_earn
                          and r["Dias_Alcistas"] >= 3
                          and r["Momentum_3d"] >= 4
                          and vol_r >= 120
                          and _rsi_card <= 55      # criterio M3 (relajado vs Tab3 para swing)
                          and _dd_card <= -5)      # corrección real

            # Criterios solo swing (momentun fuerte pero RSI más alto)
            _es_swing_hoy = (not _bloqueado_earn
                            and r["Dias_Alcistas"] >= 3
                            and r["Momentum_3d"] >= 4
                            and vol_r >= 120
                            and not _es_m3_real)

            if _es_m3_real:
                fase       = "🔥 ENTRAR HOY"
                fase_c     = G; fase_bg = G_BG; fase_bor = G_BOR
                fase_momento = "M3 - Confirmado (aparece también en Tab Entrar Hoy)"
                fase_desc  = "Señal M3 completa. Debería aparecer también en Tab Entrar Hoy."
                if _earn_badge_card:
                    fase_desc += f"  - {_earn_badge_card}"
                fase_accion= "✅ Entrar 100% del tamaño planificado"
            elif _es_swing_hoy:
                fase       = "⚡ SWING HOY"
                fase_c     = C; fase_bg = C_BG; fase_bor = C_BOR
                fase_momento = "Swing momentum — criterios propios (NO es Tab3 M3)"
                fase_desc  = ("Señal de swing por momentum/días alcistas. "
                              "RSI o DD no cumplen los criterios M3 estrictos del Tab Entrar Hoy "
                              f"(RSI {_rsi_card:.0f} / DD {_dd_card:.0f}%). "
                              "Es una señal válida de swing — diferente al patrón NBIS.")
                if _earn_badge_card:
                    fase_desc += f"  - {_earn_badge_card}"
                fase_accion= "⚡ Entrar 50% — señal de swing, no M3 completo"
            elif r["Dias_Alcistas"] >= 3 and r["Momentum_3d"] >= 4:  # v14: 3 días mínimo
                fase       = "⚡ EN FORMACIÓN M2"
                fase_c     = C; fase_bg = C_BG; fase_bor = C_BOR
                fase_momento = "M2 - Confirmando"
                fase_desc  = "Rebote iniciado pero sin plena convicción. Entrar con la mitad."
                fase_accion= "⚡ Entrar 50% ahora  - completar si mañana confirma volumen"
            else:
                fase       = "👀 TEMPRANA"
                fase_c     = A; fase_bg = A_BG; fase_bor = A_BOR
                fase_momento = "M1->M2 - Vigilar"
                fase_desc  = "Solo 2 días subiendo. Puede revertir. Esperar un día más."
                fase_accion= "⏳ Solo watchlist - no entrar todavía"

            # ── VOLUMEN ──────────────────────────────────────
            if vol_r >= 200:
                vol_label = "🟢 ALTO"; vol_c = G; vol_desc = f"{vol_r}% del promedio  - Confirma el movimiento"
            elif vol_r >= 120:
                vol_label = "🟡 NORMAL"; vol_c = A; vol_desc = f"{vol_r}% del promedio  - Movimiento moderado"
            else:
                vol_label = "🔴 BAJO"; vol_c = R; vol_desc = f"{vol_r}% del promedio  - Sin convicción - cuidado"

            st.markdown(
                f'<div style="background:{BG_CARD};border:1px solid {C_BOR};'
                f'border-left:4px solid {fase_c};border-radius:12px;'
                f'padding:14px 18px;margin-bottom:10px">'

                # Header con NBIS badge integrado
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">'
                f'<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
                f'  <span style="font-size:20px;font-weight:800;color:{B}">{r["Ticker"]}</span>'
                f'  <span style="font-size:12px;color:{TXT_MUT}">{r["Nombre"][:20]}</span>'
                f'{badge_castigada(float(r.get("RSI",0) or 0), float(str(r.get("DD","0") or "0").replace("%","").replace("+","") or 0))}'
                f'{r.get("Div_Badge","")}'
                f'  <span style="background:{C_BG};color:{C};border:1px solid {C_BOR};'
                f'  border-radius:6px;padding:2px 8px;font-size:10px;font-weight:700">⚡ SWING</span>'
                + (lambda p=r.get("Prob_NBIS",0), s=r.get("Sim_NBIS",0):
                    f'  <span style="background:{"#F0FDF4" if p>=65 else "#FFFBEB" if p>=45 else "#F8FAFC"};'
                    f'  color:{"#16A34A" if p>=65 else "#D97706" if p>=45 else "#64748B"};'
                    f'  border:1px solid {"#86EFAC" if p>=65 else "#FDE68A" if p>=45 else "#E2E8F0"};'
                    f'  border-radius:6px;padding:2px 8px;font-size:10px;font-weight:700">'
                    f'  ⭐ NBIS {p:.0f}%</span>'
                    f'  <span style="background:{"#EFF6FF" if s>=55 else "#FFFBEB" if s>=35 else "#F8FAFC"};'
                    f'  color:{"#2563EB" if s>=55 else "#D97706" if s>=35 else "#64748B"};'
                    f'  border:1px solid {"#BFDBFE" if s>=55 else "#FDE68A" if s>=35 else "#E2E8F0"};'
                    f'  border-radius:6px;padding:2px 8px;font-size:10px;font-weight:700">'
                    f'  📊 Sim {s:.0f}%</span>'
                )() +
                f'</div>'
                f'<div style="text-align:right;font-size:11px;color:{TXT_MUT}">'
                f'${r["Precio"]:.2f}  - {r["Area"]}  - Beta {r["Beta"]}</div>'
                f'</div>'

                # ── FASE + VOLUMEN - nueva fila destacada ────
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">'
                f'  <div style="background:{fase_bg};border:1px solid {fase_bor};'
                f'  border-radius:8px;padding:8px 12px">'
                f'    <div style="font-size:9px;color:{fase_c};font-weight:700;margin-bottom:2px">FASE DE ENTRADA  - {fase_momento}</div>'
                f'    <div style="font-size:13px;font-weight:700;color:{fase_c}">{fase}</div>'
                f'    <div style="font-size:10px;color:{TXT_MUT};margin-top:2px">{fase_desc}</div>'
                f'    <div style="font-size:10px;color:{fase_c};font-weight:600;margin-top:4px">{fase_accion}</div>'
                f'  </div>'
                f'  <div style="background:{BG_HEAD};border:1px solid {BOR};'
                f'  border-radius:8px;padding:8px 12px">'
                f'    <div style="font-size:10px;color:{TXT_MUT};font-weight:700;margin-bottom:2px">VOLUMEN</div>'
                f'    <div style="font-size:13px;font-weight:700;color:{vol_c}">{vol_label}</div>'
                f'    <div style="font-size:10px;color:{TXT_MUT};margin-top:2px">{vol_desc}</div>'
                f'  </div>'
                f'</div>'

                # Métricas
                f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px">'
                f'  <div style="background:{BG_HEAD};border-radius:8px;padding:8px;text-align:center">'
                f'    <div style="font-size:10px;color:{TXT_MUT}">Días alcistas</div>'
                f'    <div style="font-size:20px;font-weight:800;color:{dias_c}">{r["Dias_Alcistas"]}</div></div>'
                f'  <div style="background:{BG_HEAD};border-radius:8px;padding:8px;text-align:center">'
                f'    <div style="font-size:10px;color:{TXT_MUT}">Momentum 3d</div>'
                f'    <div style="font-size:20px;font-weight:800;color:{mom_c}">+{r["Momentum_3d"]:.1f}%</div></div>'
                f'  <div style="background:{BG_HEAD};border-radius:8px;padding:8px;text-align:center">'
                f'    <div style="font-size:10px;color:{TXT_MUT}">RSI actual</div>'
                f'    <div style="font-size:20px;font-weight:800;color:{rsi_c}">{r["RSI"]:.0f} ↑</div></div>'
                f'  <div style="background:{BG_HEAD};border-radius:8px;padding:8px;text-align:center">'
                f'    <div style="font-size:10px;color:{TXT_MUT}">DD desde pico</div>'
                f'    <div style="font-size:18px;font-weight:700;color:{R}">{r["DD_pico"]:.0f}%</div></div>'
                f'</div>'

                # Targets
                f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">'
                f'  <div style="background:{R_BG};border:1px solid {R_BOR};border-radius:8px;padding:8px">'
                f'    <div style="font-size:10px;color:{R};font-weight:700">🛑 Stop (-5%)</div>'
                f'    <div style="font-size:14px;font-weight:700;color:{R}">${r["Stop_Swing"]:.2f}</div>'
                f'    <div style="font-size:9px;color:{TXT_SOFT}">Salir si llega aquí</div></div>'
                f'  <div style="background:{A_BG};border:1px solid {A_BOR};border-radius:8px;padding:8px">'
                f'    <div style="font-size:10px;color:{A};font-weight:700">🎯 Target 1 (+8%)</div>'
                f'    <div style="font-size:14px;font-weight:700;color:{A}">${r["Target_1"]:.2f}</div>'
                f'    <div style="font-size:9px;color:{TXT_SOFT}">Vender 60%</div></div>'
                f'  <div style="background:{G_BG};border:1px solid {G_BOR};border-radius:8px;padding:8px">'
                f'    <div style="font-size:10px;color:{G};font-weight:700">🎯 Target 2 (+12%)</div>'
                f'    <div style="font-size:14px;font-weight:700;color:{G}">${r["Target_2"]:.2f}</div>'
                f'    <div style="font-size:9px;color:{TXT_SOFT}">Runner 40%</div></div>'
                f'</div>'


                # ── ARRASTRADAS Y LÍDER v16 ──────────────────────────────
                # Muestra el tren completo: líder que arrastra + siguientes vagones
                + (lambda _arr_v, _lid_v: (
                    f'<div style="background:linear-gradient(135deg,#EFF6FF,#F0FDF4);'
                    f'border:1px solid #BFDBFE;border-radius:10px;'
                    f'padding:10px 14px;margin-top:8px">'
                    f'<div style="font-size:10px;font-weight:800;color:#1D4ED8;margin-bottom:6px">'
                    f'🚂 TREN DE ARRASTRE — Estrategia Escalonada</div>'
                    + (f'<div style="font-size:10px;color:#64748B;margin-bottom:4px">'
                       f'Líder del movimiento: '
                       f'<span style="background:#7C3AED;color:white;border-radius:4px;'
                       f'padding:1px 8px;font-weight:700;font-size:11px">🏆 {_lid_v}</span>'
                       f' — ya subió, verifica si aún tiene recorrido</div>'
                       if _lid_v not in ("-","","nan") else "")
                    + (f'<div style="font-size:10px;color:#374151;margin-top:4px">'
                       f'Arrastradas (aún no subieron): '
                       + " ".join([
                           f'<span style="background:#0891B2;color:white;border-radius:4px;'
                           f'padding:2px 9px;font-weight:700;font-size:11px;margin:1px;display:inline-block">'
                           f'🔗 {a.strip()}</span>'
                           for a in _arr_v.split(",") if a.strip() and a.strip() != "-"
                       ])
                       + f'</div>'
                       f'<div style="font-size:9px;color:#6B7280;margin-top:4px;line-height:1.5">'
                       f'💡 Estrategia: si {r["Ticker"]} ya está en M3, '
                       f'busca las arrastradas en M1/M2 — entran 3-7 días después.</div>'
                       if _arr_v not in ("-","","nan") else
                       f'<div style="font-size:9px;color:#9CA3AF">'
                       f'Esta acción no arrastra otras identificadas — puede ser arrastrada por {_lid_v if _lid_v not in ("-","","nan") else "su sector"}.</div>'
                    )
                    + f'</div>'
                ) if _arr_v not in ("-","","nan") or _lid_v not in ("-","","nan") else ""
                )(str(r.get("Arrastradas","-")), str(r.get("Lider","-")))

                + f'<div style="font-size:10px;color:{TXT_MUT};margin-top:8px;'
                f'border-top:1px solid {BOR};padding-top:6px">'
                f'{r["Lectura"]}</div>'
                f'</div>', unsafe_allow_html=True)

        # ── v18: Registro candidato Swing ────────────────────
        _sw_res2 = st.session_state.get("scan_swing")
        if _sw_res2 is not None and not _sw_res2.empty:
            with st.expander("📌 Registrar candidato swing en Google Sheets", expanded=False):
                _tk_sw = st.selectbox("Ticker candidato",
                    ["— seleccionar —"] + list(_sw_res2["Ticker"].unique()),
                    key="sel_swing_tab2")
                if _tk_sw and _tk_sw != "— seleccionar —":
                    _rw = _sw_res2[_sw_res2["Ticker"]==_tk_sw].iloc[0]
                    render_boton_registro(
                        ticker=_tk_sw, fase=str(_rw.get("Fase", _rw.get("Etapa_v12", "Swing"))),
                        precio=float(_rw.get("Precio",0)),
                        score=int(_rw.get("Score_Rebote",0)),
                        prob_nbis=float(_rw.get("Prob_NBIS",0)),
                        cat_fecha=str(_rw.get("Cat_Fecha","-")),
                        arrastradas=str(_rw.get("Arrastradas","-")),
                        lider=str(_rw.get("Lider","-")),
                        opinion=str(_rw.get("Opinion_Trader", _rw.get("Lectura", "-"))),
                        key_prefix="tab2", tipo="CANDIDATO",
                        area=str(_rw.get("Area","-")),
                        rsi_ticker=float(_rw.get("RSI", 0)),
                    )

        # Exportar
        sw_export = sw_result[["Ticker","Area","Precio","RSI","Dias_Alcistas",
                                "Momentum_3d","DD_pico","Stop_Swing","Target_1","Target_2","Beta","Lectura"]]
        boton_exportar(sw_result, "Swing Activo", "exp_swing", fase_col=None, es_swing=True)
        # Noticias Swing Activo
        st.markdown("---")
        render_noticias_mini(sw_result["Ticker"].tolist(), "Noticias Swing Activo")
# ══ TAB 1 - ENTRAR HOY ══════════════════════════════════════════
with tab3:
    st.markdown(
        f'<div class="sec-header" style="background:{G_BG};border-color:{G_BOR}">'
        f'<span style="font-size:20px">🔥</span>'
        f'<div><span style="font-size:16px;font-weight:700;color:{G}">Entrar Hoy — M3 Confirmado</span>'
        f'<div style="font-size:11px;color:{TXT_MUT};margin-top:3px">'
        f'RSI 48-68 · DD ≤ -15% · Score 40-55 · Prob_NBIS 30-45% · Decisión ENTRAR o ANTICIPAR</div>'
        f'</div></div>', unsafe_allow_html=True)
    with st.expander("📋 ¿Qué busca este tab? — Reglas Entrar Hoy (M3)", expanded=False):
        st.markdown(
            "<div style='font-size:11px;line-height:1.8'>"
            "<strong style='color:#16A34A'>🔥 Tab Entrar Hoy — Señal M3 Confirmada</strong><br>"
            "Filtra las señales M3 ENTRAR/ANTICIPAR del scan Swing · con botón de scan propio.<br>"
            "<strong style='color:#EA580C'>🌡️ Banner macro:</strong> muestra SPY RSI · con SPY sobrecomprado, exigir Score MVALLE ≥ 17 antes de entrar.<br><br>"
            "<strong>✅ CRITERIOS M3 para aparecer:</strong><br>"
            "🔸 Decision: ENTRAR o ANTICIPAR (no SEGUIR/VIGILAR)<br>"
            "🔸 RSI: 35-68 · DD ≤-15% · Score ≥ 40 · Prob_NBIS ≥ 25%<br><br>"
            "<strong>⚡ SECCIÓN M2 EN FORMACIÓN (secundaria):</strong><br>"
            "RSI 40-65 · Score ≥ 38 · entrar 20-40% · esperar confirmación M3<br><br>"
            "<strong>🌡️ Lectura del banner macro:</strong><br>"
            "SPY RSI ≤65 → condiciones ideales · entrar señales ≥15pts<br>"
            "SPY RSI 65-75 → selectivo · entrar solo ≥17pts<br>"
            "SPY RSI &gt;75 → muy selectivo · solo NBIS con DD &lt;-25% y defensa<br>"
            "<strong>📐 Gestión:</strong> ENTRAR 100% · ANTICIPAR 40% · Stop -7% · T1 +8%<br>"
            "💥 M3 + CASTIGADA + MACD+ = señal más fuerte del modelo<br><br>"
            "<strong>⏱️ Vigencia actualizada (v19.2):</strong><br>"
            "M2 NBIS → <strong>10 días</strong> (antes 5d) · datos reales confirman en 6-20d<br>"
            "M2 Momentum → 5 días · funciona desde día 1 (WR 89%)<br>"
            "M3 NBIS → 14 días · Runner P&L &gt;T1 → sin vencimiento"
            "Tiene su <strong>propio botón de scan</strong> (no depende de Swing Activo).<br>"
            "Si Swing ya escaneó, reutiliza esos resultados automáticamente.<br><br>"
            "<strong>✅ CRITERIOS M3 PARA APARECER:</strong><br>"
            "🔸 Decision: <strong>ENTRAR o ANTICIPAR</strong> (no SEGUIR/VIGILAR)<br>"
            "🔸 RSI: <strong>35 - 68</strong> (rebote iniciando)<br>"
            "🔸 DD desde pico: <strong>≤ -15%</strong><br>"
            "🔸 Score técnico: <strong>≥ 40</strong><br>"
            "🔸 Prob_NBIS: <strong>≥ 25%</strong><br><br>"
            "<strong>❌ NO APARECE SI:</strong><br>"
            "🔸 Decision = SEGUIR o VIGILAR → aún en M2, esperar confirmación<br>"
            "🔸 RSI &gt; 68 → Tab ⚡ Momentum (ya es momentum, no rebote)<br>"
            "🔸 RSI &lt; 35 → muy oversold, esperar estabilización<br><br>"
            "<strong>📐 GESTIÓN:</strong><br>"
            "🔹 ENTRAR → 100% · ANTICIPAR → 40% · Stop -7% · T1 +8% · T2 +12%<br><br>"
            "<strong>💥 BADGE CASTIGADA:</strong> M3 + CASTIGADA + MACD+ = señal más fuerte<br>"
            "<strong>📈 DIV ALCISTA FUERTE</strong> + M3 = máxima convicción de rebote"
            "</div>", unsafe_allow_html=True)

    # v19 Prioridad 1: banner Tab3
    _spy_tab3 = get_spy_filtro()
    if _spy_tab3.get("mercado_sobrecomprado", False):
        st.markdown(
            f'<div style="background:#FEF2F2;border:2px solid #FCA5A5;'
            f'border-radius:10px;padding:10px 16px;margin-bottom:8px">'
            f'<strong style="color:#DC2626">🚨 SPY RSI {_spy_tab3.get("spy_rsi",0):.0f} — MERCADO EN MÁXIMOS</strong><br>'
            f'<span style="font-size:10px;color:#374151">'
            f'No se generan señales ENTRAR. Las señales se degradan a ANTICIPAR (40% posición). '
            f'Esperar que SPY RSI baje bajo 65 para volver a entradas normales.</span>'
            f'</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="info-box" style="border-left:4px solid {G}">'
        f'<strong>📊 Lógica Entrar Hoy:</strong> señales listas para ejecutar HOY. '
        f'El rebote ya inició (RSI 48-68 subiendo) · corrección real (DD ≤ -15%) · '
        f'score fresco (40-55, no tardío) · Prob ≥ 25% confirma absorción institucional.<br>'
        f'<span style="color:{G}">✅ ENTRAR</span> = posición completa · '
        f'<span style="color:{C}">⚡ ANTICIPAR</span> = 40% posición, completar si confirma mañana · '
        f'🛑 Stop -7% · ⚠️ Si Prob_NBIS < 25% → baja a SEGUIR Fase 2'
        f'</div>',
        unsafe_allow_html=True)
    # ── v15: Banner de earnings próximos críticos (NBIS/NVDA/CRWD) ──
    import datetime as _dttB
    _today_b = _dttB.date.today()
    _earn_criticos = []
    for _key in ["scan_entrar","scan_swing","scan_detectadas"]:
        _df_tmp = st.session_state.get(_key)
        if _df_tmp is not None and not _df_tmp.empty and "Cat_Fecha" in _df_tmp.columns:
            for _, _r in _df_tmp.iterrows():
                _cf3 = str(_r.get("Cat_Fecha","-"))
                if _cf3 in ("-","","nan","\u2014"): continue
                try:
                    _fc3 = _dttB.date.fromisoformat(_cf3[:10])
                    _d3  = (_fc3 - _today_b).days
                    if 1 <= _d3 <= 15:
                        _earn_criticos.append((_r["Ticker"], _d3, _cf3[:10]))
                    elif _d3 == 0:
                        _earn_criticos.append((_r["Ticker"], 0, _cf3[:10]))
                except: pass
    _earn_criticos = sorted(set(_earn_criticos), key=lambda x: x[1])[:5]
    if _earn_criticos:
        def _earn_badge_fn(tk, d):
            if d == 0:   return f'<span style="font-weight:800;color:#7C3AED">\U0001f4e3 {tk} (HOY)</span>'
            elif d <= 2: return f'<span style="font-weight:800;color:#DC2626">\U0001f6ab {tk} ({d}d)</span>'
            elif d <= 6: return f'<span style="font-weight:800;color:#D97706">\u26a0\ufe0f {tk} ({d}d)</span>'
            else:        return f'<span style="font-weight:800;color:#16A34A">\U0001f3af {tk} ({d}d)</span>'
        _earn_html = " &nbsp;\u00b7&nbsp; ".join([_earn_badge_fn(tk,d) for tk,d,_ in _earn_criticos])
        st.markdown(
            f'<div style="background:#F8FAFF;border:1px solid #BFDBFE;border-radius:10px;'
            f'padding:10px 16px;margin-bottom:10px">'
            f'<span style="font-size:11px;font-weight:700;color:#1D4ED8">\U0001f4c5 Earnings pr\u00f3ximos en se\u00f1ales activas: </span>'
            f'{_earn_html}'
            f'</div>', unsafe_allow_html=True)
    # v19.2 FIX: Entrar Hoy tiene su propio botón de scan
    # Si ya hay datos de Swing usa esos, si no escanea propio
    _banner_mercado_macro()

    _col_e1, _col_e2 = st.columns([3,1])
    with _col_e1:
        _sw_entrar = st.session_state.get("scan_swing")
        _n_entrar  = 0
        if _sw_entrar is not None and not _sw_entrar.empty:
            _mask_e = (
                _sw_entrar["Decision"].isin(["ENTRAR","ANTICIPAR"]) &
                (_sw_entrar["RSI"].apply(lambda x: float(x or 0)) >= 35) &
                (_sw_entrar["RSI"].apply(lambda x: float(x or 0)) <= 68)
            )
            _df_eh = _sw_entrar[_mask_e].copy()
            _n_entrar = len(_df_eh)
        if _n_entrar > 0:
            st.markdown(
                f'<div style="font-size:11px;color:{G};font-weight:700">'
                f'🔥 {_n_entrar} señales M3 listas · del scan Swing Activo</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="font-size:11px;color:{TXT_MUT}">'
                f'Escanea para detectar señales M3 confirmadas</div>',
                unsafe_allow_html=True)
    with _col_e2:
        _btn_scan_eh = st.button("🔥 Escanear M3", key="btn_scan_entrar_hoy",
                                  use_container_width=True,
                                  help="Escanea el universo buscando señales M3 confirmadas")

    # Ejecutar scan propio si se presiona el botón
    if _btn_scan_eh:
        render_scan_tab(
            tab_key="scan_swing",
            titulo="Scan M3",
            emoji="🔥",
            color=G, color_bg=G_BG, color_bor=G_BOR,
            desc="Escaneando M3 confirmados...",
            rsi_max=68, dd_min=-15, score_min=40,
            decisions=["ENTRAR","ANTICIPAR"],
            prob_nbis_min=25,
            default_sort="Score",
        )

    # Mostrar resultados
    _sw_entrar2 = st.session_state.get("scan_swing")
    if _sw_entrar2 is None or _sw_entrar2.empty:
        st.markdown(
            f'<div style="background:{G_BG};border:1px solid {G_BOR};border-radius:10px;'
            f'padding:24px;text-align:center;color:{TXT_MUT}">'
            f'<div style="font-size:28px;margin-bottom:8px">🔥</div>'
            f'<strong>Sin señales M3 todavía</strong><br>'
            f'<span style="font-size:11px">'
            f'Presiona "🔥 Escanear M3" arriba, o primero escanea en ⚡ Swing Activo</span>'
            f'</div>', unsafe_allow_html=True)
    else:
        # M3 confirmados (ENTRAR/ANTICIPAR)
        _mask_m3_eh = (
            _sw_entrar2["Decision"].isin(["ENTRAR","ANTICIPAR"]) &
            (_sw_entrar2["RSI"].apply(lambda x: float(x or 0)) >= 35) &
            (_sw_entrar2["RSI"].apply(lambda x: float(x or 0)) <= 68)
        )
        # M2 en formación (SEGUIR con Fase M2)
        _mask_m2_eh = (
            ~_mask_m3_eh &
            (_sw_entrar2.get("Fase", "").astype(str).str.upper().str.contains("M2|FORMACI", na=False) |
             _sw_entrar2["Decision"].isin(["SEGUIR"])) &
            (_sw_entrar2["RSI"].apply(lambda x: float(x or 0)) >= 40) &
            (_sw_entrar2["RSI"].apply(lambda x: float(x or 0)) <= 65) &
            (_sw_entrar2["Score"].apply(lambda x: float(x or 0)) >= 38)
        )
        _df_m3_eh = _sw_entrar2[_mask_m3_eh].copy()
        _df_m2_eh = _sw_entrar2[_mask_m2_eh].copy()

        if _df_m3_eh.empty and _df_m2_eh.empty:
            _total_sw = len(_sw_entrar2)
            st.markdown(
                f'<div style="background:{G_BG};border:1px solid {G_BOR};border-radius:10px;'
                f'padding:20px;text-align:center">'
                f'<div style="font-size:28px;margin-bottom:8px">⏳</div>'
                f'<strong>Sin señales de entrada en el scan actual</strong><br>'
                f'<span style="font-size:11px;color:{TXT_MUT}">'
                f'{_total_sw} señales en Swing Activo · ninguna cumple RSI 40-68 · DD≤-15% · Score≥38</span>'
                f'</div>', unsafe_allow_html=True)
        else:
            # ── M3 confirmados (100% posición) ──────────────────
            if not _df_m3_eh.empty:
                st.markdown(
                    f'<div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;'
                    f'padding:6px 14px;margin-bottom:8px;font-size:11px;font-weight:700;color:#16A34A">'
                    f'🔥 {len(_df_m3_eh)} señales M3 confirmadas — entrar 100% posición'+
                    f'</div>', unsafe_allow_html=True)
                st.session_state["scan_entrar"] = _df_m3_eh
                render_scan_tab(
                    tab_key="scan_entrar",
                    titulo="Entrar hoy",
                    emoji="🔥",
                    color=G, color_bg=G_BG, color_bor=G_BOR,
                    desc="M3 confirmados — ENTRAR/ANTICIPAR · RSI 35-68 · DD≤-15%",
                    rsi_max=68, dd_min=-15, score_min=40,
                    decisions=["ENTRAR","ANTICIPAR"],
                    prob_nbis_min=25,
                    default_sort="Score",
                )

            # ── M2 en formación (20-40% posición) ───────────────
            if not _df_m2_eh.empty:
                st.markdown(
                    f'<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;'
                    f'padding:6px 14px;margin-bottom:8px;margin-top:12px;font-size:11px;'
                    f'font-weight:700;color:#D97706">'
                    f'⚡ {len(_df_m2_eh)} señales M2 en formación — ANTICIPAR 20-40% · esperar confirmación M3'+
                    f'</div>', unsafe_allow_html=True)
                _m2_key = f"scan_m2_entrar_{hash(str(_df_m2_eh['Ticker'].tolist()))}"
                st.session_state[_m2_key] = _df_m2_eh
                render_scan_tab(
                    tab_key=_m2_key,
                    titulo="M2 en formación",
                    emoji="⚡",
                    color=A, color_bg=C_BG, color_bor=C_BOR,
                    desc="M2 — RSI 40-65 · Score≥38 · Entrar parcial 20-40%",
                    rsi_max=65, dd_min=-10, score_min=38,
                    decisions=["SEGUIR","ENTRAR","ANTICIPAR"],
                    prob_nbis_min=20,
                    default_sort="Score",
                )

    # ── v18: Registro rápido de entrada en Sheets ───────────
    _scan_e = st.session_state.get("scan_entrar")
    if _scan_e is not None and not _scan_e.empty:
        st.markdown(
            f'<div style="background:{G_BG};border:1px solid {G_BOR};border-radius:10px;'
            f'padding:12px 16px;margin-top:10px">'
            f'<div style="font-size:12px;font-weight:700;color:{G};margin-bottom:8px">'
            f'💾 Registrar entrada en Google Sheets</div>',
            unsafe_allow_html=True)
        _tk_sel_e = st.selectbox(
            "Ticker a registrar",
            options=["— seleccionar —"] + list(_scan_e["Ticker"].unique()),
            key="sel_entrada_tab3"
        )
        if _tk_sel_e and _tk_sel_e != "— seleccionar —":
            _row_e = _scan_e[_scan_e["Ticker"]==_tk_sel_e].iloc[0]
            render_boton_registro(
                ticker=_tk_sel_e,
                fase=str(_row_e.get("Etapa_v12","-")),
                precio=float(_row_e.get("Precio",0)),
                score=int(_row_e.get("Score",0)),
                prob_nbis=float(_row_e.get("Prob_NBIS",0)),
                cat_fecha=str(_row_e.get("Cat_Fecha","-")),
                arrastradas=str(_row_e.get("Arrastradas","-")),
                lider=str(_row_e.get("Lider","-")),
                opinion=str(_row_e.get("Opinion_Trader","-")),
                key_prefix="tab3", tipo="ENTRADA"
            )
        st.markdown('</div>', unsafe_allow_html=True)


# ══ TAB 4 - SYMPATHY ═══════════════════════════════════════════
# ══ TAB 5 - SYMPATHY ═════════════════════════════════════════════
with tab4:
    st.markdown(
        f'<div class="sec-header" style="background:#F5F3FF;border-color:#C4B5FD">'
        f'<span style="font-size:20px">🔗</span>'
        f'<div><span style="font-size:16px;font-weight:700;color:#7C3AED">Trenes de Arrastre</span>'
        f'<div style="font-size:11px;color:#6B7280;margin-top:2px">'
        f'Cuando el líder sube → ¿debo entrar a las arrastradas?</div>'
        f'</div></div>', unsafe_allow_html=True)

    _symp_data_t4 = leer_sympathy_sheets()

    if not _symp_data_t4:
        _symp_err  = st.session_state.get("_sympathy_error", "Sin detalle")
        _symp_id   = _get_sheet_id_from_secrets("sympathy_id")
        st.markdown(
            f'<div style="background:#FEF2F2;border:2px solid #FCA5A5;'
            f'border-radius:10px;padding:14px 18px">'
            f'<div style="font-size:13px;font-weight:700;color:#DC2626;margin-bottom:8px">'
            f'⚠️ Sin datos en GrekoTrader_Sympathy</div>'
            f'<code style="font-size:10px">'
            f'Sheet ID: {"✅ " + _symp_id[:24] if _symp_id else "❌ No encontrado"}<br>'
            f'Diagnóstico: {_symp_err.replace(" | ", chr(10))}'
            f'</code></div>', unsafe_allow_html=True)
    else:
        # Agrupar por líder
        _por_lider_t4 = {}
        for _t4k, _t4v in _symp_data_t4.items():
            _t4l = _t4v["lider"]
            if _t4l in ("-","","nan"): continue
            # v19 FIX: ignorar si el líder es la misma acción
            if str(_t4l).upper().strip() == str(_t4k).upper().strip(): continue
            _por_lider_t4.setdefault(_t4l, []).append((_t4k, _t4v))

        # Estado líderes y arrastradas en tiempo real
        with st.spinner("⚡ Calculando señales de entrada..."):
            _estados_t4    = {_l: get_lider_estado(_l) for _l in _por_lider_t4}
            _estados_arr_t4 = {}
            for _arrs in _por_lider_t4.values():
                for _atk, _ in _arrs:
                    if _atk not in _estados_arr_t4:
                        _estados_arr_t4[_atk] = get_lider_estado(_atk)

        # ── Función para obtener fase actual desde Watchlist/Swing ──
        def _get_fase_watchlist(ticker: str) -> tuple:
            """
            Busca el ticker en los datos de Watchlist, Swing y Entrar Hoy.
            Retorna (fase, decision, apto) desde los datos más recientes.
            """
            # Buscar en Watchlist primero
            _wl_df = st.session_state.get("wl_res_df")
            if _wl_df is not None and not _wl_df.empty:
                _row = _wl_df[_wl_df["Ticker"].str.upper() == ticker.upper()]
                if not _row.empty:
                    _r = _row.iloc[0]
                    return (
                        str(_r.get("Fase", "-")),
                        str(_r.get("Decision", "-")),
                        bool(_r.get("_apto_entrada", False))
                    )
            # Buscar en Swing Activo
            _sw_df = st.session_state.get("scan_swing")
            if _sw_df is not None and not _sw_df.empty:
                _row = _sw_df[_sw_df["Ticker"].str.upper() == ticker.upper()]
                if not _row.empty:
                    _r = _row.iloc[0]
                    return (str(_r.get("Etapa_v12", "-")), "SWING", True)
            # Buscar en Entrar Hoy
            _et_df = st.session_state.get("scan_entrar")
            if _et_df is not None and not _et_df.empty:
                _row = _et_df[_et_df["Ticker"].str.upper() == ticker.upper()]
                if not _row.empty:
                    return ("M3", "ENTRAR HOY", True)
            return ("-", "-", False)

        # ── Función de decisión por arrastrada ────────────
        def _decision_arrastrada(arr_estado, lider_activo):
            """Retorna (emoji, label, color, descripcion) para la arrastrada."""
            rsi  = arr_estado.get("rsi", 0)
            mom3 = arr_estado.get("mom3", 0)
            dd   = arr_estado.get("dd", 0)
            ema_ok = arr_estado.get("sobre_ema20", False)

            if not lider_activo:
                return "🚫", "NO ENTRAR", "#DC2626", "Líder débil — esperar que el tren se reactive"

            if not arr_estado:
                return "❓", "SIN DATOS", "#9CA3AF", "Sin datos de mercado"

            # Arrastrada ya subió mucho — tarde
            if rsi > 68:
                return "⏰", "TARDE", "#D97706", f"RSI {rsi:.0f} — llegaste tarde, esperar corrección"

            # Zona ideal de entrada
            if 48 <= rsi <= 65 and dd <= -5 and lider_activo:
                if mom3 > 0:
                    return "✅", "ENTRAR", "#16A34A", f"RSI {rsi:.0f} · Mom {mom3:+.1f}% · Líder activo → entrada válida"
                else:
                    return "👀", "VIGILAR", "#2563EB", f"RSI {rsi:.0f} pero sin momentum aún → esperar vela verde"

            # RSI bajo — corrección real, posible oportunidad si líder sube
            if rsi < 48 and lider_activo and dd <= -15:
                return "⚡", "OPORTUNIDAD", "#7C3AED", f"RSI {rsi:.0f} · DD {dd:.0f}% · Si líder confirma → entrada especulativa"

            # RSI bajo sin DD suficiente
            if rsi < 48:
                return "⏳", "ESPERAR", "#D97706", f"RSI {rsi:.0f} — aún débil, no ha absorbido la corrección"

            return "👀", "VIGILAR", "#2563EB", f"RSI {rsi:.0f} · Mom {mom3:+.1f}% — monitorear"

        # ── Cards por tren ─────────────────────────────────
        for _t4lider, _t4arrs in sorted(_por_lider_t4.items()):
            _le4   = _estados_t4.get(_t4lider, {})
            _ok4   = _le4.get("tren_activo", False)
            _c4    = "#16A34A" if _ok4 else "#DC2626"
            _bg4   = "#F0FDF4" if _ok4 else "#FEF2F2"
            _lbl4  = "🟢 TREN ACTIVO — buscar entradas en arrastradas" if _ok4 else "🔴 TREN DÉBIL — no entrar a arrastradas"
            _l_rsi = _le4.get("rsi", 0)
            _l_mom = _le4.get("mom3", 0)
            _l_pr  = _le4.get("precio", 0)

            # Header del tren
            st.markdown(
                f'<div style="background:{_bg4};border:2px solid {_c4}30;'
                f'border-radius:12px;padding:14px 18px;margin-bottom:14px">',
                unsafe_allow_html=True)

            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">'
                f'<span style="font-size:18px;font-weight:900;color:{_c4}">{_t4lider}</span>'
                f'<span style="background:{_c4};color:white;border-radius:6px;'
                f'padding:3px 10px;font-size:11px;font-weight:700">{_lbl4}</span>'
                f'</div>'
                f'<div style="font-size:11px;color:#374151;margin-bottom:12px;'
                f'background:white;border-radius:6px;padding:6px 12px;display:inline-block">'
                f'Precio ${_l_pr:.2f} · RSI {_l_rsi:.0f} · Momentum {_l_mom:+.1f}% · '
                f'EMA20 {"✅ respetada" if _le4.get("sobre_ema20") else "❌ rota"}'
                f'</div>', unsafe_allow_html=True)

            # Arrastradas con decisión clara
            _cols_arrs = st.columns(min(len(_t4arrs), 3))
            for _ci, (_atk4, _adata4) in enumerate(sorted(_t4arrs)):
                _ae4 = _estados_arr_t4.get(_atk4, {})
                _emoji4, _dec4, _dec_c4, _desc4 = _decision_arrastrada(_ae4, _ok4)
                _a_rsi = _ae4.get("rsi", 0)
                _a_pr  = _ae4.get("precio", 0)
                _a_dd  = _ae4.get("dd", 0)
                _a_mom = _ae4.get("mom3", 0)
                _a_vol = _ae4.get("vol_ratio", 100)
                _corr  = _adata4.get("correlacion","-")
                _nota  = _adata4.get("notas","")[:40]

                # Fase del Watchlist/Swing
                _wl_fase, _wl_dec, _wl_apto = _get_fase_watchlist(_atk4)
                _fase_colors = {
                    "M3": ("#16A34A","#F0FDF4"),
                    "M2": ("#D97706","#FFFBEB"),
                    "M1": ("#6B7280","#F9FAFB"),
                    "SWING": ("#2563EB","#EFF6FF"),
                    "ENTRAR HOY": ("#16A34A","#F0FDF4"),
                }
                _fc, _fbg = _fase_colors.get(_wl_fase, ("#9CA3AF","#F3F4F6"))
                _fase_badge = (
                    f'<span style="background:{_fbg};color:{_fc};'
                    f'border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700">'
                    f'{"✅" if _wl_apto else "👁"} WL: {_wl_fase} · {_wl_dec}</span>'
                    if _wl_fase != "-" else
                    f'<span style="background:#F3F4F6;color:#9CA3AF;'
                    f'border-radius:4px;padding:1px 6px;font-size:9px">'
                    f'👁 No en Watchlist</span>'
                )

                with _cols_arrs[_ci % 3]:
                    st.markdown(
                        f'<div style="background:white;border:2px solid {_dec_c4}50;'
                        f'border-radius:10px;padding:12px;margin-bottom:8px">'

                        # Ticker + decisión sympathy
                        f'<div style="display:flex;justify-content:space-between;margin-bottom:6px">'
                        f'<span style="font-size:16px;font-weight:800;color:{_dec_c4}">{_atk4}</span>'
                        f'<span style="background:{_dec_c4};color:white;border-radius:5px;'
                        f'padding:2px 8px;font-size:11px;font-weight:700">{_emoji4} {_dec4}</span>'
                        f'</div>'

                        # Fase del Watchlist — perspectiva técnica propia
                        f'<div style="margin-bottom:8px">{_fase_badge}</div>'

                        # Precio y RSI
                        f'<div style="font-size:13px;font-weight:700;margin-bottom:4px">'
                        f'${_a_pr:.2f}'
                        f'<span style="font-size:11px;font-weight:400;color:#6B7280;margin-left:8px">'
                        f'RSI {_a_rsi:.0f}</span></div>'

                        # DD y Momentum
                        f'<div style="font-size:10px;color:#6B7280;margin-bottom:6px">'
                        f'DD {_a_dd:.0f}% · Mom {_a_mom:+.1f}% · Vol {_a_vol}%</div>'

                        # Descripción accionable — cruzando ambas perspectivas
                        f'<div style="font-size:10px;color:{_dec_c4};font-weight:600;'
                        f'border-top:1px solid {_dec_c4}20;padding-top:6px">'
                        f'{_desc4}</div>'

                        + (f'<div style="font-size:9px;color:#9CA3AF;margin-top:4px">'
                           f'Correlación: {_corr}</div>' if _corr not in ("-","") else "")
                        + (f'<div style="font-size:9px;color:#9CA3AF">{_nota}</div>' if _nota else "")
                        # Noticia inline
                        + render_noticia_inline(_atk4, G, R, A, TXT_MUT, BOR)
                        + f'</div>', unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

with tab5:
    st.markdown(
        f'<div class="sec-header" style="background:{B_BG};border-color:{B_BOR}">'
        f'<span style="font-size:20px">🔎</span>'
        f'<div><span style="font-size:16px;font-weight:700;color:{B}">Mi Watchlist personal</span>'
        f'<span style="font-size:12px;color:{TXT_MUT};margin-left:10px">'
        f'Carga tus acciones de seguimiento  - El modelo analiza cada una bajo el patrón NBIS</span></div>'
        f'</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="info-box">Ingresa cualquier acción que quieras monitorear. '
        f'El modelo calculará su score, momento del patrón, similitud con NBIS y señal. '
        f'Si tienes internet con <code>yfinance</code> instalado, usará datos reales. '
        f'Si no, estimará a partir del precio que ingreses.</div>',
        unsafe_allow_html=True)

    # ── Instrucciones y plantilla ──────────────────────────────
    with st.expander("📋 Formato del CSV de Watchlist", expanded=False):
        st.markdown(f"""
**Columnas requeridas - solo el Ticker es obligatorio:**

| Ticker | Nombre | Area | Nota |
|--------|--------|------|------|
| TAN    | Invesco Solar ETF | Energía | Solar sector recovery |
| CROX   | Crocs Inc | Consumo | Post earnings dip |
| CNC    | Centene Corp | Salud | Healthcare turnaround |
| SOFI   | SoFi Tech | Fintech | Banking license catalyst |

- **Ticker**: obligatorio, en mayúsculas
- **Nombre**: opcional, nombre descriptivo
- **Area**: opcional, sector (Tech, Salud, Energía, Finanzas, Consumo, Industrial, Cripto/AI, Quantum, Fintech)
- **Nota**: opcional, tu tesis o razón de seguimiento

El modelo descarga el precio actual y calcula todos los indicadores automáticamente.
""")
        wl_template = pd.DataFrame({
            "Ticker":  ["TAN","CROX","CNC","OCUL","VRDN"],
            "Nombre":  ["Invesco Solar ETF","Crocs Inc","Centene Corp","Ocugen Inc","Viridian Therapeutics"],
            "Area":    ["Energía","Consumo","Salud","Biotech","Biotech"],
            "Nota":    ["Solar recovery","Post dip consumer","Healthcare turnaround",
                        "visto en X — FDA catalyst","dilución reciente — esperar absorción"],
            "Fuente":  ["Investing","Amigo","Manual","Twitter/X","Earnings"],
        })
        st.download_button(
            "⬇️ Descargar plantilla Watchlist CSV",
            wl_template.to_csv(index=False, sep=";", decimal=","),
            "watchlist_template.csv","text/csv",key="dl_wl_template")

    st.markdown(
        f'<div class="info-box">'
        f'<strong>📊 Cómo leer el Watchlist:</strong> '
        f'<span style="color:{G}">✅ APTA</span> = cumple DD≤-20% + RSI 48-65 + Score 40-55 + Prob≥25% → entrada válida · '
        f'<span style="color:{TXT_MUT}">👁 RADAR</span> = en observación, aún no cumple criterios.<br>'
        f'<strong>Fases:</strong> M1 = solo radar · M2 = fondo formando · M3 = listo para entrar · '
        f'ANTICIPAR = set-up casi listo (Prob ≥ 25% requerida)'
        f'</div>', unsafe_allow_html=True)

    # ── PANEL DE VALIDACIÓN — qué buscamos en NBIS ───────────────
    with st.expander("📋 ¿Qué busca este tab? — Reglas NBIS (Rebote)", expanded=False):
        st.markdown(
            "<div style='font-size:11px;line-height:1.8'>"
            "<strong style='color:#2563EB'>🔎 Tab Mi Watchlist — NBIS con semáforo RSI</strong><br>"
            "Lee tu Watchlist de Google Sheets y clasifica cada acción por su estado NBIS.<br>"
            "<strong style='color:#EA580C'>🌡️ Banner macro:</strong> muestra SPY RSI — "
            "ajusta tu criterio de entrada según el nivel del mercado.<br><br>"
            "<strong>✅ CRITERIOS DE ENTRADA:</strong><br>"
            "🔸 RSI: <strong>35 - 62</strong> (zona oversold o recuperación)<br>"
            "🔸 DD desde pico: <strong>-15% a -45%</strong><br>"
            "🔸 Prob_NBIS: <strong>30% - 50%</strong><br>"
            "🔸 MACD: positivo o cruzando<br>"
            "🔸 Score: <strong>40 - 55</strong><br>"
            "🔸 P/E &lt; 500x · Analistas ≥ 3<br><br>"
            "<strong>❌ NO APARECE COMO SEÑAL SI:</strong><br>"
            "🔸 RSI &gt; 65 → tiene momentum → <strong>ver Tab ⚡ Momentum</strong><br>"
            "🔸 RSI &lt; 35 → caída libre, sin suelo<br>"
            "🔸 P/E &gt; 500x → burbuja especulativa<br>"
            "🔸 Solo 1-2 analistas → riesgo short attack<br>"
            "🔸 Precio en ATH ±5%<br>"
            "🔸 Earnings el mismo día<br><br>"
            "<strong>📐 GESTIÓN:</strong> Tamaño 100% · Stop -7% · T1 +8% · T2 +12%<br><br>"
            "<strong>🔄 Semáforo RSI:</strong><br>"
            "RSI 35-62 → 🔎 Este tab (NBIS Rebote)<br>"
            "RSI 65-85 → ⚡ Tab Momentum Catalizador<br>"
            "RSI &gt; 85 → 🚫 Ninguno (muy extendido)<br><br>"
            "<strong style='color:#2563EB'>📊 DATO REAL (104 posiciones Mayo 2026):</strong><br>"
            "RSI 35-55 sin catalizador: WR 32% · prom −5.3% ← trampa de valor<br>"
            "RSI 65-82 con catalizador: WR 84% · prom +13.4% ← zona óptima del modelo<br>"
            "<strong>Semáforo actualizado:</strong> RSI 65-82 también es señal APTA (no solo 35-65)<br><br>"
            "<strong style='color:#2563EB'>💥 BADGE CASTIGADA:</strong><br>"

            "<span style='color:#D97706'>💥 CASTIGADA</span>: RSI &lt; 55 + DD &lt; -25% → acción sobrevendida<br>"
            "<span style='color:#EA580C'>⚠️ CASTIGADA</span>: RSI &lt; 62 + DD &lt; -20% → corrección real<br>"
            "Ejemplo: CRM RSI 44 · DD -45% → ⚠️ CASTIGADA · revisar si el negocio sigue bien"
            "<strong>💥 BADGE CASTIGADA en Watchlist:</strong><br>"
            "💥 CASTIGADA: RSI &lt; 55 + DD &lt; -25%<br>"
            "⚠️ CASTIGADA: RSI &lt; 62 + DD &lt; -20%<br>"
            "El badge aparece junto al ticker cuando la acción fue sobrevendida<br>"
            "Ejemplo: CRM RSI 44 · DD -45% → ⚠️ CASTIGADA · revisar fundamentos<br><br>"
            "<strong style='color:#2563EB'>📈 DIVERGENCIA RSI (v19.1):</strong><br>"
            "El indicador más usado por traders profesionales para detectar suelos<br>"
            "Precio hace mínimos más bajos · RSI hace mínimos más ALTOS → momentum bajista agotado<br>"
            "<span style='color:#065F46'>📈 DIV ALCISTA FUERTE</span>: precio -5%+ · RSI +8pts<br>"
            "<span style='color:#065F46'>📈 DIV ALCISTA</span>: señal de suelo moderada<br>"
            "ENPH Feb 2026: divergencia fuerte a $32 · 4 meses después → $64 (+100%)<br>"
            "RCAT Mayo 2026: divergencia activa a $9.50 · señal NBIS válida"
            "</div>", unsafe_allow_html=True)


    # ── v18: Cargar Watchlist desde Google Sheets (primario) ───
    _wl_sheets = leer_watchlist_sheets()
    # P5_OK = conectado exitosamente aunque session_state diga error
    _wl_diag = st.session_state.get("_wl_sheets_error","")
    _wl_sheets_ok = (_wl_sheets is not None and not _wl_sheets.empty) or "P5_OK" in _wl_diag

    if _wl_sheets_ok:
        _wl_col_ok1, _wl_col_ok2 = st.columns([4,1])
        with _wl_col_ok1:
            st.markdown(
                f'<div style="background:#F0FDF4;border:1px solid #86EFAC;'
                f'border-radius:8px;padding:7px 14px;margin-bottom:8px;font-size:11px">'
                f'✅ <strong style="color:#16A34A">GrekoTrader_Watchlist conectado</strong> — '
                f'{len(_wl_sheets)} acciones · se actualiza automáticamente'
                f'</div>', unsafe_allow_html=True)
        with _wl_col_ok2:
            _banner_mercado_macro()

    if st.button("🔄 Recargar", key="btn_reload_wl", help="Forzar recarga desde Sheets"):
                leer_watchlist_sheets.clear()
                st.rerun()
    else:
        _wl_err = st.session_state.get("_wl_sheets_error", "Sin detalle")
        _wl_id  = _get_sheet_id_from_secrets("watchlist_id")
        st.markdown(
            f'<div style="background:#FEF2F2;border:2px solid #FCA5A5;'
            f'border-radius:10px;padding:12px 16px;margin-bottom:8px">'
            f'<div style="font-size:12px;font-weight:700;color:#DC2626;margin-bottom:6px">'
            f'⚠️ GrekoTrader_Watchlist no conectado</div>'
            f'<div style="font-size:10px;color:#374151;line-height:1.8">'
            f'<strong>Sheet ID:</strong> {"✅ " + _wl_id[:20] + "..." if _wl_id else "❌ watchlist_id no encontrado en Secrets"}<br>'
            f'<strong>Diagnóstico:</strong> <code>{_wl_err}</code>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True)

    # ── Fallback: CSV upload ────────────────────────────────────
    # Solo mostrar CSV upload si Sheets NO está conectado
    if not _wl_sheets_ok:
        with st.expander("📂 Subir Watchlist CSV", expanded=True):
            st.download_button(
                "⬇️ Descargar plantilla Watchlist CSV",
                pd.DataFrame({
                    "Ticker":["NBIS","IONQ","MRNA"],
                    "Nombre":["NeuroBase AI","IonQ Inc","Moderna"],
                    "Area":["AI Infra","Quantum","Biotech"],
                    "Nota":["Líder AI infra","Quantum computing","Vacunas ARN"],
                }).to_csv(index=False, sep=";", decimal=","),
                "watchlist_template.csv","text/csv",key="dl_wl_template_csv")
            wl_file = st.file_uploader(
                "📂 Subir Watchlist CSV",
                type=["csv"],
                help="Solo el Ticker es obligatorio",
                key="wl_uploader")
    else:
        wl_file = None

    wl_df = None

    # Prioridad: 1) Google Sheets, 2) CSV subido, 3) Ejemplos
    if _wl_sheets_ok:
        wl_df = _wl_sheets.copy()
    elif wl_file:
        try:
            wl_df = pd.read_csv(wl_file)
            wl_df.columns = [c.strip() for c in wl_df.columns]
            if "Ticker" not in wl_df.columns:
                st.error("❌ El CSV debe tener al menos la columna 'Ticker'")
                wl_df = None
            else:
                wl_df["Ticker"] = wl_df["Ticker"].str.upper().str.strip().str.replace("$","")
                st.success(f"✅ CSV cargado — {len(wl_df)} acciones")
        except Exception as e:
            st.error(f"❌ Error: {e}"); wl_df = None
    else:
        st.markdown(
            f'<div class="info-box">💡 Conecta GrekoTrader_Watchlist en Sheets para carga automática. '
            f'Mostrando ejemplos mientras tanto.</div>',
            unsafe_allow_html=True)
        wl_df = pd.DataFrame({
            "Ticker": ["TAN","CROX","CNC","MSTR","SOFI"],
            "Nombre": ["Invesco Solar ETF","Crocs Inc","Centene Corp","Strategy Inc","SoFi Tech"],
            "Area":   ["Energía","Consumo","Salud","Cripto/AI","Fintech"],
            "Nota":   ["Solar recovery","Post dip","Healthcare turnaround","BTC proxy","Banking license"],
        })

    if wl_df is not None and len(wl_df) > 0:
        # Avisar de tickers externos
        tickers_wl = wl_df["Ticker"].tolist()
        ext_wl = tickers_wl  # v8: todos son externos, no hay universo fijo
        if ext_wl:
            st.info(f"🔄 Cargando datos para: {', '.join(ext_wl)} - usando yfinance si disponible...")

        # v19: auto-cargar noticias para todos los tickers del Watchlist
        _wl_tickers_news = [str(r["Ticker"]).upper() for _, r in wl_df.iterrows()]
        with st.spinner("📰 Cargando noticias..."):
            auto_cargar_noticias(_wl_tickers_news, max_tickers=15)

        # ── Analizar cada acción ────────────────────────────────
        wl_results = []
        _prob_debug_list = []
        for _, row in wl_df.iterrows():
            tk      = str(row["Ticker"]).upper()
            nombre  = str(row.get("Nombre", tk))
            area    = str(row.get("Area", "-"))
            nota    = str(row.get("Nota", "-"))

            r = get_row_for_ticker(tk, 0.0)  # precio_compra=0 -> se usará el actual
            source = r.get("_source", "universo")

            # DEBUG: capturar Prob_NBIS real que viene de fetch
            _prob_debug_list.append(f"{tk}={r.get('Prob_NBIS','?')}({type(r.get('Prob_NBIS','?')).__name__})")

            # Sobrescribir nombre/area si el usuario los dio y son más específicos
            if nombre != tk and r["Nombre"] in [tk, "-"]:
                r["Nombre"] = nombre
            if area != "-" and r["Area"] == "-":
                r["Area"] = area

            wl_results.append({**r, "Nota": nota, "_source": source})

        wl_res_df = pd.DataFrame(wl_results)
        st.session_state["wl_res_df"] = wl_res_df.copy()

        # DEBUG temporal — ver valores reales de Prob_NBIS
        st.markdown(
            f'<details style="font-size:10px;color:#6B7280;margin-bottom:6px">'
            f'<summary>🔬 Debug Prob_NBIS (click para ver)</summary>'
            f'<code>{"  ·  ".join(_prob_debug_list[:15])}</code>'
            f'</details>', unsafe_allow_html=True)

        # v18: forzar tipos numéricos preservando valores originales cuando falla
        for _num_col in ["Score","RSI","Volumen","EMA50","MACD","DD_pico","Sim_NBIS"]:
            if _num_col in wl_res_df.columns:
                wl_res_df[_num_col] = pd.to_numeric(wl_res_df[_num_col], errors="coerce").fillna(0)

        # Prob_NBIS: conversión especial — NO usar fillna(0) para no perder valores reales
        if "Prob_NBIS" in wl_res_df.columns:
            _prob_original = wl_res_df["Prob_NBIS"].copy()
            _prob_numeric  = pd.to_numeric(wl_res_df["Prob_NBIS"], errors="coerce")
            # Solo reemplazar donde la conversión funcionó (no NaN)
            _mask_ok = _prob_numeric.notna()
            wl_res_df.loc[_mask_ok, "Prob_NBIS"] = _prob_numeric[_mask_ok]
            # Para los que fallaron (NaN), calcular directamente desde Score y RSI
            _mask_fail = ~_mask_ok
            if _mask_fail.any():
                _sc_f = pd.to_numeric(wl_res_df.loc[_mask_fail, "Score"], errors="coerce").fillna(0)
                _vol_f = pd.to_numeric(wl_res_df.loc[_mask_fail, "Volumen"], errors="coerce").fillna(100)
                # prob_nbis simplificado: score*0.65 + min(vol/100*8,20) + 7
                _prob_calc = (_sc_f * 0.65 + (_vol_f/100 * 8).clip(upper=20) + 7).round(1)
                wl_res_df.loc[_mask_fail, "Prob_NBIS"] = _prob_calc
            wl_res_df["Prob_NBIS"] = wl_res_df["Prob_NBIS"].astype(float).round(1)

        # Filtrar tickers con _source='error' del display
        if "_source" in wl_res_df.columns:
            _wl_errors = wl_res_df[wl_res_df["_source"] == "error"]["Ticker"].tolist()
            wl_res_df  = wl_res_df[wl_res_df["_source"] != "error"].copy()
            if _wl_errors:
                st.caption(f"⚠️ Sin datos: {', '.join(_wl_errors)} — tickers no soportados o delistados")

        # DEBUG: tickers válidos con Prob_NBIS=0 (fuente no es error)
        if not wl_res_df.empty and "Prob_NBIS" in wl_res_df.columns:
            _prob_cero = wl_res_df[
                (wl_res_df["Prob_NBIS"] == 0) &
                (wl_res_df.get("_source", "ok") != "error")
            ][["Ticker","Score","RSI","Volumen","Decision","_source"]].copy()
            if not _prob_cero.empty:
                st.markdown(
                    f'<div style="background:#FEF9C3;border:1px solid #FCD34D;'
                    f'border-radius:8px;padding:6px 12px;font-size:10px;margin-bottom:6px">'
                    f'<strong>🔬 Debug Prob=0:</strong> {_prob_cero.to_dict("records")}'
                    f'</div>', unsafe_allow_html=True)

        # ── v18: Filtros de calidad en Watchlist (semana 27abr-08may) ──
        # Solo para la vista "ENTRAR/ANTICIPAR" — no bloquear el radar completo
        # El watchlist sigue mostrando todas las acciones
        # pero marca claramente cuáles cumplen los criterios de entrada
        if not wl_res_df.empty:
            _wl_n_total = len(wl_res_df)
            _wl_filtros = wl_res_df.copy()

            # Aplicar filtros — v19: incluir MACD > 0 (momentum real)
            if "DD_pico" in _wl_filtros.columns:
                _wl_filtros = _wl_filtros[
                    pd.to_numeric(_wl_filtros["DD_pico"], errors="coerce") <= -20
                ]
            if "RSI" in _wl_filtros.columns:
                _rsi_wl = pd.to_numeric(_wl_filtros["RSI"], errors="coerce")
                _wl_filtros = _wl_filtros[(_rsi_wl >= 48) & (_rsi_wl <= 65)]
            if "Score" in _wl_filtros.columns:
                _sc_wl = pd.to_numeric(_wl_filtros["Score"], errors="coerce")
                _wl_filtros = _wl_filtros[(_sc_wl >= 40) & (_sc_wl <= 55)]
            # v19: MACD debe ser positivo para ser APTA
            if "MACD" in _wl_filtros.columns:
                _macd_wl = pd.to_numeric(_wl_filtros["MACD"], errors="coerce")
                _wl_filtros = _wl_filtros[_macd_wl > 0]
            # v19: No marcar APTA si hay earnings hoy o mañana
            if "Cat_Fecha" in _wl_filtros.columns:
                import datetime as _dt_wlf
                _hoy_wlf = _dt_wlf.date.today()
                def _earn_ok(cf):
                    try:
                        d = (_dt_wlf.date.fromisoformat(str(cf)[:10]) - _hoy_wlf).days
                        return d > 1  # earnings en más de 1 día → ok
                    except Exception:
                        return True
                _wl_filtros = _wl_filtros[_wl_filtros["Cat_Fecha"].apply(_earn_ok)]

            _tickers_aptos = set(_wl_filtros["Ticker"].tolist()) if not _wl_filtros.empty and "Ticker" in _wl_filtros.columns else set()
            _n_aptos = len(_tickers_aptos)

            # Agregar columna que indica si cumple filtros
            wl_res_df["_apto_entrada"] = wl_res_df["Ticker"].isin(_tickers_aptos)

            if _n_aptos > 0:
                st.markdown(
                    f'<div style="background:#F0FDF4;border:2px solid #86EFAC;'
                    f'border-radius:10px;padding:10px 16px;margin-bottom:10px">'
                    f'<span style="font-weight:800;color:#16A34A;font-size:13px">'
                    f'✅ {_n_aptos} de {_wl_n_total} acciones cumplen filtros de entrada</span>'
                    f'<span style="font-size:11px;color:#374151;margin-left:10px">'
                    f'DD≤-20% · RSI 48-65 · Score 40-55 · WR histórico 80%+</span><br>'
                    f'<span style="font-size:11px;font-weight:700;color:#16A34A">'
                    f'{"  ·  ".join(sorted(_tickers_aptos))}</span>'
                    f'</div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="background:#FEF3C7;border:1px solid #FCD34D;'
                    f'border-radius:8px;padding:8px 14px;margin-bottom:8px;font-size:11px">'
                    f'<strong>⚠️ Ninguna acción del Watchlist cumple los filtros de entrada hoy</strong>'
                    f' — DD≤-20% · RSI 48-65 · Score 40-55. '
                    f'Monitorear para cuando las condiciones mejoren.</div>',
                    unsafe_allow_html=True)

        # ── Resumen por momento ─────────────────────────────────
        sm1,sm2,sm3,sm4 = st.columns(4)
        for col,dec,lbl,color in [
            (sm1,"ENTRAR","🔥 Entrar hoy",G),
            (sm2,"ANTICIPAR","⚡ Anticipar",C),
            (sm3,"SEGUIR","👀 Radar",A),
            (sm4,"OBSERVAR","📡 Seguimiento",TXT_MUT),
        ]:
            cnt = len(wl_res_df[wl_res_df["Decision"]==dec])
            with col:
                st.markdown(
                    f'<div style="background:{BG_CARD};border:1px solid {BOR};border-radius:10px;'
                    f'padding:12px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.04)">'
                    f'<div style="font-size:11px;color:{color};font-weight:700">{lbl}</div>'
                    f'<div style="font-size:28px;font-weight:800;color:{color}">{cnt}</div>'
                    f'<div style="font-size:10px;color:{TXT_MUT}">de {len(wl_res_df)}</div>'
                    f'</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

        # ── Tabla de resultados ─────────────────────────────────
        st.markdown(f'<div style="font-size:13px;font-weight:700;color:{TXT};margin-bottom:10px">Análisis del patrón NBIS - tu watchlist</div>', unsafe_allow_html=True)

        rows_html = ""
        cols_wl = ["Ticker","Area","Decision","Fase","Trigger","Precio",
                   "RSI","Volumen","EMA50","MACD","Score","Cat_Fecha",
                   "Opinion_Trader",
                   "Prob_NBIS","Sim_NBIS","Motivo","Nota","Fuente"]

        hdr_names = {
            "Ticker":"Ticker","Area":"Área","Decision":"Decisión","Fase":"Fase",
            "Trigger":"Trigger","Precio":"Precio","RSI":"RSI","Volumen":"Vol %",
            "EMA50":"vs EMA50","MACD":"MACD","Score":"Score","Cat_Fecha":"Earnings",
            "Arrastradas":"🔗 Arrastra a","Lider":"🏆 Líder","Opinion_Trader":"🦅 Opinión Trader",
            "Prob_NBIS":"Prob NBIS","Sim_NBIS":"Sim. NBIS",
            "Motivo":"Motivo","Nota":"Tu nota","Fuente":"📌 Fuente",
        }

        for _, r in (wl_res_df.sort_values("Score", ascending=False) if "Score" in wl_res_df.columns else wl_res_df).iterrows():
            source_badge_html = (
                f'<span style="background:{G_BG};color:{G};border:1px solid {G_BOR};'
                f'border-radius:3px;padding:1px 5px;font-size:9px;font-weight:700">● live</span>'
                if r.get("_source")=="yfinance" else
                f'<span style="background:{A_BG};color:{A};border:1px solid {A_BOR};'
                f'border-radius:3px;padding:1px 5px;font-size:9px;font-weight:700">⚠ est.</span>'
                if r.get("_source")=="estimado" else
                f'<span style="background:{B_BG};color:{B};border:1px solid {B_BOR};'
                f'border-radius:3px;padding:1px 5px;font-size:9px;font-weight:700">◆ modelo</span>'
            )
            dec_cls = {"ENTRAR":"bg-g","ANTICIPAR":"bg-c","SEGUIR":"bg-a",
                       "OBSERVAR":"bg-gr","REFERENCIA":"bg-p"}.get(r["Decision"],"bg-gr")
            trig_cls = ("bg-g" if "RUPTURA" in str(r["Trigger"]) else
                        "bg-c" if "PRE-SEÑAL" in str(r["Trigger"]) else
                        "bg-a" if "FONDO" in str(r["Trigger"]) else "bg-r")
            sc2 = G if r["Score"]>=75 else A if r["Score"]>=55 else R
            prob_c = G if r["Prob_NBIS"]>=75 else A if r["Prob_NBIS"]>=55 else TXT_MUT
            sim_c  = G if r["Sim_NBIS"]>=60 else A if r["Sim_NBIS"]>=40 else TXT_MUT
            # v15: Arrastradas y Lider chips para watchlist
            _arr_wl = str(r.get("Arrastradas","-"))
            _lid_wl = str(r.get("Lider","-"))
            arr_chips_wl = " ".join([
                f'<span style="background:{C_BG};color:{C};border-radius:4px;padding:1px 6px;font-size:10px;font-weight:700;border:1px solid {C_BOR}">🔗 {t.strip()}</span>'
                for t in _arr_wl.split(",") if t.strip() and t.strip() != "-"
            ]) if _arr_wl not in ("-","","nan") else f'<span style="color:{TXT_SOFT}">-</span>'
            lid_chip_wl = (f'<span style="background:{P_BG};color:{P};border-radius:4px;padding:1px 6px;font-size:10px;font-weight:700;border:1px solid {P_BOR}">🏆 {_lid_wl}</span>'
                          if _lid_wl not in ("-","","nan") else f'<span style="color:{TXT_SOFT}">-</span>')
            sec_c  = SECTOR_COLORS.get(str(r["Area"]), TXT_MUT)
            nota_str = str(r.get("Nota","-"))[:40]
            ema_v = float(r["EMA50"]) if r["EMA50"] else 0
            macd_v = float(r["MACD"]) if r["MACD"] else 0

            # v15: earnings badge en watchlist
            import datetime as _dtt2
            _cf_wl = str(r.get("Cat_Fecha","-"))
            if _cf_wl in ("-","","nan"):
                _cf_wl = get_earnings_single(str(r["Ticker"]))
            try:
                _dias_wl = (_dtt2.date.fromisoformat(_cf_wl[:10]) - _dtt2.date.today()).days
                if _dias_wl < 0:
                    earn_cell = f'<span style="color:{TXT_SOFT};font-size:10px">✅ pasado</span>'
                elif _dias_wl <= 2:
                    earn_cell = f'<span style="background:#FEF2F2;color:#DC2626;border:1px solid #FCA5A5;border-radius:5px;padding:1px 5px;font-size:10px;font-weight:800">🚫 {_dias_wl}d</span>'
                elif _dias_wl <= 6:
                    earn_cell = f'<span style="background:#FFFBEB;color:#D97706;border:1px solid #FCD34D;border-radius:5px;padding:1px 5px;font-size:10px;font-weight:700">⚠️ {_dias_wl}d</span>'
                elif _dias_wl <= 15:
                    earn_cell = f'<span style="background:#F0FDF4;color:#16A34A;border:1px solid #86EFAC;border-radius:5px;padding:1px 5px;font-size:10px;font-weight:700">🎯 {_dias_wl}d</span>'
                elif _dias_wl <= 30:
                    earn_cell = f'<span style="background:#EFF6FF;color:#2563EB;border:1px solid #BFDBFE;border-radius:5px;padding:1px 5px;font-size:10px;font-weight:700">📅 {_dias_wl}d</span>'
                else:
                    earn_cell = f'<span style="color:{TXT_MUT};font-size:10px">📅 {_cf_wl[:10]}</span>'
            except Exception:
                earn_cell = f'<span style="color:{TXT_SOFT};font-size:10px">-</span>'

            _tk_r = r['Ticker']; _area_r = r['Area']; _dec_r = r['Decision']
            # v19.1: Semáforo RSI — determina qué tab aplica
            _rsi_r_val = float(r.get('RSI', 0) or 0)
            _apto_r = r.get("_apto_entrada", False)
            _fase_r_raw = r.get('Fase', 'Fase 1')
            _fase_num = int(''.join(filter(str.isdigit, str(_fase_r_raw))) or '1')

            # RSI routing: si RSI > 65 → redirigir a Tab Momentum
            if _rsi_r_val > 85:
                _apto_badge = (
                    '<span style="background:#FEF2F2;color:#DC2626;border-radius:4px;'
                    'padding:1px 6px;font-size:9px;font-weight:700">'
                    '🚫 RSI muy alto · sin señal</span>'
                )
            elif _rsi_r_val > 65:
                _apto_badge = (
                    '<span style="background:#FFFBEB;color:#D97706;border-radius:4px;'
                    'padding:1px 6px;font-size:9px;font-weight:700">'
                    '⚡ RSI alto → ver Tab Momentum</span>'
                )
            elif _apto_r and _dec_r in ("ENTRAR",):
                _apto_badge = (
                    '<span style="background:#DCFCE7;color:#16A34A;border-radius:4px;'
                    'padding:1px 6px;font-size:9px;font-weight:800">🔥 APTA · SEÑAL ACTIVA</span>'
                )
            elif _apto_r and _dec_r in ("ANTICIPAR",):
                _apto_badge = (
                    '<span style="background:#EFF6FF;color:#2563EB;border-radius:4px;'
                    'padding:1px 6px;font-size:9px;font-weight:800">⚡ APTA · ANTICIPAR</span>'
                )
            elif _apto_r and _dec_r in ("VIGILAR",) or (_apto_r and _fase_num >= 2):
                _apto_badge = (
                    '<span style="background:#FFFBEB;color:#D97706;border-radius:4px;'
                    'padding:1px 6px;font-size:9px;font-weight:700">⏳ PERFIL OK · sin timing</span>'
                )
            elif _apto_r:
                _apto_badge = (
                    '<span style="background:#F1F5F9;color:#64748B;border-radius:4px;'
                    'padding:1px 6px;font-size:9px;font-weight:700">⏳ PERFIL OK · en radar</span>'
                )
            else:
                _apto_badge = (
                    '<span style="background:#F3F4F6;color:#9CA3AF;border-radius:4px;'
                    'padding:1px 6px;font-size:9px">👁 RADAR</span>'
                )
            _fase_r = r['Fase']; _trig_r = r['Trigger']; _precio_r = r['Precio']
            _rsi_r = r['RSI']; _vol_r2 = r['Volumen']
            _vol_color = G if _vol_r2>150 else TXT_MUT
            _ema_color = G if ema_v<-10 else A if ema_v<-5 else TXT_MUT
            _macd_color = G if macd_v>0 else R
                        # v16: pre-assign to avoid f-string quote conflict
            _r_score = r['Score']
            _r_prob_nbis = r['Prob_NBIS']
            _r_sim_nbis = r['Sim_NBIS']
            _r_motivo = r['Motivo']

            # v18: Fuente con badge de color según origen
            _fuente_raw = str(r.get("Fuente","-")).strip()
            _fuente_cfg = {
                "Twitter/X":   ("#000000","#F0F0F0","🐦"),
                "X":           ("#000000","#F0F0F0","🐦"),
                "Investing":   ("#1D4ED8","#EFF6FF","📊"),
                "Amigo":       ("#7C3AED","#F5F3FF","👥"),
                "Earnings":    ("#16A34A","#F0FDF4","📅"),
                "Manual":      ("#374151","#F9FAFB","✏️"),
                "Modelo":      ("#D97706","#FFFBEB","🦅"),
                "Swing":       ("#D97706","#FFFBEB","⚡"),
                "Watchlist":   ("#2563EB","#EFF6FF","👁"),
            }
            # Buscar coincidencia parcial
            _f_color, _f_bg, _f_icon = "#374151","#F3F4F6","📌"
            for _fk, (_fc, _fb, _fi) in _fuente_cfg.items():
                if _fk.lower() in _fuente_raw.lower():
                    _f_color, _f_bg, _f_icon = _fc, _fb, _fi
                    break
            _fuente_html = (
                f'<span style="background:{_f_bg};color:{_f_color};'
                f'border-radius:5px;padding:2px 7px;font-size:10px;font-weight:600">'
                f'{_f_icon} {_fuente_raw}</span>'
                if _fuente_raw not in ("-","","nan") else
                f'<span style="color:{TXT_SOFT};font-size:10px">—</span>'
            )

            rows_html += (
                f"<tr>"
                f"<td><strong style='color:{B};font-size:13px'>{_tk_r}</strong> {_apto_badge}"
                f"{get_badge_cartera(_tk_r, G, R, A)}"
                f"{badge_castigada(float(r.get('RSI',0) or 0), float(str(r.get('DD','0') or '0').replace('%','').replace('+','') or 0))}"
                f"{r.get('Div_Badge','')}</td>"
                f"<td><span style='color:{sec_c};font-size:11px'>{_area_r}</span></td>"
                f"<td>{badge(_dec_r,dec_cls)}</td>"
                f"<td><span style='color:{TXT_MUT};font-size:11px'>{_fase_r}</span></td>"
                f"<td>{badge(_trig_r,trig_cls)}</td>"
                f"<td><strong>${_precio_r:.2f}</strong></td>"
                f"<td><span style='color:{c_rsi(_rsi_r)};font-weight:700'>{_rsi_r}</span></td>"
                f"<td><span style='color:{_vol_color};font-weight:600'>{_vol_r2}%</span></td>"
                f"<td><span style='color:{_ema_color};font-weight:600'>{ema_v:.1f}%</span></td>"
                f"<td><span style='color:{_macd_color};font-weight:600'>{macd_v:+.2f}</span></td>"
                f"<td><span style='color:{sc2};font-weight:700'>{_r_score}</span></td>"
                f"<td>{earn_cell}</td>"
                # Arrastradas/Lider ocultos visualmente — datos en Google Sheet
                f"<td><span style='color:{prob_c};font-weight:700'>{_r_prob_nbis}</span></td>"
                f"<td><span style='color:{sim_c};font-weight:700'>{round(float(_r_sim_nbis),1)}</span></td>"
                f"<td><span style='color:{TXT_MUT};font-size:11px'>{_r_motivo}</span></td>"
                f"<td><span style='color:{B};font-style:italic'>{nota_str}</span></td>"
                f"<td>{_fuente_html}</td>"
                f"</tr>"
            )

        ths = "".join([f"<th>{hdr_names.get(c,c)}</th>" for c in cols_wl])
        st.markdown(
            f'<div class="tbl-wrap"><table class="dtbl">'
            f'<thead><tr>{ths}</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table></div>',
            unsafe_allow_html=True)

        # ── v18: Panel de contexto por ticker — noticias + comentario ──
        # Se muestra para TODAS las acciones, expandible por ticker
        st.markdown(
            f'<div style="font-size:12px;font-weight:700;color:{TXT};margin:14px 0 8px">'
            f'📰 Contexto por acción — noticias y comentario trader</div>',
            unsafe_allow_html=True)

        for _, _rwn in wl_res_df.iterrows():
            _tkn      = _rwn["Ticker"]
            _decn     = str(_rwn.get("Decision",""))
            _fasen    = str(_rwn.get("Fase",""))
            _rsin     = _rwn.get("RSI", 0)
            _probn    = _rwn.get("Prob_NBIS", 0)
            _notan    = str(_rwn.get("Nota",""))

            # Color por decisión
            _dc = G if _decn == "ENTRAR" else C if _decn == "ANTICIPAR" else TXT_MUT
            _dbg = G_BG if _decn == "ENTRAR" else C_BG if _decn == "ANTICIPAR" else "transparent"
            _dico = "🔥" if _decn == "ENTRAR" else "⚡" if _decn == "ANTICIPAR" else "👁"

            # Noticia
            _noticia_n = render_noticia_inline(_tkn, G, R, A, TXT_MUT, BOR)

            # Earnings
            _earn_n = ""
            _cat_fn = str(_rwn.get("Cat_Fecha","-"))
            if _cat_fn not in ("-","","nan"):
                try:
                    _dn = (datetime.date.fromisoformat(_cat_fn[:10]) - datetime.date.today()).days
                    if 0 <= _dn <= 14:
                        _earn_color = "#DC2626" if _dn <= 3 else "#D97706"
                        _earn_n = (f'<span style="background:#FEF2F2;color:{_earn_color};'
                                   f'border-radius:4px;padding:1px 7px;font-size:10px;'
                                   f'font-weight:700;margin-left:6px">'
                                   f'📅 Earnings {"HOY" if _dn==0 else f"en {_dn}d"}</span>')
                except Exception:
                    pass

            # Solo renderizar si hay algo que mostrar (noticia o earnings)
            if not _noticia_n and not _earn_n:
                continue

            with st.expander(
                f"{_dico} {_tkn} — RSI {_rsin:.0f} · Prob {_probn:.0f}% · {_decn}",
                expanded=(_decn in ["ENTRAR","ANTICIPAR"])
            ):
                # v19: Earnings + Noticia unificados
                _en_card_wl = render_earn_news_card(
                    _tkn, str(_rwn.get("Cat_Fecha","-")), G, R, A, TXT_MUT, BOR)
                if _en_card_wl:
                    st.markdown(_en_card_wl, unsafe_allow_html=True)
                # v19: Badge pullback en Watchlist
                _pb_wl_dd  = float(str(_rwn.get("DD_pico",0)).replace(",",".") or 0)
                _pb_wl_rsi = float(str(_rwn.get("RSI",50)).replace(",",".") or 50)
                _pb_wl_ema = float(str(_rwn.get("EMA50",0)).replace(",",".") or 0)
                _pb_wl_vol = float(str(_rwn.get("Volumen",100)).replace(",",".") or 100)
                _pb_wl_html = render_pullback_badge(
                    _tkn, _pb_wl_dd, _pb_wl_rsi, _pb_wl_ema, 0, _pb_wl_vol,
                    G, R, A, C, TXT_MUT)
                if _pb_wl_html:
                    st.markdown(_pb_wl_html, unsafe_allow_html=True)

                # v19: Price Target badge en Watchlist
                _pt_wl_html = render_price_target_badge(_tkn, 0, G, R, A, TXT_MUT)
                if _pt_wl_html:
                    st.markdown(_pt_wl_html, unsafe_allow_html=True)

                # v19: SMA 50/200 badge en Watchlist
                _sma_wl_html = render_sma_badge(_tkn, 0, TXT_MUT)
                if _sma_wl_html:
                    st.markdown(_sma_wl_html, unsafe_allow_html=True)

                if _notan and _notan not in ("-","","nan"):
                    st.markdown(
                        f'<div style="font-size:10px;color:{TXT_MUT};margin-top:4px">'
                        f'📝 {_notan}</div>', unsafe_allow_html=True)

        _wl_con_tren = wl_res_df[
            wl_res_df["Arrastradas"].apply(lambda x: str(x) not in ("-","","nan"))
            | wl_res_df["Lider"].apply(lambda x: str(x) not in ("-","","nan"))
        ] if "Arrastradas" in wl_res_df.columns else pd.DataFrame()

        if not _wl_con_tren.empty:
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#EFF6FF,#F0FDF4);'
                f'border:2px solid #BFDBFE;border-radius:14px;'
                f'padding:16px 20px;margin:12px 0">'
                f'<div style="font-size:13px;font-weight:800;color:#1D4ED8;margin-bottom:8px">'
                f'🚂 Trenes de Arrastre en tu Watchlist</div>'
                f'<div style="font-size:11px;color:#374151;margin-bottom:10px">'
                f'Acciones en tu watchlist con relación líder-arrastrada. '
                f'Entra al líder primero, luego escala en las arrastradas 3-7 días después.</div>',
                unsafe_allow_html=True)

            for _, _wt in _wl_con_tren.iterrows():
                _tk_wt  = str(_wt["Ticker"])
                _arr_wt = str(_wt.get("Arrastradas","-"))
                _lid_wt = str(_wt.get("Lider","-"))
                _dec_wt = str(_wt.get("Decision",""))
                _dec_c  = "#16A34A" if _dec_wt=="ENTRAR" else "#D97706" if _dec_wt=="ANTICIPAR" else "#2563EB"

                _arr_ch = " ".join([
                    f'<span style="background:#0891B2;color:white;border-radius:5px;'
                    f'padding:2px 8px;font-weight:700;font-size:11px">🔗 {a.strip()}</span>'
                    for a in _arr_wt.split(",") if a.strip() and a.strip() != "-"
                ]) if _arr_wt not in ("-","","nan") else ""

                _lid_ch = (f'<span style="background:#7C3AED;color:white;border-radius:5px;'
                           f'padding:2px 8px;font-weight:700;font-size:11px">🏆 {_lid_wt}</span>'
                           if _lid_wt not in ("-","","nan") else "")

                if _arr_ch or _lid_ch:
                    st.markdown(
                        f'<div style="background:white;border:1px solid #BFDBFE;'
                        f'border-radius:8px;padding:10px 14px;margin-bottom:6px">'
                        f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'
                        + (f'{_lid_ch} <span style="color:#9CA3AF;font-size:10px">→</span> ' if _lid_ch else "")
                        + f'<span style="background:{_dec_c};color:white;border-radius:5px;'
                        f'padding:2px 10px;font-weight:800;font-size:12px">{_tk_wt}</span>'
                        + (f' <span style="color:#9CA3AF;font-size:10px">arrastra →</span> {_arr_ch}' if _arr_ch else "")
                        + f'</div>'
                        f'<div style="font-size:9px;color:#6B7280;margin-top:4px">'
                        + (f'Arrastradas de {_tk_wt}: buscar en M1/M2 para entrada escalonada' if _arr_ch else
                           f'{_tk_wt} es arrastrada de {_lid_wt} — monitorear si el líder sigue subiendo')
                        + f'</div></div>',
                        unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        # ── v18: Registro entrada desde Watchlist ────────────
        if wl_res_df is not None and not wl_res_df.empty:
            st.markdown(
                f'<div style="background:{G_BG};border:1px solid {G_BOR};border-radius:10px;'
                f'padding:12px 16px;margin-top:10px">'
                f'<div style="font-size:12px;font-weight:700;color:{G};margin-bottom:8px">'
                f'💾 Registrar entrada en Google Sheets</div>',
                unsafe_allow_html=True)

            # v18: solo mostrar tickers con ENTRAR o ANTICIPAR
            _wl_candidatas = []
            _wl_dec_map = {}
            if "Decision" in wl_res_df.columns:
                _wl_aptas = wl_res_df[wl_res_df["Decision"].isin(["ENTRAR","ANTICIPAR"])]
                _wl_candidatas = _wl_aptas["Ticker"].tolist()
                _wl_dec_map = _wl_aptas.set_index("Ticker")["Decision"].to_dict()

            if not _wl_candidatas:
                st.markdown(
                    f'<div style="background:#FEF3C7;border:1px solid #FCD34D;'
                    f'border-radius:8px;padding:8px 14px;font-size:11px;color:#92400E">'
                    f'⏳ <strong>Sin señales ENTRAR o ANTICIPAR ahora.</strong> '
                    f'Espera a que alguna acción alcance esa fase. '
                    f'Solo se registran posiciones cuando el modelo tiene convicción.</div>',
                    unsafe_allow_html=True)
                _tk_wl_reg = "— seleccionar —"
            else:
                _cartera_gbl = st.session_state.get("_cartera_global_cache", {})

                # v19: solo mostrar tickers que NO están en ninguna cartera
                # Los que ya están → se manejan desde el tab de posiciones (Recompra)
                _nuevos    = [tk for tk in _wl_candidatas if tk not in _cartera_gbl]
                _en_cartera = [tk for tk in _wl_candidatas if tk in _cartera_gbl]

                # Mensaje si algunos ya están en cartera
                if _en_cartera:
                    _cart_info = []
                    for _et in _en_cartera:
                        _ep = _cartera_gbl[_et].get("pnl", 0)
                        _ec = " y ".join(_cartera_gbl[_et].get("carteras",[]))
                        _cart_info.append(f"{_et} ({_ep:+.1f}% en {_ec})")
                    st.markdown(
                        f'<div style="background:#EFF6FF;border:1px solid #BFDBFE;'
                        f'border-radius:8px;padding:6px 12px;margin-bottom:6px;font-size:10px">'
                        f'📌 <strong>Ya en cartera</strong> — {", ".join(_cart_info)}<br>'
                        f'<span style="color:#6B7280">Para recomprar, ir al tab de posiciones correspondiente.</span>'
                        f'</div>', unsafe_allow_html=True)

                if not _nuevos:
                    st.markdown(
                        f'<div style="background:#F0FDF4;border:1px solid #86EFAC;'
                        f'border-radius:8px;padding:8px 12px;font-size:11px;color:#16A34A">'
                        f'✅ Todas las acciones con señal ya están en cartera. '
                        f'Revisa los tabs de posiciones para gestión de recompra.</div>',
                        unsafe_allow_html=True)
                    _tk_wl_reg = "— seleccionar —"
                else:
                    _wl_opciones_lbl = [
                        f"{tk}  ({_wl_dec_map.get(tk,'')})"
                        for tk in _nuevos
                    ]
                    _sel_wl = st.selectbox(
                        f"Ticker a registrar — {len(_nuevos)} nuevas señales",
                        ["— seleccionar —"] + _wl_opciones_lbl,
                        key="sel_wl_reg",
                        help="Solo acciones con señal ENTRAR/ANTICIPAR que no están en ninguna cartera"
                    )
                    _tk_wl_reg = _sel_wl.split("  (")[0] if _sel_wl != "— seleccionar —" else "— seleccionar —"

            if _tk_wl_reg and _tk_wl_reg != "— seleccionar —":
                _rw_wl = wl_res_df[wl_res_df["Ticker"]==_tk_wl_reg].iloc[0]

                # v18: inputs adicionales para completar los campos del Sheet
                _wl_col1, _wl_col2, _wl_col3 = st.columns(3)
                with _wl_col1:
                    _wl_cantidad = st.number_input(
                        "Cantidad (acciones)", min_value=0.0, value=1.0,
                        step=0.1, format="%.1f", key=f"wl_cant_{_tk_wl_reg}",
                        help="Acepta decimales: ej. 23.5")
                with _wl_col2:
                    _area_detectada = str(_rw_wl.get("Area","-"))
                    _areas_opciones = ["AI Infra","Biotech","Cloud","Cripto","Solar","Consumo",
                                       "Industrial","Salud","ETF","Fintech","LatAm","Otro"]
                    _area_default   = _area_detectada if _area_detectada in _areas_opciones else "Otro"
                    _wl_area = st.selectbox(
                        "Área/Sector", _areas_opciones,
                        index=_areas_opciones.index(_area_default),
                        key=f"wl_area_{_tk_wl_reg}")
                with _wl_col3:
                    _tipos_op = ["Accion","ETF_Sectorial","ETF_Indice","ETF_Cripto"]
                    _wl_tipo = st.selectbox(
                        "Tipo", _tipos_op,
                        key=f"wl_tipo_{_tk_wl_reg}")

                _wl_notas = st.text_input(
                    "Notas (opcional)", 
                    value=st.session_state.get(f"ctx_wl_{_tk_wl_reg}",
                          st.session_state.get(f"comentario_wl_{_tk_wl_reg}",
                          str(_rw_wl.get("Nota","")))),
                    key=f"wl_notas_{_tk_wl_reg}", 
                    placeholder="Ej: sympathy de NBIS, earning próximo...")

                render_boton_registro(
                    ticker=_tk_wl_reg,
                    fase=str(_rw_wl.get("Fase","-")),
                    precio=float(_rw_wl.get("Precio",0)),
                    score=int(_rw_wl.get("Score",0)),
                    prob_nbis=float(_rw_wl.get("Prob_NBIS",0)),
                    cat_fecha=str(_rw_wl.get("Cat_Fecha","-")),
                    arrastradas=str(_rw_wl.get("Arrastradas","-")),
                    lider=str(_rw_wl.get("Lider","-")),
                    opinion=str(_rw_wl.get("Opinion_Trader","-")),
                    key_prefix="tab5", tipo="ENTRADA",
                    area=_wl_area  # v19: pasar área seleccionada
                )
                # ── Botón 🦅 Greko en Watchlist ──────────────
                _wl_tk_g = str(_rw_wl.get("Ticker",""))

                # Mostrar SPY RSI actual antes de guardar
                _spy_prev = st.session_state.get("mercado_data",{}).get("spy",{}).get("rsi",0)
                if _spy_prev and float(_spy_prev) > 0:
                    _spy_color = "#16A34A" if float(_spy_prev) >= 55 else "#D97706" if float(_spy_prev) >= 45 else "#DC2626"
                    st.markdown(
                        f'<div style="font-size:10px;color:{TXT_MUT};margin-bottom:4px">'
                        f'📊 SPY RSI al guardar: <strong style="color:{_spy_color}">'
                        f'{round(float(_spy_prev),1)}</strong> — se guardará en columna SPY_RSI_Dia</div>',
                        unsafe_allow_html=True)
                else:
                    st.caption("⚠️ SPY RSI no disponible en sesión — se calculará al guardar")

                if st.button(f"🦅 Agregar a Posiciones Greko",
                             key=f"btn_greko_wl_{_wl_tk_g}",
                             use_container_width=True,
                             help="Paper trading — registra para validar el modelo"):
                    # v19.1: calcular datos técnicos actuales para nuevas columnas
                    _rsi_wl   = float(_rw_wl.get("RSI", st.session_state.get(f"_rsi_{_wl_tk_g}", 0)) or 0)
                    _macd_wl  = "+" if float(_rw_wl.get("MACD",0) or 0) > 0 else "-"
                    _dd_wl    = float(_rw_wl.get("DD",0) or 0)
                    # Tipo_Señal: NBIS si RSI<65, Momentum si RSI≥65
                    _tipo_sen_wl = "Momentum" if _rsi_wl >= 65 else "NBIS"
                    if str(_rw_wl.get("Arrastradas","-")) not in ("-","","nan"):
                        _tipo_sen_wl = "Momentum"  # Sympathy = siempre Momentum

                    _ok_wg, _msg_wg = escribir_greko_sheets(
                        ticker=_wl_tk_g,
                        precio_compra=float(_rw_wl.get("Precio",0)),
                        fase=str(_rw_wl.get("Fase","")),
                        score=int(_rw_wl.get("Score",0)),
                        prob_nbis=float(_rw_wl.get("Prob_NBIS",0)),
                        area=_wl_area,
                        tipo=_wl_tipo,
                        fuente="Watchlist",
                        arrastradas=str(_rw_wl.get("Arrastradas","-")),
                        opinion=str(_rw_wl.get("Opinion_Trader","-")),
                        cantidad=_wl_cantidad,
                        notas=_wl_notas,
                        rsi_ticker=_rsi_wl,
                        rsi_accion=_rsi_wl,
                        macd_estado=_macd_wl,
                        dd_pico_pct=_dd_wl,
                        tipo_senal=_tipo_sen_wl,
                    )
                    if _ok_wg:
                        st.success(_msg_wg)
                        # v19: solo invalidar cartera global (lo mínimo necesario)
                        # NO limpiar todo el caché — evita recargar 147 tickers
                        st.session_state.pop("_cartera_global_cache", None)
                        st.session_state.pop("_cartera_global_ts", None)
                        # Actualizar lista local de candidatas para el selectbox
                        # sin necesidad de recargar toda la app
                        st.session_state["_wl_just_saved"] = _wl_tk_g
                    else:
                        st.error(_msg_wg)
            st.markdown('</div>', unsafe_allow_html=True)
        # v19.2 FIX: mostrar TODAS las aptas (incluyendo M2/Fase 2 que tienen Decision=SEGUIR)
        # No solo ENTRAR/ANTICIPAR — si pasó los filtros técnicos debe aparecer aquí
        _mask_entrar = (
            wl_res_df["Decision"].isin(["ENTRAR","ANTICIPAR"]) |
            wl_res_df.get("_apto_entrada", pd.Series(False, index=wl_res_df.index))
        )
        wl_entrar = wl_res_df[_mask_entrar].sort_values("Score",ascending=False) if "Score" in wl_res_df.columns else wl_res_df[_mask_entrar]
        if not wl_entrar.empty:
            st.markdown(
                f'<div style="font-size:13px;font-weight:700;color:{G};margin:16px 0 10px">'
                f'✅ Oportunidades detectadas — {len(wl_entrar)} acciones listas</div>',
                unsafe_allow_html=True)
            for _, r in wl_entrar.iterrows():
                sc2       = G if r["Score"] >= 75 else A
                dec_color = G if r["Decision"] == "ENTRAR" else C
                dec_bg    = G_BG if r["Decision"] == "ENTRAR" else C_BG
                dec_bor   = G_BOR if r["Decision"] == "ENTRAR" else C_BOR
                _wl_tk_e  = r["Ticker"]
                _wl_nota  = str(r.get("Nota",""))[:60]
                _cat_fe   = str(r.get("Cat_Fecha","-"))
                _cat_desc = str(r.get("Cat_Desc","-"))

                # Earnings próximos
                _earn_badge = ""
                if _cat_fe not in ("-","","nan"):
                    try:
                        import datetime as _dte
                        _dias_earn = (datetime.date.fromisoformat(_cat_fe[:10]) - datetime.date.today()).days
                        if 0 <= _dias_earn <= 3:
                            _earn_badge = f'<span style="background:#FEF2F2;color:#DC2626;border-radius:4px;padding:2px 7px;font-size:10px;font-weight:700">🚨 Earnings en {_dias_earn}d</span>'
                        elif 4 <= _dias_earn <= 14:
                            _earn_badge = f'<span style="background:#FFFBEB;color:#D97706;border-radius:4px;padding:2px 7px;font-size:10px;font-weight:700">📅 Earnings en {_dias_earn}d</span>'
                    except Exception:
                        pass

                # Noticia inline
                _noticia_wl = render_noticia_inline(_wl_tk_e, G, R, A, TXT_MUT, BOR)

                # Card principal
                st.markdown(
                    f'<div style="background:{dec_bg};border:1px solid {dec_bor};'
                    f'border-left:4px solid {dec_color};border-radius:10px;'
                    f'padding:12px 16px;margin-bottom:4px">'
                    f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:6px">'
                    f'<span style="font-size:18px;font-weight:800;color:{B}">{_wl_tk_e}</span>'
                    f'<span style="font-size:11px;color:{TXT_MUT}">{r["Nombre"]}</span>'
                    f'{badge(r["Decision"], dec_cls)}'
                    f'<span style="font-size:12px;font-weight:700;color:{sc2}">Score {r["Score"]}/100</span>'
                    f'<span style="font-size:11px;color:{TXT_MUT}">RSI <strong>{r["RSI"]}</strong></span>'
                    f'<span style="font-size:11px;color:{TXT_MUT}">Prob <strong style="color:{G}">{r["Prob_NBIS"]}%</strong></span>'
                    f'{" " + _earn_badge if _earn_badge else ""}'
                    f'</div>'
                    + (f'<div style="font-size:10px;color:{TXT_MUT};margin-bottom:4px">📝 {_wl_nota}</div>' if _wl_nota and _wl_nota != "-" else "")
                    + (_noticia_wl if _noticia_wl else "")
                    + f'</div>',
                    unsafe_allow_html=True)

        # ── Exportar resultados ─────────────────────────────────
        export_wl = wl_res_df[[
            "Ticker","Nombre","Area","Precio","RSI","Volumen","EMA50","MACD",
            "Score","Decision","Fase","Prob_NBIS","Sim_NBIS","Motivo","Lectura"
        ]].copy()
        export_wl["Nota"] = wl_res_df.get("Nota","-")
        st.download_button(
            "⬇️ Exportar análisis de watchlist (CSV)",
            df_to_csv_chile(export_wl),
            "watchlist_analisis.csv","text/csv",
            key="dl_wl_export")


# ══ TAB 6 - MIS POSICIONES ═════════════════════════════════════
# ══ TAB 7 - MIS POSICIONES ═════════════════════════════════════
with tab_posiciones:
    # ═══ v19.1: Tab Posiciones Unificado ════════════════════════════
    # Selector de cartera — reemplaza 3 tabs separados
    _col_sel1, _col_sel2, _col_sel3 = st.columns([2,1,1])
    with _col_sel1:
        _cartera_nombre = st.selectbox(
            "📂 Seleccionar cartera",
            list(CARTERAS.keys()),
            key="cartera_activa_sel",
            label_visibility="collapsed",
        )
    _cfg_cartera = CARTERAS[_cartera_nombre]
    _SHEET_ACTIVO      = _cfg_cartera["sheet"]
    _COLOR_CARTERA     = _cfg_cartera["color"]
    _COLOR_BG_CARTERA  = _cfg_cartera["color_bg"]
    _EMOJI_CARTERA     = _cfg_cartera["emoji"]
    _CACHE_DF_KEY      = _cfg_cartera["cache_df"]
    _CACHE_BATCH_KEY   = _cfg_cartera["cache_batch"]
    _CACHE_TS_KEY      = _cfg_cartera["cache_ts"]

    # Header dinámico según cartera seleccionada
    _nombres_cartera = {
        "🦅 Greko":    ("Posiciones Greko", "Paper Trading del modelo"),
        "📈 MVALLE":   ("Posiciones MVALLE", "Dinero real — Mauri"),
        "💜 Amparito": ("Posiciones Amparito", "Dinero real — Amparito"),
    }
    _h1, _h2 = _nombres_cartera.get(_cartera_nombre, ("Posiciones",""))
    st.markdown(
        f'<div class="sec-header" style="background:{_COLOR_BG_CARTERA};border-color:{_COLOR_CARTERA}44">'
        f'<span style="font-size:20px">{_EMOJI_CARTERA}</span>'
        f'<div><span style="font-size:16px;font-weight:700;color:{_COLOR_CARTERA}">{_h1}</span>'
        f'<span style="font-size:12px;color:{TXT_MUT};margin-left:10px">{_h2}</span>'
        f'</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="sec-header" style="background:#F5F3FF;border-color:#C4B5FD"><span style="font-size:20px">🦅</span><div><span style="font-size:16px;font-weight:700;color:#7C3AED">Posiciones Greko — Paper Trading</span><span style="font-size:12px;color:{TXT_MUT};margin-left:10px">Carga tu CSV  - señales de salida  - Prob. NBIS  - Similitud</span></div></div>',unsafe_allow_html=True)

    # ── Instrucciones CSV ──────────────────────────────────
    with st.expander("📋 Formato del CSV - cómo preparar el archivo", expanded=False):
        st.markdown("""
**El CSV debe tener exactamente estas 4 columnas (en cualquier orden):**

| Ticker | Fecha_Compra | Precio_Compra | Cantidad |
|--------|-------------|--------------|----------|
| NBIS   | 2026-03-10  | 92.00        | 50       |
| RGTI   | 2026-02-15  | 12.50        | 200      |
| HOOD   | 2026-03-20  | 71.00        | 80       |

- **Ticker**: debe coincidir con los tickers del universo del modelo
- **Fecha_Compra**: formato YYYY-MM-DD
- **Precio_Compra**: precio en USD con decimales (usar punto, no coma)
- **Cantidad**: número entero de acciones

También puedes descargar la plantilla de abajo y completarla.
""")
        # Plantilla descargable
        template_df = pd.DataFrame({
            "Ticker":["NBIS","RGTI","HOOD","APLD"],
            "Fecha_Compra":["2026-03-10","2026-02-15","2026-03-20","2026-03-05"],
            "Precio_Compra":[92.00,12.50,71.00,18.50],
            "Cantidad":[50,200,80,150],
        })
        csv_template = template_df.to_csv(index=False, sep=";", decimal=",")
        st.download_button(
            "⬇️ Descargar plantilla CSV",
            csv_template,
            "posiciones_template.csv",
            "text/csv",
            key="dl_template_g",
        )

    # ── v18: Cargar posiciones VIVAS desde Google Sheets ───────
    st.markdown(
        f'<div class="info-box" style="border-left:4px solid #7C3AED;background:#F5F3FF">'
        f'<strong>📊 Paper Trading / Modelo en Papel:</strong> '
        f'posiciones registradas para validar señales del modelo sin dinero real. '
        f'Cada card muestra señal de salida según reglas: '
        f'Stop -7% · T1 +8% (55%) · T2 +15% (runner) · alerta día 7 · alerta día 10.<br>'
        f'<span style="color:#7C3AED">⚡ Alerta día 7</span> = ventana óptima de salida (IONQ +24.9% día 9, RUN +26.5% día 8) · '
        f'🔗 Panel Sympathy activo si el ticker tiene líder definido en GrekoTrader_Sympathy'
        f'</div>', unsafe_allow_html=True)
    # v19: Checkboxes PRIMERO — antes del cache para que el filtro los lea correctamente
    _cg1, _cg2, _cg3 = st.columns([1,1,2])
    with _cg1:
        _ck_act_greko = st.checkbox("✅ Activas", value=True, key="ck_act_pos")
    with _cg2:
        _ck_cer_greko = st.checkbox("🏁 Cerradas", value=False, key="ck_cer_pos")
    if _ck_act_greko and _ck_cer_greko:
        st.session_state["filtro_pos_activa"] = "ambas"
    elif _ck_cer_greko:
        st.session_state["filtro_pos_activa"] = "cerradas"
    else:
        st.session_state["filtro_pos_activa"] = "activas"

    # v19 FIX SPEED: cachear Sheet + batch precios para no repetir en cada cambio de checkbox
    _GREKO_CACHE_TTL = 300  # 5 minutos
    import time as _time_gc
    _greko_cache_ts  = st.session_state.get(_CACHE_TS_KEY, 0)
    _greko_cache_age = _time_gc.time() - _greko_cache_ts

    if (_CACHE_DF_KEY not in st.session_state or
        _CACHE_BATCH_KEY not in st.session_state or
        _greko_cache_age > _GREKO_CACHE_TTL):
        # Recargar solo si caché expiró o no existe
        _sheets_greko_p = leer_posiciones_sheets(_SHEET_ACTIVO)
        st.session_state[_CACHE_DF_KEY]    = _sheets_greko_p
        st.session_state[_CACHE_BATCH_KEY] = {}  # se llena más abajo
        st.session_state[_CACHE_TS_KEY]    = _time_gc.time()
    else:
        _sheets_greko_p = st.session_state[_CACHE_DF_KEY]
    _sheets_error = st.session_state.get("sheets_error")

    if _sheets_greko_p is not None:
        st.markdown(
            f'<div style="background:#F0FDF4;border:1px solid #86EFAC;'
            f'border-radius:8px;padding:8px 14px;margin-bottom:8px;font-size:11px">'
            f'<span style="font-weight:700;color:#16A34A">✅ Google Sheets conectado</span> — '
            f'{len(_sheets_greko_p)} posiciones cargadas desde <strong>{_SHEET_ACTIVO}</strong> · '
            f'Ventas y retiros persisten automáticamente.</div>',
            unsafe_allow_html=True)
    elif _sheets_error:
        # Mostrar diagnóstico específico del error
        _error_msgs = {
            "secrets_missing":
                ("⚙️ Secrets no configurados",
                 "Ve a Streamlit Cloud → Settings → Secrets y pega el bloque toml."),
            "not_found:GrekoTrader_Posiciones_Greko":
                ("📄 Sheet no encontrado",
                 f"El Sheet '{_SHEET_ACTIVO}' no existe o no está compartido. "
                 f"Compártelo con el email del service account (ver guía)."),
            "empty_sheet":
                ("📋 Sheet vacío",
                 f"El Sheet existe pero no tiene datos. Agrega tus posiciones en '{_SHEET_NAME_MAURI}'."),
            "no_data_rows":
                ("📋 Solo headers, sin posiciones",
                 f"El Sheet tiene los headers pero no hay filas de datos. "
                 f"Agrega tus posiciones bajo la fila 1."),
            "no_ticker_column":
                ("❌ Columna 'Ticker' no encontrada",
                 "El Sheet no tiene una columna llamada 'Ticker'. "
                 "Verifica que la primera fila tenga: Ticker | Precio_Compra | Cantidad | Fecha"),
        }
        _title, _detail = _error_msgs.get(
            _sheets_error,
            ("❌ Error de conexión",
             f"Error: {_sheets_error}. Verifica las credenciales y que el Sheet esté compartido.")
        )
        st.markdown(
            f'<div style="background:#FEF2F2;border:1px solid #FCA5A5;'
            f'border-radius:8px;padding:10px 14px;margin-bottom:8px">'
            f'<div style="font-size:12px;font-weight:700;color:#DC2626">'
            f'🔴 Google Sheets: {_title}</div>'
            f'<div style="font-size:11px;color:#7F1D1D;margin-top:4px">{_detail}</div>'
            f'<div style="font-size:10px;color:#991B1B;margin-top:6px">'
            f'Solución rápida: usa el CSV manual mientras resuelves la configuración.</div>'
            f'</div>', unsafe_allow_html=True)

        # Botón para limpiar cache y reintentar
        if st.button("🔄 Reintentar conexión a Google Sheets",
                     key="btn_retry_sheets_g", use_container_width=False):
            limpiar_cache_sheets_only()
            st.rerun()

        # ── DEBUG LOG — muestra exactamente dónde falla ─────
        _debug_log = st.session_state.get("sheets_debug_log", [])
        if _debug_log:
            with st.expander("🔍 Ver diagnóstico paso a paso", expanded=True):
                for step in _debug_log:
                    _ico = "✅" if step.startswith("P") and "FALLO" not in step else "❌" if "FALLO" in step else "ℹ️"
                    color = "#16A34A" if _ico == "✅" else "#DC2626" if _ico == "❌" else "#374151"
                    st.markdown(
                        f'<div style="font-size:11px;color:{color};'
                        f'font-family:monospace;padding:2px 0">{_ico} {step}</div>',
                        unsafe_allow_html=True
                    )
    else:
        st.markdown(
            f'<div style="background:#FFFBEB;border:1px solid #FCD34D;'
            f'border-radius:8px;padding:8px 14px;margin-bottom:8px;font-size:11px;color:#92400E">'
            f'⚠️ <strong>Google Sheets no configurado</strong> — usando CSV manual. '
            f'Configura los Secrets en Streamlit para persistencia.</div>',
            unsafe_allow_html=True)

    # ── Upload CSV manual (si no hay Sheets) ────────────────────
    uploaded = st.file_uploader(
        "📂 Subir archivo CSV con posiciones" + (" (opcional — ya cargado desde Sheets)" if _sheets_greko_p is not None else ""),
        type=["csv"],
        help="Formato: Ticker, Fecha_Compra, Precio_Compra, Cantidad",
        key="uploader_greko",
    )

    posiciones_greko_df = None

    # v18: usar Sheets como fuente primaria si está disponible
    if _sheets_greko_p is not None:
        posiciones_greko_df = _sheets_greko_p.copy()
        # Normalizar columnas igual que el CSV
        # v18 fix: normalizar tanto Fecha_Compra como Fecha_Entrada → Fecha
        if "Fecha_Entrada" in posiciones_greko_df.columns and "Fecha" not in posiciones_greko_df.columns:
            posiciones_greko_df = posiciones_greko_df.rename(columns={"Fecha_Entrada":"Fecha"})
        elif "Fecha_Compra" in posiciones_greko_df.columns and "Fecha" not in posiciones_greko_df.columns:
            posiciones_greko_df = posiciones_greko_df.rename(columns={"Fecha_Compra":"Fecha"})

    if uploaded:
        try:
            # Auto-detectar separador (coma o punto y coma)
            _raw_pos = uploaded.read()
            _sep_pos = ";" if b";" in _raw_pos[:200] else ","
            import io
            posiciones_greko_df = pd.read_csv(io.BytesIO(_raw_pos),
                                        sep=_sep_pos,
                                        encoding="utf-8-sig",
                                        on_bad_lines="skip")
            posiciones_greko_df.columns = [c.strip() for c in posiciones_greko_df.columns]
            if "Fecha_Compra" in posiciones_greko_df.columns and "Fecha" not in posiciones_greko_df.columns:
                posiciones_greko_df = posiciones_greko_df.rename(columns={"Fecha_Compra": "Fecha"})
            required = ["Ticker","Precio_Compra","Cantidad","Fecha"]
            missing = [c for c in required if c not in posiciones_greko_df.columns]
            if missing:
                st.error(f"❌ Columnas faltantes en el CSV: {', '.join(missing)}")
                posiciones_greko_df = _sheets_greko_p.copy() if _sheets_greko_p is not None else None
            else:
                posiciones_greko_df["Ticker"]        = posiciones_greko_df["Ticker"].str.upper().str.strip()
                posiciones_greko_df = _normalizar_precios_df(posiciones_greko_df)
                posiciones_greko_df["Cantidad"]      = pd.to_numeric(posiciones_greko_df["Cantidad"], errors="coerce")
                posiciones_greko_df = posiciones_greko_df.dropna(subset=["Precio_Compra","Cantidad"])
                # v19: auto-cargar noticias Greko
                if not posiciones_greko_df.empty:
                    auto_cargar_noticias(posiciones_greko_df["Ticker"].tolist(), max_tickers=20)
                for _fcol in ["Fecha","Cat_Fecha"]:
                    if _fcol in posiciones_greko_df.columns:
                        posiciones_greko_df[_fcol] = pd.to_datetime(
                            posiciones_greko_df[_fcol], dayfirst=True, errors="coerce"
                        ).dt.strftime("%Y-%m-%d").fillna("-")
                if "Cat_Fecha" not in posiciones_greko_df.columns:
                    posiciones_greko_df["Cat_Fecha"] = "-"
                if "Tipo" not in posiciones_greko_df.columns:
                    posiciones_greko_df["Tipo"] = "Accion"
                if "Estrategia" not in posiciones_greko_df.columns:
                    posiciones_greko_df["Estrategia"] = "Swing"
                if posiciones_greko_df["Ticker"].duplicated().any():
                    n_dup = posiciones_greko_df["Ticker"].duplicated().sum()
                    tickers_dup = posiciones_greko_df[posiciones_greko_df["Ticker"].duplicated(keep=False)]["Ticker"].unique().tolist()
                    st.info(f"ℹ️ {tickers_dup} tienen múltiples compras - se muestran como filas separadas.")
                st.success(f"✅ CSV cargado — {len(posiciones_greko_df)} posiciones encontradas")
        except Exception as e:
            st.error(f"❌ Error leyendo el CSV: {e}")
            posiciones_greko_df = _sheets_greko_p.copy() if _sheets_greko_p is not None else None
    elif _sheets_greko_p is not None:
        # ── v18 fix: usar Sheets si no hay CSV subido ─────────
        posiciones_greko_df = _sheets_greko_p.copy()  # ← asignación que faltaba
        # Normalizar columnas necesarias
        posiciones_greko_df["Ticker"]        = posiciones_greko_df["Ticker"].str.upper().str.strip()
        posiciones_greko_df = _normalizar_precios_df(posiciones_greko_df)
        posiciones_greko_df["Cantidad"]      = pd.to_numeric(posiciones_greko_df["Cantidad"], errors="coerce")
        posiciones_greko_df = posiciones_greko_df.dropna(subset=["Precio_Compra","Cantidad"])
        # v18: normalizar todos los nombres posibles de fecha
        for _fcol in ["Fecha","Cat_Fecha","Fecha_Compra","Fecha_Entrada"]:
            if _fcol in posiciones_greko_df.columns:
                posiciones_greko_df[_fcol] = pd.to_datetime(
                    posiciones_greko_df[_fcol], dayfirst=True, errors="coerce"
                ).dt.strftime("%Y-%m-%d").fillna("-")
        # Consolidar Fecha_Entrada → Fecha después de normalizar
        if "Fecha_Entrada" in posiciones_greko_df.columns and "Fecha" not in posiciones_greko_df.columns:
            posiciones_greko_df = posiciones_greko_df.rename(columns={"Fecha_Entrada":"Fecha"})
        if "Cat_Fecha" not in posiciones_greko_df.columns:
            posiciones_greko_df["Cat_Fecha"] = "-"
        if "Tipo" not in posiciones_greko_df.columns:
            posiciones_greko_df["Tipo"] = "Accion"

        # v18: mostrar tickers descartados por datos inválidos en lugar de eliminarlos silenciosamente
        _antes_drop_g = posiciones_greko_df.copy()
        posiciones_greko_df = posiciones_greko_df.dropna(subset=["Precio_Compra","Cantidad"])
        _descartados_g = _antes_drop_g[~_antes_drop_g.index.isin(posiciones_greko_df.index)]["Ticker"].tolist()
        if _descartados_g:
            st.warning(f"⚠️ {len(_descartados_g)} tickers sin Precio_Compra o Cantidad válidos en el Sheet: "
                      f"**{', '.join(_descartados_g)}** — revisa las columnas en GrekoTrader_Posiciones_Greko")
        if "Estrategia" not in posiciones_greko_df.columns:
            posiciones_greko_df["Estrategia"] = "Swing"

        # ── v19 FIX SPEED: Cachear DF procesado completo ──────────
        # El checkbox no debe recargar yfinance — solo filtra en memoria
        _greko_needs_process = (
            _CACHE_DF_KEY not in st.session_state or
            st.session_state.get(_CACHE_TS_KEY, 0) == 0 or
            (__import__('time').time() - st.session_state.get(_CACHE_TS_KEY, 0)) > 300
        )

        if _greko_needs_process:
            # ── Batch download precios ────────────────────────────
            with st.spinner("⚡ Cargando precios Greko (batch)..."):
                _tickers_greko = posiciones_greko_df["Ticker"].dropna().unique().tolist()
                _batch_precios = st.session_state.get(_CACHE_BATCH_KEY, {})
                _tickers_sin_precio = [t for t in _tickers_greko
                                       if t not in _batch_precios or _batch_precios[t] <= 0]
                if _tickers_sin_precio:
                    try:
                        import yfinance as _yf_batch
                        _batch_dl = _yf_batch.download(
                            " ".join(_tickers_sin_precio),
                            period="3mo",
                            auto_adjust=True,
                            progress=False,
                            threads=True,
                        )
                        _close_batch = _batch_dl["Close"] if "Close" in _batch_dl.columns else _batch_dl
                        for _tk_b in _tickers_sin_precio:
                            try:
                                if hasattr(_close_batch, 'columns') and _tk_b in _close_batch.columns:
                                    _pa_b = float(_close_batch[_tk_b].dropna().iloc[-1])
                                else:
                                    _pa_b = float(_close_batch.dropna().iloc[-1])
                                _batch_precios[_tk_b] = _pa_b
                            except Exception:
                                _batch_precios[_tk_b] = 0
                        st.session_state[_CACHE_BATCH_KEY] = _batch_precios
                        for _tk_b, _pa_b in _batch_precios.items():
                            if _pa_b > 0:
                                st.session_state.setdefault("_precios_live", {})[_tk_b] = _pa_b
                    except Exception:
                        pass

            for _ig, _rowg in posiciones_greko_df.iterrows():
                _tkg  = str(_rowg.get("Ticker","")).upper()
                _pcg  = float(str(_rowg.get("Precio_Compra",0) or 0).replace(",","."))
                _fchg = str(_rowg.get("Fecha_Entrada", _rowg.get("Fecha","")) or "")[:10]
                if not _tkg or _pcg <= 0:
                    continue
                # v19: excluir ETFs del scan de acciones
                if _es_etf(_tkg):
                    continue
                try:
                    import datetime as _dt_ev
                    # Precio actual desde batch (mucho más rápido)
                    _pa_ev = _batch_precios.get(_tkg, 0)
                    if _pa_ev <= 0:
                        # Fallback individual solo si batch falló
                        import yfinance as _yf_ev
                        _pa_ev = float(_yf_ev.Ticker(_tkg).fast_info.last_price or _pcg)
                    _res_ev = round((_pa_ev/_pcg-1)*100,2)
                    posiciones_greko_df.at[_ig, "Resultado_Pct"] = _res_ev

                    # Días en posición
                    try:
                        _dias_ev = (_dt_ev.date.today() - _dt_ev.date.fromisoformat(_fchg)).days
                        posiciones_greko_df.at[_ig, "Dias_En_Posicion"] = _dias_ev
                    except Exception:
                        pass

                    # Precio max/min desde entrada (para T1/T2/DD)
                    if _fchg and _fchg not in ("-","","nan"):
                        try:
                            import datetime as _dt_ev
                            _hist_ev = _yf_ev.Ticker(_tkg).history(
                                start=_fchg,
                                end=_dt_ev.date.today().strftime("%Y-%m-%d"))
                            if not _hist_ev.empty:
                                _pmax = float(_hist_ev["High"].max())
                                _pmin = float(_hist_ev["Low"].min())
                                posiciones_greko_df.at[_ig, "Precio_Max_Alcanzado"] = round(_pmax,2)
                                posiciones_greko_df.at[_ig, "DD_Max_Sufrido"]       = round((_pmin-_pcg)/_pcg*100,2)
                                posiciones_greko_df.at[_ig, "T1_Alcanzado"]  = "SÍ" if _pmax >= _pcg*1.08  else "NO"
                                posiciones_greko_df.at[_ig, "T2_Alcanzado"]  = "SÍ" if _pmax >= _pcg*1.20  else "NO"
                        except Exception:
                            pass
                except Exception:
                    pass
    else:
        # Sin Sheets ni CSV — mostrar instrucciones
        posiciones_greko_df = None
        st.markdown(
            f'<div style="background:{B_BG};border:1px solid {B_BOR};border-radius:12px;'
            f'padding:32px;text-align:center;margin-top:16px">'
            f'<div style="font-size:36px;margin-bottom:10px">💼</div>'
            f'<div style="font-size:15px;font-weight:700;color:{B};margin-bottom:8px">'
            f'Sube tu archivo CSV para ver tus posiciones</div>'
            f'<div style="font-size:12px;color:{TXT_MUT};margin-bottom:16px;line-height:1.7">'
            f'Formato requerido:<br>'
            f'<code style="background:{BG_HEAD};padding:2px 8px;border-radius:4px;font-size:11px">'
            f'Ticker, Precio_Compra, Cantidad, Fecha</code><br><br>'
            f'Ejemplo:<br>'
            f'<code style="background:{BG_HEAD};padding:4px 8px;border-radius:4px;font-size:11px;display:inline-block;text-align:left">'
            f'NBIS,129.90,3,2026-04-09<br>MRNA,42.58,15,2026-02-17<br>CROX,78.72,4,2026-02-17</code>'
            f'</div>'
            f'<div style="font-size:11px;color:{TXT_SOFT}">'
            f'Usa el botón "Browse files" del sidebar para subir tu archivo</div>'
            f'</div>', unsafe_allow_html=True)

    # ── Análisis de posiciones ──────────────────────────────
    if posiciones_greko_df is not None and len(posiciones_greko_df) > 0:
        total_inv=0; total_act=0; total_pnl=0; n_ok=0

        # Barra de progreso mientras carga tickers externos
        tickers_csv = posiciones_greko_df["Ticker"].str.upper().str.strip().tolist()
        externos = tickers_csv  # v8: todos son externos

        # ── v19.2: Detector automático de cambio de Fase ──────────
        # yf.download batch (1 llamada rápida ~8-10 seg) para todas las activas
        # Compara Fase del Sheet vs Fase calculada live
        # Si cambió → actualiza Sheet automáticamente + invalida caché Score MVALLE
        _fase_cache_key = f"_fase_live_{_SHEET_ACTIVO}"
        import time as _tfa

        # v19.2: Botón para actualizar fases y vigencias manualmente
        _col_ref1, _col_ref2 = st.columns([3,1])
        with _col_ref2:
            if st.button("🔄 Actualizar Fases", key="btn_actualizar_fases",
                         use_container_width=True,
                         help="Recorre TODAS las posiciones activas y actualiza F+AB con datos live"):
                with st.spinner("📡 Descargando precios y actualizando fases..."):
                    # Opción B: recorrer todas las posiciones y actualizar en batch
                    _sheets_to_update = [_SHEET_NAME_GREKO, _SHEET_NAME_MAURI]
                    _ok_batch, _msg_batch = actualizar_todas_fases_batch(_sheets_to_update)
                if _ok_batch:
                    st.success(f"✅ Fases actualizadas: {_msg_batch}")
                else:
                    st.error(f"⚠️ {_msg_batch}")
                # Limpiar caché local también
                st.session_state.pop(f"{_fase_cache_key}_ts", None)
                st.session_state.pop(f"{_fase_cache_key}_vigencias", None)
                st.session_state.pop(_fase_cache_key, None)
                st.rerun()

        _fase_cache_ts  = st.session_state.get(f"{_fase_cache_key}_ts", 0)
        _fase_recalc    = _tfa.time() - _fase_cache_ts > 300  # recalcular cada 5 min

        # Si no hay vigencias calculadas → forzar recálculo
        if not st.session_state.get(f"{_fase_cache_key}_vigencias"):
            _fase_recalc = True

        if _fase_recalc and externos:
            _fs_live_col = st.empty()
            _fs_live_col.info(f"🔄 Verificando fases para {len(externos)} posiciones...")
            try:
                import yfinance as _yf_fase
                _dl_fase = _yf_fase.download(
                    " ".join(externos), period="6mo",
                    auto_adjust=True, progress=False, threads=True)
                _cl_fase = _dl_fase.get("Close", _dl_fase)
                _fases_live = {}  # {ticker: fase_calculada}

                for _tk_fa in externos:
                    try:
                        _s_fa = (_cl_fase[_tk_fa].dropna()
                                 if hasattr(_cl_fase,"columns") and _tk_fa in _cl_fase.columns
                                 else _cl_fase.dropna())
                        if len(_s_fa) < 20: continue
                        _pa_fa   = float(_s_fa.iloc[-1])
                        _pico_fa = float(_s_fa.rolling(120, min_periods=1).max().iloc[-1])
                        _dd_fa   = round((_pa_fa-_pico_fa)/_pico_fa*100,1) if _pico_fa>0 else 0
                        _d_fa    = _s_fa.diff()
                        _g_fa    = _d_fa.clip(lower=0).rolling(14).mean()
                        _lo_fa   = (-_d_fa.clip(upper=0)).rolling(14).mean()
                        _rsi_fa  = round(float(100-100/(1+_g_fa.iloc[-1]/(_lo_fa.iloc[-1]+1e-9))),1)
                        _macd_fa = "+" if _s_fa.ewm(span=12).mean().iloc[-1] > _s_fa.ewm(span=26).mean().iloc[-1] else "-"

                        if 48<=_rsi_fa<=65 and _dd_fa<=-15 and _macd_fa=="+":
                            _fase_fa = "M3"
                        elif 40<=_rsi_fa<=65 and _dd_fa<=-10:
                            _fase_fa = "M2"
                        elif _rsi_fa > 65:
                            _fase_fa = "Momentum"
                        else:
                            _fase_fa = "M1"
                        _fases_live[_tk_fa] = {
                            "fase": _fase_fa, "rsi": _rsi_fa,
                            "dd": _dd_fa, "macd": _macd_fa
                        }
                    except Exception:
                        pass

                # Detectar cambios y actualizar Sheet
                _cambios_fase = []
                if "Fase" in posiciones_greko_df.columns:
                    for _idx_fa, _row_fa in posiciones_greko_df.iterrows():
                        _tk_c    = str(_row_fa.get("Ticker","")).upper().strip()
                        _fs_c    = str(_row_fa.get("Fecha_Salida","-"))
                        if _fs_c.strip() not in ("-","","nan","None","NaT"): continue  # ya cerrada
                        if _tk_c not in _fases_live: continue

                        _fase_sheet_c = str(_row_fa.get("Fase","-")).upper()
                        _fase_live_c  = _fases_live[_tk_c]["fase"]
                        _era_m3 = any(x in _fase_sheet_c for x in ["M3","FASE 3","ENTRAR","ANTICIPAR"])
                        _era_m2 = any(x in _fase_sheet_c for x in ["M2","FASE 2","ENTRADA"])

                        if _era_m2 and _fase_live_c == "M3":
                            _cambios_fase.append((_tk_c, "M2", "M3", "⬆️"))
                        elif _era_m3 and _fase_live_c in ("M2","M1"):
                            _cambios_fase.append((_tk_c, "M3", _fase_live_c, "⬇️"))
                        elif _era_m2 and _fase_live_c == "Momentum":
                            _cambios_fase.append((_tk_c, "M2", "Momentum ⚡", "⬆️"))

                st.session_state[_fase_cache_key]         = _fases_live
                st.session_state[f"{_fase_cache_key}_ts"] = _tfa.time()
                st.session_state[f"{_fase_cache_key}_cambios"] = _cambios_fase

                # v19.2: Actualizar Fase en Sheet — solo cuando es Greko
                _hoy_str = _tfa.strftime("%d-%m-%Y", _tfa.localtime())
                _msgs_fase_update = []
                if _SHEET_ACTIVO == _SHEET_NAME_GREKO:
                    for _tk_ch, _fase_ant, _fase_nv, _dir in _cambios_fase:
                        try:
                            _ok_fa, _msg_fa = actualizar_fase_en_sheet(
                                _SHEET_NAME_GREKO, _tk_ch, _fase_nv, _hoy_str)
                            _msgs_fase_update.append(
                                f"{'✅' if _ok_fa else '❌'} {_tk_ch}: {_fase_ant}→{_fase_nv}"
                                + ("" if _ok_fa else f" · {_msg_fa[:30]}"))
                        except Exception as _efa:
                            _msgs_fase_update.append(f"❌ {_tk_ch}: {str(_efa)[:40]}")

                if _msgs_fase_update:
                    st.session_state["_msgs_fase_update"] = _msgs_fase_update
                    # Limpiar caché para que recargue con datos frescos
                    st.session_state.pop("_greko_processed_df", None)
                    limpiar_cache_sheets_only()

                # Calcular vigencia para cada posición activa
                _vigencias = {}
                if "Fecha_Salida" in _df_activas.columns:
                    for _, _rv in _df_activas.iterrows():
                        _tk_v  = str(_rv.get("Ticker","")).upper().strip()
                        _pa_v  = float(_fases_live.get(_tk_v,{}).get("precio", 0) or 0)
                        _pc_v  = float(str(_rv.get("Precio_Compra","0") or "0").replace(",","."))
                        _pnl_v = round((_pa_v-_pc_v)/_pc_v*100,2) if _pc_v>0 and _pa_v>0 else 0
                        _vv    = calcular_vigencia(
                            str(_rv.get("Fecha_Entrada","-")),
                            str(_rv.get("Fecha_Cambio_Fase","-") or "-"),
                            str(_rv.get("Tipo_Señal","-")),
                            str(_rv.get("Fase","-")),
                            _pnl_v)
                        _vigencias[_tk_v] = _vv
                st.session_state[f"{_fase_cache_key}_vigencias"] = _vigencias

                # Si hubo cambios → actualizar Sheet + invalidar Score MVALLE
                if _cambios_fase:
                    st.session_state.pop("_score_rows_base", None)
                    st.session_state.pop("_greko_processed_df", None)

            except Exception as _e_fa:
                pass
            finally:
                _fs_live_col.empty()

        # Si no hay vigencias (caché frío sin batch), calcular desde Sheet solo
        if not st.session_state.get(f"{_fase_cache_key}_vigencias") and posiciones_greko_df is not None:
            _vig_from_sheet = {}
            _fs_col_vs = posiciones_greko_df.get("Fecha_Salida", pd.Series(dtype=str)).astype(str)
            _df_act_vs = posiciones_greko_df[_fs_col_vs.apply(
                lambda v: v.strip() in ("-","","nan","None","NaT"))].copy()
            for _, _rv_vs in _df_act_vs.iterrows():
                _tk_vs  = str(_rv_vs.get("Ticker","")).upper().strip()
                _pc_vs  = float(str(_rv_vs.get("Precio_Compra","0") or "0").replace(",","."))
                # Usar precio del precios_live si disponible
                _pa_vs  = float(st.session_state.get(f"_precio_{_tk_vs}", _pc_vs) or _pc_vs)
                _pnl_vs = round((_pa_vs-_pc_vs)/_pc_vs*100,2) if _pc_vs>0 and _pa_vs>0 else 0
                _vig_vs = calcular_vigencia(
                    str(_rv_vs.get("Fecha_Entrada","-")),
                    str(_rv_vs.get("Fecha_Cambio_Fase","-") or "-"),
                    str(_rv_vs.get("Tipo_Señal","-")),
                    str(_rv_vs.get("Fase","-")),
                    _pnl_vs)
                _vig_from_sheet[_tk_vs] = _vig_vs
            st.session_state[f"{_fase_cache_key}_vigencias"] = _vig_from_sheet

        # Mostrar resultados de actualización al Sheet
        _update_msgs = st.session_state.pop(f"{_fase_cache_key}_update_msgs", [])
        if _update_msgs:
            st.success("📝 Fases actualizadas en Google Sheet: " + " · ".join(_update_msgs))

        # Mostrar cambios de fase detectados
        _cambios   = st.session_state.get(f"{_fase_cache_key}_cambios", [])

        # Mostrar resultado de actualizaciones al Sheet
        _msgs_upd = st.session_state.pop("_msgs_fase_update", [])
        for _mu in _msgs_upd:
            if _mu.startswith("✅"):
                st.success(_mu)
            else:
                st.error(_mu)
        _vigencias = st.session_state.get(f"{_fase_cache_key}_vigencias", {})
        _n_vencidas = sum(1 for v in _vigencias.values() if v.get("vencida"))
        _n_runners  = sum(1 for v in _vigencias.values() if v.get("es_runner"))

        # Badge resumen de vigencia — siempre visible si hay posiciones
        if _vigencias or posiciones_greko_df is not None:
            _resumen_cols = st.columns([1,1,1])
            with _resumen_cols[0]:
                if _n_vencidas > 0:
                    st.markdown(
                        f'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;'
                        f'padding:6px 12px;text-align:center">'
                        f'<span style="font-size:11px;font-weight:800;color:#DC2626">'
                        f'🔴 {_n_vencidas} vencidas</span></div>',
                        unsafe_allow_html=True)
            with _resumen_cols[1]:
                if _n_runners > 0:
                    st.markdown(
                        f'<div style="background:#EFF6FF;border:1px solid #93C5FD;border-radius:8px;'
                        f'padding:6px 12px;text-align:center">'
                        f'<span style="font-size:11px;font-weight:800;color:#2563EB">'
                        f'🚀 {_n_runners} runners</span></div>',
                        unsafe_allow_html=True)
            with _resumen_cols[2]:
                if _n_vencidas > 0 and _SHEET_ACTIVO == _SHEET_NAME_GREKO:
                    if st.button(f"🗂️ Cerrar {_n_vencidas} vencidas",
                                 key="btn_cerrar_vencidas",
                                 type="primary",
                                 help="Cierra automáticamente las posiciones vencidas en Greko"):
                        with st.spinner("Cerrando posiciones vencidas..."):
                            _ok_cv, _msg_cv = cerrar_vencidas_greko(_SHEET_NAME_GREKO)
                        if _ok_cv:
                            st.success(_msg_cv)
                            st.session_state.pop("_greko_processed_df", None)
                            st.session_state.pop("_score_rows_base", None)
                            st.session_state.pop(f"{_fase_cache_key}_vigencias", None)
                            st.session_state.pop(f"{_fase_cache_key}_ts", None)
                            st.rerun()
                        else:
                            st.error(_msg_cv)
        if _cambios:
            _upside_c = [(t,f,n,e) for t,f,n,e in _cambios if e == "⬆️"]
            _downside_c = [(t,f,n,e) for t,f,n,e in _cambios if e == "⬇️"]
            if _upside_c:
                _up_str = " · ".join([f"**{t}** {f}→{n}" for t,f,n,_ in _upside_c])
                st.success(f"📈 Subieron de fase: {_up_str}")
            if _downside_c:
                _dn_str = " · ".join([f"**{t}** {f}→{n}" for t,f,n,_ in _downside_c])
                st.warning(f"📉 Bajaron de fase: {_dn_str}")

        if externos:
            st.info(f"🔄 Cargando datos para: {', '.join(externos)} - puede tomar unos segundos si hay internet...")

        # ── v18: Ordenar posiciones por prioridad de acción ──────
        # 1° Urgentes (stop cerca / earnings próximos)
        # 2° Ganadoras con piramidación
        # 3° Ganadoras en tendencia
        # 4° Neutras
        # 5° Pérdidas moderadas
        # 6° Pérdidas fuertes
        def _prioridad_pos(row):
            try:
                import yfinance as _yf_ord
                _pc = float(row.get("Precio_Compra", 0))
                _pa = float(_yf_ord.Ticker(str(row["Ticker"]).upper()).fast_info.last_price or _pc)
                _pnl = (_pa - _pc) / _pc * 100 if _pc > 0 else 0
                _cat = str(row.get("Cat_Fecha", "-"))
                _dias_cat = 999
                try:
                    import datetime as _dtt_ord
                    _dias_cat = (_dtt_ord.date.fromisoformat(_cat[:10]) - _dtt_ord.date.today()).days
                except Exception:
                    pass
                # Urgente: stop cerca o earnings en 1-3 días
                if _pnl <= -8 or (0 <= _dias_cat <= 3):
                    return 0
                # Ganadora con piramidación (earnings próximos)
                if _pnl >= 5 and 1 <= _dias_cat <= 15:
                    return 1
                # Ganadora en tendencia
                if _pnl >= 5:
                    return 2
                # Neutra
                if -3 <= _pnl < 5:
                    return 3
                # Pérdida moderada
                if -8 < _pnl < -3:
                    return 4
                return 5
            except Exception:
                return 3

        try:
            posiciones_greko_df = posiciones_greko_df.copy()
            posiciones_greko_df["_orden"] = posiciones_greko_df.apply(_prioridad_pos, axis=1)
            posiciones_greko_df = posiciones_greko_df.sort_values("_orden").drop(columns=["_orden"])
            posiciones_greko_df = posiciones_greko_df.reset_index(drop=True)
        except Exception:
            pass  # Si falla el sort, usar orden original

        # v19 FIX C: filtrar posiciones según checkbox
        _filtro_greko_loop = st.session_state.get("filtro_pos_activa", "activas")
        _df_pos_filtered = posiciones_greko_df.copy()
        _CERRADAS_VALS = ["-","","nan","NaT","None","nat"]
        if _filtro_greko_loop == "activas":
            _fs_mask = _df_pos_filtered.get("Fecha_Salida",
                pd.Series(["-"]*len(_df_pos_filtered))).astype(str).isin(_CERRADAS_VALS)
            # Runner activo: sin fecha salida O Cantidad_Activa > 0
            _qa_mask = pd.Series([True]*len(_df_pos_filtered), index=_df_pos_filtered.index)
            if "Cantidad_Activa" in _df_pos_filtered.columns:
                def _is_active(v):
                    try: return float(str(v).replace(",",".")) > 0
                    except: return False
                _qa_mask = _df_pos_filtered["Cantidad_Activa"].apply(_is_active)
            _df_pos_filtered = _df_pos_filtered[_fs_mask | _qa_mask]
        elif _filtro_greko_loop == "cerradas":
            _fs_mask_c = ~_df_pos_filtered.get("Fecha_Salida",
                pd.Series(["-"]*len(_df_pos_filtered))).astype(str).isin(_CERRADAS_VALS)
            _df_pos_filtered = _df_pos_filtered[_fs_mask_c]

        for _gloop_idx, (_,pos) in enumerate(_df_pos_filtered.iterrows()):
            tk  = str(pos["Ticker"]).upper()
            # v18 fix: unique key suffix per row to avoid duplicate widget keys
            _gtk_key = f"{tk}_{_gloop_idx}"
            pc  = _parse_precio(pos["Precio_Compra"])
            qty = float(str(pos["Cantidad"]).replace(",","."))  # v18: float para acciones fraccionarias
            fch = str(pos.get("Fecha_Entrada", pos.get("Fecha", pos.get("Fecha_Compra", "-"))))
            # v19: detectar si es runner (venta parcial)
            _qty_act = pos.get("Cantidad_Activa", "")
            _qty_vend = pos.get("Cantidad_Vendida", "")
            _tramos = pos.get("Tramos_Salida", "")
            _pnl_real_pct = pos.get("PnL_Realizado_Pct", "")
            try:
                _qty_act_f = float(str(_qty_act).replace(",",".")) if _qty_act else qty
                _qty_vend_f = float(str(_qty_vend).replace(",",".")) if _qty_vend else 0
                _es_runner = _qty_vend_f > 0 and _qty_act_f > 0
            except:
                _es_runner = False
                _qty_act_f = qty
                _qty_vend_f = 0

            r = get_row_for_ticker(tk, pc)
            source = r.get("_source","universo")
            pa  = r["Precio"]
            inv = pc*qty; act=pa*qty
            pnl_pct     = (pa - pc) / pc * 100 if pc > 0 else 0
            # v19 FIX C: Ganancia por acción y total correcto
            _qty_real   = float(str(_qty_act_f if _es_runner else qty))
            ganancia_x_accion = pa - pc  # diferencia por acción
            pnl_usd     = ganancia_x_accion * _qty_real  # total $ ganado/perdido
            total_inv+=inv; total_act+=act; total_pnl+=pnl_usd; n_ok+=1

            _dias_pos = (pd.Timestamp.now()-pd.to_datetime(fch,errors="coerce")).days if fch not in ("-","","nan") else 0
            # Usar Cat_Fecha del CSV si existe, sino del scanner
            _cat_fecha_csv = str(pos.get("Cat_Fecha","-")) if "Cat_Fecha" in pos else "-"
            _cat_fecha_use = _cat_fecha_csv if _cat_fecha_csv not in ("-","","nan") else str(r.get("Cat_Fecha","-"))
            _tipo_pos = str(pos.get("Tipo","Accion")) if "Tipo" in pos else "Accion"
            _estrategia_pos = str(pos.get("Estrategia","Swing")) if "Estrategia" in pos else "Swing"
            # Auto-detectar cripto ETFs por ticker si Tipo no está definido
            _crypto_etfs   = ["IBIT","ETHA","GBTC","FBTC","ETHW","BITB","ARKB","BRRR","BTCO","DEFI"]
            _index_etfs    = ["VOO","SPY","IVV","QQQ","VTI","SCHB","ITOT","VEA","VWO","AGG","BND"]
            _sector_etfs   = ["XLK","XLF","XLV","XLE","XLI","XLU","XLB","XLRE","XLC","XLP","XLY",
                               "TAN","ARKK","ARKG","ARKF","SMH","SOXX","IBB","GDX","GDXJ"]
            _latam_etfs    = ["EWZ","EWW","ILF","ARGT","ECH","GXG","EPU"]

            if _tipo_pos in ("Accion", "", "nan", "-"):
                if tk in _crypto_etfs:
                    _tipo_pos = "ETF_Cripto"
                elif tk in _index_etfs:
                    _tipo_pos = "ETF_Indice"
                elif tk in _sector_etfs:
                    _tipo_pos = "ETF_Sectorial"
                elif tk in _latam_etfs:
                    _tipo_pos = "ETF_LatAm"
                else:
                    # v19 FIX SPEED: cachear quoteType para no repetir llamada .info
                    _qt_cache_key = f"_qtype_{tk}"
                    if _qt_cache_key in st.session_state:
                        _tipo_pos = st.session_state[_qt_cache_key]
                    else:
                        try:
                            import yfinance as _yf_tipo
                            _info_tipo = _yf_tipo.Ticker(tk).info or {}
                            _qt = str(_info_tipo.get("quoteType","")).upper()
                            if _qt == "ETF":
                                _long_name = str(_info_tipo.get("longName","")).lower()
                                if any(x in _long_name for x in ["bitcoin","ethereum","crypto","blockchain"]):
                                    _tipo_pos = "ETF_Cripto"
                                elif any(x in _long_name for x in ["s&p","nasdaq","index","total market"]):
                                    _tipo_pos = "ETF_Indice"
                                else:
                                    _tipo_pos = "ETF_Sectorial"
                            st.session_state[_qt_cache_key] = _tipo_pos
                        except Exception:
                            pass
            # Score de rebote v11
            _tiene_cat = _cat_fecha_use not in ("-","","nan")
            _dias_cat  = 999
            try:
                import datetime as _dtt
                if _tiene_cat:
                    _fc = pd.to_datetime(_cat_fecha_use, errors="coerce")
                    if not pd.isna(_fc):
                        _dias_cat = (_fc.date() - _dtt.date.today()).days
            except Exception: pass
            _score_rebote = calcular_score_rebote(
                dd=float(r.get("DD_pico",0)),
                rsi=float(r["RSI"]),
                vol_ratio=float(r.get("Volumen",100)),
                dias_alcistas=0,
                momentum_3d=float(r.get("MACD",0)),
                tiene_catalizador=_tiene_cat,
                dias_para_cat=_dias_cat,
                beta=float(r.get("Beta",1.5))
            )
            _vix_val = float(vix.get("valor",20)) if vix.get("_ok") else 20
            _sizing  = clasificar_sizing(_score_rebote["score"], _vix_val)
            # v12: usar nuevas señales de salida
            # Calcular precio máximo real desde fecha de compra
            try:
                import yfinance as _yf_pm
                _hist_pm = _yf_pm.Ticker(tk).history(period="3mo")
                if not _hist_pm.empty and len(_hist_pm) > 0:
                    # Filtrar desde fecha de compra
                    _fc_pm = pd.to_datetime(_cat_fecha_use if _cat_fecha_use not in ("-","","nan") else "2026-01-01", errors="coerce")
                    try:
                        _fc_pm2 = pd.to_datetime(str(row_pos.get("Fecha","2026-01-01")), errors="coerce")
                        _hist_filtrada = _hist_pm[_hist_pm.index >= _fc_pm2] if not pd.isna(_fc_pm2) else _hist_pm
                        _precio_max = float(_hist_filtrada["High"].max()) if not _hist_filtrada.empty else max(pa, pc)
                    except Exception:
                        _precio_max = max(pa, pc * (1 + pnl_pct/100))
                else:
                    _precio_max = max(pa, pc * (1 + pnl_pct/100))
            except Exception:
                _precio_max = max(pa, pc * (1 + pnl_pct/100))
            analisis_v12 = calcular_señales_salida_v12(
                pnl_pct=pnl_pct,
                precio_compra=pc,
                precio_actual=pa,
                precio_max=_precio_max,
                dias_posicion=_dias_pos,
                estrategia=_estrategia_pos,
                tipo=_tipo_pos
            )
            analisis = analizar_posicion(
                pc,pa,r["RSI"],r["MACD"],
                abs(r["EMA50"]) if r["EMA50"]>0 else 0,
                r["Score"],pnl_pct,r["Prob_NBIS"],r["Sim_NBIS"],r["Beta"],
                cat_fecha=_cat_fecha_use,
                dias_posicion=_dias_pos,
                tipo=_tipo_pos,
                estrategia=_estrategia_pos)
            # v13: usar señales v12 como fuente principal
            # La lógica v12 tiene T1/T2/Trailing/Stop correctos
            señal    = analisis_v12["señal"]
            razon    = analisis_v12["accion"]
            s_color  = "#" + analisis_v12["color"]
            urgencia = analisis_v12["urgencia"]
            tramos   = [(t[0], t[1]) for t in analisis_v12.get("tramos", [])]

            # Solo usar analisis legacy para campos que v12 no cubre
            if urgencia == "-" or not señal:
                señal    = analisis["señal"]
                razon    = analisis["razon"]
                s_color  = analisis["color"]
                urgencia = analisis["urgencia"]
                tramos   = analisis["tramos"]

            pnl_color=G if pnl_pct>0 else R
            urg_cls={"URGENTE":"bg-r","HOY":"bg-or","ESTA SEMANA":"bg-a","AJUSTAR":"bg-a","REVISAR":"bg-r","HOLD":"bg-g","MONITOR":"bg-b"}.get(urgencia,"bg-gr")
            borde=s_color
            sec_c=SECTOR_COLORS.get(r["Area"],TXT_MUT)

            # ── Tarjeta posición ──
            st.markdown(f'<div class="pos-card" style="border-left:5px solid {borde}">',unsafe_allow_html=True)

            # Fila 1: identificación + resumen
            ci1,ci2,ci3,ci4,ci5 = st.columns([2,1,1,1,2])
            with ci1:
                # Badge Tipo (Acción/ETF) v18
                _tipo_cfg = {
                    "Accion":        ("🔷","#1D4ED8","#DBEAFE"),
                    "ETF_Indice":    ("📊","#16A34A","#F0FDF4"),
                    "ETF_Cripto":    ("₿", "#D97706","#FFFBEB"),
                    "ETF_Sectorial": ("🏭","#7C3AED","#F5F3FF"),
                    "ETF_LatAm":     ("🌎","#DC2626","#FEF2F2"),
                }
                _t_icon, _t_color, _t_bg = _tipo_cfg.get(_tipo_pos, ("🔷","#1D4ED8","#DBEAFE"))
                _tipo_badge = (f'<span style="background:{_t_bg};color:{_t_color};'
                               f'border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700">'
                               f'{_t_icon} {_tipo_pos.replace("ETF_","ETF ")}</span>')

                source_badge = ""
                if source == "yfinance":
                    source_badge = f'<span style="background:{G_BG};color:{G};border:1px solid {G_BOR};border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700;margin-left:6px">● live</span>'
                elif source == "estimado":
                    source_badge = f'<span style="background:{A_BG};color:{A};border:1px solid {A_BOR};border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700;margin-left:6px">⚠ estimado</span>'
                st.markdown(f'<div><span style="font-size:22px;font-weight:800;color:{B}">{tk}</span>{source_badge}<span style="color:{sec_c};font-size:11px;font-weight:700;margin-left:8px">{r["Area"]}</span><br>'
                    f'<span style="color:{TXT_MUT};font-size:11px">'
                    f'{"%.4g" % (_qty_act_f if _es_runner else qty)} acciones activas'
                    f'{"· " + "%.4g" % _qty_vend_f + " vendidas" if _es_runner else ""}'
                    f' · compra ${pc:.2f} · '
                    f'{"Fecha: " + str(fch)[:10] if fch not in ("-","","nan","NaT","None","nat") else "Sin fecha"}'
                    f'</span></div>',unsafe_allow_html=True)
            with ci2:
                # Determinar fuente del precio
                es_live_pos = r.get("_precio_live", False) or source == "yfinance"
                precio_badge = (
                    f'<div style="font-size:9px;color:{G};font-weight:600;margin-top:2px">● live</div>'
                    if es_live_pos else
                    f'<div style="font-size:9px;color:{A};font-weight:600;margin-top:2px">⚠ estático</div>'
                )
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:11px;color:{TXT_MUT};font-weight:600">Precio actual</div>'
                    f'<div style="font-size:20px;font-weight:800;color:{TXT}">${pa:.2f}</div>'
                    f'{precio_badge}'
                    f'</div>', unsafe_allow_html=True)
            with ci3:
                _gxa_color = G if ganancia_x_accion > 0 else R
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:11px;color:{TXT_MUT};font-weight:600">P&L</div>'
                    f'<div style="font-size:20px;font-weight:800;color:{pnl_color}">{pnl_pct:+.1f}%</div>'
                    f'<div style="font-size:11px;color:{pnl_color};font-weight:600">Ganancia $ {pnl_usd:+,.0f}</div>'
                    f'<div style="font-size:10px;color:{_gxa_color}">({ganancia_x_accion:+.2f}/acc)</div>'
                    f'</div>', unsafe_allow_html=True)
            with ci4:
                sc_c=G if _score_rebote["score"]>=75 else A if _score_rebote["score"]>=55 else R
                st.markdown(
                    f'<div style="text-align:center">'
                    f'<div style="font-size:11px;color:{TXT_MUT};font-weight:600">Score Rebote</div>'
                    f'<div style="font-size:20px;font-weight:800;color:{sc_c}">{_score_rebote["score"]}</div>'
                    f'<div style="font-size:10px;color:{sc_c}">{_score_rebote["nivel"]}</div>'
                    f'</div>',unsafe_allow_html=True)
            with ci5:
                # Barra visual de tramos
                tramo_html = ""
                for _t in tramos:
                    pct   = _t[0] if len(_t) > 0 else 0
                    etiq  = _t[1] if len(_t) > 1 else ""
                    color = _t[2] if len(_t) > 2 else (
                        R if "VENDER" in str(etiq) or "STOP" in str(etiq)
                        else G if "RUNNER" in str(etiq) or "MANT" in str(etiq)
                        else A
                    )
                    if pct > 0:
                        tramo_html += (
                            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:5px">'
                            f'<div style="width:{max(pct,8)*1.4:.0f}px;height:10px;border-radius:5px;background:{color}"></div>'
                            f'<span style="font-size:11px;font-weight:700;color:{color}">{pct}%</span>'
                            f'<span style="font-size:10px;color:{TXT_MUT}">{etiq}</span>'
                            f'</div>'
                        )
                st.markdown(
                    f'<div>'
                    f'<div style="font-size:10px;color:{TXT_MUT};font-weight:600;margin-bottom:6px">GESTIÓN DE POSICIÓN</div>'
                    f'{tramo_html}'
                    f'<span class="badge {urg_cls}" style="margin-top:4px;display:inline-block">{urgencia}</span>'
                    f'</div>',
                    unsafe_allow_html=True)

            st.markdown(f'<hr style="border:none;border-top:1px solid {BOR};margin:12px 0">',unsafe_allow_html=True)


            # Tren de Arrastre — datos en Sheet GrekoTrader_Sympathy (próximamente)

            # Fila 2: indicadores + NBIS + objetivos + lectura
            cd1,cd2,cd3,cd4 = st.columns(4)
            with cd1:
                st.markdown(
                    f'<div style="background:{BG_HEAD};border-radius:10px;padding:12px">'
                    f'<div style="font-size:11px;font-weight:700;color:{TXT};margin-bottom:8px">Indicadores actuales</div>'
                    f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 10px;font-size:11px">'
                    f'<span style="color:{TXT_MUT}">RSI</span><span style="color:{c_rsi(r["RSI"])};font-weight:700">{r["RSI"]}</span>'
                    f'<span style="color:{TXT_MUT}">MACD</span><span style="color:{G if r["MACD"]>0 else R};font-weight:700">{r["MACD"]:+.2f}</span>'
                    f'<span style="color:{TXT_MUT}">Volumen</span><span style="color:{c_vol(r["Volumen"]/100)};font-weight:700">{r["Volumen"]}%</span>'
                    f'<span style="color:{TXT_MUT}">Beta</span><span style="color:{TXT};font-weight:700">{r["Beta"]}</span>'
                    f'<span style="color:{TXT_MUT}">Pre-Mkt</span><span style="color:{c_pre(r["Pre_Move"])};font-weight:700">{r["Pre_Move"]:+.1f}%</span>'
                    f'<span style="color:{TXT_MUT}">Vol Pre</span><span style="color:{c_vol(r["Pre_Vol"])};font-weight:700">{r["Pre_Vol"]:.1f}x</span>'
                    f'<span style="color:{TXT_MUT}">Post-Mkt</span>'
                    f'<span style="color:{c_pre(r.get("Post_Move",0))};font-weight:700">{r.get("Post_Move",0):+.1f}%</span>'
                    f'<span style="color:{TXT_MUT}">DD desde pico</span>'
                    f'<span style="color:{R if float(r.get("DD_pico",0)) < -15 else A if float(r.get("DD_pico",0)) < -8 else G};font-weight:700">{float(r.get("DD_pico",0)):+.1f}%</span>'
                    f'</div></div>',unsafe_allow_html=True)
                # v19: Price Target badge en posición
                _pt_html_pos = render_price_target_badge(tk, pa, G, R, A, TXT_MUT)
                if _pt_html_pos:
                    st.markdown(_pt_html_pos, unsafe_allow_html=True)
                # v19: SMA 50/200 badge
                _sma_html_pos = render_sma_badge(tk, pa, TXT_MUT)
                if _sma_html_pos:
                    st.markdown(_sma_html_pos, unsafe_allow_html=True)
                # v19.2: Fase HOY badge
                _fbh = locals().get("_fase_badge_html", "")
                if _fbh:
                    st.markdown(_fbh, unsafe_allow_html=True)
                # v19.2: Badge de vigencia de la señal
                _vig_data = st.session_state.get(
                    f"_fase_live_{_SHEET_ACTIVO}_vigencias", {}).get(tk, {})
                if _vig_data.get("badge_html"):
                    st.markdown(_vig_data["badge_html"], unsafe_allow_html=True)
            with cd2:
                # Señal de gestión de posición - no score de entrada
                rsi_pos = r["RSI"]
                pnl_pos = pnl_pct

                # v19: calcular _stop_data antes de usarlo
                _beta_p_cd2   = float(r.get("Beta", 1.5))
                _score_e_cd2  = float(r.get("Score", 0) or 0)
                _prob_e_cd2   = float(r.get("Prob_NBIS", 0) or 0)
                _cat_e_cd2    = str(r.get("Cat_Fecha", "-"))
                _fue_earn_cd2 = False
                try:
                    import datetime as _dt_cd2
                    if _cat_e_cd2 not in ("-","","nan"):
                        _fue_earn_cd2 = abs((_dt_cd2.date.today() -
                            _dt_cd2.date.fromisoformat(_cat_e_cd2[:10])).days) <= 5
                except Exception:
                    pass
                _stop_data = calcular_stop_tipo(
                    pc=pc, tipo=_tipo_pos, beta=_beta_p_cd2,
                    score_entrada=_score_e_cd2, prob_entrada=_prob_e_cd2,
                    tenia_earnings=_fue_earn_cd2, pnl_pct=pnl_pct, pa=pa)

                # v19: stop type labels
                _stop_tipo_lbl  = _stop_data.get("tipo_stop", "Normal")
                _stop_razon_lbl = _stop_data.get("razon", "")
                _stop_estricto_flag = "Estricto" in _stop_tipo_lbl

                # Determinar semáforo de gestión
                if pnl_pos >= 40:
                    gest_color = G; gest_emoji = "🟢"
                    gest_titulo = "Ganancia sólida"
                    gest_msg = "Tramo 1 ejecutado? Si no, vender 30% ahora. Dejar runner."
                elif pnl_pos >= 20:
                    gest_color = G; gest_emoji = "🟢"
                    gest_titulo = "Objetivo 1 alcanzado"
                    gest_msg = "Vender 30% para asegurar ganancia. Mantener 70% con stop."
                elif pnl_pos >= 10:
                    gest_color = A; gest_emoji = "🟡"
                    gest_titulo = "En camino"
                    gest_msg = "Mantener. Vigilar RSI y catalizador próximo."
                elif pnl_pos >= 0:
                    gest_color = A; gest_emoji = "🟡"
                    gest_titulo = "Break even"
                    gest_msg = "Sin ganancia aún. Confirmar que el catalizador sigue activo."
                elif pnl_pos >= -15:
                    gest_color = R; gest_emoji = "🔴"
                    gest_titulo = "En pérdida moderada"
                    gest_msg = "Revisar catalizador. ¿Sigue válido? Si no, evaluar salida."
                    if _stop_estricto_flag:
                        gest_msg += f" ⚠️ Stop {_stop_data.get('stop_pct',0):.0f}% — señal tardía al entrar."
                else:
                    gest_color = R; gest_emoji = "🔴"
                    gest_titulo = "Pérdida alta - acción requerida"
                    gest_msg = "Stop loss cercano. Evaluar salida inmediata."

                # v19 FIX: alerta si stop ya fue cruzado
                if _stop_data.get("stop_activado", False):
                    st.markdown(
                        f'<div style="background:#FEF2F2;border:2px solid #DC2626;'
                        f'border-radius:8px;padding:8px 14px;margin-top:6px">'
                        f'<div style="font-size:12px;font-weight:800;color:#DC2626">'
                        f'🔴 STOP ACTIVADO — Precio actual ${pa:.2f} cruzó stop ${_stop_data.get("stop_val",0):.2f}</div>'
                        f'<div style="font-size:10px;color:#374151;margin-top:2px">'
                        f'Evaluar salida. Si es ETF Cripto en ciclo bajista → considerar salir y reentrar cuando retome tendencia.</div>'
                        f'</div>', unsafe_allow_html=True)

                # RSI de la posición
                rsi_gest = "RSI alto - zona salida" if rsi_pos > 65 else \
                           "RSI medio - mantener" if rsi_pos > 45 else \
                           "RSI bajo - posición sana"
                rsi_gest_c = R if rsi_pos > 65 else A if rsi_pos > 45 else G

                st.markdown(
                    f'<div style="background:{BG_HEAD};border-radius:10px;padding:12px">'
                    f'<div style="font-size:11px;font-weight:700;color:{TXT};margin-bottom:8px">📊 Estado de la posición</div>'
                    f'<div style="background:{gest_color}18;border:1px solid {gest_color}44;border-radius:8px;padding:8px;margin-bottom:10px">'
                    f'  <div style="font-size:12px;font-weight:700;color:{gest_color}">{gest_emoji} {gest_titulo}</div>'
                    f'  <div style="font-size:11px;color:{TXT_MUT};margin-top:4px;line-height:1.5">{gest_msg}</div>'
                    f'</div>'
                    f'<div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px">'
                    f'  <span style="color:{TXT_MUT}">RSI actual</span>'
                    f'  <span style="color:{rsi_gest_c};font-weight:700">{rsi_pos:.0f} - {rsi_gest}</span>'
                    f'</div>'
                    f'<div style="display:flex;justify-content:space-between;font-size:11px">'
                    f'  <span style="color:{TXT_MUT}">Días en posición</span>'
                    f'  <span style="color:{TXT};font-weight:700">'
                    f'{(pd.Timestamp.now()-pd.to_datetime(pos["Fecha"],errors="coerce")).days if "Fecha" in pos else "-"} días</span>'
                    f'</div>'
                    f'</div>', unsafe_allow_html=True)
            with cd3:
                # Objetivos y stop - usar _tipo_pos ya calculado arriba
                _beta_p    = float(r.get("Beta", 1.5))
                _score_e   = float(r.get("Score", 0) or 0)
                _prob_e    = float(r.get("Prob_NBIS", 0) or 0)
                _cat_e     = str(r.get("Cat_Fecha", "-"))
                # Detectar si entró con earnings próximos
                _fue_earnings = False
                try:
                    import datetime as _dt_sp
                    if _cat_e not in ("-","","nan"):
                        _dias_entry = abs((
                            _dt_sp.date.today() -
                            _dt_sp.date.fromisoformat(_cat_e[:10])
                        ).days)
                        _fue_earnings = _dias_entry <= 5
                except Exception:
                    pass

                _stop_data = calcular_stop_tipo(
                    pc=pc, tipo=_tipo_pos, beta=_beta_p,
                    score_entrada=_score_e, prob_entrada=_prob_e,
                    tenia_earnings=_fue_earnings, pnl_pct=pnl_pct, pa=pa)

                stop_val  = _stop_data["stop_val"]
                obj1      = _stop_data["obj1"]
                obj2      = _stop_data["obj2"]
                obj3      = _stop_data["obj3"]
                stop_pct  = (stop_val/pa-1)*100 if pa > 0 and stop_val > 0 else 0
                obj1_pct  = (obj1/pa-1)*100 if pa > 0 else 0
                obj2_pct  = (obj2/pa-1)*100 if pa > 0 else 0
                obj3_pct  = (obj3/pa-1)*100 if pa > 0 else 0

                def obj_color(pct):
                    return G if pct <= 0 else A if pct <= 20 else C

                def tramo_badge(label, color):
                    return (f'<span style="background:{color}22;color:{color};border:1px solid {color}55;'
                            f'border-radius:4px;padding:1px 6px;font-size:9px;font-weight:700">{label}</span>')

                st.markdown(
                    f'<div style="background:{BG_HEAD};border-radius:10px;padding:12px">'
                    f'<div style="font-size:11px;font-weight:700;color:{TXT};margin-bottom:10px">🎯 Plan de salida - 3 tramos</div>'

                    # Stop loss
                    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid {BOR}">'
                    f'<div>'
                    f'  <span style="font-size:13px;font-weight:700;color:{R}">${stop_val:.2f}</span>'
                    f'  <span style="font-size:10px;color:{R}"> ({stop_pct:+.1f}%)</span>'
                    f'</div>'
                    f'<div>{tramo_badge("🛑 STOP LOSS", R)}</div>'
                    f'</div>'

                    # Tramo 1
                    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid {BOR}">'
                    f'<div>'
                    f'  <span style="font-size:13px;font-weight:700;color:{obj_color(obj1_pct)}">${obj1:.2f}</span>'
                    f'  <span style="font-size:10px;color:{obj_color(obj1_pct)}"> ({obj1_pct:+.1f}%)</span>'
                    f'</div>'
                    f'<div>{tramo_badge("VENDER 30%", A)}</div>'
                    f'</div>'

                    # Tramo 2
                    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid {BOR}">'
                    f'<div>'
                    f'  <span style="font-size:13px;font-weight:700;color:{obj_color(obj2_pct)}">${obj2:.2f}</span>'
                    f'  <span style="font-size:10px;color:{obj_color(obj2_pct)}"> ({obj2_pct:+.1f}%)</span>'
                    f'</div>'
                    f'<div>{tramo_badge("VENDER 40%", G)}</div>'
                    f'</div>'

                    # Tramo 3
                    f'<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0">'
                    f'<div>'
                    f'  <span style="font-size:13px;font-weight:700;color:{obj_color(obj3_pct)}">${obj3:.2f}</span>'
                    f'  <span style="font-size:10px;color:{obj_color(obj3_pct)}"> ({obj3_pct:+.1f}%)</span>'
                    f'</div>'
                    f'<div>{tramo_badge("RUNNER 30%", C)}</div>'
                    f'</div>'

                    f'<div style="font-size:9px;color:{TXT_SOFT};margin-top:6px;border-top:1px solid {BOR};padding-top:5px">'
                    f'% = cuánto falta desde precio actual  - Verde = ya alcanzado</div>'
                    f'</div>', unsafe_allow_html=True)
            with cd4:
                tramos_resumen = "  - ".join([
                    f'<span style="color:{(_t[2] if len(_t)>2 else (R if "VENDER" in str(_t[1]) else G))};font-weight:700">{_t[0]}% {_t[1]}</span>'
                    for _t in tramos if _t[0] > 0
                ])
                # v15: earnings badge urgencia + live fetch si falta
                import datetime as _dttC4
                _cat_c4 = _cat_fecha_use if _cat_fecha_use not in ("-","","nan") else get_earnings_single(tk)
                try:
                    _dias_c4 = (_dttC4.date.fromisoformat(_cat_c4[:10]) - _dttC4.date.today()).days
                    if _dias_c4 < 0:
                        _earn_html_c4 = f'<div style="font-size:10px;color:{TXT_SOFT}">✅ Earnings {_cat_c4[:10]} (ya reportó)</div>'
                    elif _dias_c4 <= 2:
                        _earn_html_c4 = (f'<div style="background:#FEF2F2;border:2px solid #EF4444;border-radius:8px;padding:7px 10px;margin-top:6px">'
                            f'<div style="font-size:12px;font-weight:800;color:#DC2626">🚫 Earnings en {_dias_c4}d - NO agregar</div>'
                            f'<div style="font-size:10px;color:#7F1D1D">Riesgo binario. Esperar resultado.</div></div>')
                    elif _dias_c4 <= 6:
                        _earn_html_c4 = (f'<div style="background:#FFFBEB;border:1px solid #FCD34D;border-radius:8px;padding:7px 10px;margin-top:6px">'
                            f'<div style="font-size:12px;font-weight:700;color:#D97706">⚠️ Earnings en {_dias_c4}d - Cuidado</div>'
                            f'<div style="font-size:10px;color:#92400E">Definir plan antes del reporte.</div></div>')
                    elif _dias_c4 <= 15:
                        _earn_html_c4 = (f'<div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;padding:7px 10px;margin-top:6px">'
                            f'<div style="font-size:12px;font-weight:700;color:#16A34A">🎯 Earnings en {_dias_c4}d - Zona NBIS</div>'
                            f'<div style="font-size:10px;color:#14532D">{_cat_c4[:10]}  - Catal. activo.</div></div>')
                    elif _dias_c4 <= 30:
                        _earn_html_c4 = (f'<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;padding:7px 10px;margin-top:6px">'
                            f'<div style="font-size:12px;font-weight:700;color:#2563EB">📅 Earnings en {_dias_c4}d</div>'
                            f'<div style="font-size:10px;color:#1E3A8A">{_cat_c4[:10]}  - Monitorear.</div></div>')
                    else:
                        _earn_html_c4 = f'<div style="font-size:10px;color:{TXT_MUT}">📅 {_cat_c4[:10]}</div>'
                except Exception:
                    _earn_html_c4 = f'<div style="font-size:10px;color:{TXT_SOFT}">{"Sin earnings detectados" if _cat_c4 in ("-","","nan") else _cat_c4[:10]}</div>'
                # v19: mostrar accion con stop prominente
                _stop_precio_lbl = analisis_v12.get("stop_precio", 0)
                _falta_stop_lbl  = analisis_v12.get("falta_stop", 0)
                _accion_lbl      = analisis_v12.get("accion", razon)
                _lect_bg  = BG_HEAD; _lect_bor = BOR
                _lect_col = "#D97706" if urgencia in ("Vigilar","VIGILAR") else TXT
                _stop_badge = ""
                if _stop_precio_lbl > 0 and _falta_stop_lbl > 0:
                    _sc = "#DC2626" if abs(_falta_stop_lbl) < 2 else "#D97706"
                    _stop_badge = (
                        f'<div style="background:{_sc}18;border:1px solid {_sc}44;'
                        f'border-radius:6px;padding:5px 8px;margin-top:6px">'
                        f'<span style="font-size:10px;color:{_sc};font-weight:700">'
                        f'🛡️ Stop duro ${_stop_precio_lbl:.2f} · a {abs(_falta_stop_lbl):.1f}% de activarse</span>'
                        f'</div>')
                st.markdown(
                    f'<div style="background:{_lect_bg};border:1px solid {_lect_bor};border-radius:10px;padding:12px">'
                    f'<div style="font-size:11px;font-weight:700;color:{TXT};margin-bottom:6px">Lectura del trader</div>'
                    f'<div style="font-size:12px;margin-bottom:6px">{tramos_resumen}</div>'
                    f'<div style="font-size:11px;color:{_lect_col};font-weight:600;line-height:1.7">{_accion_lbl}</div>'
                    f'{_stop_badge}'
                    f'{_earn_html_c4}'
                    f'</div>', unsafe_allow_html=True)

            # ── POST-EARNINGS DETECTOR v15 ────────────────────
            # Detecta si el earning ya ocurrió y da decisión concreta
            _peg = detect_post_earning_gap(tk, _cat_c4)
            if _peg["ocurrio"]:
                _peg_bg = {"positivo_fuerte":"#F0FDF4","positivo_moderado":"#F0FDF4",
                           "neutral":"#FFFBEB","negativo_moderado":"#FEF2F2",
                           "negativo_fuerte":"#FFF1F2"}.get(_peg["clasificacion"],"#F8FAFC")
                _peg_bor = {"positivo_fuerte":"#86EFAC","positivo_moderado":"#86EFAC",
                            "neutral":"#FCD34D","negativo_moderado":"#FCA5A5",
                            "negativo_fuerte":"#FDA4AF"}.get(_peg["clasificacion"],"#E2E8F0")
                st.markdown(
                    f'<div style="background:{_peg_bg};border:2px solid {_peg_bor};'
                    f'border-radius:10px;padding:12px 16px;margin-top:8px">'
                    f'<div style="font-size:12px;font-weight:800;color:{_peg["color"]};margin-bottom:6px">'
                    f'{_peg["emoji"]} RESULTADO EARNING - Gap {_peg["gap_pct"]:+.1f}%  - Vol {_peg["vol_ratio"]:.1f}x promedio</div>'
                    f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px">'
                    f'  <div style="background:rgba(255,255,255,0.6);border-radius:7px;padding:8px">'
                    f'    <div style="font-size:9px;font-weight:700;color:{_peg["color"]};margin-bottom:3px">💼 YA TIENES POSICIÓN</div>'
                    f'    <div style="font-size:11px;color:#1E293B;line-height:1.5">{_peg["decision_tiene"]}</div>'
                    f'  </div>'
                    f'  <div style="background:rgba(255,255,255,0.6);border-radius:7px;padding:8px">'
                    f'    <div style="font-size:9px;font-weight:700;color:#2563EB;margin-bottom:3px">🔍 SIN POSICIÓN / RECOMPRA</div>'
                    f'    <div style="font-size:11px;color:#1E293B;line-height:1.5">{_peg["decision_notiene"]}</div>'
                    f'  </div>'
                    f'</div>'
                    f'{"<div style=margin-top:8px;background:#FFF7ED;border:1px solid #FED7AA;border-radius:7px;padding:8px>" + "<div style=font-size:10px;font-weight:700;color:#EA580C>🎯 SETUP RECOMPRA NBIS ACTIVO</div>" + "<div style=font-size:11px;color:#7C2D12>Caída post-earning = mercado sobrereaccionó. Monitorear RSI + Volumen + Soporte los próximos 3 días.</div></div>" if _peg["recompra_activa"] else ""}'
                    f'</div>', unsafe_allow_html=True)
            # ── NBIS Panel + Sympathy Panel ──────────────────
            _symp_html_t6 = render_sympathy_panel(tk, pc, pa, pnl_pct, G, A, R, TXT_MUT, BOR)
            st.markdown(
                render_nbis_panel(
                    r.get("Prob_NBIS", 0), r.get("Sim_NBIS", 0),
                    G, A, R, C, TXT, TXT_MUT, TXT_SOFT, BG_HEAD, BOR
                ) + _symp_html_t6, unsafe_allow_html=True)

            # v19: Earnings + Noticia unificados en Greko
            _en_card_gk = render_earn_news_card(
                tk, str(r.get("Cat_Fecha","-")), G, R, A, TXT_MUT, BOR)
            if _en_card_gk:
                st.markdown(_en_card_gk, unsafe_allow_html=True)

            # v19: Badge Pullback P3 Greko
            _pb_gk_dd  = float(str(r.get("DD_pico", 0) or 0).replace(",","."))
            _pb_gk_rsi = float(str(r.get("RSI", 50) or 50).replace(",","."))
            _pb_gk_ema = float(str(r.get("EMA50", 0) or 0).replace(",","."))
            _pb_gk_vol = float(str(r.get("Volumen", 100) or 100).replace(",","."))
            _pb_gk_html = render_pullback_badge(
                tk, _pb_gk_dd, _pb_gk_rsi, _pb_gk_ema, 0, _pb_gk_vol,
                G, R, A, C, TXT_MUT,
                tiene_posicion=True, pnl_pct=pnl_pct)
            if _pb_gk_html:
                st.markdown(_pb_gk_html, unsafe_allow_html=True)

            # v19: Panel de Recompra
            if pnl_pct >= 5:
                _recompra_data_g = calcular_señal_recompra(
                    ticker=tk, precio_entrada=pc,
                    pnl_pct=pnl_pct, tipo=str(pos.get("Tipo","Accion")),
                    cat_fecha=str(r.get("Cat_Fecha","-")))
                _recompra_html_g = render_panel_recompra(
                    _recompra_data_g, str(pos.get("Tipo","Accion")),
                    G, R, A, C, TXT, TXT_MUT, BOR)
                if _recompra_html_g:
                    st.markdown(_recompra_html_g, unsafe_allow_html=True)
                elif _recompra_data_g.get("señal") == "esperar_pullback":
                    _rsi_g   = _recompra_data_g.get("rsi", 0)
                    _dd_g    = _recompra_data_g.get("dd_max", 0)
                    _tgt_g   = _recompra_data_g.get("target_entrada", 0)
                    st.markdown(
                        f'<div style="background:#EFF6FF;border:1px solid #BFDBFE;'
                        f'border-left:3px solid #2563EB;border-radius:8px;'
                        f'padding:8px 14px;margin-top:6px">'
                        f'<div style="font-size:11px;font-weight:700;color:#2563EB;margin-bottom:4px">'
                        f'🔄 Recompra: NO ahora — precio en máximos</div>'
                        f'<div style="font-size:10px;color:#374151;line-height:1.8">'
                        f'RSI {_rsi_g} → sobrecomprado · '
                        f'DD actual {_dd_g:.1f}% desde máximo<br>'
                        f'<strong>Zona de entrada:</strong> '
                        f'${_tgt_g:.2f} (cuando RSI baje a 52-58)<br>'
                        f'<span style="color:#6B7280">Mantener posición · No agregar hasta que corrija</span>'
                        f'</div></div>',
                        unsafe_allow_html=True)

                # v19 FIX A: Botón de salida en Greko (al final del cd2)
                render_botones_salida(
                    ticker=tk, pc=pc, pa=pa, pnl_pct=pnl_pct,
                    sheet_name=_SHEET_ACTIVO, key_prefix=f"pos_{_cartera_nombre[:3]}",
                    G=G, R=R, A=A, TXT_MUT=TXT_MUT,
                    BG_HEAD=BG_HEAD, BOR=BOR, idx=_gloop_idx)

            # ── PIRAMIDACIÓN v18 — agregar a posición ganadora ──
            _pir = analisis.get("piramidar") if analisis else None
            if _pir:
                _pir_bg  = {"#16A34A":"#F0FDF4","#0891B2":"#ECFEFF","#7C3AED":"#F5F3FF"}.get(_pir["color"],"#F8FAFC")
                _pir_bor = {"#16A34A":"#86EFAC","#0891B2":"#A5F3FC","#7C3AED":"#C4B5FD"}.get(_pir["color"],"#E2E8F0")
                st.markdown(
                    f'<div style="background:{_pir_bg};border:2px solid {_pir_bor};'
                    f'border-radius:10px;padding:12px 16px;margin-top:8px">'
                    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
                    f'  <span style="font-size:14px;font-weight:800;color:{_pir["color"]}">'
                    f'  {_pir["accion"]}</span>'
                    f'  <span style="background:{_pir["color"]};color:white;border-radius:5px;'
                    f'  padding:2px 8px;font-size:10px;font-weight:700">{_pir["urgencia"]}</span>'
                    f'</div>'
                    f'<div style="font-size:11px;color:#374151;line-height:1.6">{_pir["razon"]}</div>'
                    f'</div>', unsafe_allow_html=True)

            # ── v18: Botón de salida / T1 / Stop ─────────────
            with st.expander(f"🏁 Registrar salida / T1 / Stop — {tk}", expanded=False):
                _tipo_sal = st.radio("Tipo de cierre",
                    ["T1 — venta parcial","SALIDA — cierre total","STOP — stop loss"],
                    horizontal=True, key=f"gtipo_sal_{_gtk_key}")
                _tipo_map = {"T1 — venta parcial":"T1","SALIDA — cierre total":"SALIDA","STOP — stop loss":"STOP"}
                render_boton_registro(
                    ticker=tk, fase=str(r.get("Etapa_v12","-")),
                    precio=float(pc), score=int(r.get("Score",0)),
                    prob_nbis=float(r.get("Prob_NBIS",0)),
                    cat_fecha=str(r.get("Cat_Fecha","-")),
                    arrastradas=str(get_sympathy(tk)["arrastradas"]),
                    lider=str(get_sympathy(tk)["lider"]),
                    opinion=str(r.get("Opinion_Trader","-")),
                    key_prefix=f"pos6_{_gtk_key}",
                    tipo=_tipo_map.get(_tipo_sal,"SALIDA")
                )

            st.markdown('</div>',unsafe_allow_html=True)  # cierra pos-card

        # ── Alerta concentración sectorial ──────────────────
        sectores_pos = {}
        for _, _prow in posiciones_greko_df.iterrows():
            _ptk = str(_prow["Ticker"]).upper()
        # Calcular concentración desde los datos ya cargados
        if n_ok > 0:
            _areas = {}
            for _, _prow in posiciones_greko_df.iterrows():
                _tipo_c = str(_prow.get("Tipo","Accion"))
                _areas[_tipo_c] = _areas.get(_tipo_c, 0) + 1
            _concentradas = {k:v for k,v in _areas.items() if v >= 3}
            if _concentradas:
                for _sector_c, _cnt_c in _concentradas.items():
                    st.warning(f"⚠️ Concentración: tienes {_cnt_c} posiciones en {_sector_c}. "
                               f"Si el sector cae, caen todas juntas. Considera diversificar.")

        # ── Resumen portafolio ──────────────────────────────
        if n_ok>0:
            pnl_total_pct=(total_act/total_inv-1)*100 if total_inv>0 else 0
            st.markdown("---")
            st.markdown(f'<div style="font-size:13px;font-weight:700;color:{TXT};margin-bottom:10px">Resumen del portafolio</div>',unsafe_allow_html=True)
            pr1,pr2,pr3,pr4=st.columns(4)
            with pr1: st.metric("Invertido",f"${total_inv:,.0f}")
            with pr2: st.metric("Valor actual",f"${total_act:,.0f}")
            with pr3: st.metric("P&L total",f"${total_pnl:+,.0f}",f"{pnl_total_pct:+.1f}%",delta_color="normal" if pnl_total_pct>0 else "inverse")
            with pr4: st.metric("Posiciones",n_ok)

            # ── Botón A: Exportar análisis completo (como v11) ──────
            export_rows = []
            for _gloop_idx_b, (_, pos) in enumerate(posiciones_greko_df.iterrows()):
                try:
                    tk  = str(pos["Ticker"]).upper()
                    # v18 fix: unique key suffix to avoid duplicate widget keys
                    _tk_key = f"{tk}_b{_gloop_idx_b}"  # "b" prefix distinguishes from loop1
                    pc  = _parse_precio(pos["Precio_Compra"])
                    qty = float(pos.get("Cantidad", 1))
                    r   = get_row_for_ticker(tk, pc)
                    pa  = float(r["Precio"])
                    pnl_e = round((pa - pc) / pc * 100, 2) if pc > 0 else 0

                    # Días en posición
                    try:
                        import datetime as _dte
                        _fd = pd.to_datetime(pos.get("Fecha",""), errors="coerce")
                        _dias_e = (_dte.date.today() - _fd.date()).days if not pd.isna(_fd) else 0
                    except Exception:
                        _dias_e = 0

                    # Etapa de la señal — usar Sheet o live si disponible
                    _fase_sheet_pos  = str(pos.get("Fase", "-"))
                    _fases_live_dict = st.session_state.get(f"_fase_live_{_SHEET_ACTIVO}", {})
                    _live_info_pos   = _fases_live_dict.get(tk, {})
                    _fase_live_pos   = _live_info_pos.get("fase", None)
                    _rsi_live_pos    = _live_info_pos.get("rsi", 0)

                    # Badge de cambio de Fase
                    _fase_origen_up  = _fase_sheet_pos.upper()
                    _era_m3_pos = any(x in _fase_origen_up for x in ["M3","FASE 3","ENTRAR","ANTICIPAR"])
                    _era_m2_pos = any(x in _fase_origen_up for x in ["M2","FASE 2","ENTRADA"])

                    _fase_badge_html = ""
                    if _fase_live_pos:
                        if _era_m2_pos and _fase_live_pos == "M3":
                            _fase_badge_html = (
                                f'<span style="background:#DCFCE7;color:#16A34A;border:1px solid #86EFAC;'
                                f'border-radius:4px;padding:2px 8px;font-size:10px;font-weight:800;margin-left:6px">'
                                f'📈 M2→M3 HOY</span>')
                        elif _era_m3_pos and _fase_live_pos in ("M2","M1"):
                            _fase_badge_html = (
                                f'<span style="background:#FEF2F2;color:#DC2626;border:1px solid #FECACA;'
                                f'border-radius:4px;padding:2px 8px;font-size:10px;font-weight:800;margin-left:6px">'
                                f'📉 M3→{_fase_live_pos}</span>')
                        elif _era_m2_pos and _fase_live_pos == "Momentum":
                            _fase_badge_html = (
                                f'<span style="background:#FEF9C3;color:#D97706;border:1px solid #FDE68A;'
                                f'border-radius:4px;padding:2px 8px;font-size:10px;font-weight:800;margin-left:6px">'
                                f'⚡ →Momentum</span>')
                        elif _era_m3_pos and _fase_live_pos == "M3":
                            _fase_badge_html = (
                                f'<span style="background:#EFF6FF;color:#2563EB;border:1px solid #BFDBFE;'
                                f'border-radius:4px;padding:2px 8px;font-size:10px;font-weight:700;margin-left:6px">'
                                f'M3 ✅ RSI {_rsi_live_pos:.0f}</span>')
                        else:
                            _fase_badge_html = (
                                f'<span style="background:#F8FAFC;color:#94A3B8;border:1px solid #E2E8F0;'
                                f'border-radius:4px;padding:2px 8px;font-size:10px;margin-left:6px">'
                                f'{_fase_live_pos} RSI {_rsi_live_pos:.0f}</span>')

                    if _dias_e <= 1:
                        _etapa = "M3 - Entrar Hoy"
                    elif _dias_e <= 3:
                        _etapa = "M2 - Entrada Valida"
                    elif pnl_e < -3:
                        _etapa = "M1 - Detectadas"
                    else:
                        _etapa = "M2 - Entrada Temprana"

                    # Señal v12
                    _sr_e = calcular_señales_salida_v12(
                        pnl_pct=pnl_e, precio_compra=pc,
                        precio_actual=pa, precio_max=max(pa, pc*1.1),
                        dias_posicion=_dias_e,
                        estrategia=str(pos.get("Estrategia","Swing")),
                        tipo=str(pos.get("Tipo","Accion"))
                    )

                    export_rows.append({
                        "Ticker":         tk,
                        "Fase_Origen":    _ascii(str(pos.get("Fase_Origen",""))).replace("-","") if str(pos.get("Fase_Origen","")) in ("-","","nan") else _ascii(str(pos.get("Fase_Origen",""))),
                        "Etapa_Senal":    _etapa,
                        "Fecha_Compra":   str(pos.get("Fecha","-")),
                        "Precio_Compra":  round(pc, 2),
                        "Precio_Actual":  round(pa, 2),
                        "Cantidad":       round(qty, 4),
                        "PnL_Pct":        pnl_e,
                        "PnL_USD":        round((pa - pc) * qty, 2),
                        "Dias_Posicion":  _dias_e,
                        "Score_Rebote":   r.get("Score_Rebote", 0),
                        "Nivel_Rebote":   _ascii(str(r.get("Nivel_Rebote","-"))),
                        "Prob_NBIS":      r.get("Prob_NBIS", 0),
                        "RSI":            r.get("RSI", 0),
                        "DD_pico":        r.get("DD_pico", 0),
                        "Senal_v12":      _ascii(_sr_e["señal"]),
                        "Urgencia":       _ascii(str(_sr_e["urgencia"])),
                        "Tipo":           str(pos.get("Tipo","Accion")),
                        "Estrategia":     str(pos.get("Estrategia","Swing")),
                        "Cat_Fecha":      _ascii(str(pos.get("Cat_Fecha","-"))),
                        "FLUJO_VALIDADO": "SI" if _dias_e > 0 else "NO",
                    })
                except Exception:
                    continue

            if export_rows:
                _df_exp = pd.DataFrame(export_rows)
                _csv_a  = df_to_csv_chile(_df_exp)
                st.download_button(
                    "⬇️ Exportar análisis posiciones (CSV)",
                    _csv_a,
                    f"analisis_posiciones_{pd.Timestamp.now().strftime('%Y-%m-%d_%H%M')}.csv",
                    "text/csv",
                    help="Análisis completo con PnL  - Señal v12  - Score  - Urgencia",
                    key="dl_pos_greko_csv",
                )

                # ── Botón B: CSV posiciones actualizadas con salidas ─
                # Simula que aplicaste las salidas T1/T2/Stop
                # Recalcula cantidades y genera nuevo CSV para re-subir
                rows_actualizado = []
                for row_e in export_rows:
                    señal = row_e["Senal_v12"].lower()
                    qty_orig = float(row_e["Cantidad"])

                    if "stop" in señal or "stop activado" in señal:
                        continue  # posición cerrada - no incluir

                    elif "t2 +12%" in señal or "t2" in señal:
                        qty_nueva = round(qty_orig * 0.20, 6)
                        nota = f"Vendido 80% (T1:40% + T2:40%). Queda 20% runner con trailing stop -5%"

                    elif "t1 +8%" in señal or "t1" in señal:
                        qty_nueva = round(qty_orig * 0.60, 6)
                        nota = f"Vendido 40% en T1 (+8%). Queda 60% con stop en breakeven (precio compra)"

                    elif "muerta" in señal or "reasignar" in señal:
                        qty_nueva = qty_orig
                        nota = f"Posicion muerta +5 dias en +-1%. Salir y reasignar a señal M3 activa"

                    else:
                        qty_nueva = qty_orig
                        nota = ""

                    qty_vender = round(qty_orig - qty_nueva, 6)
                    rows_actualizado.append({
                        "Ticker":           row_e["Ticker"],
                        "Fecha":            row_e["Fecha_Compra"],
                        "Precio_Compra":    row_e["Precio_Compra"],
                        "Cantidad_Original": round(qty_orig, 4),
                        "Cantidad_Vender":  qty_vender,
                        "Cantidad_Mantener":qty_nueva,
                        "Cat_Fecha":        row_e["Cat_Fecha"],
                        "Tipo":             row_e["Tipo"],
                        "Estrategia":       row_e["Estrategia"],
                        "Fase_Origen":      row_e["Fase_Origen"],
                        "Notas_Salida":     nota,
                    })

                if rows_actualizado:
                    _df_act = pd.DataFrame(rows_actualizado)
                    _csv_act = df_to_csv_chile(_df_act)
                    st.download_button(
                        "🔄 CSV posiciones actualizadas (re-subir para ver ganancia futura)",
                        _csv_act,
                        f"Activos_actualizado_{pd.Timestamp.now().strftime('%Y-%m-%d')}.csv",
                        "text/csv",
                        help="CSV listo para re-subir. T1 ejecutado -> 60% de cantidad. T2 ejecutado -> 20%. Stop -> posición eliminada.",
                        key="dl_pos_greko_upd",
                    )

        if posiciones_greko_df is not None and len(posiciones_greko_df) > 0:
            render_catalysts_section(posiciones_greko_df, "greko_pos")
            st.markdown("---")
            render_noticias_mini(posiciones_greko_df["Ticker"].tolist(), "Noticias Posiciones Greko")

            # v19: Guardar DF procesado en caché para checkbox rápido
            st.session_state[_CACHE_DF_KEY] = posiciones_greko_df.copy()
            st.session_state[_CACHE_TS_KEY]     = __import__('time').time()

    else:
        # Checkbox cambió — usar DF en memoria sin recargar yfinance
        posiciones_greko_df = st.session_state.get(_CACHE_DF_KEY)
        if posiciones_greko_df is None:
            posiciones_greko_df = pd.DataFrame()
        _batch_precios = st.session_state.get(_CACHE_BATCH_KEY, {})

    # [checkboxes moved to top]

    _pos_lista_activa = []
    try:
        _filtro_greko = st.session_state.get("filtro_pos_activa", "activas")
        for _rg in (posiciones_greko_df.to_dict("records")
                    if posiciones_greko_df is not None and len(posiciones_greko_df) > 0
                    else []):
            _tkg  = str(_rg.get("Ticker","")).upper().strip()
            _pcg  = _parse_precio(_rg.get("Precio_Compra",0))
            _qtg  = float(_rg.get("Cantidad",1) or 1)
            _fsg  = str(_rg.get("Fecha_Salida","-")).strip()
            _esta_cerrada_g = _fsg not in ("-","","nan","NaT","None")
            if _filtro_greko == "activas" and _esta_cerrada_g:
                continue
            if _filtro_greko == "cerradas" and not _esta_cerrada_g:
                continue
            if _tkg and _pcg > 0:
                _pag = float(st.session_state.get("_precios_live",{}).get(_tkg, _pcg))
                _psg = str(_rg.get("Precio_Salida","") or "")
                _ps_g = float(_psg.replace(",",".")) if _psg not in ("-","","nan","") else 0
                _qag = str(_rg.get("Cantidad_Activa","") or "")
                _qa_g = float(_qag.replace(",",".")) if _qag not in ("-","","nan","0","") else 0
                _pos_lista_activa.append({"ticker":_tkg,"pc":_pcg,"pa":_pag,"qty":_qtg,
                    "pnl_pct":(_pag-_pcg)/_pcg*100 if _pcg>0 else 0,
                    "area":str(_rg.get("Area","")),
                    "precio_salida":_ps_g,"qty_activa":_qa_g})
    except Exception:
        pass
    if _pos_lista_activa:
        render_resumen_sector(_pos_lista_activa, G, R, A, TXT, TXT_MUT, BOR, BG_CARD, BG_HEAD)

# v19.1: tab6 y tab7 fusionados en tab_posiciones (combobox selector)
# El contenido original de MVALLE y Amparito fue integrado al tab unificado.

with tab8:
    # ═══ v19: Tab ETF — Monitoreo separado de ETFs ══════════════

    st.markdown(
        f'<div class="sec-header" style="background:#FEF9C3;border-color:#FDE047">'
        f'<span style="font-size:20px">💰</span>'
        f'<div><span style="font-size:16px;font-weight:700;color:#854D0E">Estrategia ETF</span>'
        f'<span style="font-size:12px;color:{TXT_MUT};margin-left:10px">'
        f'Monitoreo separado · Lógica propia · No aparecen en Swing ni Watchlist</span>'
        f'</div></div>', unsafe_allow_html=True)

    # ── Botón de carga ────────────────────────────────────────
    if st.button("🔄 Cargar datos de ETFs", use_container_width=False, key="btn_etf_v19"):
        with st.spinner("Cargando ETFs..."):
            import yfinance as _yf_etf
            _etf_resultados = {}
            _todos_etfs_tab8 = {
                "Crypto":     ["IBIT","ETHA","MSTU","COIN","MARA","CLSK"],
                "Sectoriales":["TAN","ARKK","SMH","SOXX","IBB","XLK","XLE"],
                "Índice":     ["VOO","SPY","QQQ"],
                "Apalancados":["CONL","NVDL","SOXL","TQQQ"],
            }
            for categoria, tks in _todos_etfs_tab8.items():
                _etf_resultados[categoria] = {}
                for _tk_e in tks:
                    try:
                        _h_e = _yf_etf.Ticker(_tk_e).history(period="3mo")
                        if _h_e.empty:
                            continue
                        _pa_e  = float(_h_e["Close"].iloc[-1])
                        _s50   = float(_h_e["Close"].rolling(50).mean().iloc[-1])
                        _s200  = float(_h_e["Close"].rolling(200).mean().dropna().iloc[-1]) if len(_h_e) >= 200 else 0
                        _rsi_e = round(lambda c: 100-100/(1+c.diff().clip(lower=0).rolling(14).mean().iloc[-1]/((-c.diff().clip(upper=0).rolling(14).mean().iloc[-1])+1e-9))(_h_e["Close"]), 1)
                        _vs50  = round((_pa_e-_s50)/_s50*100, 1) if _s50 > 0 else 0
                        _etf_resultados[categoria][_tk_e] = {
                            "precio": round(_pa_e,2), "sma50": round(_s50,2),
                            "sma200": round(_s200,2), "rsi": _rsi_e,
                            "vs_sma50": _vs50,
                        }
                    except Exception:
                        pass
            st.session_state["_etf_tab8_data"] = _etf_resultados

    _etf_data = st.session_state.get("_etf_tab8_data", {})

    if not _etf_data:
        st.info("Presiona **Cargar datos de ETFs** para ver el estado actual")
    else:
        # ── Advertencia ETFs apalancados ─────────────────────
        st.markdown(
            f'<div style="background:#FEF2F2;border:1px solid #FECACA;'
            f'border-left:4px solid #DC2626;border-radius:8px;'
            f'padding:10px 14px;margin-bottom:12px;font-size:11px;color:#DC2626">'
            f'<strong>⚠️ ETFs Apalancados (CONL, NVDL, SOXL, TQQQ):</strong> '
            f'Solo para day trading. El volatility decay diario destruye valor en Swing. '
            f'No registrar en posiciones de largo plazo.</div>',
            unsafe_allow_html=True)

        for categoria, datos in _etf_data.items():
            if not datos:
                continue
            _cat_colors = {
                "Crypto": ("#D97706","#FFFBEB","₿"),
                "Sectoriales": ("#2563EB","#EFF6FF","📊"),
                "Índice": ("#16A34A","#F0FDF4","📈"),
                "Apalancados": ("#DC2626","#FEF2F2","⚡"),
            }
            _cc, _cbg, _cic = _cat_colors.get(categoria, (TXT,"#F8FAFC","📌"))

            st.markdown(
                f'<div style="font-size:13px;font-weight:800;color:{_cc};'
                f'margin:14px 0 8px;border-left:3px solid {_cc};padding-left:8px">'
                f'{_cic} ETFs {categoria}</div>',
                unsafe_allow_html=True)

            _cols_etf = st.columns(min(len(datos), 3))
            for i_e, (_tk_e, _d_e) in enumerate(datos.items()):
                with _cols_etf[i_e % 3]:
                    _pa_e  = _d_e.get("precio",0)
                    _rsi_e = _d_e.get("rsi",0)
                    _vs50  = _d_e.get("vs_sma50",0)
                    _s50   = _d_e.get("sma50",0)
                    _s200  = _d_e.get("sma200",0)

                    # Señal ETF
                    if categoria == "Apalancados":
                        _sig = "🚫 Solo day trading"
                        _sig_c = "#DC2626"
                    elif _pa_e > _s200 > 0 and _rsi_e < 65:
                        _sig = "✅ Sobre SMA200 · válido"
                        _sig_c = "#16A34A"
                    elif _pa_e > _s200 > 0 and _rsi_e >= 65:
                        _sig = "⚠️ Sobre SMA200 pero RSI alto"
                        _sig_c = "#D97706"
                    elif _pa_e < _s200 > 0:
                        _sig = "🔴 Bajo SMA200 · esperar"
                        _sig_c = "#DC2626"
                    else:
                        _sig = "⚪ Sin datos suficientes"
                        _sig_c = TXT_MUT

                    st.markdown(
                        f'<div style="background:{BG_CARD};border:1px solid {BOR};'
                        f'border-left:3px solid {_cc};border-radius:8px;padding:10px 12px;margin-bottom:8px">'
                        f'<div style="font-size:15px;font-weight:800;color:{TXT}">{_tk_e}</div>'
                        f'<div style="font-size:18px;font-weight:700;color:{TXT};margin:2px 0">${_pa_e:.2f}</div>'
                        f'<div style="font-size:10px;color:{TXT_MUT}">RSI {_rsi_e:.0f} · SMA50 ${_s50:.0f}'
                        f'{"· SMA200 $" + str(round(_s200,0)) if _s200 > 0 else ""}</div>'
                        f'<div style="font-size:10px;color:{_cc}">SMA50: {_vs50:+.1f}%</div>'
                        f'<div style="font-size:10px;font-weight:600;color:{_sig_c};margin-top:4px">{_sig}</div>'
                        f'</div>',
                        unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        f'<div style="font-size:11px;color:{TXT_MUT};padding:8px">'
        f'💡 Los ETFs han sido excluidos de Swing Activo, Entrar Hoy y Mi Watchlist. '
        f'Se monitorean aquí con su propia lógica. '
        f'Próximamente: Google Sheet dedicado para posiciones ETF.</div>',
        unsafe_allow_html=True)

# ══ TAB 9 - BACKTESTING REAL + DASHBOARD RENDIMIENTO v16 ══════

# ══ TAB SCORE MVALLE v4 — 2 secciones con datos reales ════════
with tab_score:

    st.markdown(
        f'<div class="sec-header" style="background:#FFF7ED;border-color:#FB923C">'+
        f'<span style="font-size:20px">🎯</span>'+
        f'<div><span style="font-size:16px;font-weight:700;color:#EA580C">Score MVALLE</span>'+
        f'<span style="font-size:12px;color:{TXT_MUT};margin-left:10px">'+
        f'Ranking para invertir dinero real · NBIS vs Momentum</span>'+
        f'</div></div>', unsafe_allow_html=True)

    with st.expander("📋 ¿Qué busca este tab? — Cómo leer el Score MVALLE", expanded=False):
        st.markdown(
            "<div style='font-size:11px;line-height:1.8'>"
            "<strong style='color:#EA580C'>🎯 Tab Score MVALLE — Decisión para mañana al abrir mercado</strong><br>"
            "Úsalo a las <strong>16:00 hrs</strong> cuando cierra el mercado. "
            "Rankea tus posiciones de Greko + MVALLE para decidir "
            "<strong>cuál entra a MVALLE mañana</strong> con dinero real.<br><br>"

            "<strong>⚡ FLUJO RECOMENDADO DEL DÍA:</strong><br>"
            "1️⃣ Tab Posiciones → <strong>🔄 Actualizar Fases</strong> "
            "(descarga precios live · calcula RSI/MACD/DD · actualiza col F y AB en Sheet)<br>"
            "2️⃣ Tab Score MVALLE → <strong>🔄 Recalcular</strong> "
            "(lee Sheet actualizado · calcula score con datos live · muestra ranking)<br>"
            "3️⃣ Decide qué entra a MVALLE mañana según Score ≥15 y GTU Nivel 3-4<br><br>"

            "<strong>¿Cuáles acciones aparecen?</strong><br>"
            "🔸 Posiciones activas de <strong>Greko y MVALLE</strong> con Fase M3/M3-A o Momentum<br>"
            "🔸 M2 y señales SEGUIR/VIGILAR → no aparecen (aún en formación)<br>"
            "🔸 Las fases se actualizan con el botón de Tab Posiciones<br><br>"

            "<strong>📡 Datos para el cálculo — todos LIVE al momento de calcular:</strong><br>"
            "• N1 Fase: del Sheet (actualizada con 🔄 Actualizar Fases)<br>"
            "• N2 RSI, N3 DD, N5 MACD → yf.download batch live<br>"
            "• N4 Prob_NBIS → del Sheet (foto del día de entrada · no cambia)<br>"
            "• N6 SPY RSI → calculado live<br>"
            "• N7 Urgencia, Analistas, RevYoY, Upside → yfinance.info live<br><br>"

            "<strong>🔄 SECCIÓN NBIS — N1 a N7 (máx 20pts):</strong><br>"
            "N1 Fase: M3→5pts · M3-A→4pts · M2→3pts<br>"
            "N2 RSI (v19.2): 35-52→+3 NBIS · 52-82→+2 · 82+→+1 EXT<br>"
            "N3 DD LIVE: ≤-25%→+3 · ≤-15%→+2 · ≤-10%→+1<br>"
            "N4 Prob_NBIS: 30-45%→+3 · 45-50%→+2 · &gt;0→+1<br>"
            "N5 MACD LIVE: positivo→+3 · negativo→-1<br>"
            "N6 SPY LIVE: ≤60→+2 · ≤68→+1 · &gt;68→-2<br>"
            "N7 Urgencia: Post-Earn BEAT→+3 🟢 · Earn 3-7d→+2 · MISS→-2 🔴<br>"
            "<strong>Gestión NBIS:</strong> 100% · Stop -7% · T1 +8% · T2 +12%<br><br>"

            "<strong>⚡ SECCIÓN MOMENTUM — M1 a M7 (máx 20pts):</strong><br>"
            "M1 Fuente: Momentum→5pts · Sympathy→3pts · WL≥65→3pts<br>"
            "M2 RSI LIVE: 65-75→+3 · 75-82→+2 · &gt;82→+1<br>"
            "M3 MACD LIVE: positivo→+3 · negativo→-2<br>"
            "M4-M7: Score modelo · SPY · Prob · Urgencia<br>"
            "<strong>Gestión Momentum:</strong> 20-30% · Stop -5% · T1 +15% · T2 +30%<br><br>"

            "<strong>🎯 Umbrales de decisión (sobre 20 pts):</strong><br>"
            "🔴 <strong>≥15 → ENTRAR MAÑANA</strong> · 🟡 11-14 → Buena señal · ⚪ 7-10 → Esperar · ⬇️ &lt;7 → No entrar<br><br>"

            "<strong>🎯 GTU GrekoTrader + 📊 Rango Histórico (nuevas columnas):</strong><br>"
            "🎯 GTU: fórmula propia basada en correlaciones reales de 104 posiciones<br>"
            "Pesos: RSI×0.45 · Prob×0.25 · Momentum×0.15 · Score×0.10 · DD×RSI×0.03 · Earn×0.02<br>"
            "Niveles: 🔥N4 +40-80% · 🟢N3 +20-50% · 🟡N2 +10-25% · ⚪N1 +5-15%<br>"
            "📊 Rango Hist: basado en 8 perfiles de 104 posiciones reales (WR + P25/P50/P75)<br><br>"

            "<strong>🚫 Bloqueos:</strong> Earnings HOY · Sin analistas (NBIS) · Precio sobre target<br>"
            "<strong>💥 Señal ideal:</strong> RSI LIVE 48-65 · DD ≤-25% · MACD+ · Rev &gt;30% · GTU N3-4"
            "</div>", unsafe_allow_html=True)
    # Banner macro con SPY RSI live (calculado en el batch)
    _spy_rsi_banner = st.session_state.get("_spy_rsi_for_banner", 0)
    _banner_mercado_macro(_spy_rsi_banner)

    # Botón recalcular + live
    _sc1, _sc2, _sc3 = st.columns([1,1,2])
    with _sc1:
        if st.button("🔄 Recalcular", key="btn_recalc_score", use_container_width=True):
            st.session_state.pop("_score_rows_base", None)
            st.session_state.pop("_score_live_ok", None)
            st.session_state.pop("_score_total_activas", None)
            st.session_state.pop("_score_total_m3", None)
            st.rerun()
    with _sc2:
        _btn_live = st.button("⚡ Datos live", key="btn_live_score",
                              use_container_width=True,
                              help="Actualiza RSI/MACD actuales (5-10 seg)")

    # ── Contador SIEMPRE visible — fuera de todos los bloques condicionales ──
    _cnt_sc = st.empty()

    # ── Cargar posiciones activas ────────────────────────────────
    import time as _time_score
    _cache_ts = st.session_state.get("_score_cache_ts", 0)
    # TTL: limpiar caché si tiene más de 10 minutos (sin escribir timestamp aún)
    if _time_score.time() - _cache_ts > 600:
        st.session_state.pop("_score_rows_base", None)

    if "_score_rows_base" not in st.session_state:
        # ── Mostrar progreso con spinner + empty (patrón Momentum) ──
        with st.spinner("📡 Calculando Score MVALLE..."):
            _cnt_sc.info("📋 1 de 3: Leyendo posiciones Greko + MVALLE...")
            import time as _tsc2
            import datetime as _dtsc_main

            # ── PASO 1: Leer Sheets ─────────────────────────────────────
            _df_g  = leer_posiciones_sheets(_SHEET_NAME_GREKO)
            _df_mv = leer_posiciones_sheets(_SHEET_NAME_MAURI)

            _dfs_m = []
            if _df_mv is not None and not _df_mv.empty:
                _df_mv2 = _df_mv.copy(); _df_mv2["_cartera"] = "MVALLE 💰"
                _dfs_m.append(_df_mv2)
            if _df_g is not None and not _df_g.empty:
                _df_g2 = _df_g.copy(); _df_g2["_cartera"] = "Greko"
                _dfs_m.append(_df_g2)

            _df_combined = pd.concat(_dfs_m, ignore_index=True) if _dfs_m else None

            _nbis_rows_new = []
            _mom_rows_new  = []

            if _df_combined is not None and not _df_combined.empty:
                # Solo activas
                _fs_sc = _df_combined.get("Fecha_Salida", pd.Series(dtype=str)).astype(str)
                _df_act_sc = _df_combined[_fs_sc.apply(
                    lambda v: v.strip() in ("-","","nan","None","NaT"))].copy()

                def _es_m3_sc(row):
                    _f  = str(row.get("Fase","-")).upper()
                    _s  = str(row.get("Fuente","")).upper()
                    _ts = str(row.get("Tipo_Señal","-")).upper()
                    if any(x in _f for x in ["M3","FASE 3","FASE3","ENTRAR HOY",
                                              "ENTRAR","M3-A","ANTICIPAR","RUPTURA","PRE-SEÑAL"]):
                        return True
                    return "MOMENTUM" in _s or "MOMENTUM" in _ts or "SYMPATHY" in _s

                _df_m3_sc  = _df_act_sc[_df_act_sc.apply(_es_m3_sc, axis=1)].copy()
                _tks_sc    = [str(r.get("Ticker","")).upper().strip()
                              for _, r in _df_m3_sc.iterrows()
                              if str(r.get("Ticker","")).strip()]
                st.session_state["_score_total_activas"] = len(_df_act_sc)
                st.session_state["_score_total_m3"]      = len(_df_m3_sc)

                # ── PASO 2: yf.download BATCH — RSI/MACD/DD + SPY live ──
                _cnt_sc.info(f"⚡ 2 de 3: Descargando datos live para {len(_tks_sc)} acciones...")
                _live_sc   = {}   # {ticker: {rsi, macd, dd, precio}}
                _spy_rsi_live = 0.0
                if _tks_sc:
                    try:
                        import yfinance as _yf_sc_dl
                        _tks_dl = _tks_sc + ["SPY"]
                        _dl_sc  = _yf_sc_dl.download(
                            " ".join(_tks_dl), period="6mo",
                            auto_adjust=True, progress=False, threads=True)
                        _cl_sc  = _dl_sc.get("Close", _dl_sc)

                        for _tk_dl in _tks_dl:
                            try:
                                _s_dl = (_cl_sc[_tk_dl].dropna()
                                         if hasattr(_cl_sc,"columns") and _tk_dl in _cl_sc.columns
                                         else _cl_sc.dropna())
                                if len(_s_dl) < 20: continue
                                _pa_dl    = float(_s_dl.iloc[-1])
                                _pico_dl  = float(_s_dl.rolling(120, min_periods=1).max().iloc[-1])
                                _dd_dl    = round((_pa_dl-_pico_dl)/_pico_dl*100,1) if _pico_dl>0 else 0
                                _d_dl     = _s_dl.diff()
                                _g_dl     = _d_dl.clip(lower=0).rolling(14).mean()
                                _lo_dl    = (-_d_dl.clip(upper=0)).rolling(14).mean()
                                _rsi_dl   = round(float(100-100/(1+_g_dl.iloc[-1]/(_lo_dl.iloc[-1]+1e-9))),1)
                                _macd_dl  = "+" if _s_dl.ewm(span=12).mean().iloc[-1] > _s_dl.ewm(span=26).mean().iloc[-1] else "-"
                                if _tk_dl == "SPY":
                                    _spy_rsi_live = _rsi_dl
                                    st.session_state["_spy_rsi_for_banner"] = _rsi_dl
                                else:
                                    _live_sc[_tk_dl] = {
                                        "rsi": _rsi_dl, "macd": _macd_dl,
                                        "dd": _dd_dl, "precio": round(_pa_dl, 2)
                                    }
                            except Exception: pass
                    except Exception: pass

                # ── PASO 3: yf.info por ticker — fundamentales live ─────
                _cnt_sc.info(f"📊 3 de 3: Cargando fundamentales para {len(_tks_sc)} acciones...")
                _fund_sc = {}
                if _tks_sc:
                    try:
                        import yfinance as _yf_sc_info
                        import datetime as _dt_sc_info
                        for _i_sc, _tk_sc in enumerate(_tks_sc):
                            _cnt_sc.info(f"⚡ {_i_sc+1} de {len(_tks_sc)}: {_tk_sc}")
                            try:
                                _inf_sc  = _yf_sc_info.Ticker(_tk_sc).info or {}
                                _n_an    = int(_inf_sc.get("numberOfAnalystOpinions",0) or 0)
                                _tm_sc   = float(_inf_sc.get("targetMeanPrice",0) or 0)
                                _pa_sc   = float(_inf_sc.get("currentPrice",
                                           _inf_sc.get("regularMarketPrice",0)) or 0)
                                _rv_sc   = float(_inf_sc.get("revenueGrowth",0) or 0)
                                _et_sc   = _inf_sc.get("earningsTimestamp")
                                _ehoy_sc = False
                                if _et_sc:
                                    try:
                                        _ehoy_sc = (_dt_sc_info.datetime
                                                    .fromtimestamp(int(_et_sc)).date()
                                                    == _dt_sc_info.date.today())
                                    except Exception: pass
                                _up_sc    = round((_tm_sc-_pa_sc)/_pa_sc*100,1) if _tm_sc>0 and _pa_sc>0 else 0
                                _info_ok  = True
                                _fund_sc[_tk_sc] = {
                                    "n_analistas": _n_an, "target_mean": _tm_sc,
                                    "precio": _pa_sc, "revenue_yoy": round(_rv_sc*100,1),
                                    "upside": _up_sc, "earn_hoy": _ehoy_sc,
                                    "sobre_target": _pa_sc > _tm_sc > 0,
                                    "earn_ts_raw": _et_sc,  # timestamp raw para N7
                                    "info_ok": True,
                                }
                            except Exception:
                                _fund_sc[_tk_sc] = {
                                    "n_analistas":0,"target_mean":0,"precio":0,
                                    "revenue_yoy":None,"upside":0,"earn_hoy":False,
                                    "sobre_target":False,"info_ok":False,
                                }
                    except Exception: pass

                # ── Calcular score para cada posición ──────────────────
                for _, _r in _df_m3_sc.iterrows():
                    _tk    = str(_r.get("Ticker","")).upper().strip()
                    if not _tk: continue

                    # Datos del Sheet (solo lo que no cambia)
                    _fase   = str(_r.get("Fase","-"))
                    _fuente = str(_r.get("Fuente","")).upper()
                    _prob   = float(str(_r.get("Prob_NBIS",0) or 0).replace(",","."))
                    _cat    = str(_r.get("Cat_Fecha","-"))
                    _arras  = str(_r.get("Arrastradas","-"))
                    _area   = str(_r.get("Area","-"))
                    _sc_m   = float(str(_r.get("Score",0) or 0).replace(",","."))
                    _tipo_s = str(_r.get("Tipo_Señal",_r.get("Tipo_Senal","-")))
                    _pc     = float(str(_r.get("Precio_Compra",0) or 0).replace(",","."))

                    # Datos LIVE (N2, N3, N5, N6 — no del Sheet)
                    _ld      = _live_sc.get(_tk, {})
                    _rsi_ac  = _ld.get("rsi", 0)   # RSI live
                    _macd_e  = _ld.get("macd", "-") # MACD live
                    _dd_p    = _ld.get("dd", 0)     # DD live
                    _pa_live = _ld.get("precio", _pc)
                    _spy     = _spy_rsi_live         # SPY RSI live

                    # Fundamentales live
                    _f       = _fund_sc.get(_tk, {})
                    _n_an_f  = _f.get("n_analistas", 0)
                    _ehoy_f  = _f.get("earn_hoy", False)
                    _up_f    = _f.get("upside", 0)
                    _rv_f    = _f.get("revenue_yoy", None)
                    _sob_tgt = _f.get("sobre_target", False)
                    _info_ok = _f.get("info_ok", False)

                    # Tipo
                    if _tipo_s in ("-","","nan"):
                        if "MOMENTUM" in _fuente or "SYMPATHY" in _fuente: _tipo_s="Momentum"
                        elif _rsi_ac>=65: _tipo_s="Momentum"
                        else: _tipo_s="NBIS"

                    # Alertas
                    _alertas = []
                    _bloq    = False
                    if _ehoy_f: _alertas.append("🚫 Earnings HOY"); _bloq=True
                    if not _info_ok:
                        _alertas.append("⚠️ Sin datos live")
                    elif _n_an_f==0 and "MOMENTUM" not in _fuente:
                        _alertas.append("❌ Sin analistas"); _bloq=True
                    elif 0 < _n_an_f < 3:
                        _alertas.append(f"⚠️ Solo {_n_an_f} analistas")
                    if _sob_tgt:
                        _alertas.append(f"⚠️ Sobre target (+{_up_f:.0f}%)")
                    _alerta_str = " · ".join(_alertas) if _alertas else "—"

                    # RevYoY display
                    if _rv_f is None:
                        _rv_str = "N/D"
                    else:
                        _rv_str = f"{_rv_f:+.0f}%"

                    # N7 Urgencia — ajustado por earnings BEAT/MISS (v19.2)
                    # Detecta automáticamente la fecha y reacción del mercado
                    _urg=1; _urg_l="Sin earn próx"
                    try:
                        import datetime as _dtsc_n7
                        _hoy_n7 = _dtsc_n7.date.today()

                        # Buscar earnings desde yfinance (ya tenemos _inf_sc del paso 3)
                        _et_n7 = _f.get("earn_ts_raw", None)
                        # Si no está en _fund_sc, usar Cat_Fecha del Sheet como fallback
                        _earn_date_n7 = None
                        if _et_n7:
                            try:
                                _earn_date_n7 = _dtsc_n7.datetime.fromtimestamp(int(_et_n7)).date()
                            except Exception: pass
                        if not _earn_date_n7 and _cat not in ("-","","nan"):
                            try:
                                _earn_date_n7 = _dtsc_n7.date.fromisoformat(_cat[:10])
                            except Exception: pass

                        if _earn_date_n7:
                            _dias_earn = (_earn_date_n7 - _hoy_n7).days

                            if _dias_earn == 0:
                                # Earnings HOY → bloqueado
                                _urg=-3; _urg_l="Earn HOY 🚫"; _bloq=True

                            elif _dias_earn < 0:
                                # Earnings YA OCURRIÓ — detectar reacción del mercado
                                _dias_pasados = abs(_dias_earn)
                                if _dias_pasados <= 14:
                                    # Dentro de 14 días — analizar reacción de precio
                                    _pa_earn   = _pa_live  # precio actual
                                    _pc_earn   = _pc        # precio de entrada

                                    # Intentar obtener precio del día de earnings desde yf.download
                                    # ya tenemos el historial en _live_sc si calculamos bien
                                    # Proxy: si precio subió >3% desde entrada → BEAT
                                    #        si bajó >3% → MISS
                                    #        ±3% → IN LINE
                                    _pnl_post = (_pa_earn - _pc_earn) / _pc_earn * 100 if _pc_earn > 0 else 0

                                    # Complementar con revenueGrowth
                                    _rv_n7 = _rv_f if _rv_f is not None else 0

                                    if _pnl_post > 5 or _rv_n7 > 30:
                                        # Reacción positiva o revenue fuerte → BEAT
                                        _urg=3; _urg_l=f"Post-Earn BEAT +{_pnl_post:.0f}% 🟢"
                                    elif _pnl_post < -5:
                                        # Caída post-earnings → MISS o decepción
                                        _urg=-2; _urg_l=f"Post-Earn MISS {_pnl_post:.0f}% 🔴"
                                        if not _alertas: _alertas.append(f"⚠️ Post-earn -ve")
                                    else:
                                        # In line
                                        _urg=1; _urg_l=f"Post-Earn IN LINE ({_pnl_post:+.0f}%)"
                                else:
                                    # Más de 14 días → earnings ya digerido por el mercado
                                    _urg=1; _urg_l="Earn digerido"

                            elif _dias_earn <= 2:
                                # Earnings muy próximos → riesgo binario ALTO
                                _urg=1; _urg_l=f"Earn {_dias_earn}d ⚠️ riesgo binario"
                                _alertas.append(f"⚠️ Earnings en {_dias_earn}d — riesgo binario")

                            elif _dias_earn <= 7:
                                # Zona óptima — el mercado aún no reaccionó
                                _urg=2; _urg_l=f"Earn {_dias_earn}d · zona óptima"

                            else:
                                # Lejos
                                _urg=1; _urg_l=f"Earn en {_dias_earn}d"
                        else:
                            # Sin fecha de earnings → señal técnica pura
                            _urg=1; _urg_l="Sin earn detectado"

                    except Exception:
                        _urg=1; _urg_l="Urgencia N/D"
                    _alerta_str = " · ".join(_alertas) if _alertas else "—"

                    # SPY N6
                    if 0<_spy<=60:  _c_spy=2; _spy_l=f"SPY {_spy:.0f} ✅"
                    elif _spy<=68:  _c_spy=1; _spy_l=f"SPY {_spy:.0f} ⚠️"
                    elif _spy>68:   _c_spy=-2;_spy_l=f"SPY {_spy:.0f} 🚫"
                    else:           _c_spy=0; _spy_l="SPY N/D"

                    if _tipo_s=="NBIS":
                        _fu=_fase.upper().strip()
                        if _fu=="M3" or any(x in _fu for x in ["RUPTURA","ENTRAR HOY"]):
                            _n1=5;_n1_l="M3"
                        elif any(x in _fu for x in ["M3-A","ANTICIPAR","FASE 3","FASE3","PRE-SEÑAL"]):
                            _n1=4;_n1_l="M3-A"
                        elif any(x in _fu for x in ["M2","FASE 2","ENTRADA"]):
                            _n1=3;_n1_l="M2"
                        else: _n1=1;_n1_l=_fase[:10]

                        # N2 v19.2: RSI 65-82 también puntúa +2pts
                        # Datos reales: WR 84% en RSI 65-82 vs 32% en RSI 35-55
                        if 0<_rsi_ac<=52:   _n2=3;_n2_l=f"RSI {_rsi_ac:.0f}🟢 NBIS"
                        elif _rsi_ac<=65:   _n2=2;_n2_l=f"RSI {_rsi_ac:.0f}"
                        elif _rsi_ac<=82:   _n2=2;_n2_l=f"RSI {_rsi_ac:.0f} MOM"
                        elif _rsi_ac>82:    _n2=1;_n2_l=f"RSI {_rsi_ac:.0f} EXT"
                        else:               _n2=0;_n2_l="RSI N/D"

                        if _dd_p<=-25:  _n3=3;_n3_l=f"DD {_dd_p:.0f}%"
                        elif _dd_p<=-15:_n3=2;_n3_l=f"DD {_dd_p:.0f}%"
                        elif _dd_p<=-10:_n3=1;_n3_l=f"DD {_dd_p:.0f}%"
                        elif _dd_p<0:   _n3=0;_n3_l=f"DD {_dd_p:.0f}%"
                        else:           _n3=0;_n3_l="DD N/D"

                        if 30<=_prob<=45:_n4=3;_n4_l=f"Pr {_prob:.0f}%"
                        elif _prob<=50:  _n4=2;_n4_l=f"Pr {_prob:.0f}%"
                        elif _prob>0:    _n4=1;_n4_l=f"Pr {_prob:.0f}%"
                        else:           _n4=0;_n4_l="Pr N/D"

                        if _macd_e=="+": _n5=3;_n5_l="MACD+ 🟢"
                        elif _macd_e=="-":_n5=-1;_n5_l="MACD−"
                        else:           _n5=0;_n5_l="MACD N/D"

                        _total=max(0,min(20,_n1+_n2+_n3+_n4+_n5+_c_spy+_urg))
                        if _bloq:       _total=min(_total,8);_rec="🚫 BLOQUEADO";_rc="#6B7280"
                        elif _total>=15:_rec="🔴 ENTRAR MAÑANA";_rc="#DC2626"
                        elif _total>=11:_rec="🟡 Buena señal";_rc="#D97706"
                        elif _total>=7: _rec="⚪ Esperar";_rc="#64748B"
                        else:           _rec="⬇️ Baja prio";_rc="#94A3B8"

                        # GTU calculation
                        _earn_flag = 1 if (_urg_l and "⚡" in _urg_l) else 0
                        _gtu_result = calcular_gtu(
                            rsi=_rsi_ac, prob_nbis=_prob,
                            score_mvalle=_total, dd_abs=abs(_dd_p),
                            earnings_flag=_earn_flag)

                        _nbis_rows_new.append({
                            "Ticker":_tk,"Sector":_area[:14],"Fase":_n1_l,
                            "N1":_n1,"N2":_n2,"N3":_n3,"N4":_n4,"N5":_n5,
                            "N6":_c_spy,"N7":_urg,"TOTAL":_total,"Rec":_rec,"Rc":_rc,
                            "N2_l":_n2_l,"N3_l":_n3_l,"N4_l":_n4_l,"N5_l":_n5_l,
                            "N6_l":_spy_l,"N7_l":_urg_l,"Precio":_pa_live,
                            "RSI":_rsi_ac,"MACD":_macd_e,
                            "Gestion":"100% · Stop -7% · T1 +8% · T2 +12%",
                            "Analistas":_n_an_f,
                            "Upside":f"+{_up_f:.0f}%" if _info_ok else "N/D",
                            "RevYoY":_rv_str,
                            "Alertas":_alerta_str,"Bloqueado":_bloq,
                            "Cartera":str(_r.get("_cartera","Greko")),
                            "GTU":_gtu_result,
                        })
                    else:
                        # Momentum
                        if "MOMENTUM" in _fuente: _m1=5;_m1_l="Momentum"
                        elif "SYMPATHY" in _fuente or _arras not in ("-","","nan"):
                            _m1=3;_m1_l="Sympathy"
                        else: _m1=3;_m1_l="WL≥65"

                        if 65<=_rsi_ac<=75:_m2=3;_m2_l=f"RSI {_rsi_ac:.0f}🟢"
                        elif _rsi_ac<=82:  _m2=2;_m2_l=f"RSI {_rsi_ac:.0f}"
                        elif _rsi_ac>82:   _m2=1;_m2_l=f"RSI {_rsi_ac:.0f}"
                        elif _rsi_ac>0:    _m2=0;_m2_l=f"RSI {_rsi_ac:.0f}⚠️"
                        else:              _m2=0;_m2_l="RSI N/D"

                        if _macd_e=="+":  _m3=3;_m3_l="MACD+ 🟢"
                        elif _macd_e=="-":_m3=-2;_m3_l="MACD− 🚫"
                        else:             _m3=0;_m3_l="MACD N/D"

                        if _sc_m>=52:  _m4=3;_m4_l=f"Sc {_sc_m:.0f}"
                        elif _sc_m>=48:_m4=2;_m4_l=f"Sc {_sc_m:.0f}"
                        elif _sc_m>=42:_m4=1;_m4_l=f"Sc {_sc_m:.0f}"
                        else:          _m4=0;_m4_l="Sc bajo"

                        if 0<_spy<=65: _m5=2;_m5_l=f"SPY {_spy:.0f} ✅"
                        elif _spy<=70: _m5=1;_m5_l=f"SPY {_spy:.0f} ⚠️"
                        elif _spy>70:  _m5=-2;_m5_l=f"SPY {_spy:.0f} 🚫"
                        else:          _m5=0;_m5_l="SPY N/D"

                        if 40<=_prob<=50:_m6=2;_m6_l=f"Pr {_prob:.0f}%"
                        elif _prob>0:    _m6=1;_m6_l=f"Pr {_prob:.0f}%"
                        else:           _m6=0;_m6_l="Pr N/D"

                        _total=max(0,min(20,_m1+_m2+_m3+_m4+_m5+_m6+_urg))
                        if _bloq:       _total=min(_total,8);_rec="🚫 BLOQUEADO";_rc="#6B7280"
                        elif _total>=15:_rec="🔴 ENTRAR MAÑANA";_rc="#DC2626"
                        elif _total>=11:_rec="🟡 Buena señal";_rc="#D97706"
                        elif _total>=7: _rec="⚪ Esperar";_rc="#64748B"
                        else:           _rec="⬇️ Baja prio";_rc="#94A3B8"

                        # GTU calculation
                        _earn_flag_m = 1 if (_urg_l and "⚡" in _urg_l) else 0
                        _gtu_result_m = calcular_gtu(
                            rsi=_rsi_ac, prob_nbis=_prob,
                            score_mvalle=_total, dd_abs=abs(_dd_p),
                            earnings_flag=_earn_flag_m)

                        _mom_rows_new.append({
                            "Ticker":_tk,"Sector":_area[:14],"Fuente":_m1_l,
                            "M1":_m1,"M2":_m2,"M3":_m3,"M4":_m4,"M5":_m5,"M6":_m6,"M7":_urg,
                            "TOTAL":_total,"Rec":_rec,"Rc":_rc,
                            "M2_l":_m2_l,"M3_l":_m3_l,"M4_l":_m4_l,"M5_l":_m5_l,
                            "M6_l":_m6_l,"M7_l":_urg_l,"Precio":_pa_live,
                            "RSI":_rsi_ac,"MACD":_macd_e,
                            "Gestion":"20-30% · Stop -5% · T1 +15% · T2 +30%",
                            "Analistas":_n_an_f,
                            "Upside":f"+{_up_f:.0f}%" if _info_ok else "N/D",
                            "RevYoY":_rv_str,
                            "Alertas":_alerta_str,"Bloqueado":_bloq,
                            "Cartera":str(_r.get("_cartera","Greko")),
                            "GTU":_gtu_result_m,
                        })

            _nbis_rows_new.sort(key=lambda x: x["TOTAL"], reverse=True)
            _mom_rows_new.sort(key=lambda x:  x["TOTAL"], reverse=True)
            _cnt_sc.empty()
            st.session_state["_score_rows_base"] = (_nbis_rows_new, _mom_rows_new)
            st.session_state["_score_cache_ts"]  = _tsc2.time()
            st.session_state["_score_total_m3"]  = len(_nbis_rows_new)+len(_mom_rows_new)

    _nbis_rows, _mom_rows = st.session_state.get("_score_rows_base", ([],[]))

    # ── Botón Live (opcional) ─────────────────────────────────
    if _btn_live and (_nbis_rows or _mom_rows):
        _all_tks = [r["Ticker"] for r in _nbis_rows+_mom_rows]
        with st.spinner(f"⚡ Descargando datos live para {len(_all_tks)} acciones..."):
            try:
                import yfinance as _yf_live_sc
                _dl = _yf_live_sc.download(" ".join(_all_tks), period="3mo",
                    auto_adjust=True, progress=False, threads=True)
                _cl = _dl.get("Close", _dl)
                _live = {}
                for _tk in _all_tks:
                    try:
                        _s = _cl[_tk].dropna() if hasattr(_cl,"columns") and _tk in _cl.columns else _cl.dropna()
                        if len(_s) < 14: continue
                        _d = _s.diff(); _g = _d.clip(lower=0).rolling(14).mean()
                        _l = (-_d.clip(upper=0)).rolling(14).mean()
                        _rsi_l = round(float(100-100/(1+_g.iloc[-1]/(_l.iloc[-1]+1e-9))),1)
                        _macd_l = "+" if _s.ewm(span=12).mean().iloc[-1] > _s.ewm(span=26).mean().iloc[-1] else "-"
                        _live[_tk] = {"RSI": _rsi_l, "MACD": _macd_l}
                    except Exception: pass
                # Actualizar rows
                for rows_list in [_nbis_rows, _mom_rows]:
                    for r in rows_list:
                        if r["Ticker"] in _live:
                            r["RSI"]  = _live[r["Ticker"]]["RSI"]
                            r["MACD"] = _live[r["Ticker"]]["MACD"]
                _nbis_rows.sort(key=lambda x: x["TOTAL"], reverse=True)
                _mom_rows.sort(key=lambda x: x["TOTAL"], reverse=True)
                st.session_state["_score_rows_base"] = (_nbis_rows, _mom_rows)
                st.session_state["_score_live_ok"] = True
                st.success(f"✅ Datos live actualizados")
            except Exception as _e: st.warning(f"Error live: {_e}")

    _live_ok = st.session_state.get("_score_live_ok", False)

    # ── Helper render tabla ───────────────────────────────────
    def _cel(v, lbl=""):
        try:
            _v = int(v); _c = G if _v>0 else R if _v<0 else TXT_MUT
            _t = f"{_v:+d}<br><span style='font-size:8px;font-weight:400'>{lbl}</span>" if lbl else f"{_v:+d}"
            return f'<div style="text-align:center;font-weight:800;font-size:11px;color:{_c};line-height:1.3">{_t}</div>'
        except: return f'<div style="text-align:center;font-size:9px;color:{TXT_MUT}">{v}</div>'

    if not _nbis_rows and not _mom_rows:
        _total_act = st.session_state.get("_score_total_activas", 0)
        _total_m3s = st.session_state.get("_score_total_m3", 0)
        if _total_act > 0 and _total_m3s == 0:
            st.info(
                f"Tienes {_total_act} posiciones activas en Greko pero ninguna es M3 o Momentum confirmado. "
                f"Las señales M2 se quedan en Watchlist/Swing hasta confirmar. "
                f"Solo pasan a Score MVALLE las señales listas para dinero real.")
        else:
            st.info("No hay posiciones activas en Greko. Registra señales desde Swing Activo, Watchlist o Momentum.")
    else:
        _t_act = st.session_state.get("_score_total_activas", 0)
        _t_m3  = st.session_state.get("_score_total_m3", 0)
        st.markdown(
            f'<div style="font-size:11px;color:{TXT_MUT};margin-bottom:4px">'
            f'Posiciones Greko: {_t_act} activas → {_t_m3} con señal M3/Momentum · '
            f'{len(_nbis_rows)} NBIS · {len(_mom_rows)} Momentum · '
            f'{"✅ live" if _live_ok else "⚡ para datos live"}'
            f'</div>', unsafe_allow_html=True)

        # Info si hay M2 filtradas
        if _t_act > _t_m3:
            st.markdown(
                f'<div style="background:#F8FAFF;border:1px solid #BFDBFE;border-radius:6px;'
                f'padding:5px 12px;margin-bottom:8px;font-size:10px;color:#1D4ED8">'
                f'ℹ️ {_t_act - _t_m3} posiciones M2 filtradas · '
                f'M2 = señal en formación → queda en Watchlist/Swing hasta confirmar como M3'
                f'</div>', unsafe_allow_html=True)

        # ══ SECCIÓN NBIS ══════════════════════════════════════
        if _nbis_rows:
            st.markdown(
                f'<div style="background:#EFF6FF;border:1px solid #BFDBFE;'
                f'border-radius:8px 8px 0 0;padding:8px 14px;margin-top:12px">'
                f'<span style="font-size:13px;font-weight:800;color:#1D4ED8">🔄 NBIS — Rebote</span>'
                f'<span style="font-size:10px;color:#64748B;margin-left:10px">'
                f'Gestión: 100% · Stop -7% · T1 +8% · T2 +12%</span>'
                f'</div>', unsafe_allow_html=True)
            _CN = "70px 75px 40px 55px 55px 55px 50px 50px 45px 55px 55px 110px"
            st.markdown(
                f'<div style="display:grid;grid-template-columns:{_CN};gap:3px;'
                f'padding:5px 8px;background:#F8FAFF;border:1px solid #BFDBFE;'
                f'border-top:none;font-size:9px;font-weight:700;color:{TXT_MUT}">'
                f'<div>Ticker</div><div>Sector</div><div>N1<br>Fase</div>'
                f'<div style="text-align:center">N2<br>RSI</div>'
                f'<div style="text-align:center">N3<br>DD</div>'
                f'<div style="text-align:center">N4<br>Prob</div>'
                f'<div style="text-align:center">N5<br>MACD</div>'
                f'<div style="text-align:center">N6<br>SPY</div>'
                f'<div style="text-align:center;font-weight:900;color:#1D4ED8">TOTAL</div>'
                f'<div style="text-align:center">An.<br>Up%</div>'
                f'<div style="text-align:center">Rev<br>YoY</div>'
                f'<div>Recomendación / Alertas</div>'
                f'</div>', unsafe_allow_html=True)
            for _rn in _nbis_rows:
                _bg = "#FFFBEB" if _rn["TOTAL"]>=15 else "#F8FAFF" if _rn["TOTAL"]>=11 else BG_CARD
                _bl = "#FB923C" if _rn["TOTAL"]>=15 else "#93C5FD" if _rn["TOTAL"]>=11 else "#BFDBFE"
                _sc = G if _rn["TOTAL"]>=15 else A if _rn["TOTAL"]>=11 else TXT_MUT
                _gtu_rn = _rn.get("GTU", {})
                _rev_rn = _rn.get("RevYoY","N/D")
                _an_rn  = _rn.get("Analistas", 0)
                _up_rn  = _rn.get("Upside","N/D")
                st.markdown(
                    f'<div style="display:grid;grid-template-columns:{_CN};gap:3px;'
                    f'padding:7px 8px;background:{_bg};border:1px solid {_bl};'
                    f'border-top:none;border-left:3px solid {_bl}">'
                    f'<div style="font-weight:800;font-size:12px">{_rn["Ticker"]}</div>'
                    f'<div style="font-size:9px;color:{TXT_MUT}">{_rn["Sector"]}</div>'
                    f'<div style="font-size:10px;color:#1D4ED8;font-weight:700">{_rn["Fase"]}</div>'
                    f'{_cel(_rn["N2"],_rn["N2_l"])}{_cel(_rn["N3"],_rn["N3_l"])}'
                    f'{_cel(_rn["N4"],_rn["N4_l"])}{_cel(_rn["N5"],_rn["N5_l"])}'
                    f'{_cel(_rn["N6"],_rn["N6_l"])}'
                    f'<div style="text-align:center;font-size:18px;font-weight:900;color:{_sc}">{_rn["TOTAL"]}</div>'
                    f'<div style="font-size:10px;font-weight:700;color:{_rn["Rc"]}">{_rn["Rec"]}</div>'
                    f'</div>', unsafe_allow_html=True)
                # GTU + Rango Histórico + Fundamentales
                if _gtu_rn:
                    _rh_color = _gtu_rn.get("rh_color","#64748B")
                    _rh_wr    = _gtu_rn.get("rh_wr",0)
                    _rh_p50   = _gtu_rn.get("rh_p50",0)
                    _rh_p25   = _gtu_rn.get("rh_p25",0)
                    _rh_p75   = _gtu_rn.get("rh_p75",0)
                    _rh_n     = _gtu_rn.get("rh_n",0)
                    _rh_emoji = _gtu_rn.get("rh_emoji","—")
                    _gtu_score= _gtu_rn.get("gtu",0)
                    _gtu_emoji= _gtu_rn.get("emoji","")
                    _gtu_rango= _gtu_rn.get("rango","")
                    _gtu_nivel= _gtu_rn.get("nivel",1)
                    _gtu_color= _gtu_rn.get("color","#64748B")
                    _an_display = f"{_an_rn} analistas" if _an_rn > 0 else "Sin cobertura"
                    _rev_display= _rev_rn if _rev_rn not in ("","None","nan") else "N/D"
                    _up_display = _up_rn if _up_rn not in ("","None","nan","+0%") else "N/D"
                    st.markdown(
                        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;'
                        f'padding:4px 8px 8px 8px;background:{_bg};border:1px solid {_bl};'
                        f'border-top:none;border-left:3px solid {_bl};border-bottom:3px solid {_bl};'
                        f'margin-bottom:4px">'
                        # GTU GrekoTrader
                        f'<div style="background:#0A1020;border:1px solid {_gtu_color}40;border-radius:6px;padding:5px 8px">'
                        f'<div style="font-size:8px;color:#64748B;font-weight:700;text-transform:uppercase;letter-spacing:.8px">🎯 GTU GrekoTrader</div>'
                        f'<div style="font-size:13px;font-weight:800;color:{_gtu_color}">{_gtu_emoji} N{_gtu_nivel} · {_gtu_score:.0f}/100</div>'
                        f'<div style="font-size:9px;color:#94A3B8">Rango estimado: <strong style="color:{_gtu_color}">{_gtu_rango}</strong></div>'
                        f'</div>'
                        # Rango Histórico
                        f'<div style="background:#0A1020;border:1px solid {_rh_color}40;border-radius:6px;padding:5px 8px">'
                        f'<div style="font-size:8px;color:#64748B;font-weight:700;text-transform:uppercase;letter-spacing:.8px">📊 Rango Histórico</div>'
                        f'<div style="font-size:13px;font-weight:800;color:{_rh_color}">{_rh_emoji} WR {_rh_wr:.0f}% · N={_rh_n}</div>'
                        f'<div style="font-size:9px;color:#94A3B8">P25:{_rh_p25:+.0f}% · P50:{_rh_p50:+.0f}% · P75:{_rh_p75:+.0f}%</div>'
                        f'</div>'
                        # Fundamentales
                        f'<div style="background:#0A1020;border:1px solid #2A3547;border-radius:6px;padding:5px 8px">'
                        f'<div style="font-size:8px;color:#64748B;font-weight:700;text-transform:uppercase;letter-spacing:.8px">📈 Fundamentales</div>'
                        f'<div style="font-size:11px;font-weight:700;color:#E2E8F0">Rev: <span style="color:{"#22C55E" if _rev_display!="N/D" else "#64748B"}">{_rev_display}</span> · Up: <span style="color:{"#22C55E" if _up_display!="N/D" else "#64748B"}">{_up_display}</span></div>'
                        f'<div style="font-size:9px;color:#94A3B8">{_an_display} · {_rn.get("Alertas","—")[:35]}</div>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True)

        # ══ SECCIÓN MOMENTUM ══════════════════════════════════
        if _mom_rows:
            st.markdown(
                f'<div style="background:#FFFBEB;border:1px solid #FDE68A;'
                f'border-radius:8px 8px 0 0;padding:8px 14px;margin-top:16px">'
                f'<span style="font-size:13px;font-weight:800;color:#D97706">⚡ MOMENTUM — Catalizador</span>'
                f'<span style="font-size:10px;color:#64748B;margin-left:10px">'
                f'Gestión: 20-30% · Stop -5% · T1 +15% · T2 +30%</span>'
                f'</div>', unsafe_allow_html=True)
            _CM = "70px 75px 70px 55px 55px 55px 50px 45px 45px 55px 55px 110px"
            st.markdown(
                f'<div style="display:grid;grid-template-columns:{_CM};gap:3px;'
                f'padding:5px 8px;background:#FFFEF0;border:1px solid #FDE68A;'
                f'border-top:none;font-size:9px;font-weight:700;color:{TXT_MUT}">'
                f'<div>Ticker</div><div>Sector</div><div>M1<br>Fuente</div>'
                f'<div style="text-align:center">M2<br>RSI</div>'
                f'<div style="text-align:center">M3<br>MACD</div>'
                f'<div style="text-align:center">M4<br>Score</div>'
                f'<div style="text-align:center">M5<br>SPY</div>'
                f'<div style="text-align:center">M6<br>Prob</div>'
                f'<div style="text-align:center;font-weight:900;color:#D97706">TOTAL</div>'
                f'<div style="text-align:center">An.<br>Up%</div>'
                f'<div style="text-align:center">Rev<br>YoY</div>'
                f'<div>Recomendación / Alertas</div>'
                f'</div>', unsafe_allow_html=True)
            for _rm in _mom_rows:
                _bg = "#FFFBEB" if _rm["TOTAL"]>=15 else "#FFFEF0" if _rm["TOTAL"]>=11 else BG_CARD
                _bl = "#FB923C" if _rm["TOTAL"]>=15 else "#FDE68A" if _rm["TOTAL"]>=11 else "#FDE68A"
                _sc = G if _rm["TOTAL"]>=15 else A if _rm["TOTAL"]>=11 else TXT_MUT
                st.markdown(
                    f'<div style="display:grid;grid-template-columns:{_CM};gap:3px;'
                    f'padding:7px 8px;background:{_bg};border:1px solid {_bl};'
                    f'border-top:none;border-left:3px solid {_bl}">'
                    f'<div style="font-weight:800;font-size:12px">{_rm["Ticker"]}</div>'
                    f'<div style="font-size:9px;color:{TXT_MUT}">{_rm["Sector"]}</div>'
                    f'<div style="font-size:10px;color:#D97706;font-weight:700">{_rm["Fuente"]}</div>'
                    f'{_cel(_rm["M2"],_rm["M2_l"])}{_cel(_rm["M3"],_rm["M3_l"])}'
                    f'{_cel(_rm["M4"],_rm["M4_l"])}{_cel(_rm["M5"],_rm["M5_l"])}'
                    f'{_cel(_rm["M6"],_rm["M6_l"])}'
                    f'<div style="text-align:center;font-size:18px;font-weight:900;color:{_sc}">{_rm["TOTAL"]}</div>'
                    f'<div style="font-size:10px;font-weight:700;color:{_rm["Rc"]}">{_rm["Rec"]}</div>'
                    f'</div>', unsafe_allow_html=True)

        # ══ CAPITAL ALLOCATOR ═════════════════════════════════
        _top_nbis = [r for r in _nbis_rows  if r["TOTAL"] >= 11]
        _top_mom  = [r for r in _mom_rows   if r["TOTAL"] >= 11]

        if _top_nbis or _top_mom:
            st.markdown(f'<div style="margin-top:16px;font-size:13px;font-weight:800;color:{TXT}">💰 Candidatos para MVALLE</div>', unsafe_allow_html=True)

            for _ii, _rv in enumerate(_top_nbis[:3]):
                _ca, _cb, _cc = st.columns([2,1,1])
                with _ca:
                    st.markdown(
                        f'<div style="padding:7px 12px;background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px">'
                        f'<strong>{_rv["Ticker"]}</strong> <span style="color:{TXT_MUT};font-size:11px">🔄 NBIS · {_rv["Fase"]} · RSI {_rv["RSI"]:.0f} · MACD {_rv["MACD"]}</span>'
                        f'<br><span style="font-size:9px;color:#64748B">{_rv["Gestion"]}</span></div>',
                        unsafe_allow_html=True)
                with _cb:
                    _sc2 = G if _rv["TOTAL"]>=15 else A
                    st.markdown(f'<div style="padding:7px;text-align:center;background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;font-size:16px;font-weight:900;color:{_sc2}">{_rv["TOTAL"]}/20</div>', unsafe_allow_html=True)
                with _cc:
                    if st.button("✅ → MVALLE", key=f"mvnbis_{_rv['Ticker']}_{_ii}", use_container_width=True, type="primary"):
                        st.session_state[f"_prefill_mvalle_{_rv['Ticker']}"] = _rv
                        st.success(f"✅ {_rv['Ticker']} marcado NBIS → Tab 💼 Posiciones → MVALLE")

            for _jj, _rv in enumerate(_top_mom[:3]):
                _ca, _cb, _cc = st.columns([2,1,1])
                with _ca:
                    _gtu_rv   = _rv.get("GTU", {})
                    _gtu_e_rv = _gtu_rv.get("emoji","") if _gtu_rv else ""
                    _gtu_n_rv = _gtu_rv.get("nivel",0) if _gtu_rv else 0
                    _gtu_r_rv = _gtu_rv.get("rango","") if _gtu_rv else ""
                    _rh_p50_rv= _gtu_rv.get("rh_p50",0) if _gtu_rv else 0
                    _rh_wr_rv = _gtu_rv.get("rh_wr",0) if _gtu_rv else 0
                    _rev_rv   = _rv.get("RevYoY","N/D")
                    _an_rv    = _rv.get("Analistas",0)
                    _up_rv    = _rv.get("Upside","N/D")
                    st.markdown(
                        f'<div style="padding:7px 12px;background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px">'
                        f'<strong>{_rv["Ticker"]}</strong> <span style="color:{TXT_MUT};font-size:11px">⚡ Momentum · {_rv["Fuente"]} · RSI {_rv["RSI"]:.0f} · MACD {_rv["MACD"]}</span>'
                        f'<br><span style="font-size:9px;color:#64748B">{_rv["Gestion"]}</span>'
                        + (f'<br><span style="font-size:9px;font-weight:600">'
                           f'🎯 GTU: {_gtu_e_rv}N{_gtu_n_rv} {_gtu_r_rv} · '
                           f'📊 Hist WR {_rh_wr_rv:.0f}% P50:{_rh_p50_rv:+.0f}% · '
                           f'Rev:{_rev_rv} Up:{_up_rv} {_an_rv}analistas</span>' if _gtu_rv else '')
                        + f'</div>',
                        unsafe_allow_html=True)
                with _cb:
                    _sc2 = G if _rv["TOTAL"]>=15 else A
                    st.markdown(f'<div style="padding:7px;text-align:center;background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;font-size:16px;font-weight:900;color:{_sc2}">{_rv["TOTAL"]}/20</div>', unsafe_allow_html=True)
                with _cc:
                    if st.button("✅ → MVALLE", key=f"mvmom_{_rv['Ticker']}_{_jj}", use_container_width=True, type="primary"):
                        st.session_state[f"_prefill_mvalle_{_rv['Ticker']}"] = _rv
                        st.success(f"✅ {_rv['Ticker']} marcado Momentum → Tab 💼 Posiciones → MVALLE")

with tab9:
    # ══ TAB 9 — BACKTESTING Y ATR SIZING v19 ══════════════════

    # v19.1: Link al Dashboard de Métricas (app separada)
    st.markdown(
        f'<div style="background:#EFF6FF;border:1px solid #BFDBFE;'
        f'border-radius:10px;padding:14px 18px;margin-bottom:16px">'
        f'<div style="font-size:14px;font-weight:700;color:#1D4ED8;margin-bottom:6px">'
        f'📊 Dashboard de Métricas — App Separada</div>'
        f'<div style="font-size:11px;color:#1E40AF;margin-bottom:10px">'
        f'El dashboard de métricas corre en una app independiente para no afectar '
        f'la estabilidad de GrekoTrader v19.1. Lee los mismos Google Sheets.</div>'
        f'<div style="font-size:11px;color:#64748B;margin-bottom:8px">'
        f'Para iniciarlo: <code>streamlit run grekotrader_metricas.py --server.port 8502</code>'
        f'</div>'
        f'<a href="http://localhost:8502" target="_blank" '
        f'style="background:#2563EB;color:white;border-radius:6px;'
        f'padding:6px 16px;font-size:11px;font-weight:700;text-decoration:none">'
        f'📊 Abrir Dashboard de Métricas →</a>'
        f'</div>', unsafe_allow_html=True)

    # ══ v19: TABLA WR POR SECTOR — basado en trades REALES ════════
    st.markdown(
        f'<div style="font-size:15px;font-weight:800;color:{TXT};margin:16px 0 10px">'
        f'📊 Win Rate por Sector — Trades reales de tus posiciones</div>',
        unsafe_allow_html=True)

    # Leer las 3 carteras y combinar posiciones CERRADAS
    _wr_frames = []
    for _wr_sheet, _wr_label in [
        (_SHEET_NAME_MAURI,    "MVALLE"),
        (_SHEET_NAME_AMPARITO, "Amparito"),
        (_SHEET_NAME_GREKO,    "Greko"),
    ]:
        try:
            _df_wr = leer_posiciones_sheets(_wr_sheet)
            if _df_wr is not None and not _df_wr.empty:
                _df_wr["_cartera"] = _wr_label
                _wr_frames.append(_df_wr)
        except Exception:
            pass

    if _wr_frames:
        import pandas as _pd_wr
        _df_all = _pd_wr.concat(_wr_frames, ignore_index=True)
        _df_all = _normalizar_precios_df(_df_all)

        # Solo posiciones CERRADAS (tienen Precio_Salida > 0)
        if "Precio_Salida" in _df_all.columns and "Precio_Compra" in _df_all.columns:
            _df_all["Precio_Salida"] = _pd_wr.to_numeric(_df_all["Precio_Salida"], errors="coerce")
            _df_all["Precio_Compra"] = _pd_wr.to_numeric(_df_all["Precio_Compra"], errors="coerce")
            _df_cerradas = _df_all[
                _df_all["Precio_Salida"].notna() &
                (_df_all["Precio_Salida"] > 0)
            ].copy()

            if not _df_cerradas.empty:
                _df_cerradas["Retorno_%"] = (
                    (_df_cerradas["Precio_Salida"] - _df_cerradas["Precio_Compra"])
                    / _df_cerradas["Precio_Compra"] * 100
                ).round(1)
                _df_cerradas["Ganadora"] = _df_cerradas["Retorno_%"] > 0

                # Agrupar por Area (sector)
                _area_col = "Area" if "Area" in _df_cerradas.columns else None
                if _area_col:
                    _wr_by_sector = (
                        _df_cerradas.groupby(_area_col)
                        .agg(
                            Señales  = ("Ticker",   "count"),
                            Ganadoras= ("Ganadora",  "sum"),
                            Avg_Ret  = ("Retorno_%", "mean"),
                            Max_Ret  = ("Retorno_%", "max"),
                            Min_Ret  = ("Retorno_%", "min"),
                        )
                        .reset_index()
                    )
                    _wr_by_sector["WR_%"] = (
                        _wr_by_sector["Ganadoras"] / _wr_by_sector["Señales"] * 100
                    ).round(0).astype(int)
                    _wr_by_sector["Avg_Ret"] = _wr_by_sector["Avg_Ret"].round(1)
                    _wr_by_sector = _wr_by_sector.sort_values("WR_%", ascending=False)

                    # Renderizar tabla
                    _wr_rows = ""
                    for _, _rw in _wr_by_sector.iterrows():
                        _wr_pct  = int(_rw["WR_%"])
                        _wr_c    = G if _wr_pct >= 70 else A if _wr_pct >= 50 else R
                        _wr_bg   = G_BG if _wr_pct >= 70 else A_BG if _wr_pct >= 50 else R_BG
                        _ret_c   = G if _rw["Avg_Ret"] > 0 else R
                        _sector  = str(_rw[_area_col])
                        _wr_rows += (
                            f'<tr style="background:{_wr_bg}">'
                            f'<td style="font-weight:700;color:{TXT}">{_sector}</td>'
                            f'<td style="text-align:center">{int(_rw["Señales"])}</td>'
                            f'<td style="text-align:center">{int(_rw["Ganadoras"])}</td>'
                            f'<td style="text-align:center;font-weight:800;color:{_wr_c}">'
                            f'{_wr_pct}%</td>'
                            f'<td style="text-align:center;color:{_ret_c}">'
                            f'{_rw["Avg_Ret"]:+.1f}%</td>'
                            f'<td style="text-align:center;color:{G}">'
                            f'{_rw["Max_Ret"]:+.1f}%</td>'
                            f'<td style="text-align:center;color:{R}">'
                            f'{_rw["Min_Ret"]:+.1f}%</td>'
                            f'</tr>'
                        )

                    # Totales
                    _tot_sen = len(_df_cerradas)
                    _tot_gan = int(_df_cerradas["Ganadora"].sum())
                    _tot_wr  = round(_tot_gan/_tot_sen*100) if _tot_sen > 0 else 0
                    _tot_ret = round(_df_cerradas["Retorno_%"].mean(), 1)

                    st.markdown(
                        f'<div class="tbl-wrap">'
                        f'<table class="dtbl">'
                        f'<thead><tr>'
                        f'<th>Sector / Área</th><th>Señales</th><th>Ganadoras</th>'
                        f'<th>WR%</th><th>Avg Retorno</th><th>Mejor</th><th>Peor</th>'
                        f'</tr></thead>'
                        f'<tbody>{_wr_rows}</tbody>'
                        f'<tfoot><tr style="font-weight:800;border-top:2px solid {BOR}">'
                        f'<td>TOTAL</td>'
                        f'<td style="text-align:center">{_tot_sen}</td>'
                        f'<td style="text-align:center">{_tot_gan}</td>'
                        f'<td style="text-align:center;color:{G if _tot_wr>=60 else R}">{_tot_wr}%</td>'
                        f'<td style="text-align:center;color:{G if _tot_ret>0 else R}">{_tot_ret:+.1f}%</td>'
                        f'<td></td><td></td></tr></tfoot>'
                        f'</table></div>',
                        unsafe_allow_html=True)

                    # Recomendación automática
                    _mejores = _wr_by_sector[_wr_by_sector["WR_%"] >= 70]["Area"].tolist()
                    _peores  = _wr_by_sector[_wr_by_sector["WR_%"] < 40]["Area"].tolist()
                    if _mejores:
                        st.success(f"🎯 **Sectores con mayor WR:** {', '.join(_mejores[:3])} — concentrar señales aquí")
                    if _peores:
                        st.warning(f"⚠️ **Sectores con bajo WR:** {', '.join(_peores[:3])} — revisar criterios o evitar")
                else:
                    st.info("ℹ️ Agrega la columna 'Area' en tus Sheets de posiciones para ver WR por sector.")
            else:
                st.info("ℹ️ Sin posiciones cerradas aún. El WR por sector aparecerá cuando registres salidas.")
        else:
            st.info("ℹ️ Las posiciones necesitan las columnas Precio_Compra y Precio_Salida.")
    else:
        st.info("ℹ️ Conecta las planillas de posiciones para ver el análisis de WR por sector.")

    st.divider()
    # ══════════════════════════════════════════════════════════════

    st.markdown(
        f'<div style="background:#F0FDF4;border:2px solid #86EFAC;border-radius:14px;'
        f'padding:16px 20px;margin-bottom:16px">'
        f'<div style="font-size:16px;font-weight:800;color:#16A34A;margin-bottom:8px">'
        f'📊 ¿Para qué sirve este Tab?</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:12px;color:{TXT}">'
        f'  <div style="background:white;border-radius:8px;padding:10px">'
        f'    <div style="font-weight:700;color:#16A34A;margin-bottom:4px">🔬 Backtesting Real</div>'
        f'    Prueba el modelo con datos históricos reales. Responde: si hubieras seguido las señales M2/M3 '
        f'    del modelo en los últimos 6 meses, ¿cuánto hubieras ganado o perdido? '
        f'    Calcula win rate real, promedio de ganancia y pérdida.'
        f'  </div>'
        f'  <div style="background:white;border-radius:8px;padding:10px">'
        f'    <div style="font-weight:700;color:#2563EB;margin-bottom:4px">📐 ATR Sizing</div>'
        f'    Calcula cuántas acciones comprar para que si el trade sale mal, '
        f'    pierdas exactamente lo que decidiste arriesgar (ej: $500). '
        f'    Usa el ATR (volatilidad real) del ticker para calcular el stop loss.'
        f'  </div>'
        f'</div></div>', unsafe_allow_html=True)

    # ── Selector de herramienta ─────────────────────────────
    _tool = st.radio("Selecciona herramienta",
        ["🔬 Backtesting — ¿funcionó el modelo?",
         "📐 ATR Sizing — ¿cuántas acciones comprar?"],
        horizontal=True, label_visibility="collapsed")

    # ════════════════════════════════════════════════════════
    # SECCIÓN 1 — BACKTESTING
    # ════════════════════════════════════════════════════════
    if "Backtesting" in _tool:
        st.markdown(
            f'<div class="info-box">'
            f'<strong>Cómo funciona:</strong> El sistema descarga precios históricos de cada ticker, '
            f'busca los momentos donde el modelo habría generado señal M2/M3, '
            f'simula la entrada al precio de cierre de ese día, y calcula si '
            f'el precio llegó a Target +8% antes de tocar el Stop Loss (ATR x 1.5). '
            f'⏱️ Puede tardar 30-60 segundos dependiendo de cuántos tickers analices.</div>',
            unsafe_allow_html=True)

        _bc1, _bc2, _bc3, _bc4 = st.columns(4)
        with _bc1:
            _bt_tickers = st.text_input(
                "Tickers a testear",
                value="NBIS,AMD,IONQ,NVDA,VRDN",
                help="Pon los tickers de acciones que quieres analizar, separados por coma"
            )
        with _bc2:
            _bt_meses = st.selectbox("¿Cuántos meses atrás?",
                ["3 meses","6 meses","9 meses","12 meses"], index=1,
                help="Período histórico a analizar. Más meses = más señales = más confiable")
            _bt_meses_n = int(_bt_meses.split()[0])
        with _bc3:
            _bt_riesgo = st.number_input("Riesgo por trade ($USD)",
                min_value=100, max_value=10000, value=500, step=100,
                help="¿Cuánto estás dispuesto a perder si el trade sale mal?")
        with _bc4:
            _bt_dias = st.selectbox("Días máx por trade",
                [10,15,20], index=1,
                help="Cuántos días esperar antes de cerrar el trade")

        st.markdown(
            f'<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;'
            f'padding:10px 14px;margin:8px 0;font-size:11px;color:#1D4ED8">'
            f'📋 <strong>Lo que verás al ejecutar:</strong> Win Rate % real · '
            f'Promedio ganancia vs pérdida · Expectativa matemática por trade · '
            f'Tabla de cada señal con precio entrada, salida y resultado</div>',
            unsafe_allow_html=True)

        if st.button("🔬 Ejecutar Backtesting — analizar señales históricas",
                     use_container_width=True, type="primary", key="btn_bt_v18"):
            _tickers_list = [t.strip().upper() for t in _bt_tickers.split(",") if t.strip()]
            _progress = st.progress(0, text=f"Iniciando análisis de {len(_tickers_list)} tickers...")
            _resultados_bt = []
            _all_trades    = []
            for _idx, _tk_bt in enumerate(_tickers_list):
                _progress.progress(
                    (_idx) / len(_tickers_list),
                    text=f"Analizando {_tk_bt} ({_idx+1}/{len(_tickers_list)})... puede tardar 10-15s por ticker"
                )
                _r = backtest_real_v16(_tk_bt, meses=_bt_meses_n, dias_max=_bt_dias)
                if _r["_ok"]:
                    _resultados_bt.append(_r)
                    _all_trades.extend(_r["trades"])
            _progress.progress(1.0, text="✅ Análisis completado")
            st.session_state["bt_v19_resultados"] = _resultados_bt
            st.session_state["bt_v19_trades"]     = _all_trades
            st.session_state["bt_v19_ts"]         = datetime.datetime.now().strftime("%H:%M")

        _bt_res  = st.session_state.get("bt_v19_resultados", [])
        _bt_trds = st.session_state.get("bt_v19_trades", [])
        _bt_ts   = st.session_state.get("bt_v19_ts", "")

        if not _bt_res:
            st.markdown(
                f'<div style="background:{BG_HEAD};border:2px dashed {BOR};border-radius:12px;'
                f'padding:40px;text-align:center">'
                f'<div style="font-size:40px;margin-bottom:12px">🔬</div>'
                f'<div style="font-size:15px;font-weight:700;color:{TXT};margin-bottom:6px">'
                f'Aún no has ejecutado el backtesting</div>'
                f'<div style="font-size:12px;color:{TXT_MUT}">'
                f'1. Escribe los tickers que quieres analizar (ej: NBIS,AMD,IONQ)<br>'
                f'2. Elige el período (recomendado: 6 meses)<br>'
                f'3. Haz click en el botón verde <strong>"Ejecutar Backtesting"</strong><br>'
                f'4. Espera 30-60 segundos mientras descarga datos históricos</div>'
                f'</div>', unsafe_allow_html=True)
        else:
            # ── RESUMEN GLOBAL ───────────────────────────────
            import numpy as _np
            _n_tot  = sum(r["n_señales"]   for r in _bt_res)
            _n_win  = sum(r["n_ganadoras"] for r in _bt_res)
            _n_los  = sum(r["n_perdedoras"] for r in _bt_res)
            _wr_g   = round(_n_win / _n_tot * 100, 1) if _n_tot > 0 else 0
            _avg_g  = round(_np.mean([t["resultado"] for t in _bt_trds if t.get("ganadora")]), 2) if any(t.get("ganadora") for t in _bt_trds) else 0
            _avg_p  = round(_np.mean([t["resultado"] for t in _bt_trds if not t.get("ganadora")]), 2) if any(not t.get("ganadora") for t in _bt_trds) else 0
            _ratio  = round(abs(_avg_g / _avg_p), 2) if _avg_p != 0 else 0
            _expect = round(_wr_g/100 * _avg_g + (1-_wr_g/100) * _avg_p, 2)
            _wr_col = "#16A34A" if _wr_g >= 60 else "#D97706" if _wr_g >= 50 else "#DC2626"

            st.markdown(f'<div style="font-size:11px;color:{TXT_MUT};margin:6px 0">Ejecutado {_bt_ts} · {_n_tot} señales analizadas</div>', unsafe_allow_html=True)

            # KPIs
            _k1,_k2,_k3,_k4,_k5 = st.columns(5)
            for _kc, _kv, _kl, _kco, _khelp in [
                (_k1, f"{_wr_g}%",        "Win Rate",             _wr_col,   "De cada 100 señales, cuántas terminaron en ganancia"),
                (_k2, f"+{_avg_g}%",      "Promedio ganadora",    "#16A34A", "Cuando el modelo acierta, ¿cuánto gana en promedio?"),
                (_k3, f"{_avg_p}%",       "Promedio perdedora",   "#DC2626", "Cuando el modelo falla, ¿cuánto pierde en promedio?"),
                (_k4, f"{_ratio}x",       "Ratio ganancia/pérdida","#7C3AED","Si el ratio > 1 el sistema es rentable a largo plazo"),
                (_k5, f"{_expect:+.1f}%", "Expectativa/trade",    "#16A34A" if _expect>0 else "#DC2626",
                                                                              "Resultado esperado promedio por cada señal tomada"),
            ]:
                with _kc:
                    st.markdown(
                        f'<div style="background:{BG_CARD};border:1px solid {BOR};'
                        f'border-radius:10px;padding:12px;text-align:center" title="{_khelp}">'
                        f'<div style="font-size:10px;color:{TXT_MUT};font-weight:600">{_kl}</div>'
                        f'<div style="font-size:24px;font-weight:800;color:{_kco}">{_kv}</div>'
                        f'</div>', unsafe_allow_html=True)

            # Interpretación
            _msg = ("✅ El modelo es rentable — gana más de lo que pierde" if _expect > 0 and _wr_g >= 50
                    else "⚠️ Revisar — win rate o ratio necesitan mejorar" if _expect > -2
                    else "❌ Modelo necesita ajuste — pérdida esperada por trade")
            st.markdown(
                f'<div style="background:{"#F0FDF4" if _expect>0 else "#FEF2F2"};'
                f'border:1px solid {"#86EFAC" if _expect>0 else "#FCA5A5"};'
                f'border-radius:8px;padding:10px 14px;margin:10px 0;font-size:12px">'
                f'<strong>{_msg}</strong><br>'
                f'Win Rate {_wr_g}% · Ganancia avg +{_avg_g}% · Pérdida avg {_avg_p}% · '
                f'Cada señal tomada tiene expectativa de {_expect:+.1f}%</div>',
                unsafe_allow_html=True)

            # Tabla de trades
            if _bt_trds:
                # ── RENDIMIENTO POR SECTOR ──────────────────────
                _areas_bt = {}
                for _t in _bt_trds:
                    _a = str(_t.get("area", _t.get("Area", "Sin área")))
                    if not _a or _a in ("", "-", "nan"): _a = "Sin área"
                    if _a not in _areas_bt:
                        _areas_bt[_a] = {"total":0,"gan":0,"res":[]}
                    _areas_bt[_a]["total"] += 1
                    if _t.get("ganadora"): _areas_bt[_a]["gan"] += 1
                    _areas_bt[_a]["res"].append(float(_t.get("resultado",0)))

                if len(_areas_bt) > 1:
                    st.markdown(
                        f'<div style="font-size:13px;font-weight:700;color:{TXT};margin:14px 0 6px">'
                        f'📊 Rendimiento por Sector — ¿cuál funciona mejor con el modelo?</div>',
                        unsafe_allow_html=True)
                    _area_rows_bt = ""
                    for _an, _av in sorted(_areas_bt.items(),
                            key=lambda x: x[1]["gan"]/max(x[1]["total"],1), reverse=True):
                        _wr_a  = round(_av["gan"]/_av["total"]*100,1) if _av["total"]>0 else 0
                        _avg_a = round(sum(_av["res"])/_av["total"],1) if _av["total"]>0 else 0
                        _wrc   = G if _wr_a>=60 else A if _wr_a>=50 else R
                        _avrc  = "#16A34A" if _avg_a>0 else "#DC2626"
                        _sector_c = SECTOR_COLORS.get(_an, TXT_MUT)
                        _area_rows_bt += (
                            f"<tr>"
                            f"<td><span style='color:{_sector_c};font-weight:600'>{_an}</span></td>"
                            f"<td style='text-align:center'>{_av['total']}</td>"
                            f"<td style='text-align:center;color:{_wrc};font-weight:800'>{_wr_a}%</td>"
                            f"<td style='text-align:center;color:{_avrc};font-weight:700'>{_avg_a:+.1f}%</td>"
                            f"<td style='text-align:center'>"
                            f"{'✅ Modelo funciona bien aquí' if _wr_a>=60 else '⚠️ Mejorable' if _wr_a>=50 else '❌ Filtrar este sector'}"
                            f"</td>"
                            f"</tr>"
                        )
                    st.markdown(
                        f'<div class="tbl-wrap"><table class="dtbl">'
                        f'<thead><tr>'
                        f'<th>Sector</th><th>Señales</th><th>Win Rate</th>'
                        f'<th>Promedio %</th><th>Diagnóstico</th>'
                        f'</tr></thead>'
                        f'<tbody>{_area_rows_bt}</tbody></table></div>',
                        unsafe_allow_html=True)

                st.markdown(f'<div style="font-size:13px;font-weight:700;color:{TXT};margin:10px 0 4px">📋 Detalle de señales históricas</div>', unsafe_allow_html=True)
                _rows = ""
                for _t in sorted(_bt_trds, key=lambda x: x.get("fecha",""), reverse=True)[:40]:
                    _rc = "#16A34A" if _t.get("ganadora") else "#DC2626"
                    _res = float(_t.get("resultado",0))
                    _rows += (
                        f"<tr style='background:{'#F0FDF420' if _t.get('ganadora') else '#FEF2F220'}'>"
                        f"<td><strong style='color:{B}'>{_t.get('ticker','')}</strong></td>"
                        f"<td style='font-size:11px;color:{TXT_MUT}'>{_t.get('fecha','')}</td>"
                        f"<td><strong>${_t.get('entrada',0):.2f}</strong></td>"
                        f"<td>${_t.get('salida',0):.2f}</td>"
                        f"<td style='color:{TXT_MUT};font-size:10px'>${_t.get('stop',0):.2f}</td>"
                        f"<td><span style='color:{_rc};font-weight:800'>{_res:+.1f}%</span></td>"
                        f"<td>{'✅' if _t.get('ganadora') else '❌'}</td>"
                        f"<td style='font-size:10px;color:{TXT_MUT}'>{_t.get('dias_trade',0)}d</td>"
                        f"</tr>"
                    )
                _hdr = "<tr>" + "".join(f"<th>{h}</th>" for h in ["Ticker","Fecha","Entrada","Salida","Stop","Resultado","✓","Días"]) + "</tr>"
                st.markdown(
                    f'<div class="tbl-wrap"><table class="dtbl"><thead>{_hdr}</thead><tbody>{_rows}</tbody></table></div>',
                    unsafe_allow_html=True)

                _csv_bt = "\n".join([",".join(str(v) for v in [
                    t.get("ticker",""),t.get("fecha",""),t.get("entrada",0),
                    t.get("salida",0),t.get("stop",0),t.get("resultado",0),
                    "SI" if t.get("ganadora") else "NO",t.get("dias_trade",0)
                ]) for t in _bt_trds])
                st.download_button("⬇️ Descargar CSV de señales",
                    ("Ticker,Fecha,Entrada,Salida,Stop,Resultado%,Ganadora,Dias\n" + _csv_bt).encode(),
                    f"backtesting_v18_{datetime.date.today()}.csv", "text/csv",
                    use_container_width=True, key="dl_senales_csv")

    # ════════════════════════════════════════════════════════
    # SECCIÓN EXPORTACIÓN SEMANAL — memoria de trades
    # ════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown(
        f'<div style="font-size:13px;font-weight:700;color:{TXT};margin-bottom:8px">'
        f'📤 Exportación semanal — memoria de trades</div>',
        unsafe_allow_html=True)

    _exp_col1, _exp_col2, _exp_col3 = st.columns(3)
    with _exp_col1:
        # Exportar señales del modelo (candidatos guardados)
        _local_trades = st.session_state.get("memoria_trades_local", [])
        if _local_trades:
            import pandas as _pd_exp, io as _io_exp, datetime as _dt_exp
            _df_exp = _pd_exp.DataFrame(_local_trades)
            _csv_exp = _df_exp.to_csv(index=False).encode("utf-8")
            st.download_button(
                f"⬇️ Señales del modelo ({len(_local_trades)} registros)",
                _csv_exp,
                f"senales_modelo_{_dt_exp.date.today()}.csv",
                "text/csv", use_container_width=True,
                help="Señales M2/M3 que guardaste como candidatos esta semana",
                key="dl_senales_local",
            )
        else:
            st.info("Sin señales registradas aún")

    with _exp_col2:
        # Exportar trades reales (posiciones reales Tab6/7)
        _pos_mauri = st.session_state.get("posiciones_df_mauri")
        _pos_amp   = st.session_state.get("posiciones_df_amparito")
        if _pos_mauri is not None or _pos_amp is not None:
            import pandas as _pd_pos, datetime as _dt_pos
            _frames = []
            if _pos_mauri is not None:
                _df_m = _pos_mauri.copy(); _df_m["Cartera"] = "Mauri"; _frames.append(_df_m)
            if _pos_amp is not None:
                _df_a = _pos_amp.copy(); _df_a["Cartera"] = "Amparito"; _frames.append(_df_a)
            if _frames:
                _df_pos_exp = _pd_pos.concat(_frames, ignore_index=True)
                st.download_button(
                    "⬇️ Mis posiciones actuales",
                    _df_pos_exp.to_csv(index=False).encode("utf-8"),
                    f"posiciones_{_dt_pos.date.today()}.csv",
                    "text/csv", use_container_width=True,
                    help="Estado actual de todas tus posiciones con P&L",
                    key="dl_pos_act",
                )
        else:
            st.info("Carga tus posiciones primero")

    with _exp_col3:
        # Botón para limpiar memoria local (después de exportar)
        if st.button("🗑️ Limpiar memoria local",
                     key="btn_clear_local", use_container_width=True,
                     help="Borra las señales guardadas localmente (ya las descargaste)"):
            st.session_state["memoria_trades_local"] = []
            st.success("✅ Memoria local limpiada")

    # Instrucción semanal
    st.markdown(
        f'<div style="background:#FFFBEB;border:1px solid #FCD34D;border-radius:8px;'
        f'padding:10px 14px;font-size:11px;color:#92400E;margin-top:8px">'
        f'📅 <strong>Rutina semanal recomendada (lunes, 10 min):</strong> '
        f'1) Descargar "Señales del modelo" · '
        f'2) Descargar "Mis posiciones" · '
        f'3) Pegar ambos en Google Sheets "GrekoTrader_Memoria" · '
        f'4) Actualizar campo Error_Modelo para señales que fallaron · '
        f'5) Limpiar memoria local'
        f'</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ════════════════════════════════════════════════════════
    # SECCIÓN 2 — ATR SIZING (else del radio _tool)
    # ════════════════════════════════════════════════════════
    if "ATR Sizing" in _tool:
        st.markdown(
            f'<div class="info-box">'
            f'<strong>¿Qué es el ATR Sizing?</strong> El ATR (Average True Range) mide '
            f'cuánto se mueve una acción en un día normal. Usamos eso para calcular '
            f'el stop loss y de ahí cuántas acciones comprar. '
            f'Ejemplo: Si arriesgas $500 y el stop está a $12 de distancia → compras 41 acciones.</div>',
            unsafe_allow_html=True)

        _as1, _as2, _as3 = st.columns(3)
        with _as1:
            _atr_tk = st.text_input("Ticker", value="NBIS", key="atr_tk_v18").upper()
        with _as2:
            _atr_capital = st.number_input("¿Cuánto puedes perder si sale mal? ($)",
                min_value=50, max_value=50000, value=500, step=50,
                help="Capital máximo en riesgo por este trade")
        with _as3:
            _atr_precio = st.number_input("Precio actual ($)",
                min_value=0.5, max_value=10000.0, value=100.0, step=0.5)

        if st.button("📐 Calcular — ¿cuántas acciones comprar?",
                     use_container_width=True, type="primary", key="btn_atr_v18"):
            with st.spinner(f"Calculando ATR real de {_atr_tk}..."):
                _sz = sizing_por_atr(
                    ticker=_atr_tk, precio_actual=_atr_precio,
                    capital_riesgo_usd=_atr_capital, atr_mult=1.5,
                    score=60, vix_val=float(vix.get("valor",20))
                )
                st.session_state["atr_v18"] = _sz

        _sz_r = st.session_state.get("atr_v18")
        if not _sz_r:
            st.markdown(
                f'<div style="background:{BG_HEAD};border:2px dashed {BOR};border-radius:12px;'
                f'padding:40px;text-align:center">'
                f'<div style="font-size:40px;margin-bottom:12px">📐</div>'
                f'<div style="font-size:15px;font-weight:700;color:{TXT};margin-bottom:6px">'
                f'Ingresa el ticker y el capital en riesgo</div>'
                f'<div style="font-size:12px;color:{TXT_MUT}">'
                f'El sistema descargará el ATR real de los últimos 14 días<br>'
                f'y calculará exactamente cuántas acciones comprar</div>'
                f'</div>', unsafe_allow_html=True)
        else:
            _c1, _c2 = st.columns(2)
            with _c1:
                st.markdown(
                    f'<div style="background:{G_BG};border:2px solid {G_BOR};border-radius:14px;padding:20px">'
                    f'<div style="font-size:14px;font-weight:800;color:{G};margin-bottom:14px">'
                    f'📐 Resultado para {_atr_tk}</div>'
                    f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">'
                    f'  <div style="background:white;border-radius:8px;padding:10px;text-align:center">'
                    f'    <div style="font-size:10px;color:{TXT_MUT};font-weight:600">ATR REAL (14d)</div>'
                    f'    <div style="font-size:22px;font-weight:800;color:#7C3AED">${_sz_r["atr"]}</div>'
                    f'    <div style="font-size:9px;color:{TXT_SOFT}">volatilidad diaria promedio</div>'
                    f'  </div>'
                    f'  <div style="background:#FEF2F2;border-radius:8px;padding:10px;text-align:center">'
                    f'    <div style="font-size:10px;color:{R};font-weight:600">STOP LOSS</div>'
                    f'    <div style="font-size:22px;font-weight:800;color:{R}">${_sz_r["stop_precio"]}</div>'
                    f'    <div style="font-size:9px;color:{TXT_SOFT}">{_sz_r["detalle"]}</div>'
                    f'  </div>'
                    f'  <div style="background:#DBEAFE;border-radius:8px;padding:12px;text-align:center;grid-column:span 2">'
                    f'    <div style="font-size:10px;color:#1D4ED8;font-weight:700">COMPRAR</div>'
                    f'    <div style="font-size:36px;font-weight:900;color:#1D4ED8">{_sz_r["acciones"]} acciones</div>'
                    f'    <div style="font-size:11px;color:#3B82F6">'
                    f'      ${_sz_r["capital_total"]:,.0f} USD total · '
                    f'      si el stop se activa pierdes exactamente ${_sz_r["riesgo_real"]:,.0f}</div>'
                    f'  </div>'
                    f'</div></div>', unsafe_allow_html=True)
            with _c2:
                st.markdown(
                    f'<div style="background:{BG_CARD};border:1px solid {BOR};border-radius:14px;padding:20px">'
                    f'<div style="font-size:14px;font-weight:800;color:{TXT};margin-bottom:14px">'
                    f'🎯 Cuándo vender</div>'
                    f'<div style="display:flex;flex-direction:column;gap:8px">'
                    f'  <div style="background:{A_BG};border:1px solid {A_BOR};border-radius:8px;padding:10px">'
                    f'    <div style="font-size:11px;font-weight:700;color:{A}">T1 — Vender 60% aquí</div>'
                    f'    <div style="font-size:20px;font-weight:800;color:{A}">${_sz_r["t1"]} (+{_sz_r["t1_pct"]}%)</div>'
                    f'    <div style="font-size:9px;color:{TXT_SOFT}">ATR x 2 desde tu entrada</div>'
                    f'  </div>'
                    f'  <div style="background:{G_BG};border:1px solid {G_BOR};border-radius:8px;padding:10px">'
                    f'    <div style="font-size:11px;font-weight:700;color:{G}">T2 — Vender 30% aquí</div>'
                    f'    <div style="font-size:20px;font-weight:800;color:{G}">${_sz_r["t2"]} (+{_sz_r["t2_pct"]}%)</div>'
                    f'    <div style="font-size:9px;color:{TXT_SOFT}">ATR x 4 desde tu entrada</div>'
                    f'  </div>'
                    f'  <div style="background:{C_BG};border:1px solid {C_BOR};border-radius:8px;padding:10px">'
                    f'    <div style="font-size:11px;font-weight:700;color:{C}">T3 — Runner 10%</div>'
                    f'    <div style="font-size:20px;font-weight:800;color:{C}">${_sz_r["t3"]} (+{_sz_r["t3_pct"]}%)</div>'
                    f'    <div style="font-size:9px;color:{TXT_SOFT}">dejar correr sin stop</div>'
                    f'  </div>'
                    f'</div></div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    f'<div style="text-align:center;font-size:11px;color:{TXT_SOFT};padding:8px">'
    f'🦅 <strong>GrekoTrader</strong>  - '
    f'v19  - Mayo 2026  - '
    f'Patrón NBIS  - 3 Momentos  - 100% Automático<br>'
    f'<span style="font-size:10px">Datos educativos  - No constituye asesoría financiera  - '
    f'Powered by yfinance + Streamlit</span>'
    f'</div>',
    unsafe_allow_html=True)