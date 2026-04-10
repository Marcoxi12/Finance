import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path

from data_loader import load_all_data, get_summary, get_expense_summary, ingest_file


# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="P&L Command Center",
    page_icon="◼",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# STYLING
# =============================================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
}
.stApp {
    background:
        radial-gradient(circle at top left, rgba(24,56,112,0.12), transparent 30%),
        linear-gradient(180deg, #f6f8fc 0%, #eef2f7 100%);
}
.main .block-container {
    max-width: 100% !important;
    padding: 0 0 2rem 0 !important;
}
[data-testid="stSidebar"], [data-testid="stSidebar"] > div {
    background: linear-gradient(180deg, #07111f 0%, #0c1728 100%) !important;
    border-right: 1px solid #18263d !important;
}
[data-testid="stSidebar"] * {
    color: #a4b4cf !important;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: #7f93b4 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-testid="stFileUploader"] section,
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background: #122038 !important;
    border-color: #233757 !important;
}
[data-testid="stSidebar"] button {
    background: #122038 !important;
    border: 1px solid #233757 !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] hr {
    border-color: #1b2b45 !important;
}
.sidebar-brand {
    display:flex;
    gap:12px;
    align-items:center;
    padding: 16px 0 18px 0;
    border-bottom:1px solid #1b2b45;
    margin-bottom:16px;
}
.sidebar-brand-box {
    width:38px;
    height:38px;
    border-radius:10px;
    background: linear-gradient(135deg,#1d4ed8,#60a5fa);
    display:flex;
    align-items:center;
    justify-content:center;
    color:#fff !important;
    font-weight:800;
    box-shadow: 0 8px 18px rgba(29,78,216,0.28);
}
.sidebar-brand-title {
    font-size:14px;
    font-weight:700;
    color:#e7eefb !important;
}
.sidebar-brand-sub {
    font-family:'JetBrains Mono', monospace;
    font-size:9px;
    letter-spacing:0.14em;
    text-transform:uppercase;
    color:#5e7499 !important;
}
.sb-section {
    font-family:'JetBrains Mono', monospace;
    font-size:10px;
    letter-spacing:0.14em;
    text-transform:uppercase;
    color:#6780a8 !important;
    margin: 14px 0 8px 0;
}
.file-item {
    background: #122038;
    border: 1px solid #233757;
    border-radius: 8px;
    padding: 10px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: #a4b4cf;
}
.file-item-name {
    flex: 1;
    word-break: break-word;
    margin-right: 8px;
}
.file-item-close {
    cursor: pointer;
    color: #dc2626;
    font-weight: bold;
    padding: 2px 6px;
    border-radius: 4px;
    transition: background 0.2s;
}
.file-item-close:hover {
    background: #1b2b45;
}
.header-shell {
    background:
        radial-gradient(circle at top right, rgba(59,130,246,0.14), transparent 28%),
        linear-gradient(135deg, #081120 0%, #0b1730 52%, #102246 100%);
    border-bottom: 1px solid #173158;
    padding: 28px 34px 22px 34px;
    box-shadow: 0 10px 30px rgba(8,17,32,0.16);
}
.header-kicker {
    font-family:'JetBrains Mono', monospace;
    font-size:10px;
    letter-spacing:0.16em;
    text-transform:uppercase;
    color:#6f8ec2;
    margin-bottom:8px;
}
.header-row {
    display:flex;
    justify-content:space-between;
    align-items:flex-end;
    gap:24px;
}
.header-title {
    font-size:28px;
    font-weight:300;
    color:#eaf1ff;
    letter-spacing:-0.03em;
}
.header-title strong {
    font-weight:800;
    color:#ffffff;
}
.header-sub {
    font-size:13px;
    color:#90a7cc;
    margin-top:6px;
}
.badge-row {
    display:flex;
    gap:10px;
    flex-wrap:wrap;
    justify-content:flex-end;
}
.h-badge {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(111,142,194,0.24);
    border-radius: 999px;
    padding: 8px 14px;
    color:#a8bddf;
    font-family:'JetBrains Mono', monospace;
    font-size:10px;
}
.h-badge strong {
    color:#e8f0ff;
    font-weight:600;
}
.h-badge.live strong {
    color:#52d6a3;
}
.kpi-wrap {
    padding: 18px 26px 0 26px;
}
.kpi-grid {
    display:grid;
    grid-template-columns: repeat(8, minmax(0,1fr));
    gap:12px;
}
@media (max-width: 1600px) {
    .kpi-grid { grid-template-columns: repeat(4, minmax(0,1fr)); }
}
@media (max-width: 900px) {
    .kpi-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
.kpi-card {
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(10px);
    border: 1px solid #dfe6f3;
    border-top: 3px solid #1d4ed8;
    border-radius: 16px;
    padding: 16px 16px 14px 16px;
    box-shadow: 0 10px 26px rgba(22,35,67,0.06);
}
.kpi-card.green { border-top-color:#059669; }
.kpi-card.red { border-top-color:#dc2626; }
.kpi-card.amber { border-top-color:#d97706; }
.kpi-card.purple { border-top-color:#7c3aed; }
.kpi-card.teal { border-top-color:#0f766e; }
.kpi-label {
    font-family:'JetBrains Mono', monospace;
    font-size:9px;
    letter-spacing:0.12em;
    text-transform:uppercase;
    color:#7b8da9;
    margin-bottom:8px;
}
.kpi-value {
    font-size:24px;
    font-weight:750;
    letter-spacing:-0.04em;
    color:#0f172a;
    line-height:1.05;
}
.kpi-value.neg { color:#b91c1c; }
.kpi-delta {
    font-family:'JetBrains Mono', monospace;
    font-size:10px;
    margin-top:8px;
}
.kpi-delta.pos { color:#059669; }
.kpi-delta.neg { color:#dc2626; }
.kpi-delta.neu { color:#94a3b8; }
.kpi-note {
    font-family:'JetBrains Mono', monospace;
    font-size:9px;
    color:#9aa8bd;
    margin-top:5px;
}
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.85) !important;
    backdrop-filter: blur(10px);
    border-bottom: 1px solid #dbe3f1 !important;
    padding: 0 28px !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    height: 52px !important;
    padding: 0 18px !important;
    color:#70839f !important;
    font-weight:600 !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color:#1d4ed8 !important;
    border-bottom-color:#1d4ed8 !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding: 22px 28px 10px 28px !important;
}
.panel {
    background: rgba(255,255,255,0.92);
    backdrop-filter: blur(10px);
    border:1px solid #dfe6f3;
    border-radius:18px;
    padding:18px 20px 16px 20px;
    margin-bottom:16px;
    box-shadow: 0 10px 30px rgba(20,31,56,0.05);
}
.panel.red { border-top:3px solid #dc2626; }
.panel.blue { border-top:3px solid #1d4ed8; }
.panel.green { border-top:3px solid #059669; }
.panel.purple { border-top:3px solid #7c3aed; }
.panel.amber { border-top:3px solid #d97706; }
.panel.teal { border-top:3px solid #0f766e; }
.panel-title {
    font-size:15px;
    font-weight:750;
    color:#0f172a;
    margin-bottom:4px;
}
.panel-sub {
    font-family:'JetBrains Mono', monospace;
    font-size:9px;
    text-transform:uppercase;
    letter-spacing:0.12em;
    color:#90a0b8;
    padding-bottom:12px;
    border-bottom:1px solid #edf2f7;
    margin-bottom:14px;
}
.callout-grid {
    display:grid;
    grid-template-columns: repeat(4, minmax(0,1fr));
    gap:12px;
    margin-top:6px;
    margin-bottom:10px;
}
@media (max-width: 1400px) {
    .callout-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
.callout {
    border:1px solid #dfe6f3;
    border-radius:14px;
    padding:12px 14px;
    background: linear-gradient(180deg, #fbfdff 0%, #f5f8fd 100%);
}
.callout.good { background: linear-gradient(180deg, #f0fdf4 0%, #ecfdf5 100%); border-color:#bae6d3; }
.callout.warn { background: linear-gradient(180deg, #fff7ed 0%, #fffbeb 100%); border-color:#fcd7aa; }
.callout.bad  { background: linear-gradient(180deg, #fff1f2 0%, #fff5f5 100%); border-color:#fecdd3; }
.callout-label {
    font-family:'JetBrains Mono', monospace;
    font-size:9px;
    text-transform:uppercase;
    letter-spacing:0.12em;
    color:#7b8da9;
    margin-bottom:5px;
}
.callout-value {
    font-size:19px;
    font-weight:750;
    color:#0f172a;
    letter-spacing:-0.03em;
}
.callout-note {
    font-size:11px;
    color:#64748b;
    margin-top:4px;
}
.footer-note {
    font-family:'JetBrains Mono', monospace;
    font-size:10px;
    color:#94a3b8;
    text-align:right;
    padding: 0 28px 18px 28px;
}
div[data-testid="metric-container"] { display: none; }
.stExpander {
    border:1px solid #dfe6f3 !important;
    border-radius:14px !important;
    background: rgba(255,255,255,0.86) !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# CONSTANTS / HELPERS
# =============================================================================
PF = "Inter, sans-serif"
MF = "JetBrains Mono, monospace"
GRID = "#e8edf5"
BG = "rgba(255,255,255,0.0)"

# FIX #1: Define cache paths at module level for file deletion
DATA_DIR = Path("data")
CACHE_FILE = DATA_DIR / "gl_cache.parquet"
META_FILE = DATA_DIR / "uploaded_files.json"

C = {
    "blue": "#1d4ed8",
    "blue_fill": "rgba(29,78,216,0.10)",
    "green": "#059669",
    "green_fill": "rgba(5,150,105,0.10)",
    "amber": "#d97706",
    "amber_fill": "rgba(217,119,6,0.10)",
    "red": "#dc2626",
    "red_fill": "rgba(220,38,38,0.10)",
    "purple": "#7c3aed",
    "purple_fill": "rgba(124,58,237,0.10)",
    "teal": "#0f766e",
    "teal_fill": "rgba(15,118,110,0.10)",
    "slate": "#334155",
    "light": "#ffffff",
    "oil": "#1d4ed8",
    "gas": "#059669",
    "plant": "#d97706",
    "deductions": "#dc2626",
    "net": "#7c3aed",
    "loe": "#2563eb",
    "workover": "#dc2626",
    "leasehold": "#d97706",
    "capital": "#7c3aed",
    "total_cost": "#111827",
}


def ensure_columns(frame: pd.DataFrame, defaults: dict) -> pd.DataFrame:
    frame = frame.copy()
    for col, default in defaults.items():
        if col not in frame.columns:
            frame[col] = default
    return frame


def normalize_str(s):
    if pd.isna(s):
        return "Unknown"
    s = str(s).strip()
    return s if s else "Unknown"


def fmt_currency(v, decimals=1):
    try:
        v = float(v)
    except Exception:
        return "$0"
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1_000_000_000:
        return f"{sign}${v/1_000_000_000:.{decimals}f}B"
    if v >= 1_000_000:
        return f"{sign}${v/1_000_000:.{decimals}f}M"
    if v >= 1_000:
        return f"{sign}${v/1_000:.{decimals}f}K"
    return f"{sign}${v:,.0f}"


def fmt_pct(v, decimals=1):
    try:
        return f"{float(v):.{decimals}f}%"
    except Exception:
        return "0.0%"


def safe_div(a, b, scale=1.0):
    try:
        if b in (0, None) or pd.isna(b):
            return 0.0
        return (a / b) * scale
    except Exception:
        return 0.0


def mom_pct(cur, prev):
    if prev in (0, None) or pd.isna(prev):
        return np.nan
    return (cur - prev) / abs(prev) * 100


def delta_html(cur, prev, label=""):
    delta = mom_pct(cur, prev)
    if pd.isna(delta):
        return '<div class="kpi-delta neu">—</div>'
    arrow = "▲" if delta >= 0 else "▼"
    cls = "pos" if delta >= 0 else "neg"
    lbl = f" vs {label}" if label else ""
    return f'<div class="kpi-delta {cls}">{arrow} {abs(delta):.1f}%{lbl}</div>'


def plot_layout(height=360, **kwargs):
    base = dict(
        height=height,
        paper_bgcolor=BG,
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(family=PF, size=11, color="#334155"),
        margin=dict(t=12, r=16, b=40, l=14),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#0b1730",
            bordercolor="#1d4ed8",
            font=dict(family=MF, size=10, color="#eaf1ff"),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            font=dict(family=MF, size=9),
            bgcolor="rgba(255,255,255,0)",
        ),
    )
    base.update(kwargs)
    return base


def style_axes(fig):
    tickfont = dict(family=MF, size=9, color="#8a9ab2")
    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor="#d8e0ed",
        tickfont=tickfont,
        ticks="outside",
        ticklen=4,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID,
        zeroline=True,
        zerolinecolor="#d8e0ed",
        tickfont=tickfont,
    )
    return fig


def category_color_from_sign(v, positive=C["green"], negative=C["red"]):
    return positive if v >= 0 else negative


def period_sort(values):
    vals = [str(v) for v in values if pd.notna(v) and str(v).strip() != ""]
    return sorted(vals)


# FIX #4: Updated expense_bucket_sum to use AmountAdj
def expense_bucket_sum(exp_frame, bucket, period=None):
    """Sum expenses by bucket, using AmountAdj (adjusted amount)."""
    if exp_frame is None or exp_frame.empty:
        return 0.0
    mask = exp_frame["Bucket"].eq(bucket)
    if period is not None:
        mask &= exp_frame["Period"].eq(period)
    # Use AmountAdj for consistency with P&L calculations
    col = "AmountAdj" if "AmountAdj" in exp_frame.columns else "Amount"
    return float(exp_frame.loc[mask, col].sum())


def add_panel(title, sub, color="blue"):
    st.markdown(
        f'<div class="panel {color}"><div class="panel-title">{title}</div><div class="panel-sub">{sub}</div>',
        unsafe_allow_html=True,
    )


def close_panel():
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# LOAD DATA & FILE MANAGEMENT
# =============================================================================
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-box">P</div>
            <div>
                <div class="sidebar-brand-title">P&amp;L Command Center</div>
                <div class="sidebar-brand-sub">Institutional FP&amp;A</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sb-section">Data Ingestion</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload GL export",
        type=["xlsx", "xls", "csv"],
        label_visibility="collapsed",
    )

    if uploaded is not None:
        try:
            res = ingest_file(uploaded)
            if isinstance(res, dict) and res.get("status") == "ok":
                st.success(f"Loaded {res.get('rows', 0):,} rows across {res.get('months', 0)} periods.")
                st.rerun()
            elif isinstance(res, dict) and res.get("status") == "duplicate":
                st.info("That file is already loaded.")
            else:
                st.error((res or {}).get("message", "Upload failed."))
        except Exception as exc:
            st.error(f"Upload failed: {exc}")

    # ── File Management ───────────────────────────────────────────────────────
    st.markdown('<div class="sb-section">Loaded Files</div>', unsafe_allow_html=True)
    
    if META_FILE.exists():
        try:
            meta = json.loads(META_FILE.read_text())
            files_list = meta.get("files", [])
            
            if files_list:
                st.markdown(f"**{len(files_list)} file(s) loaded:**", help="Click X to remove file data")
                for i, file_info in enumerate(files_list):
                    col1, col2 = st.columns([0.85, 0.15])
                    with col1:
                        st.caption(
                            f"📄 {file_info['filename']}\n"
                            f"Rows: {file_info.get('rows', 0):,} | Periods: {file_info.get('periods', 0)} | Wells: {file_info.get('wells', 0)}"
                        )
                    with col2:
                        # FIX #1: File deletion now clears cache
                        if st.button("✕", key=f"del_{i}", help="Remove this file"):
                            meta["files"].pop(i)
                            META_FILE.write_text(json.dumps(meta, indent=2))
                            # CLEAR CACHE
                            if CACHE_FILE.exists():
                                CACHE_FILE.unlink()
                            st.session_state["gl_app"] = {"df": None, "file_hashes": set()}
                            st.success("File removed and cache cleared")
                            st.rerun()
            else:
                st.caption("No files loaded yet")
        except Exception:
            st.caption("No files loaded yet")
    else:
        st.caption("No files loaded yet")

    raw = load_all_data()
    if raw is None or len(raw) == 0:
        st.warning("No data loaded yet. Upload a GL export to begin.")
        st.stop()

    df = raw.copy()
    
    # FIX #2: Ensure derived columns exist BEFORE filtering
    df = ensure_columns(
        df,
        {
            "Well": "Unknown",
            "SubAcctNum": "Unknown",
            "Period": "",
            "Bucket": "Unknown",
            "Account": 0,
            "AccountDesc": "",
            "AmountAdj": 0.0,
            "QtyAdj": 0.0,
            "AcqCode": "Unknown",
        },
    )

    df["Well"] = df["Well"].apply(normalize_str)
    df["SubAcctNum"] = df["SubAcctNum"].apply(normalize_str)
    df["Period"] = df["Period"].fillna("").astype(str).str.strip()
    df["Bucket"] = df["Bucket"].apply(normalize_str)
    if "AmountAdj" in df.columns:
        df["AmountAdj"] = pd.to_numeric(df["AmountAdj"], errors="coerce").fillna(0.0)
    if "QtyAdj" in df.columns:
        df["QtyAdj"] = pd.to_numeric(df["QtyAdj"], errors="coerce").fillna(0.0)

    st.markdown('<div class="sb-section">Company Selection</div>', unsafe_allow_html=True)
    
    # FIX #7: Derive company list from data instead of hard-coding
    if "Company" in df.columns:
        all_companies = sorted([c for c in df["Company"].unique() if pd.notna(c) and str(c).strip() != ""])
        if not all_companies:
            all_companies = ["All"]
    else:
        all_companies = ["All"]
    
    sel_companies = st.multiselect(
        "Companies",
        options=all_companies,
        default=all_companies,
        placeholder="Select companies",
        label_visibility="collapsed",
    )

    st.markdown('<div class="sb-section">Portfolio Filter</div>', unsafe_allow_html=True)

    valid_well_mask = (
        df["Well"].notna()
        & df["Well"].astype(str).str.strip().ne("")
        & df["Well"].astype(str).str.strip().str.lower().ne("unknown")
    )
    well_map = df.loc[valid_well_mask, ["SubAcctNum", "Well"]].drop_duplicates().sort_values(["SubAcctNum", "Well"])
    all_subaccts = sorted(well_map["SubAcctNum"].unique().tolist()) if not well_map.empty else []
    all_wells = sorted(well_map["Well"].unique().tolist()) if not well_map.empty else []

    sel_subaccts = st.multiselect(
        "Sub accounts",
        options=all_subaccts,
        default=[],
        placeholder="All sub accounts",
        label_visibility="collapsed",
    )

    well_options = (
        sorted(well_map.loc[well_map["SubAcctNum"].isin(sel_subaccts), "Well"].unique().tolist())
        if sel_subaccts
        else all_wells
    )

    sel_wells = st.multiselect(
        "Wells",
        options=well_options,
        default=[],
        placeholder="All wells",
        label_visibility="collapsed",
    )

    # FIX #9: Add AcqCode filter
    st.markdown('<div class="sb-section">Acquisition Code Filter</div>', unsafe_allow_html=True)
    if "AcqCode" in df.columns:
        all_acq_codes = sorted([c for c in df["AcqCode"].unique() if pd.notna(c) and str(c).strip() != ""])
        if all_acq_codes:
            sel_acq_codes = st.multiselect(
                "Acq Codes",
                options=all_acq_codes,
                default=all_acq_codes,
                placeholder="All codes",
                label_visibility="collapsed",
            )
        else:
            sel_acq_codes = []
    else:
        sel_acq_codes = []

    all_periods = period_sort(df["Period"].unique().tolist())
    st.markdown('<div class="sb-section">Period Range</div>', unsafe_allow_html=True)

    if len(all_periods) >= 2:
        period_range = st.select_slider(
            "Period range",
            options=all_periods,
            value=(all_periods[0], all_periods[-1]),
            label_visibility="collapsed",
        )
    elif len(all_periods) == 1:
        period_range = (all_periods[0], all_periods[0])
    else:
        period_range = (None, None)

    st.divider()
    st.caption(f"{df['Period'].nunique()} periods loaded • {df['Well'].nunique()} wells in model")


# =============================================================================
# FILTERED DATA / MODEL FRAMES
# =============================================================================
dff = df.copy()
if sel_subaccts:
    dff = dff[dff["SubAcctNum"].isin(sel_subaccts)]
if sel_wells:
    dff = dff[dff["Well"].isin(sel_wells)]
if sel_acq_codes:
    dff = dff[dff["AcqCode"].isin(sel_acq_codes)]

# FIX #3: Use datetime comparison for period range (robust)
if period_range[0] and period_range[1]:
    try:
        dff["Period_dt"] = pd.to_datetime(dff["Period"], errors="coerce")
        period_start = pd.to_datetime(period_range[0], errors="coerce")
        period_end = pd.to_datetime(period_range[1], errors="coerce")
        if pd.notna(period_start) and pd.notna(period_end):
            dff = dff[(dff["Period_dt"] >= period_start) & (dff["Period_dt"] <= period_end)]
        dff = dff.drop(columns=["Period_dt"], errors="ignore")
    except Exception as e:
        st.warning(f"Period filtering failed: {e}")

summary = get_summary(dff)
exp_summary = get_expense_summary(dff)

summary = pd.DataFrame() if summary is None else summary.copy()
exp_summary = pd.DataFrame() if exp_summary is None else exp_summary.copy()

summary = ensure_columns(
    summary,
    {
        "Period": "",
        "Well": "Unknown",
        "Gross_Revenue": 0.0,
        "Net_Revenue": 0.0,
        "Total_Deductions": 0.0,
        "Oil_Gross": 0.0,
        "Gas_Gross": 0.0,
        "Plant_Gross": 0.0,
        "Oil_BBL": 0.0,
        "Gas_MCF": 0.0,
        "Plant_GAL": 0.0,
        "Oil_Tax": 0.0,
        "Gas_Tax": 0.0,
        "Plant_Tax": 0.0,
        "Gas_Comp": 0.0,
        "Gas_LowVol": 0.0,
        "Plant_Deduct": 0.0,
        "Rejected_Fee": 0.0,
    },
)
exp_summary = ensure_columns(
    exp_summary,
    {
        "Period": "",
        "Well": "Unknown",
        "Bucket": "Unknown",
        "Amount": 0.0,
        "AmountAdj": 0.0,
    },
)

for frame in (summary, exp_summary):
    for c in frame.columns:
        if c not in {"Period", "Well", "Bucket"}:
            frame[c] = pd.to_numeric(frame[c], errors="coerce").fillna(0.0)

summary["Period"] = summary["Period"].fillna("").astype(str)
summary["Well"] = summary["Well"].apply(normalize_str)
exp_summary["Period"] = exp_summary["Period"].fillna("").astype(str)
exp_summary["Well"] = exp_summary["Well"].apply(normalize_str)
exp_summary["Bucket"] = exp_summary["Bucket"].apply(normalize_str)

months_sorted = period_sort(dff["Period"].unique().tolist())
last_period = months_sorted[-1] if months_sorted else None
prev_period = months_sorted[-2] if len(months_sorted) >= 2 else None
period_count = len(months_sorted)
selected_well_count = len(sel_wells) if sel_wells else dff["Well"].nunique()
total_loaded_wells = df["Well"].nunique()

rev_period = (
    summary.groupby("Period", as_index=False)
    .agg(
        Gross=("Gross_Revenue", "sum"),
        Net_Rev=("Net_Revenue", "sum"),
        Deductions=("Total_Deductions", "sum"),
        Oil=("Oil_Gross", "sum"),
        Gas=("Gas_Gross", "sum"),
        Plant=("Plant_Gross", "sum"),
        Oil_BBL=("Oil_BBL", "sum"),
        Gas_MCF=("Gas_MCF", "sum"),
        Plant_GAL=("Plant_GAL", "sum"),
        Oil_Tax=("Oil_Tax", "sum"),
        Gas_Tax=("Gas_Tax", "sum"),
        Plant_Tax=("Plant_Tax", "sum"),
        Gas_Comp=("Gas_Comp", "sum"),
        Gas_LowVol=("Gas_LowVol", "sum"),
        Plant_Deduct=("Plant_Deduct", "sum"),
        Rejected_Fee=("Rejected_Fee", "sum"),
    )
    .sort_values("Period")
    if not summary.empty
    else pd.DataFrame(columns=["Period"])
)

exp_period = (
    exp_summary.pivot_table(index="Period", columns="Bucket", values="AmountAdj" if "AmountAdj" in exp_summary.columns else "Amount", aggfunc="sum", fill_value=0.0)
    .reset_index()
    .sort_values("Period")
    if not exp_summary.empty
    else pd.DataFrame(columns=["Period"])
)
for bucket in ["LOE", "Leasehold", "Capital", "Workover"]:
    if bucket not in exp_period.columns:
        exp_period[bucket] = 0.0

all_periods_model = sorted(
    set(rev_period["Period"].tolist() if not rev_period.empty else []).union(
        set(exp_period["Period"].tolist() if not exp_period.empty else [])
    )
)

pl = pd.DataFrame({"Period": all_periods_model})
pl = pl.merge(rev_period, on="Period", how="left").fillna(0.0)
pl = pl.merge(exp_period[["Period", "LOE", "Leasehold", "Capital", "Workover"]], on="Period", how="left").fillna(0.0)
pl["OpEx"] = pl["LOE"] + pl["Workover"]
pl["Total_Exp"] = pl["LOE"] + pl["Leasehold"] + pl["Capital"] + pl["Workover"]
pl["Field_EBITDA"] = pl["Net_Rev"] - pl["OpEx"]
pl["Net_Income"] = pl["Net_Rev"] - pl["Total_Exp"]
pl["Net_Less_Cap"] = pl["Net_Rev"] - pl["Capital"]
pl["Gross_Margin"] = np.where(pl["Gross"] != 0, pl["Net_Rev"] / pl["Gross"] * 100, 0.0)
pl["EBITDA_Margin"] = np.where(pl["Gross"] != 0, pl["Field_EBITDA"] / pl["Gross"] * 100, 0.0)
pl["Net_Margin"] = np.where(pl["Gross"] != 0, pl["Net_Income"] / pl["Gross"] * 100, 0.0)
pl["Deduction_Rate"] = np.where(pl["Gross"] != 0, pl["Deductions"] / pl["Gross"] * 100, 0.0)
pl["Cum_EBITDA"] = pl["Field_EBITDA"].cumsum()
pl["Cum_NI"] = pl["Net_Income"].cumsum()
pl["MoM_EBITDA"] = pl["Field_EBITDA"].pct_change() * 100
pl["MoM_NI"] = pl["Net_Income"].pct_change() * 100
pl = pl.sort_values("Period").reset_index(drop=True)

last_gross = float(pl.loc[pl["Period"].eq(last_period), "Gross"].sum()) if last_period else 0.0
prev_gross = float(pl.loc[pl["Period"].eq(prev_period), "Gross"].sum()) if prev_period else 0.0
last_net = float(pl.loc[pl["Period"].eq(last_period), "Net_Rev"].sum()) if last_period else 0.0
prev_net = float(pl.loc[pl["Period"].eq(prev_period), "Net_Rev"].sum()) if prev_period else 0.0
last_ebitda = float(pl.loc[pl["Period"].eq(last_period), "Field_EBITDA"].sum()) if last_period else 0.0
prev_ebitda = float(pl.loc[pl["Period"].eq(prev_period), "Field_EBITDA"].sum()) if prev_period else 0.0
last_ni = float(pl.loc[pl["Period"].eq(last_period), "Net_Income"].sum()) if last_period else 0.0
last_total_exp = float(pl.loc[pl["Period"].eq(last_period), "Total_Exp"].sum()) if last_period else 0.0
last_opex = float(pl.loc[pl["Period"].eq(last_period), "OpEx"].sum()) if last_period else 0.0
last_capex = float(pl.loc[pl["Period"].eq(last_period), "Capital"].sum()) if last_period else 0.0
last_deductions = float(pl.loc[pl["Period"].eq(last_period), "Deductions"].sum()) if last_period else 0.0
last_ded_rate = safe_div(last_deductions, last_gross, 100)
last_net_margin = safe_div(last_ni, last_gross, 100)
cum_ebitda = float(pl["Field_EBITDA"].sum()) if not pl.empty else 0.0
cum_ni = float(pl["Net_Income"].sum()) if not pl.empty else 0.0
cum_gross = float(pl["Gross"].sum()) if not pl.empty else 0.0
cum_net_margin = safe_div(cum_ni, cum_gross, 100)

loe_last = expense_bucket_sum(exp_summary, "LOE", last_period)
workover_last = expense_bucket_sum(exp_summary, "Workover", last_period)
leasehold_last = expense_bucket_sum(exp_summary, "Leasehold", last_period)
capital_last = expense_bucket_sum(exp_summary, "Capital", last_period)

boe_frame = rev_period[["Period", "Oil_BBL", "Gas_MCF"]].copy() if not rev_period.empty else pd.DataFrame(columns=["Period"])
if not boe_frame.empty:
    boe_frame["BOE"] = boe_frame["Oil_BBL"] + (boe_frame["Gas_MCF"] / 6.0)
    boe_frame = boe_frame.merge(exp_period[["Period", "LOE"]] if not exp_period.empty else pd.DataFrame(columns=["Period", "LOE"]), on="Period", how="left").fillna(0.0)
    boe_frame["LOE_per_BOE"] = np.where(boe_frame["BOE"] != 0, boe_frame["LOE"] / boe_frame["BOE"], np.nan)
    latest_boe = float(boe_frame.loc[boe_frame["Period"].eq(last_period), "BOE"].sum()) if last_period else 0.0
    latest_loe_per_boe = float(boe_frame.loc[boe_frame["Period"].eq(last_period), "LOE_per_BOE"].fillna(0).sum()) if last_period else 0.0
else:
    latest_boe = 0.0
    latest_loe_per_boe = 0.0

# FIX #8: Validate period_label for None values
period_label = (
    f"{period_range[0]} → {period_range[1]}"
    if period_range[0] and period_range[1] and period_range[0] != period_range[1] and period_range[0] is not None
    else (period_range[0] if period_range[0] is not None else "—")
)
portfolio_label = f"{selected_well_count} of {total_loaded_wells} wells" if sel_wells else f"All {dff['Well'].nunique()} wells"
company_label = " + ".join(sel_companies) if sel_companies and sel_companies != ["All"] else "All"


# =============================================================================
# HEADER
# =============================================================================
st.markdown(
    f"""
<div class="header-shell">
    <div class="header-kicker">Integrated FP&amp;A • Operating Analytics • Institutional Dashboard</div>
    <div class="header-row">
        <div>
            <div class="header-title">P&amp;L Command Center <strong>{portfolio_label}</strong></div>
            <div class="header-sub">Operating Performance view: revenue quality, cost discipline, field EBITDA, and net income conversion across {company_label}.</div>
        </div>
        <div class="badge-row">
            <div class="h-badge">Companies <strong>{company_label}</strong></div>
            <div class="h-badge">Analysis Period <strong>{period_label}</strong></div>
            <div class="h-badge">Latest Month <strong>{last_period or "—"}</strong></div>
            <div class="h-badge">Coverage <strong>{period_count} period(s)</strong></div>
            <div class="h-badge live">Status <strong>GL Linked</strong></div>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

kpi_specs = [
    ("Gross Revenue", fmt_currency(last_gross), delta_html(last_gross, prev_gross, prev_period or ""), "Latest month gross before deductions", "blue", last_gross),
    ("Net Revenue", fmt_currency(last_net), delta_html(last_net, prev_net, prev_period or ""), "After taxes, gathering, and fees", "green", last_net),
    ("Field EBITDA", fmt_currency(last_ebitda), delta_html(last_ebitda, prev_ebitda, prev_period or ""), "Net revenue less LOE + workover", "green" if last_ebitda >= 0 else "red", last_ebitda),
    ("Net Income", fmt_currency(last_ni), '<div class="kpi-delta neu">All-in after leasehold + capital</div>', f"Total costs: {fmt_currency(last_total_exp)}", "green" if last_ni >= 0 else "red", last_ni),
    ("Net Margin", fmt_pct(last_net_margin), '<div class="kpi-delta neu">Profitability on gross revenue</div>', f"Cumulative: {fmt_pct(cum_net_margin)}", "teal" if last_net_margin >= 0 else "red", last_net_margin),
    ("Deduction Rate", fmt_pct(last_ded_rate), '<div class="kpi-delta neu">Revenue haircut</div>', f"Deductions: {fmt_currency(last_deductions)}", "amber", last_ded_rate),
    ("Cum. EBITDA", fmt_currency(cum_ebitda), '<div class="kpi-delta neu">Across selected history</div>', f"{period_count} period(s)", "purple" if cum_ebitda >= 0 else "red", cum_ebitda),
    ("LOE / BOE", fmt_currency(latest_loe_per_boe, 2), '<div class="kpi-delta neu">Unit operating efficiency</div>', f"BOE: {latest_boe:,.0f}", "teal", latest_loe_per_boe),
]

cards_html = '<div class="kpi-wrap"><div class="kpi-grid">'
for label, val, delta_block, note, klass, raw in kpi_specs:
    neg_cls = " neg" if raw < 0 and label not in {"Deduction Rate", "LOE / BOE"} else ""
    cards_html += f'<div class="kpi-card {klass}"><div class="kpi-label">{label}</div><div class="kpi-value{neg_cls}">{val}</div><div class="kpi-delta neu">—</div><div class="kpi-note">{note}</div></div>'
cards_html += "</div></div>"
st.markdown(cards_html, unsafe_allow_html=True)


# =============================================================================
# INSIGHT BOXES
# =============================================================================
gross_to_net = safe_div(last_net, last_gross, 100)
opex_burden = safe_div(last_opex, last_net, 100)
capex_burden = safe_div(last_capex, last_net, 100)
best_period = pl.loc[pl["Net_Income"].idxmax(), "Period"] if not pl.empty else "—"
worst_period = pl.loc[pl["Net_Income"].idxmin(), "Period"] if not pl.empty else "—"

st.markdown(
    f"""
<div style="padding:18px 28px 0 28px;">
    <div class="callout-grid">
        <div class="callout {'good' if gross_to_net >= 70 else 'warn'}">
            <div class="callout-label">Gross to Net Retention</div>
            <div class="callout-value">{fmt_pct(gross_to_net)}</div>
            <div class="callout-note">Portion of gross revenue retained after deductions in {last_period or "latest month"}.</div>
        </div>
        <div class="callout {'good' if opex_burden <= 45 else 'warn'}">
            <div class="callout-label">OpEx Burden</div>
            <div class="callout-value">{fmt_pct(opex_burden)}</div>
            <div class="callout-note">LOE + workover as a share of net revenue.</div>
        </div>
        <div class="callout {'warn' if capex_burden > 25 else 'good'}">
            <div class="callout-label">Capital Intensity</div>
            <div class="callout-value">{fmt_pct(capex_burden)}</div>
            <div class="callout-note">Capital spend as a share of net revenue.</div>
        </div>
        <div class="callout {'good' if last_ni >= 0 else 'bad'}">
            <div class="callout-label">P&amp;L Read</div>
            <div class="callout-value">{'Profitable' if last_ni >= 0 else 'Negative NI'}</div>
            <div class="callout-note">Best month: {best_period} • Weakest month: {worst_period}</div>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# MAIN TABS
# =============================================================================
tab_rev, tab_cost, tab_pl = st.tabs(["Revenue Quality", "Cost Discipline", "P&L Bridge"])

with tab_rev:
    rev_t1, rev_t2, rev_t3, rev_t4 = st.tabs(
        ["Trend & Mix", "Deduction Bridge", "Well Revenue Ranking", "Volumes & Realizations"]
    )

    with rev_t1:
        c1, c2 = st.columns([3, 2], gap="medium")

        with c1:
            add_panel(
                "Gross-to-Net Revenue Trend",
                "Monthly commodity stack, deductions, and net revenue overlay",
                "blue",
            )
            fig = go.Figure()
            if not rev_period.empty:
                fig.add_bar(x=rev_period["Period"], y=rev_period["Oil"], name="Oil", marker_color=C["oil"])
                fig.add_bar(x=rev_period["Period"], y=rev_period["Gas"], name="Gas", marker_color=C["gas"])
                fig.add_bar(x=rev_period["Period"], y=rev_period["Plant"], name="Plant / NGL", marker_color=C["plant"])
                fig.add_bar(
                    x=rev_period["Period"],
                    y=-rev_period["Deductions"],
                    name="Deductions",
                    marker_color=C["red_fill"],
                )
                fig.add_scatter(
                    x=rev_period["Period"],
                    y=rev_period["Net_Rev"],
                    name="Net Revenue",
                    mode="lines+markers",
                    line=dict(color=C["net"], width=2.6),
                    marker=dict(size=7, color=C["net"], line=dict(width=2, color="#ffffff")),
                    hovertemplate="%{x}<br>Net Revenue: $%{y:,.0f}<extra></extra>",
                )
            fig.update_layout(**plot_layout(height=390, barmode="relative", yaxis=dict(tickprefix="$", tickformat=",.0f")))
            style_axes(fig)
            st.plotly_chart(fig, use_container_width=True)
            close_panel()

        with c2:
            add_panel(
                "Cumulative Commodity Mix",
                "Contribution to total gross revenue",
                "green",
            )
            mix_vals = [
                float(rev_period["Oil"].sum()) if not rev_period.empty else 0.0,
                float(rev_period["Gas"].sum()) if not rev_period.empty else 0.0,
                float(rev_period["Plant"].sum()) if not rev_period.empty else 0.0,
            ]
            fig2 = go.Figure(
                go.Pie(
                    labels=["Oil", "Gas", "Plant / NGL"],
                    values=mix_vals,
                    hole=0.62,
                    marker=dict(colors=[C["oil"], C["gas"], C["plant"]], line=dict(color="#ffffff", width=3)),
                    textinfo="label+percent",
                    textfont=dict(family=MF, size=10),
                    hovertemplate="%{label}: $%{value:,.0f}<extra></extra>",
                )
            )
            fig2.update_layout(
                height=390,
                showlegend=False,
                paper_bgcolor=BG,
                margin=dict(t=10, b=10, l=10, r=10),
                annotations=[
                    dict(
                        x=0.5,
                        y=0.5,
                        showarrow=False,
                        text=f"<b>{fmt_currency(sum(mix_vals))}</b><br><span style='font-size:10px;color:#94a3b8'>Gross Rev</span>",
                        font=dict(family=PF, size=18, color="#0f172a"),
                    )
                ],
            )
            st.plotly_chart(fig2, use_container_width=True)
            close_panel()

    with rev_t2:
        bridge_period = st.selectbox(
            "Bridge period",
            months_sorted[::-1] if months_sorted else ["—"],
            index=0 if months_sorted else None,
            key="bridge_period",
        )
        bridge_row = rev_period.loc[rev_period["Period"].eq(bridge_period)].copy() if not rev_period.empty else pd.DataFrame()
        if bridge_row.empty:
            st.info("No revenue data is available for the selected period.")
        else:
            row = bridge_row.iloc[0]
            components = [
                ("Oil Prod Tax", float(row.get("Oil_Tax", 0.0)), C["red"]),
                ("Gas Prod Tax", float(row.get("Gas_Tax", 0.0)), C["red"]),
                ("Plant Prod Tax", float(row.get("Plant_Tax", 0.0)), C["red"]),
                ("Compression", float(row.get("Gas_Comp", 0.0)), C["amber"]),
                ("Low Vol Fee", float(row.get("Gas_LowVol", 0.0)), C["amber"]),
                ("Plant Deduct", float(row.get("Plant_Deduct", 0.0)), C["amber"]),
                ("Rejected Fee", float(row.get("Rejected_Fee", 0.0)), C["amber"]),
            ]
            components = [(n, v, c) for n, v, c in components if abs(v) > 0.01]

            labels = ["Gross Revenue"] + [n for n, _, _ in components] + ["Net Revenue"]
            measures = ["absolute"] + ["relative"] * len(components) + ["total"]
            values = [float(row["Gross"])] + [-v for _, v, _ in components] + [float(row["Net_Rev"])]
            colors = [C["blue"]] + [c for _, _, c in components] + [C["purple"]]

            add_panel(
                "Deduction Waterfall",
                "Gross revenue into taxes, gathering / transport, and net revenue",
                "amber",
            )
            wf = go.Figure(
                go.Waterfall(
                    x=labels,
                    y=values,
                    measure=measures,
                    connector=dict(line=dict(color="#94a3b8")),
                    increasing=dict(marker=dict(color=C["green"])),
                    decreasing=dict(marker=dict(color=C["red"])),
                    totals=dict(marker=dict(color=C["purple"])),
                    text=[fmt_currency(v) for v in values],
                    textposition="outside",
                    hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
                )
            )
            wf.update_layout(**plot_layout(height=430, yaxis=dict(tickprefix="$", tickformat=",.0f")))
            style_axes(wf)
            st.plotly_chart(wf, use_container_width=True)

            gross = float(row["Gross"])
            net = float(row["Net_Rev"])
            total_ded = float(row["Deductions"])
            st.dataframe(
                pd.DataFrame(
                    {
                        "Metric": ["Gross Revenue", "Total Deductions", "Net Revenue", "Retention"],
                        "Value": [
                            fmt_currency(gross),
                            fmt_currency(total_ded),
                            fmt_currency(net),
                            fmt_pct(safe_div(net, gross, 100)),
                        ],
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
            close_panel()

    with rev_t3:
        ctl1, ctl2 = st.columns([1, 4], gap="medium")
        with ctl1:
            rank_period = st.selectbox(
                "Ranking period",
                ["All periods"] + (months_sorted[::-1] if months_sorted else []),
                key="rev_rank_period",
            )
            rank_metric = st.radio("Metric", ["Gross Revenue", "Net Revenue"], key="rev_rank_metric")
            top_n = st.slider("Top N", 5, 30, 12, key="rev_top_n")
        with ctl2:
            metric_col = "Gross_Revenue" if rank_metric == "Gross Revenue" else "Net_Revenue"
            rank_base = summary.copy()
            if rank_period != "All periods":
                rank_base = rank_base[rank_base["Period"].eq(rank_period)]
            well_rank = (
                rank_base.groupby("Well", as_index=False)[metric_col]
                .sum()
                .sort_values(metric_col, ascending=False)
                .head(top_n)
            )
            add_panel(
                f"Top {top_n} Wells — {rank_metric}",
                "Concentration view by asset",
                "blue",
            )
            fig3 = go.Figure(
                go.Bar(
                    x=well_rank[metric_col],
                    y=well_rank["Well"],
                    orientation="h",
                    marker=dict(
                        color=well_rank[metric_col],
                        colorscale=[[0, "#93c5fd"], [0.5, "#3b82f6"], [1, "#1d4ed8"]],
                        showscale=False,
                    ),
                    text=well_rank[metric_col].apply(fmt_currency),
                    textposition="outside",
                    hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
                )
            )
            fig3.update_layout(
                **plot_layout(
                    height=max(380, top_n * 30),
                    xaxis=dict(tickprefix="$", tickformat=",.0f"),
                    yaxis=dict(autorange="reversed"),
                    margin=dict(t=12, r=90, b=36, l=220),
                )
            )
            style_axes(fig3)
            st.plotly_chart(fig3, use_container_width=True)

            with st.expander("Full well revenue table"):
                full_rank = (
                    rank_base.pivot_table(index="Well", columns="Period", values=metric_col, aggfunc="sum", fill_value=0.0)
                    .reset_index()
                )
                if not full_rank.empty:
                    full_rank["Total"] = full_rank.drop(columns=["Well"]).sum(axis=1)
                    full_rank = full_rank.sort_values("Total", ascending=False)
                    for col in full_rank.columns[1:]:
                        full_rank[col] = full_rank[col].apply(lambda x: fmt_currency(x, 0))
                st.dataframe(full_rank, use_container_width=True, hide_index=True)
            close_panel()

    with rev_t4:
        left, right = st.columns(2, gap="medium")

        with left:
            add_panel("Production Volumes", "Oil and gas volumes with plant liquids overlay", "teal")
            vol_fig = make_subplots(specs=[[{"secondary_y": True}]])
            if not rev_period.empty:
                vol_fig.add_bar(x=rev_period["Period"], y=rev_period["Oil_BBL"], name="Oil (BBL)", marker_color=C["oil"], secondary_y=False)
                vol_fig.add_bar(x=rev_period["Period"], y=rev_period["Gas_MCF"], name="Gas (MCF)", marker_color=C["gas"], secondary_y=False)
                vol_fig.add_scatter(
                    x=rev_period["Period"],
                    y=rev_period["Plant_GAL"],
                    name="Plant (GAL)",
                    mode="lines+markers",
                    line=dict(color=C["plant"], width=2.5),
                    marker=dict(size=6, color=C["plant"], line=dict(width=2, color="#ffffff")),
                    secondary_y=True,
                )
            vol_fig.update_layout(**plot_layout(height=340, barmode="group"))
            vol_fig.update_xaxes(showgrid=False, showline=True, linecolor="#d8e0ed", tickfont=dict(family=MF, size=9, color="#8a9ab2"))
            vol_fig.update_yaxes(showgrid=True, gridcolor=GRID, tickfont=dict(family=MF, size=9, color="#8a9ab2"), title_text="BBL / MCF", secondary_y=False)
            vol_fig.update_yaxes(showgrid=False, tickfont=dict(family=MF, size=9, color="#8a9ab2"), title_text="GAL", secondary_y=True)
            st.plotly_chart(vol_fig, use_container_width=True)
            close_panel()

        with right:
            add_panel("Implied Realizations", "Revenue per unit by commodity", "green")
            price_df = rev_period[["Period", "Oil", "Gas", "Oil_BBL", "Gas_MCF"]].copy() if not rev_period.empty else pd.DataFrame(columns=["Period"])
            if not price_df.empty:
                price_df["Oil_Price"] = np.where(price_df["Oil_BBL"] != 0, price_df["Oil"] / price_df["Oil_BBL"], np.nan)
                price_df["Gas_Price"] = np.where(price_df["Gas_MCF"] != 0, price_df["Gas"] / price_df["Gas_MCF"], np.nan)
            price_fig = make_subplots(specs=[[{"secondary_y": True}]])
            if not price_df.empty:
                price_fig.add_scatter(
                    x=price_df["Period"],
                    y=price_df["Oil_Price"],
                    name="Oil $/BBL",
                    mode="lines+markers",
                    line=dict(color=C["oil"], width=2.5),
                    marker=dict(size=6, color=C["oil"], line=dict(width=2, color="#ffffff")),
                    secondary_y=False,
                )
                price_fig.add_scatter(
                    x=price_df["Period"],
                    y=price_df["Gas_Price"],
                    name="Gas $/MCF",
                    mode="lines+markers",
                    line=dict(color=C["gas"], width=2.5),
                    marker=dict(size=6, color=C["gas"], line=dict(width=2, color="#ffffff")),
                    secondary_y=True,
                )
            price_fig.update_layout(**plot_layout(height=340))
            price_fig.update_xaxes(showgrid=False, showline=True, linecolor="#d8e0ed", tickfont=dict(family=MF, size=9, color="#8a9ab2"))
            price_fig.update_yaxes(showgrid=True, gridcolor=GRID, tickprefix="$", tickformat=",.2f", title_text="Oil $/BBL", tickfont=dict(family=MF, size=9, color="#8a9ab2"), secondary_y=False)
            price_fig.update_yaxes(showgrid=False, tickprefix="$", tickformat=",.3f", title_text="Gas $/MCF", tickfont=dict(family=MF, size=9, color="#8a9ab2"), secondary_y=True)
            st.plotly_chart(price_fig, use_container_width=True)
            close_panel()

with tab_cost:
    cost_t1, cost_t2, cost_t3, cost_t4 = st.tabs(
        ["Trend & Efficiency", "Bucket / Account View", "Well Cost Ranking", "Well Detail"]
    )

    with cost_t1:
        left, right = st.columns(2, gap="medium")

        with left:
            add_panel("Cost Stack", "LOE, leasehold, capital, and workover by month", "red")
            cost_fig = go.Figure()
            if not exp_period.empty:
                cost_fig.add_bar(x=exp_period["Period"], y=exp_period["LOE"], name="LOE", marker_color=C["loe"])
                cost_fig.add_bar(x=exp_period["Period"], y=exp_period["Leasehold"], name="Leasehold", marker_color=C["leasehold"])
                cost_fig.add_bar(x=exp_period["Period"], y=exp_period["Capital"], name="Capital", marker_color=C["capital"])
                cost_fig.add_bar(x=exp_period["Period"], y=exp_period["Workover"], name="Workover", marker_color=C["workover"])
                total_cost_series = exp_period[["LOE", "Leasehold", "Capital", "Workover"]].sum(axis=1)
                cost_fig.add_scatter(
                    x=exp_period["Period"],
                    y=total_cost_series,
                    name="Total Cost",
                    mode="lines+markers",
                    line=dict(color=C["total_cost"], width=2.5),
                    marker=dict(size=7, color=C["total_cost"], line=dict(width=2, color="#ffffff")),
                )
            cost_fig.update_layout(**plot_layout(height=360, barmode="stack", yaxis=dict(tickprefix="$", tickformat=",.0f")))
            style_axes(cost_fig)
            st.plotly_chart(cost_fig, use_container_width=True)
            close_panel()

        with right:
            add_panel("LOE per BOE", "Operating efficiency by month", "teal")
            loe_fig = go.Figure()
            if not boe_frame.empty:
                loe_fig.add_scatter(
                    x=boe_frame["Period"],
                    y=boe_frame["LOE_per_BOE"],
                    name="LOE / BOE",
                    mode="lines+markers",
                    line=dict(color=C["teal"], width=2.5),
                    marker=dict(size=7, color=C["teal"], line=dict(width=2, color="#ffffff")),
                    fill="tozeroy",
                    fillcolor=C["teal_fill"],
                    hovertemplate="%{x}<br>$%{y:.2f} / BOE<extra></extra>",
                )
            loe_fig.update_layout(**plot_layout(height=360, yaxis=dict(tickprefix="$", tickformat=",.2f")))
            style_axes(loe_fig)
            st.plotly_chart(loe_fig, use_container_width=True)
            close_panel()

    with cost_t2:
        left, right = st.columns([2, 3], gap="medium")

        bucket_period = st.selectbox(
            "Bucket view period",
            ["All periods"] + (months_sorted[::-1] if months_sorted else []),
            key="bucket_period",
        )
        bucket_filter = st.selectbox(
            "Bucket filter",
            ["All buckets", "LOE", "Leasehold", "Capital", "Workover"],
            key="bucket_filter",
        )

        cost_base = exp_summary.copy()
        raw_cost_base = dff[dff["Bucket"].ne("Revenue")].copy() if "Bucket" in dff.columns else dff.copy()

        if bucket_period != "All periods":
            cost_base = cost_base[cost_base["Period"].eq(bucket_period)]
            raw_cost_base = raw_cost_base[raw_cost_base["Period"].eq(bucket_period)]
        if bucket_filter != "All buckets":
            cost_base = cost_base[cost_base["Bucket"].eq(bucket_filter)]
            raw_cost_base = raw_cost_base[raw_cost_base["Bucket"].eq(bucket_filter)]

        acct_roll = (
            raw_cost_base.groupby(["Bucket", "Account", "AccountDesc"], as_index=False)["AmountAdj"]
            .sum()
            .sort_values("AmountAdj", ascending=False)
        )
        acct_roll = acct_roll[acct_roll["AmountAdj"].abs() > 0.01]

        with left:
            add_panel("Spend by Bucket", "Mix of total expense under current filters", "amber")
            pie_base = cost_base.groupby("Bucket", as_index=False)["Amount"].sum()
            fig4 = go.Figure(
                go.Pie(
                    labels=pie_base["Bucket"],
                    values=pie_base["Amount"],
                    hole=0.58,
                    marker=dict(
                        colors=[
                            C["loe"] if b == "LOE" else
                            C["leasehold"] if b == "Leasehold" else
                            C["capital"] if b == "Capital" else
                            C["workover"] if b == "Workover" else
                            C["slate"]
                            for b in pie_base["Bucket"]
                        ],
                        line=dict(color="#ffffff", width=3),
                    ),
                    textinfo="label+percent",
                    textfont=dict(family=MF, size=10),
                    hovertemplate="%{label}: $%{value:,.0f}<extra></extra>",
                )
            )
            total_sel = float(pie_base["Amount"].sum()) if not pie_base.empty else 0.0
            fig4.update_layout(
                height=340,
                showlegend=False,
                paper_bgcolor=BG,
                margin=dict(t=10, b=10, l=10, r=10),
                annotations=[
                    dict(
                        x=0.5, y=0.5, showarrow=False,
                        text=f"<b>{fmt_currency(total_sel)}</b><br><span style='font-size:10px;color:#94a3b8'>Selected</span>",
                        font=dict(family=PF, size=18, color="#0f172a"),
                    )
                ],
            )
            st.plotly_chart(fig4, use_container_width=True)
            close_panel()

        with right:
            add_panel("Top GL Accounts", "Largest spend lines under current filters", "red")
            top_accounts = acct_roll.head(15).copy()
            top_accounts["Label"] = top_accounts.apply(
                lambda r: f"{int(r['Account'])} - {r['AccountDesc']}" if pd.notna(r["Account"]) and str(r["AccountDesc"]).strip() else str(r["Account"]),
                axis=1,
            )
            fig5 = go.Figure(
                go.Bar(
                    x=top_accounts["AmountAdj"],
                    y=top_accounts["Label"],
                    orientation="h",
                    marker_color=[
                        C["loe"] if b == "LOE" else
                        C["leasehold"] if b == "Leasehold" else
                        C["capital"] if b == "Capital" else
                        C["workover"] if b == "Workover" else
                        C["slate"]
                        for b in top_accounts["Bucket"]
                    ],
                    text=top_accounts["AmountAdj"].apply(fmt_currency),
                    textposition="outside",
                    hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
                )
            )
            fig5.update_layout(
                **plot_layout(
                    height=340,
                    xaxis=dict(tickprefix="$", tickformat=",.0f"),
                    yaxis=dict(autorange="reversed"),
                    margin=dict(t=12, r=90, b=36, l=240),
                )
            )
            style_axes(fig5)
            st.plotly_chart(fig5, use_container_width=True)

            with st.expander("Full GL account table"):
                acct_tbl = acct_roll.copy()
                acct_tbl["Amount"] = acct_tbl["AmountAdj"].apply(lambda x: fmt_currency(x, 0))
                acct_tbl = acct_tbl.rename(columns={"AccountDesc": "Description"})
                st.dataframe(acct_tbl[["Bucket", "Account", "Description", "Amount"]], use_container_width=True, hide_index=True)
            close_panel()

    with cost_t3:
        rank_period = st.selectbox(
            "Cost ranking period",
            ["All periods"] + (months_sorted[::-1] if months_sorted else []),
            key="cost_rank_period",
        )
        rank_bucket = st.selectbox(
            "Cost ranking bucket",
            ["All buckets", "LOE", "Leasehold", "Capital", "Workover"],
            key="cost_rank_bucket",
        )
        rank_n = st.slider("Top cost wells", 5, 30, 12, key="cost_rank_n")

        cost_rank_base = exp_summary.copy()
        if rank_period != "All periods":
            cost_rank_base = cost_rank_base[cost_rank_base["Period"].eq(rank_period)]
        if rank_bucket != "All buckets":
            cost_rank_base = cost_rank_base[cost_rank_base["Bucket"].eq(rank_bucket)]

        well_cost_rank = (
            cost_rank_base.groupby("Well", as_index=False)["Amount"]
            .sum()
            .sort_values("Amount", ascending=False)
            .head(rank_n)
        )

        add_panel("Top Wells by Cost", "Which assets are driving spend", "red")
        fig6 = go.Figure(
            go.Bar(
                x=well_cost_rank["Amount"],
                y=well_cost_rank["Well"],
                orientation="h",
                marker_color=C["red"],
                text=well_cost_rank["Amount"].apply(fmt_currency),
                textposition="outside",
                hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
            )
        )
        fig6.update_layout(
            **plot_layout(
                height=max(380, rank_n * 30),
                xaxis=dict(tickprefix="$", tickformat=",.0f"),
                yaxis=dict(autorange="reversed"),
                margin=dict(t=12, r=90, b=36, l=220),
            )
        )
        style_axes(fig6)
        st.plotly_chart(fig6, use_container_width=True)

        with st.expander("Full well cost table"):
            pivot_cost = (
                cost_rank_base.pivot_table(index="Well", columns="Period", values="Amount", aggfunc="sum", fill_value=0.0)
                .reset_index()
            )
            if not pivot_cost.empty:
                pivot_cost["Total"] = pivot_cost.drop(columns=["Well"]).sum(axis=1)
                pivot_cost = pivot_cost.sort_values("Total", ascending=False)
                for col in pivot_cost.columns[1:]:
                    pivot_cost[col] = pivot_cost[col].apply(lambda x: fmt_currency(x, 0))
            st.dataframe(pivot_cost, use_container_width=True, hide_index=True)
        close_panel()

    with cost_t4:
        available_cost_wells = sorted(exp_summary["Well"].unique().tolist()) if not exp_summary.empty else []
        
        # FIX #6: Allow revenue-only P&L if no expenses exist
        if not available_cost_wells:
            st.info("No expense data available. Showing revenue wells instead:")
            available_cost_wells = sorted(summary["Well"].unique().tolist()) if not summary.empty else []
        
        if not available_cost_wells:
            st.warning("No well data available in selected filters.")
        else:
            left, right = st.columns([1, 4], gap="medium")
            with left:
                detail_well = st.selectbox("Well", available_cost_wells, key="detail_well")
                detail_period = st.selectbox("Period", ["All periods"] + (months_sorted[::-1] if months_sorted else []), key="detail_period")
            with right:
                detail_raw = dff[dff["Bucket"].ne("Revenue") & dff["Well"].eq(detail_well)].copy()
                if detail_period != "All periods":
                    detail_raw = detail_raw[detail_raw["Period"].eq(detail_period)]

                if detail_raw.empty:
                    st.info(f"No expense detail for {detail_well}" + (f" in {detail_period}" if detail_period != "All periods" else ""))
                else:
                    bucket_totals = detail_raw.groupby("Bucket", as_index=False)["AmountAdj"].sum()
                    total_well_cost = float(bucket_totals["AmountAdj"].sum())

                    add_panel(f"Well Cost Detail — {detail_well}", "Bucket totals and line-item exposure", "purple")
                    stats = bucket_totals.set_index("Bucket")["AmountAdj"].to_dict()
                    stat_df = pd.DataFrame(
                        {
                            "Metric": ["LOE", "Leasehold", "Capital", "Workover", "Total"],
                            "Value": [
                                fmt_currency(stats.get("LOE", 0.0)),
                                fmt_currency(stats.get("Leasehold", 0.0)),
                                fmt_currency(stats.get("Capital", 0.0)),
                                fmt_currency(stats.get("Workover", 0.0)),
                                fmt_currency(total_well_cost),
                            ],
                        }
                    )
                    st.dataframe(stat_df, use_container_width=True, hide_index=True)

                    acct_detail = (
                        detail_raw.groupby(["Bucket", "Account", "AccountDesc"], as_index=False)["AmountAdj"]
                        .sum()
                        .sort_values("AmountAdj", ascending=False)
                    )
                    acct_detail["Label"] = acct_detail.apply(
                        lambda r: f"{int(r['Account'])} - {r['AccountDesc']}" if pd.notna(r["Account"]) and str(r["AccountDesc"]).strip() else str(r["Account"]),
                        axis=1,
                    )
                    fig7 = go.Figure(
                        go.Bar(
                            x=acct_detail["AmountAdj"],
                            y=acct_detail["Label"],
                            orientation="h",
                            marker_color=[
                                C["loe"] if b == "LOE" else
                                C["leasehold"] if b == "Leasehold" else
                                C["capital"] if b == "Capital" else
                                C["workover"] if b == "Workover" else
                                C["slate"]
                                for b in acct_detail["Bucket"]
                            ],
                            text=acct_detail["AmountAdj"].apply(fmt_currency),
                            textposition="outside",
                            hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
                        )
                    )
                    fig7.update_layout(
                        **plot_layout(
                            height=max(340, len(acct_detail) * 28),
                            xaxis=dict(tickprefix="$", tickformat=",.0f"),
                            yaxis=dict(autorange="reversed"),
                            margin=dict(t=12, r=90, b=36, l=260),
                        )
                    )
                    style_axes(fig7)
                    st.plotly_chart(fig7, use_container_width=True)

                    if detail_period == "All periods":
                        trend_df = (
                            detail_raw.groupby(["Period", "Bucket"], as_index=False)["AmountAdj"]
                            .sum()
                            .pivot_table(index="Period", columns="Bucket", values="AmountAdj", fill_value=0.0)
                            .reset_index()
                            .sort_values("Period")
                        )
                        for bucket in ["LOE", "Leasehold", "Capital", "Workover"]:
                            if bucket not in trend_df.columns:
                                trend_df[bucket] = 0.0
                        fig8 = go.Figure()
                        fig8.add_bar(x=trend_df["Period"], y=trend_df["LOE"], name="LOE", marker_color=C["loe"])
                        fig8.add_bar(x=trend_df["Period"], y=trend_df["Leasehold"], name="Leasehold", marker_color=C["leasehold"])
                        fig8.add_bar(x=trend_df["Period"], y=trend_df["Capital"], name="Capital", marker_color=C["capital"])
                        fig8.add_bar(x=trend_df["Period"], y=trend_df["Workover"], name="Workover", marker_color=C["workover"])
                        fig8.update_layout(**plot_layout(height=320, barmode="stack", yaxis=dict(tickprefix="$", tickformat=",.0f")))
                        style_axes(fig8)
                        st.plotly_chart(fig8, use_container_width=True)

                    with st.expander("Raw line-item table"):
                        acct_tbl = acct_detail.copy()
                        acct_tbl["Amount"] = acct_tbl["AmountAdj"].apply(lambda x: fmt_currency(x, 0))
                        acct_tbl = acct_tbl.rename(columns={"AccountDesc": "Description"})
                        st.dataframe(acct_tbl[["Bucket", "Account", "Description", "Amount"]], use_container_width=True, hide_index=True)
                    close_panel()

with tab_pl:
    pl_t1, pl_t2, pl_t3, pl_t4 = st.tabs(
        ["Monthly P&L", "Full P&L Waterfall", "Well P&L", "Margins & Trend"]
    )

    with pl_t1:
        add_panel("Monthly P&L Table", "Institutional bridge from gross revenue to net income", "green")
        pnl_tbl = pl.copy()
        if not pnl_tbl.empty:
            display_cols = [
                "Period", "Gross", "Deductions", "Net_Rev", "LOE", "Workover",
                "OpEx", "Leasehold", "Capital", "Total_Exp", "Field_EBITDA", "Net_Income",
                "EBITDA_Margin", "Net_Margin"
            ]
            pnl_tbl = pnl_tbl[display_cols].copy()
            rename_map = {
                "Net_Rev": "Net Revenue",
                "LOE": "LOE",
                "Workover": "Workover",
                "OpEx": "OpEx",
                "Leasehold": "Leasehold",
                "Capital": "Capital",
                "Total_Exp": "Total Expense",
                "Field_EBITDA": "Field EBITDA",
                "Net_Income": "Net Income",
                "EBITDA_Margin": "EBITDA Margin %",
                "Net_Margin": "Net Margin %",
                "Gross": "Gross Revenue",
                "Deductions": "Deductions",
            }
            pnl_tbl = pnl_tbl.rename(columns=rename_map)
            for col in pnl_tbl.columns:
                if col in {"Period", "EBITDA Margin %", "Net Margin %"}:
                    continue
                pnl_tbl[col] = pnl_tbl[col].apply(lambda x: fmt_currency(x, 0))
            pnl_tbl["EBITDA Margin %"] = pl["EBITDA_Margin"].apply(lambda x: fmt_pct(x))
            pnl_tbl["Net Margin %"] = pl["Net_Margin"].apply(lambda x: fmt_pct(x))
        st.dataframe(pnl_tbl, use_container_width=True, hide_index=True)
        close_panel()

    with pl_t2:
        wf_col1, wf_col2 = st.columns(2, gap="medium")
        with wf_col1:
            wf_period = st.selectbox(
                "Period",
                ["All periods"] + (months_sorted[::-1] if months_sorted else ["—"]),
                key="pl_wf_period",
            )
        with wf_col2:
            wf_level = st.radio(
                "View",
                ["Portfolio", "Single Well"],
                key="pl_wf_level",
                horizontal=True,
            )
        
        wf_well = None
        if wf_level == "Single Well":
            available_wells = sorted(summary["Well"].unique().tolist()) if not summary.empty else []
            if available_wells:
                wf_well = st.selectbox("Select well", available_wells, key="pl_wf_well")
            else:
                st.warning("No wells available")
        
        if wf_level == "Single Well" and wf_well:
            if wf_period == "All periods":
                well_data = summary[(summary["Well"].eq(wf_well))].copy()
            else:
                well_data = summary[(summary["Period"].eq(wf_period)) & (summary["Well"].eq(wf_well))].copy()
            
            well_exp = exp_summary[(exp_summary["Well"].eq(wf_well))].copy() if wf_period == "All periods" else exp_summary[(exp_summary["Period"].eq(wf_period)) & (exp_summary["Well"].eq(wf_well))].copy()
            
            if well_data.empty:
                st.info(f"No data for {wf_well}" + (f" in {wf_period}" if wf_period != "All periods" else ""))
            else:
                # Aggregate across all rows
                gross_rev = float(well_data["Gross_Revenue"].sum())
                total_ded = float(well_data["Total_Deductions"].sum())
                net_rev = float(well_data["Net_Revenue"].sum())
                loe = well_exp.loc[well_exp["Bucket"].eq("LOE"), "AmountAdj" if "AmountAdj" in well_exp.columns else "Amount"].sum() if not well_exp.empty else 0.0
                workover = well_exp.loc[well_exp["Bucket"].eq("Workover"), "AmountAdj" if "AmountAdj" in well_exp.columns else "Amount"].sum() if not well_exp.empty else 0.0
                leasehold = well_exp.loc[well_exp["Bucket"].eq("Leasehold"), "AmountAdj" if "AmountAdj" in well_exp.columns else "Amount"].sum() if not well_exp.empty else 0.0
                capital = well_exp.loc[well_exp["Bucket"].eq("Capital"), "AmountAdj" if "AmountAdj" in well_exp.columns else "Amount"].sum() if not well_exp.empty else 0.0
                
                labels = ["Gross Revenue", "Deductions", "Net Revenue", "LOE", "Workover", "Leasehold", "Capital", "Net Income"]
                values = [
                    gross_rev,
                    -total_ded,
                    net_rev,
                    -loe,
                    -workover,
                    -leasehold,
                    -capital,
                    net_rev - loe - workover - leasehold - capital,
                ]
                
                period_label = wf_period if wf_period != "All periods" else "All Periods"
                add_panel(f"P&L Waterfall — {wf_well} ({period_label})", "From gross revenue to bottom-line net income", "purple")
                fig9 = go.Figure(
                    go.Waterfall(
                        x=labels,
                        y=values,
                        measure=["absolute", "relative", "total", "relative", "relative", "relative", "relative", "total"],
                        connector=dict(line=dict(color="#94a3b8")),
                        increasing=dict(marker=dict(color=C["green"])),
                        decreasing=dict(marker=dict(color=C["red"])),
                        totals=dict(marker=dict(color=C["purple"])),
                        text=[fmt_currency(v) for v in values],
                        textposition="outside",
                        hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
                    )
                )
                fig9.update_layout(**plot_layout(height=440, yaxis=dict(tickprefix="$", tickformat=",.0f")))
                style_axes(fig9)
                st.plotly_chart(fig9, use_container_width=True)
                close_panel()
        else:
            if wf_period == "All periods":
                row_data = pl.copy()
                if row_data.empty:
                    st.info("No P&L data available")
                else:
                    r_gross = float(row_data["Gross"].sum())
                    r_ded = float(row_data["Deductions"].sum())
                    r_net = float(row_data["Net_Rev"].sum())
                    r_loe = float(row_data["LOE"].sum())
                    r_workover = float(row_data["Workover"].sum())
                    r_leasehold = float(row_data["Leasehold"].sum())
                    r_capital = float(row_data["Capital"].sum())
                    r_ni = float(row_data["Net_Income"].sum())
                    
                    labels = ["Gross Revenue", "Deductions", "Net Revenue", "LOE", "Workover", "Leasehold", "Capital", "Net Income"]
                    values = [r_gross, -r_ded, r_net, -r_loe, -r_workover, -r_leasehold, -r_capital, r_ni]
                    
                    add_panel("P&L Waterfall (Portfolio View — All Periods)", "Aggregate P&L across all selected assets and months", "purple")
                    fig9 = go.Figure(
                        go.Waterfall(
                            x=labels,
                            y=values,
                            measure=["absolute", "relative", "total", "relative", "relative", "relative", "relative", "total"],
                            connector=dict(line=dict(color="#94a3b8")),
                            increasing=dict(marker=dict(color=C["green"])),
                            decreasing=dict(marker=dict(color=C["red"])),
                            totals=dict(marker=dict(color=C["purple"])),
                            text=[fmt_currency(v) for v in values],
                            textposition="outside",
                            hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
                        )
                    )
                    fig9.update_layout(**plot_layout(height=440, yaxis=dict(tickprefix="$", tickformat=",.0f")))
                    style_axes(fig9)
                    st.plotly_chart(fig9, use_container_width=True)
                    close_panel()
            else:
                row = pl.loc[pl["Period"].eq(wf_period)].copy() if not pl.empty else pd.DataFrame()
                if row.empty:
                    st.info("No P&L data is available for the selected period.")
                else:
                    r = row.iloc[0]
                    labels = ["Gross Revenue", "Deductions", "Net Revenue", "LOE", "Workover", "Leasehold", "Capital", "Net Income"]
                    measures = ["absolute", "relative", "total", "relative", "relative", "relative", "relative", "total"]
                    values = [
                        float(r["Gross"]),
                        -float(r["Deductions"]),
                        float(r["Net_Rev"]),
                        -float(r["LOE"]),
                        -float(r["Workover"]),
                        -float(r["Leasehold"]),
                        -float(r["Capital"]),
                        float(r["Net_Income"]),
                    ]
                    add_panel("P&L Waterfall (Portfolio View)", "From gross revenue to bottom-line net income across all selected assets", "purple")
                    fig9 = go.Figure(
                        go.Waterfall(
                            x=labels,
                            y=values,
                            measure=measures,
                            connector=dict(line=dict(color="#94a3b8")),
                            increasing=dict(marker=dict(color=C["green"])),
                            decreasing=dict(marker=dict(color=C["red"])),
                            totals=dict(marker=dict(color=C["purple"])),
                            text=[fmt_currency(v) for v in values],
                            textposition="outside",
                            hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
                        )
                    )
                    fig9.update_layout(**plot_layout(height=440, yaxis=dict(tickprefix="$", tickformat=",.0f")))
                    style_axes(fig9)
                    st.plotly_chart(fig9, use_container_width=True)
                    close_panel()

    with pl_t3:
        metric = st.selectbox(
            "Well P&L metric",
            ["Net Income", "Field EBITDA", "Net Revenue", "Capital"],
            key="well_pl_metric",
        )
        well_period = st.selectbox(
            "Well P&L period",
            ["All periods"] + (months_sorted[::-1] if months_sorted else []),
            key="well_pl_period",
        )
        well_n = st.slider("Top / bottom wells", 5, 20, 10, key="well_pl_n")

        well_rev = summary.copy()
        well_cost = exp_summary.copy()
        if well_period != "All periods":
            well_rev = well_rev[well_rev["Period"].eq(well_period)]
            well_cost = well_cost[well_cost["Period"].eq(well_period)]

        well_rev_agg = (
            well_rev.groupby("Well", as_index=False)
            .agg(Net_Rev=("Net_Revenue", "sum"))
        )
        well_cost_piv = (
            well_cost.pivot_table(index="Well", columns="Bucket", values="AmountAdj" if "AmountAdj" in well_cost.columns else "Amount", aggfunc="sum", fill_value=0.0)
            .reset_index()
            if not well_cost.empty
            else pd.DataFrame(columns=["Well"])
        )
        for bucket in ["LOE", "Leasehold", "Capital", "Workover"]:
            if bucket not in well_cost_piv.columns:
                well_cost_piv[bucket] = 0.0

        well_pl = well_rev_agg.merge(well_cost_piv, on="Well", how="outer").fillna(0.0)
        if not well_pl.empty:
            well_pl["OpEx"] = well_pl["LOE"] + well_pl["Workover"]
            well_pl["Total_Exp"] = well_pl["LOE"] + well_pl["Leasehold"] + well_pl["Capital"] + well_pl["Workover"]
            well_pl["Field_EBITDA"] = well_pl["Net_Rev"] - well_pl["OpEx"]
            well_pl["Net_Income"] = well_pl["Net_Rev"] - well_pl["Total_Exp"]

        metric_map = {
            "Net Income": "Net_Income",
            "Field EBITDA": "Field_EBITDA",
            "Net Revenue": "Net_Rev",
            "Capital": "Capital",
        }
        metric_col = metric_map[metric]

        top_wells = well_pl.sort_values(metric_col, ascending=False).head(well_n)
        bot_wells = well_pl.sort_values(metric_col, ascending=True).head(well_n)

        left, right = st.columns(2, gap="medium")
        with left:
            add_panel(f"Top {well_n} Wells — {metric}", "Best-performing assets under current filters", "green")
            fig10 = go.Figure(
                go.Bar(
                    x=top_wells[metric_col],
                    y=top_wells["Well"],
                    orientation="h",
                    marker_color=[category_color_from_sign(v) for v in top_wells[metric_col]],
                    text=top_wells[metric_col].apply(fmt_currency),
                    textposition="outside",
                    hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
                )
            )
            fig10.update_layout(
                **plot_layout(
                    height=max(340, well_n * 28),
                    xaxis=dict(tickprefix="$", tickformat=",.0f"),
                    yaxis=dict(autorange="reversed"),
                    margin=dict(t=12, r=90, b=36, l=220),
                )
            )
            style_axes(fig10)
            st.plotly_chart(fig10, use_container_width=True)
            close_panel()

        with right:
            add_panel(f"Bottom {well_n} Wells — {metric}", "Weakest-performing assets under current filters", "red")
            fig11 = go.Figure(
                go.Bar(
                    x=bot_wells[metric_col],
                    y=bot_wells["Well"],
                    orientation="h",
                    marker_color=[category_color_from_sign(v) for v in bot_wells[metric_col]],
                    text=bot_wells[metric_col].apply(fmt_currency),
                    textposition="outside",
                    hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
                )
            )
            fig11.update_layout(
                **plot_layout(
                    height=max(340, well_n * 28),
                    xaxis=dict(tickprefix="$", tickformat=",.0f"),
                    yaxis=dict(autorange="reversed"),
                    margin=dict(t=12, r=90, b=36, l=220),
                )
            )
            style_axes(fig11)
            st.plotly_chart(fig11, use_container_width=True)
            close_panel()

        with st.expander("Full well P&L table"):
            table = well_pl.sort_values("Net_Income", ascending=False).copy()
            if not table.empty:
                for col in ["Net_Rev", "LOE", "Workover", "OpEx", "Leasehold", "Capital", "Total_Exp", "Field_EBITDA", "Net_Income"]:
                    table[col] = table[col].apply(lambda x: fmt_currency(x, 0))
                table = table.rename(
                    columns={
                        "Net_Rev": "Net Revenue",
                        "Total_Exp": "Total Expense",
                        "Field_EBITDA": "Field EBITDA",
                        "Net_Income": "Net Income",
                    }
                )
            st.dataframe(table, use_container_width=True, hide_index=True)

    with pl_t4:
        left, right = st.columns([3, 2], gap="medium")

        with left:
            add_panel("Margin Trend", "EBITDA margin, net margin, and deduction rate by month", "teal")
            fig12 = go.Figure()
            if not pl.empty:
                fig12.add_scatter(
                    x=pl["Period"], y=pl["EBITDA_Margin"], name="EBITDA Margin %",
                    mode="lines+markers", line=dict(color=C["green"], width=2.6),
                    marker=dict(size=7, color=C["green"], line=dict(width=2, color="#ffffff")),
                    hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
                )
                fig12.add_scatter(
                    x=pl["Period"], y=pl["Net_Margin"], name="Net Margin %",
                    mode="lines+markers", line=dict(color=C["purple"], width=2.6),
                    marker=dict(size=7, color=C["purple"], line=dict(width=2, color="#ffffff")),
                    hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
                )
                fig12.add_scatter(
                    x=pl["Period"], y=pl["Deduction_Rate"], name="Deduction Rate %",
                    mode="lines+markers", line=dict(color=C["red"], width=1.8, dash="dot"),
                    marker=dict(size=6, color=C["red"], line=dict(width=1.5, color="#ffffff")),
                    hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
                )
            fig12.update_layout(**plot_layout(height=360, yaxis=dict(ticksuffix="%", tickformat=",.1f")))
            style_axes(fig12)
            st.plotly_chart(fig12, use_container_width=True)
            close_panel()

        with right:
            add_panel("Cumulative Earnings Curve", "Field EBITDA and net income build over time", "purple")
            fig13 = go.Figure()
            if not pl.empty:
                fig13.add_scatter(
                    x=pl["Period"], y=pl["Cum_EBITDA"], name="Cum. EBITDA",
                    mode="lines+markers", line=dict(color=C["green"], width=2.6),
                    marker=dict(size=7, color=C["green"], line=dict(width=2, color="#ffffff")),
                    fill="tozeroy", fillcolor=C["green_fill"],
                    hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>",
                )
                fig13.add_scatter(
                    x=pl["Period"], y=pl["Cum_NI"], name="Cum. Net Income",
                    mode="lines+markers", line=dict(color=C["purple"], width=2.6),
                    marker=dict(size=7, color=C["purple"], line=dict(width=2, color="#ffffff")),
                    hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>",
                )
            fig13.update_layout(**plot_layout(height=360, yaxis=dict(tickprefix="$", tickformat=",.0f")))
            style_axes(fig13)
            st.plotly_chart(fig13, use_container_width=True)
            close_panel()

        add_panel("FP&A Commentary", "Auto-generated operating readout from the selected portfolio", "blue")
        commentary = []
        commentary.append(
            f"In {last_period or 'the latest month'}, gross revenue was {fmt_currency(last_gross)} and converted to net revenue of {fmt_currency(last_net)}, implying {fmt_pct(gross_to_net)} gross-to-net retention."
        )
        commentary.append(
            f"Field EBITDA came in at {fmt_currency(last_ebitda)} and net income at {fmt_currency(last_ni)}. Latest net margin was {fmt_pct(last_net_margin)}."
        )
        commentary.append(
            f"Latest cost mix: LOE {fmt_currency(loe_last)}, workover {fmt_currency(workover_last)}, leasehold {fmt_currency(leasehold_last)}, and capital {fmt_currency(capital_last)}."
        )
        if not pd.isna(mom_pct(last_ebitda, prev_ebitda)):
            trend_dir = "up" if mom_pct(last_ebitda, prev_ebitda) >= 0 else "down"
            commentary.append(
                f"Field EBITDA was {trend_dir} {abs(mom_pct(last_ebitda, prev_ebitda)):.1f}% versus {prev_period}."
            )
        # FIX #5: Validate BOE/LOE_per_BOE before using in commentary
        if not boe_frame.empty and not pd.isna(latest_loe_per_boe) and latest_loe_per_boe > 0:
            commentary.append(
                f"Unit cost efficiency tracked at {fmt_currency(latest_loe_per_boe, 2)} per BOE in {last_period}."
            )

        st.write(" ".join(commentary))
        close_panel()

st.markdown(
    "<div class='footer-note'>Model note: Field EBITDA is defined here as net revenue less LOE and workover. Net income is net revenue less LOE, workover, leasehold, and capital.</div>",
    unsafe_allow_html=True,
)
