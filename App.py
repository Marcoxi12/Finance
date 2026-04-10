"""
P&L Command Center
Clean working Streamlit dashboard
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_loader import ingest_file, load_all_data, get_summary, get_expense_summary

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="P&L Command Center",
    page_icon="◼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────
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

[data-testid="stSidebar"] * { color: #a4b4cf !important; }
[data-testid="stSidebar"] .stMarkdown p { color: #7f93b4 !important; }

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

[data-testid="stSidebar"] hr { border-color: #1b2b45 !important; }

.sidebar-brand {
    display: flex;
    gap: 12px;
    align-items: center;
    padding: 16px 0 18px 0;
    border-bottom: 1px solid #1b2b45;
    margin-bottom: 16px;
}

.sidebar-brand-box {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: linear-gradient(135deg, #1d4ed8, #60a5fa);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff !important;
    font-weight: 800;
    box-shadow: 0 8px 18px rgba(29,78,216,0.28);
}

.sidebar-brand-title {
    font-size: 14px;
    font-weight: 700;
    color: #e7eefb !important;
}

.sidebar-brand-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #5e7499 !important;
}

.sb-section {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #6780a8 !important;
    margin: 14px 0 8px 0;
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
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #6f8ec2;
    margin-bottom: 8px;
}

.header-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 24px;
}

.header-title {
    font-size: 28px;
    font-weight: 300;
    color: #eaf1ff;
    letter-spacing: -0.03em;
}

.header-title strong {
    font-weight: 800;
    color: #ffffff;
}

.header-sub {
    font-size: 13px;
    color: #90a7cc;
    margin-top: 6px;
}

.badge-row {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: flex-end;
}

.h-badge {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(111,142,194,0.24);
    border-radius: 999px;
    padding: 8px 14px;
    color: #a8bddf;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
}

.h-badge strong {
    color: #e8f0ff;
    font-weight: 600;
}

.h-badge.live strong {
    color: #52d6a3;
}

.kpi-wrap { padding: 18px 26px 0 26px; }

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(8, minmax(0, 1fr));
    gap: 12px;
}

@media (max-width: 1600px) {
    .kpi-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}

@media (max-width: 900px) {
    .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
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

.kpi-card.green { border-top-color: #059669; }
.kpi-card.red { border-top-color: #dc2626; }
.kpi-card.amber { border-top-color: #d97706; }
.kpi-card.purple { border-top-color: #7c3aed; }
.kpi-card.teal { border-top-color: #0f766e; }

.kpi-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #7b8da9;
    margin-bottom: 8px;
}

.kpi-value {
    font-size: 24px;
    font-weight: 750;
    letter-spacing: -0.04em;
    color: #0f172a;
    line-height: 1.05;
}

.kpi-value.neg { color: #b91c1c; }

.kpi-delta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    margin-top: 8px;
}

.kpi-delta.pos { color: #059669; }
.kpi-delta.neg { color: #dc2626; }
.kpi-delta.neu { color: #94a3b8; }

.kpi-note {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #9aa8bd;
    margin-top: 5px;
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
    color: #70839f !important;
    font-weight: 600 !important;
    border-bottom: 2px solid transparent !important;
}

.stTabs [aria-selected="true"] {
    color: #1d4ed8 !important;
    border-bottom-color: #1d4ed8 !important;
}

.stTabs [data-baseweb="tab-panel"] {
    padding: 22px 28px 10px 28px !important;
}

.panel {
    background: rgba(255,255,255,0.92);
    backdrop-filter: blur(10px);
    border: 1px solid #dfe6f3;
    border-radius: 18px;
    padding: 18px 20px 16px 20px;
    margin-bottom: 16px;
    box-shadow: 0 10px 30px rgba(20,31,56,0.05);
}

.panel.red { border-top: 3px solid #dc2626; }
.panel.blue { border-top: 3px solid #1d4ed8; }
.panel.green { border-top: 3px solid #059669; }
.panel.purple { border-top: 3px solid #7c3aed; }
.panel.amber { border-top: 3px solid #d97706; }
.panel.teal { border-top: 3px solid #0f766e; }

.panel-title {
    font-size: 15px;
    font-weight: 750;
    color: #0f172a;
    margin-bottom: 4px;
}

.panel-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #90a0b8;
    padding-bottom: 12px;
    border-bottom: 1px solid #edf2f7;
    margin-bottom: 14px;
}

.callout-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0,1fr));
    gap: 12px;
    margin-top: 6px;
    margin-bottom: 10px;
}

@media (max-width: 1400px) {
    .callout-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
}

.callout {
    border: 1px solid #dfe6f3;
    border-radius: 14px;
    padding: 12px 14px;
    background: linear-gradient(180deg, #fbfdff 0%, #f5f8fd 100%);
}

.callout.good {
    background: linear-gradient(180deg, #f0fdf4 0%, #ecfdf5 100%);
    border-color: #bae6d3;
}

.callout.warn {
    background: linear-gradient(180deg, #fff7ed 0%, #fffbeb 100%);
    border-color: #fcd7aa;
}

.callout.bad {
    background: linear-gradient(180deg, #fff1f2 0%, #fff5f5 100%);
    border-color: #fecdd3;
}

.callout-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #7b8da9;
    margin-bottom: 5px;
}

.callout-value {
    font-size: 19px;
    font-weight: 750;
    color: #0f172a;
    letter-spacing: -0.03em;
}

.callout-note {
    font-size: 11px;
    color: #64748b;
    margin-top: 4px;
}

.footer-note {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #94a3b8;
    text-align: right;
    padding: 0 28px 18px 28px;
}

div[data-testid="metric-container"] { display: none; }

.stExpander {
    border: 1px solid #dfe6f3 !important;
    border-radius: 14px !important;
    background: rgba(255,255,255,0.86) !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Constants ─────────────────────────────────────────────────────────────────
PF = "Inter, sans-serif"
MF = "JetBrains Mono, monospace"
GRID = "#e8edf5"
BG = "rgba(255,255,255,0.0)"

COLORS = {
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
    "loe": "#2563eb",
    "workover": "#dc2626",
    "leasehold": "#d97706",
    "capital": "#7c3aed",
    "total_cost": "#111827",
}

# ── Utility functions ─────────────────────────────────────────────────────────
def fmt_currency(v: float, decimals: int = 1) -> str:
    try:
        v = float(v)
    except Exception:
        return "$0"

    sign = "-" if v < 0 else ""
    v = abs(v)

    if v >= 1_000_000_000:
        return f"{sign}${v / 1_000_000_000:.{decimals}f}B"
    if v >= 1_000_000:
        return f"{sign}${v / 1_000_000:.{decimals}f}M"
    if v >= 1_000:
        return f"{sign}${v / 1_000:.{decimals}f}K"
    return f"{sign}${v:,.0f}"


def fmt_pct(v: float, decimals: int = 1) -> str:
    try:
        return f"{float(v):.{decimals}f}%"
    except Exception:
        return "0.0%"


def safe_div(a: float, b: float, scale: float = 1.0) -> float:
    try:
        if b in (0, None) or pd.isna(b):
            return 0.0
        return (a / b) * scale
    except Exception:
        return 0.0


def mom_pct(cur: float, prev: float) -> float:
    if prev in (0, None) or pd.isna(prev):
        return np.nan
    return (cur - prev) / abs(prev) * 100


def delta_html(cur: float, prev: float, label: str = "") -> str:
    delta = mom_pct(cur, prev)
    if pd.isna(delta):
        return '<div class="kpi-delta neu">—</div>'
    arrow = "▲" if delta >= 0 else "▼"
    cls = "pos" if delta >= 0 else "neg"
    lbl = f" vs {label}" if label else ""
    return f'<div class="kpi-delta {cls}">{arrow} {abs(delta):.1f}%{lbl}</div>'


def plot_layout(height: int = 360, **kwargs) -> Dict:
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


def style_axes(fig: go.Figure) -> go.Figure:
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


def add_panel(title: str, sub: str, color: str = "blue") -> None:
    st.markdown(
        f'<div class="panel {color}"><div class="panel-title">{title}</div><div class="panel-sub">{sub}</div>',
        unsafe_allow_html=True,
    )


def close_panel() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def period_sort(values: list) -> list:
    vals = [str(v) for v in values if pd.notna(v) and str(v).strip() != ""]
    return sorted(vals)


def normalize_str(s) -> str:
    if pd.isna(s):
        return "Unknown"
    s = str(s).strip()
    return s if s else "Unknown"


@st.cache_data
def ensure_columns(frame: pd.DataFrame, defaults: dict) -> pd.DataFrame:
    frame = frame.copy()
    for col, default in defaults.items():
        if col not in frame.columns:
            frame[col] = default
    return frame


@st.cache_data
def load_and_prepare_data():
    raw = load_all_data()
    if raw is None or len(raw) == 0:
        return None, None, None

    df = raw.copy()
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
            "Company": "Unknown",
            "QtyAdj": 0.0,
        },
    )

    df["Well"] = df["Well"].apply(normalize_str)
    df["SubAcctNum"] = df["SubAcctNum"].apply(normalize_str)
    df["Period"] = df["Period"].fillna("").astype(str).str.strip()
    df["Bucket"] = df["Bucket"].apply(normalize_str)
    df["AmountAdj"] = pd.to_numeric(df["AmountAdj"], errors="coerce").fillna(0.0)
    df["QtyAdj"] = pd.to_numeric(df["QtyAdj"], errors="coerce").fillna(0.0)

    return df, raw, None


def build_summary_and_expenses(dff: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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
        exp_summary.pivot_table(
            index="Period",
            columns="Bucket",
            values="Amount",
            aggfunc="sum",
            fill_value=0.0,
        )
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
    pl = pl.merge(
        exp_period[["Period", "LOE", "Leasehold", "Capital", "Workover"]],
        on="Period",
        how="left",
    ).fillna(0.0)

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
    pl["BOE"] = pl["Oil_BBL"] + (pl["Gas_MCF"] / 6.0)
    pl["LOE_per_BOE"] = np.where(pl["BOE"] != 0, pl["LOE"] / pl["BOE"], 0.0)
    pl = pl.sort_values("Period").reset_index(drop=True)

    return summary, exp_summary, pl


def render_sidebar() -> Tuple[pd.DataFrame, pd.DataFrame, list, list, Tuple[Optional[str], Optional[str]]]:
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

        raw_result = load_and_prepare_data()
        if raw_result[0] is None:
            st.warning("No data loaded yet. Upload a GL export to begin.")
            st.stop()

        df, raw, _ = raw_result

        st.markdown('<div class="sb-section">Loaded Files</div>', unsafe_allow_html=True)
        meta_file = Path("data/uploaded_files.json")
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text())
                files_list = meta.get("files", [])
                if files_list:
                    st.markdown(f"**{len(files_list)} file(s) loaded:**")
                    for i, file_info in enumerate(files_list):
                        col1, col2 = st.columns([0.85, 0.15])
                        with col1:
                            st.caption(
                                f"📄 {file_info['filename']}\n"
                                f"Rows: {file_info.get('rows', 0):,} | "
                                f"Periods: {file_info.get('periods', 0)} | "
                                f"Wells: {file_info.get('wells', 0)}"
                            )
                        with col2:
                            if st.button("✕", key=f"del_{i}"):
                                meta["files"].pop(i)
                                meta_file.write_text(json.dumps(meta, indent=2))
                                st.success("File removed")
                                st.rerun()
                else:
                    st.caption("No files loaded yet")
            except Exception:
                st.caption("No files loaded yet")

        st.markdown('<div class="sb-section">Company Selection</div>', unsafe_allow_html=True)
        available_companies = sorted(set(df["Company"].unique().tolist())) if "Company" in df.columns else ["Unknown"]
        sel_companies = st.multiselect(
            "Companies",
            options=available_companies,
            default=available_companies,
            label_visibility="collapsed",
        )

        st.markdown('<div class="sb-section">Portfolio Filter</div>', unsafe_allow_html=True)
        valid_well_mask = (
            df["Well"].notna()
            & df["Well"].astype(str).str.strip().ne("")
            & df["Well"].astype(str).str.strip().str.lower().ne("unknown")
        )
        well_map = (
            df.loc[valid_well_mask, ["SubAcctNum", "Well"]]
            .drop_duplicates()
            .sort_values(["SubAcctNum", "Well"])
        )

        all_subaccts = sorted(well_map["SubAcctNum"].unique().tolist()) if not well_map.empty else []
        all_wells = sorted(well_map["Well"].unique().tolist()) if not well_map.empty else []

        sel_subaccts = st.multiselect(
            "Sub accounts",
            options=all_subaccts,
            default=[],
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
            label_visibility="collapsed",
        )

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

    dff = df.copy()
    if sel_companies:
        dff = dff[dff["Company"].isin(sel_companies)]
    if sel_subaccts:
        dff = dff[dff["SubAcctNum"].isin(sel_subaccts)]
    if sel_wells:
        dff = dff[dff["Well"].isin(sel_wells)]
    if period_range[0] and period_range[1]:
        dff = dff[(dff["Period"] >= period_range[0]) & (dff["Period"] <= period_range[1])]

    return dff, df, sel_companies, sel_wells, period_range


def render_kpi_cards(
    last_period: str,
    prev_period: str,
    last_gross: float,
    prev_gross: float,
    last_net: float,
    prev_net: float,
    last_ebitda: float,
    prev_ebitda: float,
    last_ni: float,
    last_total_exp: float,
    last_net_margin: float,
    cum_net_margin: float,
    last_ded_rate: float,
    last_deductions: float,
    cum_ebitda: float,
    period_count: int,
    latest_loe_per_boe: float,
    latest_boe: float,
) -> None:
    kpi_specs = [
        (
            "Gross Revenue",
            fmt_currency(last_gross),
            delta_html(last_gross, prev_gross, prev_period or ""),
            "Latest month gross before deductions",
            "blue",
            last_gross,
        ),
        (
            "Net Revenue",
            fmt_currency(last_net),
            delta_html(last_net, prev_net, prev_period or ""),
            "After taxes, gathering, and fees",
            "green",
            last_net,
        ),
        (
            "Field EBITDA",
            fmt_currency(last_ebitda),
            delta_html(last_ebitda, prev_ebitda, prev_period or ""),
            "Net revenue less LOE + workover",
            "green" if last_ebitda >= 0 else "red",
            last_ebitda,
        ),
        (
            "Net Income",
            fmt_currency(last_ni),
            '<div class="kpi-delta neu">All-in after leasehold + capital</div>',
            f"Total costs: {fmt_currency(last_total_exp)}",
            "green" if last_ni >= 0 else "red",
            last_ni,
        ),
        (
            "Net Margin",
            fmt_pct(last_net_margin),
            '<div class="kpi-delta neu">Profitability on gross revenue</div>',
            f"Cumulative: {fmt_pct(cum_net_margin)}",
            "teal" if last_net_margin >= 0 else "red",
            last_net_margin,
        ),
        (
            "Deduction Rate",
            fmt_pct(last_ded_rate),
            '<div class="kpi-delta neu">Revenue haircut</div>',
            f"Deductions: {fmt_currency(last_deductions)}",
            "amber",
            last_ded_rate,
        ),
        (
            "Cum. EBITDA",
            fmt_currency(cum_ebitda),
            '<div class="kpi-delta neu">Across selected history</div>',
            f"{period_count} period(s)",
            "purple" if cum_ebitda >= 0 else "red",
            cum_ebitda,
        ),
        (
            "LOE / BOE",
            fmt_currency(latest_loe_per_boe, 2),
            '<div class="kpi-delta neu">Unit operating efficiency</div>',
            f"BOE: {latest_boe:,.0f}",
            "teal",
            latest_loe_per_boe,
        ),
    ]

    cards_html = '<div class="kpi-wrap"><div class="kpi-grid">'
    for label, val, delta_block, note, klass, raw in kpi_specs:
        neg_cls = " neg" if raw < 0 and label not in {"Deduction Rate", "LOE / BOE"} else ""
        cards_html += (
            f'<div class="kpi-card {klass}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value{neg_cls}">{val}</div>'
            f"{delta_block}"
            f'<div class="kpi-note">{note}</div>'
            f"</div>"
        )
    cards_html += "</div></div>"
    st.markdown(cards_html, unsafe_allow_html=True)


def build_period_table_for_display(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    money_cols = [
        "Gross",
        "Deductions",
        "Net_Rev",
        "LOE",
        "Workover",
        "Leasehold",
        "Capital",
        "OpEx",
        "Field_EBITDA",
        "Total_Exp",
        "Net_Income",
        "Cum_EBITDA",
        "Cum_NI",
    ]
    pct_cols = ["Gross_Margin", "EBITDA_Margin", "Net_Margin", "Deduction_Rate"]

    for col in money_cols:
        if col in out.columns:
            out[col] = out[col].apply(lambda x: round(float(x), 2))
    for col in pct_cols:
        if col in out.columns:
            out[col] = out[col].apply(lambda x: round(float(x), 2))

    return out


def main():
    dff, df, sel_companies, sel_wells, period_range = render_sidebar()

    summary, exp_summary, pl = build_summary_and_expenses(dff)

    if pl.empty:
        st.warning("No records remain after applying your filters.")
        st.stop()

    months_sorted = period_sort(dff["Period"].unique().tolist())
    last_period = months_sorted[-1] if months_sorted else None
    prev_period = months_sorted[-2] if len(months_sorted) >= 2 else None
    period_count = len(months_sorted)
    selected_well_count = len(sel_wells) if sel_wells else dff["Well"].nunique()
    total_loaded_wells = df["Well"].nunique()

    last_row = pl.loc[pl["Period"].eq(last_period)].iloc[-1] if last_period and not pl.loc[pl["Period"].eq(last_period)].empty else None
    prev_row = pl.loc[pl["Period"].eq(prev_period)].iloc[-1] if prev_period and not pl.loc[pl["Period"].eq(prev_period)].empty else None

    last_gross = float(last_row["Gross"]) if last_row is not None else 0.0
    prev_gross = float(prev_row["Gross"]) if prev_row is not None else 0.0
    last_net = float(last_row["Net_Rev"]) if last_row is not None else 0.0
    prev_net = float(prev_row["Net_Rev"]) if prev_row is not None else 0.0
    last_ebitda = float(last_row["Field_EBITDA"]) if last_row is not None else 0.0
    prev_ebitda = float(prev_row["Field_EBITDA"]) if prev_row is not None else 0.0
    last_ni = float(last_row["Net_Income"]) if last_row is not None else 0.0
    last_total_exp = float(last_row["Total_Exp"]) if last_row is not None else 0.0
    last_opex = float(last_row["OpEx"]) if last_row is not None else 0.0
    last_capex = float(last_row["Capital"]) if last_row is not None else 0.0
    last_net_margin = float(last_row["Net_Margin"]) if last_row is not None else 0.0
    last_ded_rate = float(last_row["Deduction_Rate"]) if last_row is not None else 0.0
    last_deductions = float(last_row["Deductions"]) if last_row is not None else 0.0
    cum_ebitda = float(pl["Field_EBITDA"].sum())
    cum_net_income = float(pl["Net_Income"].sum())
    cum_gross = float(pl["Gross"].sum())
    cum_net_margin = safe_div(cum_net_income, cum_gross, 100.0)
    latest_boe = float(last_row["BOE"]) if last_row is not None and "BOE" in last_row else 0.0
    latest_loe_per_boe = float(last_row["LOE_per_BOE"]) if last_row is not None and "LOE_per_BOE" in last_row else 0.0

    gross_to_net = safe_div(last_net, last_gross, 100.0)
    opex_burden = safe_div(last_opex, last_net, 100.0)
    capex_burden = safe_div(last_capex, last_net, 100.0)

    best_period = pl.loc[pl["Net_Income"].idxmax(), "Period"] if not pl.empty else "N/A"
    worst_period = pl.loc[pl["Net_Income"].idxmin(), "Period"] if not pl.empty else "N/A"

    companies_label = ", ".join(sel_companies[:3]) if sel_companies else "All Companies"
    if sel_companies and len(sel_companies) > 3:
        companies_label += f" +{len(sel_companies) - 3}"

    header_html = f"""
    <div class="header-shell">
        <div class="header-kicker">Institutional FP&amp;A Dashboard</div>
        <div class="header-row">
            <div>
                <div class="header-title">P&amp;L <strong>Command Center</strong></div>
                <div class="header-sub">
                    Revenue, deductions, cost discipline, and field profitability across selected periods.
                </div>
            </div>
            <div class="badge-row">
                <div class="h-badge"><strong>Company</strong> {companies_label}</div>
                <div class="h-badge"><strong>Periods</strong> {period_range[0] or "N/A"} → {period_range[1] or "N/A"}</div>
                <div class="h-badge"><strong>Wells</strong> {selected_well_count:,} / {total_loaded_wells:,}</div>
                <div class="h-badge live"><strong>Latest</strong> {last_period or "N/A"}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    render_kpi_cards(
        last_period=last_period,
        prev_period=prev_period,
        last_gross=last_gross,
        prev_gross=prev_gross,
        last_net=last_net,
        prev_net=prev_net,
        last_ebitda=last_ebitda,
        prev_ebitda=prev_ebitda,
        last_ni=last_ni,
        last_total_exp=last_total_exp,
        last_net_margin=last_net_margin,
        cum_net_margin=cum_net_margin,
        last_ded_rate=last_ded_rate,
        last_deductions=last_deductions,
        cum_ebitda=cum_ebitda,
        period_count=period_count,
        latest_loe_per_boe=latest_loe_per_boe,
        latest_boe=latest_boe,
    )

    st.markdown(
        f"""
<div class="panel blue">
    <div class="panel-title">Executive Read</div>
    <div class="panel-sub">Latest operating snapshot</div>
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

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Revenue Quality",
            "Cost Discipline",
            "P&L Bridge",
            "Data Tables",
        ]
    )

    with tab1:
        add_panel("Revenue Quality", "Gross, net, deductions, and product mix", "blue")

        fig_rev = go.Figure()
        fig_rev.add_trace(
            go.Bar(
                x=pl["Period"],
                y=pl["Gross"],
                name="Gross Revenue",
                marker_color=COLORS["blue"],
            )
        )
        fig_rev.add_trace(
            go.Bar(
                x=pl["Period"],
                y=pl["Deductions"],
                name="Deductions",
                marker_color=COLORS["amber"],
            )
        )
        fig_rev.add_trace(
            go.Scatter(
                x=pl["Period"],
                y=pl["Net_Rev"],
                name="Net Revenue",
                mode="lines+markers",
                line=dict(color=COLORS["green"], width=3),
                marker=dict(size=7),
                yaxis="y2",
            )
        )
        fig_rev.update_layout(
            **plot_layout(height=430),
            barmode="group",
            yaxis=dict(title="Gross / Deductions"),
            yaxis2=dict(title="Net Revenue", overlaying="y", side="right", showgrid=False),
        )
        style_axes(fig_rev)
        st.plotly_chart(fig_rev, use_container_width=True)

        mix_cols = st.columns(3)

        with mix_cols[0]:
            commodity_fig = go.Figure()
            commodity_fig.add_trace(
                go.Bar(x=pl["Period"], y=pl["Oil"], name="Oil", marker_color=COLORS["oil"])
            )
            commodity_fig.add_trace(
                go.Bar(x=pl["Period"], y=pl["Gas"], name="Gas", marker_color=COLORS["gas"])
            )
            commodity_fig.add_trace(
                go.Bar(x=pl["Period"], y=pl["Plant"], name="Plant", marker_color=COLORS["plant"])
            )
            commodity_fig.update_layout(**plot_layout(height=320), barmode="stack")
            style_axes(commodity_fig)
            st.plotly_chart(commodity_fig, use_container_width=True)

        with mix_cols[1]:
            ded_fig = go.Figure()
            ded_fig.add_trace(go.Bar(x=pl["Period"], y=pl["Oil_Tax"], name="Oil Tax"))
            ded_fig.add_trace(go.Bar(x=pl["Period"], y=pl["Gas_Tax"], name="Gas Tax"))
            ded_fig.add_trace(go.Bar(x=pl["Period"], y=pl["Gas_Comp"], name="Gas Comp"))
            ded_fig.add_trace(go.Bar(x=pl["Period"], y=pl["Gas_LowVol"], name="Low Vol"))
            ded_fig.add_trace(go.Bar(x=pl["Period"], y=pl["Plant_Tax"], name="Plant Tax"))
            ded_fig.add_trace(go.Bar(x=pl["Period"], y=pl["Plant_Deduct"], name="Plant Deduct"))
            ded_fig.add_trace(go.Bar(x=pl["Period"], y=pl["Rejected_Fee"], name="Rejected Fee"))
            ded_fig.update_layout(**plot_layout(height=320), barmode="stack")
            style_axes(ded_fig)
            st.plotly_chart(ded_fig, use_container_width=True)

        with mix_cols[2]:
            retention_fig = go.Figure()
            retention_fig.add_trace(
                go.Scatter(
                    x=pl["Period"],
                    y=pl["Deduction_Rate"],
                    name="Deduction Rate %",
                    mode="lines+markers",
                    line=dict(color=COLORS["amber"], width=3),
                )
            )
            retention_fig.add_trace(
                go.Scatter(
                    x=pl["Period"],
                    y=pl["Gross_Margin"],
                    name="Net / Gross %",
                    mode="lines+markers",
                    line=dict(color=COLORS["teal"], width=3),
                )
            )
            retention_fig.update_layout(**plot_layout(height=320))
            style_axes(retention_fig)
            st.plotly_chart(retention_fig, use_container_width=True)

        close_panel()

    with tab2:
        add_panel("Cost Discipline", "LOE, workover, leasehold, capital, and unit costs", "green")

        fig_cost = go.Figure()
        fig_cost.add_trace(go.Bar(x=pl["Period"], y=pl["LOE"], name="LOE", marker_color=COLORS["loe"]))
        fig_cost.add_trace(go.Bar(x=pl["Period"], y=pl["Workover"], name="Workover", marker_color=COLORS["workover"]))
        fig_cost.add_trace(go.Bar(x=pl["Period"], y=pl["Leasehold"], name="Leasehold", marker_color=COLORS["leasehold"]))
        fig_cost.add_trace(go.Bar(x=pl["Period"], y=pl["Capital"], name="Capital", marker_color=COLORS["capital"]))
        fig_cost.update_layout(**plot_layout(height=430), barmode="stack")
        style_axes(fig_cost)
        st.plotly_chart(fig_cost, use_container_width=True)

        c1, c2 = st.columns(2)

        with c1:
            unit_fig = go.Figure()
            unit_fig.add_trace(
                go.Scatter(
                    x=pl["Period"],
                    y=pl["LOE_per_BOE"],
                    name="LOE / BOE",
                    mode="lines+markers",
                    line=dict(color=COLORS["teal"], width=3),
                )
            )
            unit_fig.update_layout(**plot_layout(height=320))
            style_axes(unit_fig)
            st.plotly_chart(unit_fig, use_container_width=True)

        with c2:
            burden_fig = go.Figure()
            burden_fig.add_trace(
                go.Scatter(
                    x=pl["Period"],
                    y=np.where(pl["Net_Rev"] != 0, pl["OpEx"] / pl["Net_Rev"] * 100, 0.0),
                    name="OpEx Burden %",
                    mode="lines+markers",
                    line=dict(color=COLORS["red"], width=3),
                )
            )
            burden_fig.add_trace(
                go.Scatter(
                    x=pl["Period"],
                    y=np.where(pl["Net_Rev"] != 0, pl["Capital"] / pl["Net_Rev"] * 100, 0.0),
                    name="Capital Intensity %",
                    mode="lines+markers",
                    line=dict(color=COLORS["purple"], width=3),
                )
            )
            burden_fig.update_layout(**plot_layout(height=320))
            style_axes(burden_fig)
            st.plotly_chart(burden_fig, use_container_width=True)

        close_panel()

    with tab3:
        add_panel("P&L Bridge", "EBITDA, net income, and cumulative performance", "purple")

        fig_pnl = go.Figure()
        fig_pnl.add_trace(
            go.Bar(
                x=pl["Period"],
                y=pl["Field_EBITDA"],
                name="Field EBITDA",
                marker_color=COLORS["green"],
            )
        )
        fig_pnl.add_trace(
            go.Bar(
                x=pl["Period"],
                y=pl["Net_Income"],
                name="Net Income",
                marker_color=COLORS["blue"],
            )
        )
        fig_pnl.add_trace(
            go.Scatter(
                x=pl["Period"],
                y=pl["Cum_NI"],
                name="Cumulative Net Income",
                mode="lines+markers",
                line=dict(color=COLORS["purple"], width=3),
                yaxis="y2",
            )
        )
        fig_pnl.update_layout(
            **plot_layout(height=430),
            barmode="group",
            yaxis=dict(title="Monthly P&L"),
            yaxis2=dict(title="Cumulative Net Income", overlaying="y", side="right", showgrid=False),
        )
        style_axes(fig_pnl)
        st.plotly_chart(fig_pnl, use_container_width=True)

        margin_fig = go.Figure()
        margin_fig.add_trace(
            go.Scatter(
                x=pl["Period"],
                y=pl["EBITDA_Margin"],
                name="EBITDA Margin %",
                mode="lines+markers",
                line=dict(color=COLORS["green"], width=3),
            )
        )
        margin_fig.add_trace(
            go.Scatter(
                x=pl["Period"],
                y=pl["Net_Margin"],
                name="Net Margin %",
                mode="lines+markers",
                line=dict(color=COLORS["blue"], width=3),
            )
        )
        margin_fig.update_layout(**plot_layout(height=320))
        style_axes(margin_fig)
        st.plotly_chart(margin_fig, use_container_width=True)

        close_panel()

    with tab4:
        add_panel("Period-Level Model", "Detailed table for export / validation", "teal")
        display_pl = build_period_table_for_display(pl)[
            [
                "Period",
                "Gross",
                "Deductions",
                "Net_Rev",
                "Oil",
                "Gas",
                "Plant",
                "LOE",
                "Workover",
                "Leasehold",
                "Capital",
                "OpEx",
                "Field_EBITDA",
                "Total_Exp",
                "Net_Income",
                "Gross_Margin",
                "EBITDA_Margin",
                "Net_Margin",
                "Deduction_Rate",
                "BOE",
                "LOE_per_BOE",
                "Cum_EBITDA",
                "Cum_NI",
            ]
        ].copy()

        display_pl = display_pl.rename(
            columns={
                "Gross": "Gross Revenue",
                "Net_Rev": "Net Revenue",
                "Oil": "Oil Revenue",
                "Gas": "Gas Revenue",
                "Plant": "Plant Revenue",
                "OpEx": "Operating Expense",
                "Field_EBITDA": "Field EBITDA",
                "Total_Exp": "Total Expense",
                "Net_Income": "Net Income",
                "Gross_Margin": "Net / Gross %",
                "EBITDA_Margin": "EBITDA Margin %",
                "Net_Margin": "Net Margin %",
                "Deduction_Rate": "Deduction Rate %",
                "LOE_per_BOE": "LOE / BOE",
                "Cum_EBITDA": "Cumulative EBITDA",
                "Cum_NI": "Cumulative NI",
            }
        )
        st.dataframe(display_pl, use_container_width=True)

        csv = display_pl.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download model CSV",
            data=csv,
            file_name="pl_command_center_export.csv",
            mime="text/csv",
        )
        close_panel()

    st.markdown(
        "<div class='footer-note'>Model note: Field EBITDA is defined here as net revenue less LOE and workover. Net income is net revenue less LOE, workover, leasehold, and capital.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
