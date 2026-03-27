import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_loader import (
    load_all_data, get_summary, get_expense_summary,
    get_expense_detail, ingest_file,
)

st.set_page_config(
    page_title="Integrated P&L · FP&A Console",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
}
.stApp { background: #f0f2f5; }
.main .block-container { padding: 0 !important; max-width: 100% !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"], [data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div > div,
section[data-testid="stSidebar"],
.st-emotion-cache-1d391kg, .st-emotion-cache-6qob1r,
.st-emotion-cache-eczf1x,  .st-emotion-cache-1gwvy71,
.st-emotion-cache-16txtl3, .st-emotion-cache-qrbaxs {
    background: #08111f !important;
    background-color: #08111f !important;
}
[data-testid="stSidebar"] { border-right: 1px solid #162035 !important; }
[data-testid="stSidebar"] * { color: #7a93b4 !important; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label { font-size: 11px !important; }
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"],
[data-testid="stSidebar"] [data-testid="stFileUploader"] section {
    background: #0f1e35 !important; border: 1px dashed #1e3a5f !important; border-radius: 4px !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #0f1e35 !important; border: 1px solid #1e3a5f !important; color: #a8c4e0 !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] { background: #122a4a !important; border: 1px solid #1e4878 !important; }
[data-testid="stSidebar"] button {
    background: #0f1e35 !important; border: 1px solid #1e3a5f !important;
    color: #7a93b4 !important; border-radius: 3px !important;
}
[data-testid="stSidebar"] hr { border-color: #162035 !important; }
[data-testid="stSidebar"] [data-baseweb="select"] svg { fill: #2e5080 !important; }

.sb-logo { display:flex; align-items:center; gap:10px; padding:18px 0 16px; border-bottom:1px solid #162035; margin-bottom:6px; }
.sb-logo-box {
    width:32px; height:32px; background:linear-gradient(135deg,#1040a8,#1a56db);
    border-radius:4px; display:flex; align-items:center; justify-content:center;
    font-family:'JetBrains Mono',monospace; font-size:14px; font-weight:700; color:#fff !important;
}
.sb-logo-name { font-size:13px !important; font-weight:700 !important; color:#dce8f8 !important; letter-spacing:-0.2px; }
.sb-logo-sub  { font-size:9px !important; color:#2a4060 !important; font-family:'JetBrains Mono',monospace; letter-spacing:0.12em; text-transform:uppercase; }
.sb-section   { font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:0.16em; text-transform:uppercase; color:#2a4060 !important; padding:16px 0 6px; border-bottom:1px solid #162035; margin-bottom:10px; }
.sb-label     { color:#3d5a7a !important; font-size:9px; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:4px; font-family:'JetBrains Mono',monospace; }
.sb-stat      { font-size:10px !important; color:#2a4060 !important; font-family:'JetBrains Mono',monospace; }

/* ── HEADER ── */
.ent-header {
    background:linear-gradient(135deg,#040c1a 0%,#081428 50%,#0a1c3a 100%);
    border-bottom:2px solid #1040a8;
    padding:22px 36px 18px; display:flex; align-items:flex-end; justify-content:space-between;
}
.ent-breadcrumb { font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:0.18em; text-transform:uppercase; color:#2a4060; margin-bottom:6px; }
.ent-title { font-size:20px; font-weight:300; color:#dce8f8; letter-spacing:-0.4px; }
.ent-title strong { font-weight:700; color:#ffffff; }
.ent-header-right { display:flex; align-items:center; gap:12px; }
.ent-badge {
    background:rgba(16,64,168,0.15); border:1px solid #1e3a6a; border-radius:3px;
    padding:6px 16px; font-family:'JetBrains Mono',monospace; font-size:10px; color:#4a6a9a;
}
.ent-badge strong { color:#7aaee8; font-weight:500; }
.ent-badge.live { border-color:#0e7c4a; background:rgba(14,159,110,0.1); }
.ent-badge.live strong { color:#0e9f6e; }

/* ── KPI STRIP ── */
.kpi-strip { background:#ffffff; border-bottom:1px solid #d4d9e8; display:flex; box-shadow:0 1px 4px rgba(0,0,0,0.06); }
.kpi-item  { flex:1; padding:16px 20px 14px; border-right:1px solid #e8ebf5; position:relative; }
.kpi-item:last-child { border-right:none; }
.kpi-item::after { content:''; position:absolute; top:0; left:0; right:0; height:2px; }
.kpi-item.c-blue::after   { background:linear-gradient(90deg,#1040a8,#1a56db); }
.kpi-item.c-green::after  { background:linear-gradient(90deg,#047857,#0e9f6e); }
.kpi-item.c-amber::after  { background:linear-gradient(90deg,#92400e,#c27803); }
.kpi-item.c-purple::after { background:linear-gradient(90deg,#4c1d95,#6c2bd9); }
.kpi-item.c-red::after    { background:linear-gradient(90deg,#991b1b,#e02424); }
.kpi-item.c-teal::after   { background:linear-gradient(90deg,#065f6e,#0694a2); }
.kpi-item.c-indigo::after { background:linear-gradient(90deg,#312e81,#4338ca); }
.kpi-item.c-rose::after   { background:linear-gradient(90deg,#9f1239,#e11d48); }
.kpi-lbl  { font-family:'JetBrains Mono',monospace; font-size:8.5px; letter-spacing:0.14em; text-transform:uppercase; color:#8090aa; margin-bottom:5px; }
.kpi-val  { font-size:22px; font-weight:600; color:#0d1424; letter-spacing:-0.8px; line-height:1.1; margin-bottom:4px; }
.kpi-val.neg { color:#c81e1e; }
.kpi-delta     { font-family:'JetBrains Mono',monospace; font-size:9.5px; }
.kpi-delta.pos { color:#0e9f6e; }
.kpi-delta.neg { color:#e02424; }
.kpi-delta.neu { color:#9aa4b8; }
.kpi-sub { font-family:'JetBrains Mono',monospace; font-size:9px; color:#b0bbd4; margin-top:2px; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background:#ffffff !important; border-bottom:1px solid #d4d9e8 !important;
    padding:0 36px !important; gap:0 !important; box-shadow:0 1px 3px rgba(0,0,0,0.04);
}
.stTabs [data-baseweb="tab"] {
    background:transparent !important; border:none !important;
    border-bottom:2px solid transparent !important; padding:14px 22px !important;
    font-family:'Inter',sans-serif !important; font-size:12px !important;
    font-weight:500 !important; color:#8090aa !important; margin-bottom:-1px !important;
    border-radius:0 !important; letter-spacing:0.01em;
}
.stTabs [aria-selected="true"] { color:#1040a8 !important; border-bottom-color:#1040a8 !important; font-weight:600 !important; }
.stTabs [data-baseweb="tab-panel"] { padding:24px 36px !important; background:#f0f2f5; }

/* ── PANELS ── */
.panel {
    background:#fff; border:1px solid #d4d9e8; border-top:2px solid #1040a8;
    border-radius:0 0 6px 6px; padding:20px 24px 24px; margin-bottom:16px;
    box-shadow:0 1px 4px rgba(0,0,0,0.05);
}
.panel.red    { border-top-color:#c81e1e; }
.panel.amber  { border-top-color:#c27803; }
.panel.green  { border-top-color:#047857; }
.panel.teal   { border-top-color:#0694a2; }
.panel.purple { border-top-color:#6c2bd9; }
.panel.indigo { border-top-color:#4338ca; }
.panel-title  { font-size:13px; font-weight:600; color:#0d1424; margin-bottom:2px; letter-spacing:-0.1px; }
.panel-sub    { font-family:'JetBrains Mono',monospace; font-size:8.5px; letter-spacing:0.12em; text-transform:uppercase; color:#b0bbd4; margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid #eef0f6; }

/* ── SUMMARY ROWS ── */
.sum-row  { display:flex; gap:10px; margin:16px 0 4px; }
.sum-cell {
    flex:1; background:#f7f8fc; border:1px solid #d4d9e8;
    border-left:2px solid #1040a8; padding:12px 16px;
    border-radius:0 4px 4px 0;
}
.sum-cell.green  { border-left-color:#047857; }
.sum-cell.amber  { border-left-color:#c27803; }
.sum-cell.red    { border-left-color:#c81e1e; }
.sum-cell.teal   { border-left-color:#0694a2; }
.sum-cell.purple { border-left-color:#6c2bd9; }
.sum-cell.indigo { border-left-color:#4338ca; }
.sum-cell.gray   { border-left-color:#6b7a99; }
.sum-lbl  { font-family:'JetBrains Mono',monospace; font-size:8.5px; letter-spacing:0.12em; text-transform:uppercase; color:#8090aa; margin-bottom:4px; }
.sum-val  { font-size:17px; font-weight:600; color:#0d1424; letter-spacing:-0.4px; }
.sum-val.neg { color:#c81e1e; }
.sum-note { font-family:'JetBrains Mono',monospace; font-size:8.5px; color:#b0bbd4; margin-top:3px; }

/* ── FPA INSIGHT BOXES ── */
.insight-row { display:flex; gap:10px; margin:12px 0; }
.insight-box {
    flex:1; background:linear-gradient(135deg,#f7f8fc,#eef0f6);
    border:1px solid #d4d9e8; border-radius:4px; padding:12px 16px;
}
.insight-box.warn { background:linear-gradient(135deg,#fffbeb,#fef3c7); border-color:#f59e0b; }
.insight-box.good { background:linear-gradient(135deg,#ecfdf5,#d1fae5); border-color:#059669; }
.insight-box.bad  { background:linear-gradient(135deg,#fff5f5,#fee2e2); border-color:#dc2626; }
.insight-label { font-family:'JetBrains Mono',monospace; font-size:8px; letter-spacing:0.14em; text-transform:uppercase; color:#8090aa; margin-bottom:4px; }
.insight-val   { font-size:18px; font-weight:700; color:#0d1424; letter-spacing:-0.5px; }
.insight-val.red { color:#c81e1e; }
.insight-val.green { color:#047857; }
.insight-note  { font-size:11px; color:#6b7a99; margin-top:3px; }

/* ── WATERFALL LEGEND ── */
.wf-legend { display:flex; gap:16px; margin-bottom:10px; flex-wrap:wrap; }
.wf-leg-item { display:flex; align-items:center; gap:5px; font-family:'JetBrains Mono',monospace; font-size:9px; color:#6b7a99; }
.wf-leg-dot  { width:10px; height:10px; border-radius:2px; }

div[data-testid="metric-container"] { display:none; }
.stExpander { background:#fff !important; border:1px solid #d4d9e8 !important; border-radius:4px !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sb-logo">
      <div class="sb-logo-box">P</div>
      <div>
        <div class="sb-logo-name">P&amp;L Intelligence</div>
        <div class="sb-logo-sub">FP&amp;A · Oil &amp; Gas</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section">Data Ingestion</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(" ", type=["xlsx", "xls", "csv"], label_visibility="collapsed")

    if uploaded:
        res = ingest_file(uploaded)
        if res["status"] == "ok":
            st.success(f"✓ {res['rows']:,} rows · {res['months']} periods · {res['wells']} wells")
            st.rerun()
        elif res["status"] == "duplicate":
            st.info("Already loaded.")
        else:
            st.error(res.get("message", "Unknown error"))

    st.divider()

    _raw = load_all_data()
    if _raw is None or _raw.empty:
        st.warning("No data loaded. Upload a GL export above.")
        st.stop()

    df = _raw.copy()
    for col in ["Well", "Period", "SubAcctNum"]:
        if col not in df.columns:
            df[col] = "Unknown"
    df["Well"]       = df["Well"].fillna("Unknown").astype(str)
    df["SubAcctNum"] = df["SubAcctNum"].fillna("Unknown").astype(str)

    st.markdown('<div class="sb-section">Portfolio Filter</div>', unsafe_allow_html=True)

    valid_mask = (df["Well"].notna() & (df["Well"].str.strip() != "") & (df["Well"].str.strip().str.lower() != "unknown"))
    valid      = df.loc[valid_mask, ["SubAcctNum", "Well"]].drop_duplicates().sort_values(["SubAcctNum", "Well"])
    all_nums   = sorted(valid["SubAcctNum"].unique().tolist()) if not valid.empty else []
    all_descs  = sorted(valid["Well"].unique().tolist())      if not valid.empty else []

    st.markdown('<div class="sb-label">Sub Account</div>', unsafe_allow_html=True)
    sel_nums = st.multiselect("_nums", options=all_nums, default=[], placeholder="All sub accounts…", label_visibility="collapsed")

    avail_descs = sorted(valid.loc[valid["SubAcctNum"].isin(sel_nums), "Well"].unique().tolist()) if sel_nums else all_descs
    st.markdown('<div class="sb-label" style="margin-top:10px">Well / Asset</div>', unsafe_allow_html=True)
    sel_descs = st.multiselect("_descs", options=avail_descs, default=[], placeholder="All wells…", label_visibility="collapsed")

    selected_wells = sel_descs if sel_descs else (avail_descs if sel_nums else [])
    all_months     = sorted([m for m in df["Period"].dropna().astype(str).unique().tolist() if m != ""])

    st.markdown('<div class="sb-label" style="margin-top:10px">Period Range</div>', unsafe_allow_html=True)
    if len(all_months) >= 2:
        month_range = st.select_slider("_period", options=all_months, value=(all_months[0], all_months[-1]), label_visibility="collapsed")
    elif len(all_months) == 1:
        month_range = (all_months[0], all_months[0])
    else:
        month_range = (None, None)

    st.divider()
    st.markdown(f'<div class="sb-stat">{df["Period"].nunique()} periods · {df["Well"].nunique()} wells loaded</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FILTER
# ═══════════════════════════════════════════════════════════════════════════════
dff = df.copy()
if selected_wells:
    dff = dff[dff["Well"].isin(selected_wells)]
if month_range[0] and month_range[1]:
    dff = dff[(dff["Period"] >= month_range[0]) & (dff["Period"] <= month_range[1])]

summary     = get_summary(dff)
exp_summary = get_expense_summary(dff)

# ═══════════════════════════════════════════════════════════════════════════════
# STYLE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
PF   = "Inter, sans-serif"
MF   = "JetBrains Mono, monospace"
GRID = "#eef0f6"
BG   = "#ffffff"
C = {
    "oil":       "#1040a8", "gas":       "#047857", "plant":     "#c27803",
    "ded":       "#c81e1e", "net":       "#4c1d95", "dshade":    "rgba(200,30,30,0.10)",
    "loe":       "#1040a8", "leasehold": "#c27803",
    "capital":   "#4c1d95", "workover":  "#c81e1e", "total_exp": "#374151",
    "ebitda":    "#047857", "margin":    "#0694a2",
}
BUCKET_COLORS = {
    "LOE":       C["loe"],
    "Leasehold": C["leasehold"],
    "Capital":   C["capital"],
    "Workover":  C["workover"],
}

def fmt(v, decimals=1):
    if abs(v) >= 1_000_000: return f"${v/1e6:.{decimals}f}M"
    if abs(v) >= 1_000:     return f"${v/1e3:.{decimals}f}K"
    return f"${v:,.0f}"

def fmt_pct(v): return f"{v:.1f}%"

def delta_html(cur, prev, lbl=""):
    if prev and prev != 0:
        d  = (cur - prev) / abs(prev) * 100
        cl = "pos" if d >= 0 else "neg"
        arrow = "▲" if d >= 0 else "▼"
        return f'<span class="kpi-delta {cl}">{arrow} {abs(d):.1f}% vs {lbl}</span>'
    return '<span class="kpi-delta neu">—</span>'

def bl(**kw):
    base = {
        "font": dict(family=PF, size=11, color="#374151"),
        "paper_bgcolor": BG, "plot_bgcolor": BG,
        "margin": dict(t=16, b=40, l=12, r=12),
        "hovermode": "x unified",
        "hoverlabel": dict(bgcolor="#08111f", font_color="#dce8f8", font_family=MF, font_size=11,
                           bordercolor="#1040a8"),
        "legend": dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                       font=dict(family=MF, size=9), bgcolor="rgba(0,0,0,0)", borderwidth=0),
    }
    base.update(kw)
    return base

def sax(fig):
    tf = dict(family=MF, size=9, color="#b0bbd4")
    fig.update_xaxes(showgrid=False, showline=True, linecolor="#d4d9e8", tickfont=tf, ticks="outside", ticklen=3)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor="#d4d9e8",
                     zerolinewidth=1, tickfont=tf)
    return fig

# ── Period/metric helpers ──────────────────────────────────────────────────────
months_sorted = sorted(dff["Period"].dropna().astype(str).unique().tolist())
last_m = months_sorted[-1] if months_sorted else None
prev_m = months_sorted[-2] if len(months_sorted) >= 2 else None
n_periods = len(months_sorted)

last_gross = summary.loc[summary["Period"] == last_m, "Gross_Revenue"].sum()    if (last_m and not summary.empty) else 0
prev_gross = summary.loc[summary["Period"] == prev_m, "Gross_Revenue"].sum()    if (prev_m and not summary.empty) else 0
last_net   = summary.loc[summary["Period"] == last_m, "Net_Revenue"].sum()      if (last_m and not summary.empty) else 0
prev_net   = summary.loc[summary["Period"] == prev_m, "Net_Revenue"].sum()      if (prev_m and not summary.empty) else 0
last_deds  = summary.loc[summary["Period"] == last_m, "Total_Deductions"].sum() if (last_m and not summary.empty) else 0
ded_rate   = last_deds / last_gross * 100 if last_gross else 0
total_gross = summary["Gross_Revenue"].sum() if not summary.empty else 0
total_net   = summary["Net_Revenue"].sum()   if not summary.empty else 0

def _exp_bucket_sum(es, bucket, period=None):
    if es is None or es.empty: return 0
    m = es["Bucket"] == bucket
    if period: m = m & (es["Period"] == period)
    return es.loc[m, "Amount"].sum()

last_loe       = _exp_bucket_sum(exp_summary, "LOE",       last_m)
last_workover  = _exp_bucket_sum(exp_summary, "Workover",  last_m)
last_capital   = _exp_bucket_sum(exp_summary, "Capital",   last_m)
last_leasehold = _exp_bucket_sum(exp_summary, "Leasehold", last_m)
last_opex      = last_loe + last_workover
last_exp       = last_opex + last_capital + last_leasehold

cum_loe       = _exp_bucket_sum(exp_summary, "LOE")
cum_workover  = _exp_bucket_sum(exp_summary, "Workover")
cum_capital   = _exp_bucket_sum(exp_summary, "Capital")
cum_leasehold = _exp_bucket_sum(exp_summary, "Leasehold")
cum_opex      = cum_loe + cum_workover
total_exp     = cum_opex + cum_capital + cum_leasehold

last_net_less_opex    = last_net - last_opex
last_net_less_capital = last_net - last_capital
last_net_income       = last_net - last_exp
last_ebitda           = last_net - last_opex           # proxy: net rev less field opex
last_margin_pct       = last_net_income / last_gross * 100 if last_gross else 0

cum_net_less_opex = total_net - cum_opex
cum_net_income    = total_net - total_exp
cum_margin_pct    = cum_net_income / total_gross * 100 if total_gross else 0

# prev month for MoM on EBITDA
prev_loe      = _exp_bucket_sum(exp_summary, "LOE",      prev_m)
prev_workover = _exp_bucket_sum(exp_summary, "Workover", prev_m)
prev_opex     = prev_loe + prev_workover
prev_ebitda   = prev_net - prev_opex

n_wells = df["Well"].nunique()
wlbl = f"{len(selected_wells)} of {n_wells} wells" if selected_wells else f"All {dff['Well'].nunique()} wells"
plbl = f"{month_range[0]} – {month_range[1]}" if month_range and month_range[0] != month_range[1] else (month_range[0] if month_range else "")

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="ent-header">
  <div>
    <div class="ent-breadcrumb">FP&amp;A Console &rsaquo; Integrated P&amp;L &rsaquo; Oil &amp; Gas Operations</div>
    <div class="ent-title">Integrated P&amp;L &nbsp;<strong>{wlbl}</strong></div>
  </div>
  <div class="ent-header-right">
    <div class="ent-badge">Analysis Period &nbsp;<strong>{plbl}</strong></div>
    <div class="ent-badge">Latest Close &nbsp;<strong>{last_m or "—"}</strong></div>
    <div class="ent-badge live">● &nbsp;<strong>GL-Linked</strong></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# KPI STRIP  — 8 cards, finance-first framing
# ═══════════════════════════════════════════════════════════════════════════════
ni_color  = "c-green" if last_net_income    >= 0 else "c-red"
nlo_color = "c-green" if last_net_less_opex >= 0 else "c-red"
eb_color  = "c-green" if last_ebitda        >= 0 else "c-red"
mg_color  = "c-green" if last_margin_pct    >= 0 else "c-red"

ni_val_cls  = "" if last_net_income >= 0 else " neg"
eb_val_cls  = "" if last_ebitda     >= 0 else " neg"
mg_val_cls  = "" if last_margin_pct >= 0 else " neg"

st.markdown(f"""
<div class="kpi-strip">
  <div class="kpi-item c-blue">
    <div class="kpi-lbl">Gross Revenue ({last_m or "—"})</div>
    <div class="kpi-val">{fmt(last_gross)}</div>
    {delta_html(last_gross, prev_gross, prev_m or "")}
    <div class="kpi-sub">Before deductions</div>
  </div>
  <div class="kpi-item c-green">
    <div class="kpi-lbl">Net Revenue ({last_m or "—"})</div>
    <div class="kpi-val">{fmt(last_net)}</div>
    {delta_html(last_net, prev_net, prev_m or "")}
    <div class="kpi-sub">After taxes &amp; fees</div>
  </div>
  <div class="kpi-item {eb_color}">
    <div class="kpi-lbl">Field EBITDA ({last_m or "—"})</div>
    <div class="kpi-val{eb_val_cls}">{fmt(last_ebitda)}</div>
    {delta_html(last_ebitda, prev_ebitda, prev_m or "")}
    <div class="kpi-sub">Net rev less LOE + WO</div>
  </div>
  <div class="kpi-item {ni_color}">
    <div class="kpi-lbl">Net Income ({last_m or "—"})</div>
    <div class="kpi-val{ni_val_cls}">{fmt(last_net_income)}</div>
    <div class="kpi-sub">All costs: {fmt(last_exp)}</div>
  </div>
  <div class="kpi-item {mg_color}">
    <div class="kpi-lbl">Net Margin ({last_m or "—"})</div>
    <div class="kpi-val{mg_val_cls}">{last_margin_pct:.1f}%</div>
    <div class="kpi-sub">Cum: {cum_margin_pct:.1f}% over {n_periods}mo</div>
  </div>
  <div class="kpi-item c-amber">
    <div class="kpi-lbl">Deduction Rate ({last_m or "—"})</div>
    <div class="kpi-val">{ded_rate:.1f}%</div>
    <div class="kpi-sub">Revenue haircut</div>
  </div>
  <div class="kpi-item c-purple">
    <div class="kpi-lbl">Cum. Field EBITDA</div>
    <div class="kpi-val">{fmt(cum_net_less_opex)}</div>
    <div class="kpi-sub">{n_periods} period(s)</div>
  </div>
  <div class="kpi-item c-teal">
    <div class="kpi-lbl">Cum. Net Income</div>
    <div class="kpi-val">{fmt(cum_net_income)}</div>
    <div class="kpi-sub">{n_periods} period(s)</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# BUILD UNIFIED P&L FRAME (used across multiple tabs)
# ═══════════════════════════════════════════════════════════════════════════════
rev_by_period = (
    summary.groupby("Period")
    .agg(Gross=("Gross_Revenue","sum"), Net_Rev=("Net_Revenue","sum"),
         Deductions=("Total_Deductions","sum"))
    .reset_index()
) if not summary.empty else pd.DataFrame(columns=["Period","Gross","Net_Rev","Deductions"])

exp_pivot = (
    exp_summary.pivot_table(index="Period", columns="Bucket", values="Amount", aggfunc="sum", fill_value=0)
    .reset_index()
) if not exp_summary.empty else pd.DataFrame(columns=["Period"])

for bk in ["LOE","Leasehold","Capital","Workover"]:
    if bk not in exp_pivot.columns:
        exp_pivot[bk] = 0.0

all_periods = sorted(set(
    list(rev_by_period["Period"].tolist() if not rev_by_period.empty else []) +
    list(exp_pivot["Period"].tolist()     if not exp_pivot.empty     else [])
))

pl = pd.DataFrame({"Period": all_periods})
pl = pl.merge(rev_by_period, on="Period", how="left").fillna(0)
pl = pl.merge(exp_pivot[["Period","LOE","Leasehold","Capital","Workover"]], on="Period", how="left").fillna(0)
pl["OpEx"]           = pl["LOE"] + pl["Workover"]
pl["Total_Exp"]      = pl["LOE"] + pl["Workover"] + pl["Capital"] + pl["Leasehold"]
pl["Field_EBITDA"]   = pl["Net_Rev"] - pl["OpEx"]
pl["Net_Less_OpEx"]  = pl["Net_Rev"] - pl["OpEx"]
pl["Net_Less_Cap"]   = pl["Net_Rev"] - pl["Capital"]
pl["Net_Income"]     = pl["Net_Rev"] - pl["Total_Exp"]
pl["EBITDA_Margin"]  = (pl["Field_EBITDA"] / pl["Gross"].replace(0, float("nan")) * 100).fillna(0)
pl["Net_Margin"]     = (pl["Net_Income"]   / pl["Gross"].replace(0, float("nan")) * 100).fillna(0)
pl["Ded_Rate"]       = (pl["Deductions"]   / pl["Gross"].replace(0, float("nan")) * 100).fillna(0)
pl["MoM_Net"]        = pl["Net_Income"].pct_change() * 100
pl["Cum_Net_Income"] = pl["Net_Income"].cumsum()
pl["Cum_EBITDA"]     = pl["Field_EBITDA"].cumsum()
pl = pl.sort_values("Period").reset_index(drop=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE TABS
# ═══════════════════════════════════════════════════════════════════════════════
rev_tab, exp_tab, pl_tab = st.tabs(["Revenue & Production", "Cost Structure", "P&L / FP&A"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REVENUE MODULE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with rev_tab:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Revenue Trend", "Commodity Mix", "Deduction Bridge", "Well Rankings", "Volumes & Pricing",
    ])

    with tab1:
        trend = (
            summary.groupby("Period")
            .agg(Oil=("Oil_Gross","sum"), Gas=("Gas_Gross","sum"), Plant=("Plant_Gross","sum"),
                 Deductions=("Total_Deductions","sum"), Net=("Net_Revenue","sum"))
            .reset_index().sort_values("Period")
        )
        # MoM net change
        trend["Net_MoM"] = trend["Net"].pct_change() * 100

        st.markdown('<div class="panel"><div class="panel-title">Revenue Trend — Gross to Net Bridge</div><div class="panel-sub">Monthly gross by commodity · deductions · net revenue overlay</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_bar(x=trend["Period"], y=trend["Oil"],   name="Oil",       marker_color=C["oil"],   marker_line_width=0)
        fig.add_bar(x=trend["Period"], y=trend["Gas"],   name="Gas",       marker_color=C["gas"],   marker_line_width=0)
        fig.add_bar(x=trend["Period"], y=trend["Plant"], name="Plant/NGL", marker_color=C["plant"], marker_line_width=0)
        fig.add_bar(x=trend["Period"], y=(-trend["Deductions"]).tolist(), name="Deductions",
                    marker_color=C["dshade"], marker_line_width=0)
        fig.add_scatter(x=trend["Period"], y=trend["Net"], name="Net Revenue",
                        line=dict(color=C["net"], width=2.5), mode="lines+markers",
                        marker=dict(size=6, color=C["net"], line=dict(color="#fff", width=2)))
        fig.update_layout(**bl(barmode="relative", height=380, yaxis=dict(tickprefix="$", tickformat=",.0f")))
        sax(fig)
        st.plotly_chart(fig, use_container_width=True, key="rev_trend")
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Data table"):
            td = trend.copy()
            for c in ["Oil","Gas","Plant","Deductions","Net"]:
                td[c] = td[c].apply(lambda v: f"${v:,.0f}")
            td["Net MoM%"] = trend["Net_MoM"].apply(lambda v: f"{v:+.1f}%" if pd.notna(v) else "—")
            st.dataframe(td[["Period","Oil","Gas","Plant","Deductions","Net","Net MoM%"]], use_container_width=True, hide_index=True)

    with tab2:
        mix   = (summary.groupby("Period").agg(Oil=("Oil_Gross","sum"), Gas=("Gas_Gross","sum"), Plant=("Plant_Gross","sum"))
                 .reset_index().sort_values("Period"))
        tot_o = summary["Oil_Gross"].sum()   if not summary.empty else 0
        tot_g = summary["Gas_Gross"].sum()   if not summary.empty else 0
        tot_p = summary["Plant_Gross"].sum() if not summary.empty else 0
        L, R  = st.columns([3, 2], gap="medium")
        with L:
            st.markdown('<div class="panel"><div class="panel-title">Monthly Revenue Stack</div><div class="panel-sub">Gross by commodity per period</div>', unsafe_allow_html=True)
            f2 = go.Figure()
            f2.add_bar(x=mix["Period"], y=mix["Oil"],   name="Oil",       marker_color=C["oil"],   marker_line_width=0)
            f2.add_bar(x=mix["Period"], y=mix["Gas"],   name="Gas",       marker_color=C["gas"],   marker_line_width=0)
            f2.add_bar(x=mix["Period"], y=mix["Plant"], name="Plant/NGL", marker_color=C["plant"], marker_line_width=0)
            f2.update_layout(**bl(barmode="stack", height=340, yaxis=dict(tickprefix="$", tickformat=",.0f")))
            sax(f2)
            st.plotly_chart(f2, use_container_width=True, key="mix_stack")
            st.markdown("</div>", unsafe_allow_html=True)
        with R:
            st.markdown('<div class="panel"><div class="panel-title">Cumulative Mix</div><div class="panel-sub">All selected periods</div>', unsafe_allow_html=True)
            f3 = go.Figure(go.Pie(
                labels=["Oil","Gas","Plant/NGL"], values=[tot_o, tot_g, tot_p], hole=0.64,
                marker=dict(colors=[C["oil"], C["gas"], C["plant"]], line=dict(color="#fff", width=3)),
                textinfo="label+percent", textfont=dict(family=MF, size=10),
                hovertemplate="%{label}: $%{value:,.0f}<extra></extra>", insidetextorientation="radial",
            ))
            f3.update_layout(height=340, showlegend=False, paper_bgcolor=BG, margin=dict(t=10,b=10,l=20,r=20),
                annotations=[dict(text=f"<b>{fmt(tot_o+tot_g+tot_p)}</b>", x=0.5, y=0.5, showarrow=False,
                                  font=dict(family=PF, size=17, color="#0d1424"))])
            st.plotly_chart(f3, use_container_width=True, key="mix_pie")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        sc, cc = st.columns([1, 4], gap="medium")
        with sc:
            st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
            bp_period = st.selectbox("Period", months_sorted[::-1] if months_sorted else ["—"], index=0, key="bp_sel")
        bp    = summary[summary["Period"] == bp_period].sum(numeric_only=True) if not summary.empty else pd.Series(dtype=float)
        gross = bp.get("Gross_Revenue", 0.0)
        net   = bp.get("Net_Revenue", 0.0)
        di    = [(l,v,c) for l,v,c in [
            ("Oil Prod. Tax",    bp.get("Oil_Tax",      0.0), "#991b1b"),
            ("Gas Prod. Tax",    bp.get("Gas_Tax",      0.0), "#991b1b"),
            ("Plant Prod. Tax",  bp.get("Plant_Tax",    0.0), "#991b1b"),
            ("Compression",      bp.get("Gas_Comp",     0.0), "#92400e"),
            ("Low Vol. Fee",     bp.get("Gas_LowVol",   0.0), "#92400e"),
            ("Plant Deduction",  bp.get("Plant_Deduct", 0.0), "#92400e"),
            ("Rejected Load Fee",bp.get("Rejected_Fee", 0.0), "#b45309"),
        ] if v > 0.01]
        labels = ["Gross Revenue"] + [i[0] for i in di] + ["Net Revenue"]
        bclrs  = ["#1040a8"] + [i[2] for i in di] + ["#4c1d95"]
        bases, bvals = [], []
        running = gross
        for idx in range(len(labels)):
            if idx == 0:               bases.append(0); bvals.append(gross)
            elif idx == len(labels)-1: bases.append(0); bvals.append(net)
            else:
                dv = di[idx-1][1]; bases.append(running - dv); bvals.append(dv); running -= dv
        dvals = [gross] + [-i[1] for i in di] + [net]
        with cc:
            st.markdown('<div class="panel"><div class="panel-title">Revenue Deduction Waterfall</div><div class="panel-sub">Gross → production taxes → gathering/transport fees → net</div>', unsafe_allow_html=True)
            f4 = go.Figure()
            f4.add_bar(x=labels, y=bases, marker_color="rgba(0,0,0,0)", showlegend=False, hoverinfo="skip")
            f4.add_bar(x=labels, y=bvals, marker_color=bclrs, marker_line_width=0,
                       text=[fmt(v) for v in dvals], textposition="outside",
                       textfont=dict(family=MF, size=10, color="#374151"), showlegend=False,
                       hovertemplate="%{x}: $%{y:,.0f}<extra></extra>")
            f4.update_layout(**bl(barmode="stack", height=400, yaxis=dict(tickprefix="$", tickformat=",.0f")))
            sax(f4)
            st.plotly_chart(f4, use_container_width=True, key="ded_waterfall")
            st.markdown("</div>", unsafe_allow_html=True)
        ded_total = gross - net
        st.markdown(f"""
        <div class="sum-row">
          <div class="sum-cell"><div class="sum-lbl">Gross Revenue</div><div class="sum-val">{fmt(gross)}</div><div class="sum-note">Pre-deduction</div></div>
          <div class="sum-cell amber"><div class="sum-lbl">Total Deductions</div><div class="sum-val">{fmt(ded_total)}</div><div class="sum-note">{f"{ded_total/gross*100:.1f}% of gross" if gross else "—"}</div></div>
          <div class="sum-cell green"><div class="sum-lbl">Net Revenue</div><div class="sum-val">{fmt(net)}</div><div class="sum-note">{f"{net/gross*100:.1f}% retained" if gross else "—"}</div></div>
        </div>""", unsafe_allow_html=True)

    with tab4:
        ctrl, cc = st.columns([1, 4], gap="medium")
        with ctrl:
            st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
            top_n = st.slider("Top N wells", 5, 50, 15, key="rev_topn")
            rp    = st.selectbox("Period", ["All periods"] + (months_sorted[::-1] if months_sorted else []), key="rev_rp")
            rm    = st.radio("Metric", ["Gross Revenue","Net Revenue"], key="rev_rm")
        rdf = dff[dff["Period"] == rp].copy() if rp != "All periods" else dff.copy()
        mc  = "Gross_Revenue" if rm == "Gross Revenue" else "Net_Revenue"
        ws  = get_summary(rdf)
        wr  = ws.groupby("Well")[mc].sum().sort_values(ascending=False).head(top_n).reset_index() if not ws.empty else pd.DataFrame(columns=["Well", mc])
        with cc:
            st.markdown(f'<div class="panel"><div class="panel-title">Top {top_n} Wells — {rm}</div><div class="panel-sub">{rp}</div>', unsafe_allow_html=True)
            f5 = go.Figure(go.Bar(
                x=wr[mc] if not wr.empty else [], y=wr["Well"] if not wr.empty else [],
                orientation="h",
                marker=dict(
                    color=wr[mc] if not wr.empty else [],
                    colorscale=[[0,"#93c5fd"],[0.5,"#1a56db"],[1,"#1040a8"]],
                    showscale=False,
                ),
                marker_line_width=0,
                text=wr[mc].apply(fmt) if not wr.empty else [],
                textposition="outside", textfont=dict(family=MF, size=10),
                hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
            ))
            f5.update_layout(**bl(height=max(380, top_n*30), xaxis=dict(tickprefix="$", tickformat=",.0f"),
                                  yaxis=dict(autorange="reversed"), margin=dict(t=16,b=40,l=230,r=90)))
            sax(f5)
            st.plotly_chart(f5, use_container_width=True, key="well_rank_rev")
            st.markdown("</div>", unsafe_allow_html=True)
        with st.expander("Full well-by-period detail"):
            ws2 = get_summary(dff)
            if ws2.empty:
                st.dataframe(pd.DataFrame(), use_container_width=True, hide_index=True)
            else:
                tbl = ws2.pivot_table(index="Well", columns="Period", values=mc, aggfunc="sum", fill_value=0).reset_index()
                tbl["Total"] = tbl.iloc[:,1:].sum(axis=1)
                tbl = tbl.sort_values("Total", ascending=False)
                for col in tbl.columns[1:]:
                    tbl[col] = tbl[col].apply(lambda v: f"${v:,.0f}" if v != 0 else "—")
                st.dataframe(tbl, use_container_width=True, hide_index=True)

    with tab5:
        vol = (summary.groupby("Period")
               .agg(Oil_BBL=("Oil_BBL","sum"), Gas_MCF=("Gas_MCF","sum"), Plant_GAL=("Plant_GAL","sum"))
               .reset_index().sort_values("Period"))
        rp2 = (summary.groupby("Period").agg(Oil_Rev=("Oil_Gross","sum"), Oil_BBL=("Oil_BBL","sum"),
                Gas_Rev=("Gas_Gross","sum"), Gas_MCF=("Gas_MCF","sum")).reset_index())
        rp2["Oil_Price"] = (rp2["Oil_Rev"] / rp2["Oil_BBL"].replace(0, float("nan")))
        rp2["Gas_Price"] = (rp2["Gas_Rev"] / rp2["Gas_MCF"].replace(0, float("nan")))

        L_v, R_v = st.columns(2, gap="medium")
        with L_v:
            st.markdown('<div class="panel"><div class="panel-title">Production Volumes</div><div class="panel-sub">Oil (BBL) · Gas (MCF) · Plant/NGL (GAL — right axis)</div>', unsafe_allow_html=True)
            f6 = make_subplots(specs=[[{"secondary_y": True}]])
            f6.add_bar(x=vol["Period"], y=vol["Oil_BBL"], name="Oil (BBL)", marker_color=C["oil"],  marker_line_width=0, secondary_y=False)
            f6.add_bar(x=vol["Period"], y=vol["Gas_MCF"], name="Gas (MCF)", marker_color=C["gas"],  marker_line_width=0, secondary_y=False)
            f6.add_scatter(x=vol["Period"], y=vol["Plant_GAL"], name="Plant (GAL)",
                           line=dict(color=C["plant"], width=2.5), mode="lines+markers",
                           marker=dict(size=6, color=C["plant"], line=dict(color="#fff", width=2)), secondary_y=True)
            f6.update_layout(**bl(barmode="group", height=320))
            tf2 = dict(family=MF, size=9, color="#b0bbd4")
            f6.update_xaxes(showgrid=False, showline=True, linecolor="#d4d9e8", tickfont=tf2)
            f6.update_yaxes(title_text="BBL / MCF", showgrid=True, gridcolor=GRID, tickfont=tf2, secondary_y=False)
            f6.update_yaxes(title_text="GAL", showgrid=False, tickfont=tf2, secondary_y=True)
            st.plotly_chart(f6, use_container_width=True, key="volumes")
            st.markdown("</div>", unsafe_allow_html=True)
        with R_v:
            st.markdown('<div class="panel"><div class="panel-title">Implied Realized Prices</div><div class="panel-sub">Oil ($/BBL) · Gas ($/MCF) — price realization trend</div>', unsafe_allow_html=True)
            f_pr = make_subplots(specs=[[{"secondary_y": True}]])
            f_pr.add_scatter(x=rp2["Period"], y=rp2["Oil_Price"], name="Oil $/BBL",
                             line=dict(color=C["oil"], width=2.5), mode="lines+markers",
                             marker=dict(size=6, color=C["oil"], line=dict(color="#fff", width=2)),
                             secondary_y=False)
            f_pr.add_scatter(x=rp2["Period"], y=rp2["Gas_Price"], name="Gas $/MCF",
                             line=dict(color=C["gas"], width=2.5), mode="lines+markers",
                             marker=dict(size=6, color=C["gas"], line=dict(color="#fff", width=2)),
                             secondary_y=True)
            f_pr.update_layout(**bl(height=320))
            tf3 = dict(family=MF, size=9, color="#b0bbd4")
            f_pr.update_xaxes(showgrid=False, showline=True, linecolor="#d4d9e8", tickfont=tf3)
            f_pr.update_yaxes(title_text="Oil $/BBL", tickprefix="$", tickformat=",.2f", showgrid=True, gridcolor=GRID, tickfont=tf3, secondary_y=False)
            f_pr.update_yaxes(title_text="Gas $/MCF", tickprefix="$", tickformat=",.3f", showgrid=False, tickfont=tf3, secondary_y=True)
            st.plotly_chart(f_pr, use_container_width=True, key="realized_prices")
            st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# EXPENSE MODULE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with exp_tab:
    etab1, etab2, etab3, etab4 = st.tabs([
        "Cost Trend", "Bucket Breakdown", "Well Deep-Dive", "Well Rankings",
    ])

    if exp_summary.empty:
        for t in [etab1, etab2, etab3, etab4]:
            with t:
                st.info("No expense data found in the loaded GL export.")
    else:
        exp_trend = (exp_summary.groupby(["Period","Bucket"])["Amount"]
                     .sum().reset_index().sort_values("Period"))
        exp_period = (exp_trend.pivot_table(index="Period", columns="Bucket", values="Amount", fill_value=0)
                      .reset_index().sort_values("Period"))
        for bk in ["LOE","Leasehold","Capital","Workover"]:
            if bk not in exp_period.columns:
                exp_period[bk] = 0.0
        exp_period["Total"] = exp_period[["LOE","Leasehold","Capital","Workover"]].sum(axis=1)

        with etab1:
            # LOE per BOE if volume data available
            vol_tot = summary.groupby("Period").agg(Oil_BBL=("Oil_BBL","sum"), Gas_MCF=("Gas_MCF","sum")).reset_index()
            vol_tot["BOE"] = vol_tot["Oil_BBL"] + vol_tot["Gas_MCF"] / 6  # 6 MCF ~ 1 BOE
            exp_loe_only = exp_period[["Period","LOE"]].copy()
            loe_boe = exp_loe_only.merge(vol_tot[["Period","BOE"]], on="Period", how="left")
            loe_boe["LOE_BOE"] = loe_boe["LOE"] / loe_boe["BOE"].replace(0, float("nan"))

            st.markdown('<div class="panel red"><div class="panel-title">Cost Structure Trend</div><div class="panel-sub">Monthly LOE · Leasehold · Capital · Workover · total overlay</div>', unsafe_allow_html=True)
            fe1 = go.Figure()
            for bk in ["LOE","Leasehold","Capital","Workover"]:
                fe1.add_bar(x=exp_period["Period"], y=exp_period[bk], name=bk,
                            marker_color=BUCKET_COLORS[bk], marker_line_width=0)
            fe1.add_scatter(x=exp_period["Period"], y=exp_period["Total"], name="Total Costs",
                            line=dict(color="#0d1424", width=2.5), mode="lines+markers",
                            marker=dict(size=6, color="#0d1424", line=dict(color="#fff", width=2)))
            fe1.update_layout(**bl(barmode="stack", height=360, yaxis=dict(tickprefix="$", tickformat=",.0f")))
            sax(fe1)
            st.plotly_chart(fe1, use_container_width=True, key="exp_trend")
            st.markdown("</div>", unsafe_allow_html=True)

            # LOE/BOE chart
            if loe_boe["LOE_BOE"].notna().any():
                st.markdown('<div class="panel indigo"><div class="panel-title">LOE per BOE — Unit Cost Efficiency</div><div class="panel-sub">Field operating cost per barrel of oil equivalent · key FP&A efficiency metric</div>', unsafe_allow_html=True)
                f_loe_boe = go.Figure()
                f_loe_boe.add_scatter(x=loe_boe["Period"], y=loe_boe["LOE_BOE"], name="LOE/BOE",
                                      fill="tozeroy", fillcolor="rgba(16,64,168,0.07)",
                                      line=dict(color=C["oil"], width=2.5), mode="lines+markers",
                                      marker=dict(size=6, color=C["oil"], line=dict(color="#fff", width=2)),
                                      hovertemplate="%{x}: $%{y:.2f}/BOE<extra></extra>")
                f_loe_boe.update_layout(**bl(height=240, yaxis=dict(tickprefix="$", tickformat=",.2f", title="$/BOE")))
                sax(f_loe_boe)
                st.plotly_chart(f_loe_boe, use_container_width=True, key="loe_boe")
                st.markdown("</div>", unsafe_allow_html=True)

            loe_tot = exp_period["LOE"].sum()
            lh_tot  = exp_period["Leasehold"].sum()
            cap_tot = exp_period["Capital"].sum()
            wo_tot  = exp_period["Workover"].sum()
            all_tot = loe_tot + lh_tot + cap_tot + wo_tot
            st.markdown(f"""
            <div class="sum-row">
              <div class="sum-cell"><div class="sum-lbl">LOE (9000–9099)</div><div class="sum-val">{fmt(loe_tot)}</div><div class="sum-note">{f"{loe_tot/all_tot*100:.1f}% of total" if all_tot else "—"}</div></div>
              <div class="sum-cell amber"><div class="sum-lbl">Leasehold (9100–9199)</div><div class="sum-val">{fmt(lh_tot)}</div><div class="sum-note">{f"{lh_tot/all_tot*100:.1f}% of total" if all_tot else "—"}</div></div>
              <div class="sum-cell purple"><div class="sum-lbl">Capital (9200–9399)</div><div class="sum-val">{fmt(cap_tot)}</div><div class="sum-note">{f"{cap_tot/all_tot*100:.1f}% of total" if all_tot else "—"}</div></div>
              <div class="sum-cell red"><div class="sum-lbl">Workover (9500–9598)</div><div class="sum-val">{fmt(wo_tot)}</div><div class="sum-note">{f"{wo_tot/all_tot*100:.1f}% of total" if all_tot else "—"}</div></div>
              <div class="sum-cell teal"><div class="sum-lbl">Grand Total</div><div class="sum-val">{fmt(all_tot)}</div><div class="sum-note">{n_periods} period(s)</div></div>
            </div>""", unsafe_allow_html=True)

            with st.expander("Period data table"):
                disp = exp_period.copy()
                for col in ["LOE","Leasehold","Capital","Workover","Total"]:
                    disp[col] = disp[col].apply(lambda v: f"${v:,.0f}")
                st.dataframe(disp, use_container_width=True, hide_index=True)

        with etab2:
            ctrl2, body2 = st.columns([1, 4], gap="medium")
            with ctrl2:
                st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
                e2_period = st.selectbox("Period", ["All periods"] + (months_sorted[::-1] if months_sorted else []), key="e2p")
                e2_bucket = st.selectbox("Bucket", ["All buckets","LOE","Leasehold","Capital","Workover"], key="e2b")

            e2_df = exp_summary.copy()
            if e2_period != "All periods": e2_df = e2_df[e2_df["Period"] == e2_period]
            if e2_bucket != "All buckets": e2_df = e2_df[e2_df["Bucket"] == e2_bucket]

            e2_raw = dff[dff["Bucket"] != "Revenue"].copy()
            if e2_period != "All periods": e2_raw = e2_raw[e2_raw["Period"] == e2_period]
            if e2_bucket != "All buckets": e2_raw = e2_raw[e2_raw["Bucket"] == e2_bucket]

            acct_roll = (e2_raw.groupby(["Account","AccountDesc","Bucket"])["AmountAdj"]
                         .sum().reset_index().sort_values("AmountAdj", ascending=False))
            acct_roll = acct_roll[acct_roll["AmountAdj"].abs() > 0.01]

            with body2:
                L2, R2 = st.columns(2, gap="medium")
                with L2:
                    bucket_tots = e2_df.groupby("Bucket")["Amount"].sum().reset_index()
                    st.markdown('<div class="panel red"><div class="panel-title">Spend by Bucket</div><div class="panel-sub">Selected period / filter</div>', unsafe_allow_html=True)
                    fp1 = go.Figure(go.Pie(
                        labels=bucket_tots["Bucket"], values=bucket_tots["Amount"], hole=0.56,
                        marker=dict(colors=[BUCKET_COLORS.get(b,"#888") for b in bucket_tots["Bucket"]],
                                    line=dict(color="#fff", width=2.5)),
                        textinfo="label+percent", textfont=dict(family=MF, size=10),
                        hovertemplate="%{label}: $%{value:,.0f}<extra></extra>",
                    ))
                    tot_sel = bucket_tots["Amount"].sum()
                    fp1.update_layout(height=300, showlegend=False, paper_bgcolor=BG, margin=dict(t=8,b=8,l=16,r=16),
                        annotations=[dict(text=f"<b>{fmt(tot_sel)}</b>", x=0.5, y=0.5, showarrow=False,
                                          font=dict(family=PF, size=16, color="#0d1424"))])
                    st.plotly_chart(fp1, use_container_width=True, key="exp_bucket_pie")
                    st.markdown("</div>", unsafe_allow_html=True)
                with R2:
                    st.markdown('<div class="panel red"><div class="panel-title">Top GL Accounts</div><div class="panel-sub">By total spend</div>', unsafe_allow_html=True)
                    top_accts   = acct_roll.head(15)
                    acct_labels = top_accts.apply(lambda r: f"{int(r['Account'])} – {r['AccountDesc']}" if r['AccountDesc'] else str(int(r['Account'])), axis=1)
                    fp2 = go.Figure(go.Bar(
                        x=top_accts["AmountAdj"], y=acct_labels, orientation="h",
                        marker_color=[BUCKET_COLORS.get(b, "#888") for b in top_accts["Bucket"]],
                        marker_line_width=0,
                        text=top_accts["AmountAdj"].apply(fmt), textposition="outside",
                        textfont=dict(family=MF, size=10),
                        hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
                    ))
                    fp2.update_layout(**bl(height=300, xaxis=dict(tickprefix="$", tickformat=",.0f"),
                                          yaxis=dict(autorange="reversed"), margin=dict(t=8,b=32,l=200,r=80)))
                    sax(fp2)
                    st.plotly_chart(fp2, use_container_width=True, key="exp_acct_bar")
                    st.markdown("</div>", unsafe_allow_html=True)
                with st.expander("Full GL account detail"):
                    disp2 = acct_roll.copy()
                    disp2["Amount"] = disp2["AmountAdj"].apply(lambda v: f"${v:,.0f}")
                    disp2 = disp2[["Bucket","Account","AccountDesc","Amount"]].rename(columns={"AccountDesc":"Description"})
                    st.dataframe(disp2, use_container_width=True, hide_index=True)

        with etab3:
            all_exp_wells = sorted(exp_summary["Well"].unique().tolist())
            ctrl3, body3  = st.columns([1, 4], gap="medium")
            with ctrl3:
                st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
                sel_well  = st.selectbox("Well", all_exp_wells, key="e3w")
                e3_period = st.selectbox("Period", ["All periods"] + (months_sorted[::-1] if months_sorted else []), key="e3p")

            well_exp = dff[(dff["Bucket"] != "Revenue") & (dff["Well"] == sel_well)].copy()
            if e3_period != "All periods":
                well_exp = well_exp[well_exp["Period"] == e3_period]

            with body3:
                if well_exp.empty:
                    st.info(f"No expense data for **{sel_well}** in the selected period.")
                else:
                    wb_tots = well_exp.groupby("Bucket")["AmountAdj"].sum().reset_index()
                    wb_tot  = wb_tots["AmountAdj"].sum()
                    loe_w   = wb_tots.loc[wb_tots["Bucket"]=="LOE",       "AmountAdj"].sum()
                    lh_w    = wb_tots.loc[wb_tots["Bucket"]=="Leasehold", "AmountAdj"].sum()
                    cap_w   = wb_tots.loc[wb_tots["Bucket"]=="Capital",   "AmountAdj"].sum()
                    wo_w    = wb_tots.loc[wb_tots["Bucket"]=="Workover",  "AmountAdj"].sum()

                    st.markdown(f"""
                    <div class="sum-row">
                      <div class="sum-cell"><div class="sum-lbl">LOE</div><div class="sum-val">{fmt(loe_w)}</div></div>
                      <div class="sum-cell amber"><div class="sum-lbl">Leasehold</div><div class="sum-val">{fmt(lh_w)}</div></div>
                      <div class="sum-cell purple"><div class="sum-lbl">Capital</div><div class="sum-val">{fmt(cap_w)}</div></div>
                      <div class="sum-cell red"><div class="sum-lbl">Workover</div><div class="sum-val">{fmt(wo_w)}</div></div>
                      <div class="sum-cell teal"><div class="sum-lbl">Total</div><div class="sum-val">{fmt(wb_tot)}</div></div>
                    </div>""", unsafe_allow_html=True)

                    if e3_period == "All periods":
                        st.markdown('<div class="panel red"><div class="panel-title">Expense Trend — ' + sel_well + '</div><div class="panel-sub">Monthly by bucket</div>', unsafe_allow_html=True)
                        wp_trend = (well_exp.groupby(["Period","Bucket"])["AmountAdj"]
                                    .sum().reset_index().sort_values("Period"))
                        wp_piv = wp_trend.pivot_table(index="Period", columns="Bucket", values="AmountAdj", fill_value=0).reset_index()
                        for bk in ["LOE","Leasehold","Capital","Workover"]:
                            if bk not in wp_piv.columns: wp_piv[bk] = 0.0
                        fw1 = go.Figure()
                        for bk in ["LOE","Leasehold","Capital","Workover"]:
                            fw1.add_bar(x=wp_piv["Period"], y=wp_piv[bk], name=bk,
                                        marker_color=BUCKET_COLORS[bk], marker_line_width=0)
                        fw1.update_layout(**bl(barmode="stack", height=300, yaxis=dict(tickprefix="$", tickformat=",.0f")))
                        sax(fw1)
                        st.plotly_chart(fw1, use_container_width=True, key="well_exp_trend")
                        st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown('<div class="panel red"><div class="panel-title">GL Line Items</div><div class="panel-sub">Every charge for this well · selected period</div>', unsafe_allow_html=True)
                    acct_detail = (well_exp.groupby(["Bucket","Account","AccountDesc"])["AmountAdj"]
                                   .sum().reset_index().sort_values(["Bucket","AmountAdj"], ascending=[True,False]))
                    acct_detail = acct_detail[acct_detail["AmountAdj"].abs() > 0.01]
                    fw2 = go.Figure(go.Bar(
                        x=acct_detail["AmountAdj"],
                        y=acct_detail.apply(lambda r: f"{int(r['Account'])} – {r['AccountDesc']}" if r['AccountDesc'] else str(int(r['Account'])), axis=1),
                        orientation="h",
                        marker_color=[BUCKET_COLORS.get(b,"#888") for b in acct_detail["Bucket"]],
                        marker_line_width=0,
                        text=acct_detail["AmountAdj"].apply(fmt), textposition="outside",
                        textfont=dict(family=MF, size=10),
                        hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
                    ))
                    fw2.update_layout(**bl(height=max(320, len(acct_detail)*28),
                                          xaxis=dict(tickprefix="$", tickformat=",.0f"),
                                          yaxis=dict(autorange="reversed"),
                                          margin=dict(t=8, b=32, l=260, r=90)))
                    sax(fw2)
                    st.plotly_chart(fw2, use_container_width=True, key="well_line_items")
                    st.markdown("</div>", unsafe_allow_html=True)

                    with st.expander("Raw line-item table"):
                        tbl3 = acct_detail.copy()
                        tbl3["Amount"] = tbl3["AmountAdj"].apply(lambda v: f"${v:,.0f}")
                        tbl3 = tbl3[["Bucket","Account","AccountDesc","Amount"]].rename(columns={"AccountDesc":"Description"})
                        st.dataframe(tbl3, use_container_width=True, hide_index=True)

        with etab4:
            ctrl4, body4 = st.columns([1, 4], gap="medium")
            with ctrl4:
                st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
                e4_top    = st.slider("Top N wells", 5, 50, 15, key="e4n")
                e4_period = st.selectbox("Period", ["All periods"] + (months_sorted[::-1] if months_sorted else []), key="e4p")
                e4_bucket = st.selectbox("Bucket", ["All buckets","LOE","Leasehold","Capital","Workover"], key="e4b")

            e4_df = exp_summary.copy()
            if e4_period != "All periods": e4_df = e4_df[e4_df["Period"] == e4_period]
            if e4_bucket != "All buckets": e4_df = e4_df[e4_df["Bucket"] == e4_bucket]
            well_rank = (e4_df.groupby("Well")["Amount"].sum()
                         .sort_values(ascending=False).head(e4_top).reset_index())

            with body4:
                st.markdown(f'<div class="panel red"><div class="panel-title">Top {e4_top} Wells by Cost</div><div class="panel-sub">{e4_period} · {e4_bucket}</div>', unsafe_allow_html=True)
                if well_rank.empty:
                    st.info("No data for selected filters.")
                else:
                    fw3 = go.Figure(go.Bar(
                        x=well_rank["Amount"], y=well_rank["Well"],
                        orientation="h", marker_color=C["ded"], marker_line_width=0,
                        text=well_rank["Amount"].apply(fmt), textposition="outside",
                        textfont=dict(family=MF, size=10),
                        hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
                    ))
                    fw3.update_layout(**bl(height=max(380, e4_top*30),
                                          xaxis=dict(tickprefix="$", tickformat=",.0f"),
                                          yaxis=dict(autorange="reversed"),
                                          margin=dict(t=16,b=40,l=230,r=90)))
                    sax(fw3)
                    st.plotly_chart(fw3, use_container_width=True, key="exp_well_rank")
                st.markdown("</div>", unsafe_allow_html=True)
                with st.expander("Full well-by-period expense detail"):
                    e4_full = exp_summary.copy()
                    if e4_bucket != "All buckets": e4_full = e4_full[e4_full["Bucket"] == e4_bucket]
                    if e4_full.empty:
                        st.dataframe(pd.DataFrame(), use_container_width=True, hide_index=True)
                    else:
                        tbl4 = e4_full.pivot_table(index="Well", columns="Period", values="Amount",
                                                   aggfunc="sum", fill_value=0).reset_index()
                        tbl4["Total"] = tbl4.iloc[:,1:].sum(axis=1)
                        tbl4 = tbl4.sort_values("Total", ascending=False)
                        for col in tbl4.columns[1:]:
                            tbl4[col] = tbl4[col].apply(lambda v: f"${v:,.0f}" if v != 0 else "—")
                        st.dataframe(tbl4, use_container_width=True, hide_index=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# P&L / FP&A MODULE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with pl_tab:
    pltab1, pltab2, pltab3, pltab4 = st.tabs([
        "Monthly P&L", "Full-Year Waterfall", "Well P&L", "Margin & Trend Analysis"
    ])

    # ── P&L Tab 1: Monthly P&L ────────────────────────────────────────────────
    with pltab1:
        st.markdown('<div class="panel"><div class="panel-title">Monthly P&L — Net Revenue vs Cost Structure</div><div class="panel-sub">Net revenue · OpEx · Capital · Leasehold · Net income overlay</div>', unsafe_allow_html=True)
        fp_main = go.Figure()
        fp_main.add_bar(x=pl["Period"], y=pl["Net_Rev"],    name="Net Revenue",
                        marker_color=C["gas"], marker_line_width=0)
        fp_main.add_bar(x=pl["Period"], y=-pl["OpEx"],      name="OpEx (LOE+WO)",
                        marker_color=C["loe"], marker_line_width=0)
        fp_main.add_bar(x=pl["Period"], y=-pl["Capital"],   name="Capital",
                        marker_color=C["capital"], marker_line_width=0)
        fp_main.add_bar(x=pl["Period"], y=-pl["Leasehold"], name="Leasehold",
                        marker_color=C["leasehold"], marker_line_width=0)
        fp_main.add_scatter(
            x=pl["Period"], y=pl["Net_Income"], name="Net Income",
            line=dict(color="#0d1424", width=2.5), mode="lines+markers",
            marker=dict(size=7, color=pl["Net_Income"].apply(lambda v: "#047857" if v >= 0 else "#c81e1e"),
                        line=dict(color="#fff", width=2)),
        )
        fp_main.update_layout(**bl(barmode="relative", height=400,
                                   yaxis=dict(tickprefix="$", tickformat=",.0f")))
        sax(fp_main)
        st.plotly_chart(fp_main, use_container_width=True, key="pl_main")
        st.markdown("</div>", unsafe_allow_html=True)

        L_pl, R_pl = st.columns(2, gap="medium")
        with L_pl:
            st.markdown('<div class="panel green"><div class="panel-title">Field EBITDA</div><div class="panel-sub">Net rev less LOE + Workover per period</div>', unsafe_allow_html=True)
            fp2_pl = go.Figure()
            fp2_pl.add_bar(x=pl["Period"], y=pl["Field_EBITDA"],
                           marker_color=pl["Field_EBITDA"].apply(lambda v: C["gas"] if v >= 0 else C["ded"]),
                           marker_line_width=0,
                           text=pl["Field_EBITDA"].apply(fmt), textposition="outside",
                           textfont=dict(family=MF, size=9),
                           hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
                           showlegend=False)
            fp2_pl.update_layout(**bl(height=260, yaxis=dict(tickprefix="$", tickformat=",.0f"),
                                      margin=dict(t=8, b=32, l=12, r=12)))
            sax(fp2_pl)
            st.plotly_chart(fp2_pl, use_container_width=True, key="pl_field_ebitda")
            st.markdown("</div>", unsafe_allow_html=True)

        with R_pl:
            st.markdown('<div class="panel teal"><div class="panel-title">Net Revenue Less Capital</div><div class="panel-sub">Net rev minus Capital spend per period</div>', unsafe_allow_html=True)
            fp3_pl = go.Figure()
            fp3_pl.add_bar(x=pl["Period"], y=pl["Net_Less_Cap"],
                           marker_color=pl["Net_Less_Cap"].apply(lambda v: C["gas"] if v >= 0 else C["ded"]),
                           marker_line_width=0,
                           text=pl["Net_Less_Cap"].apply(fmt), textposition="outside",
                           textfont=dict(family=MF, size=9),
                           hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
                           showlegend=False)
            fp3_pl.update_layout(**bl(height=260, yaxis=dict(tickprefix="$", tickformat=",.0f"),
                                      margin=dict(t=8, b=32, l=12, r=12)))
            sax(fp3_pl)
            st.plotly_chart(fp3_pl, use_container_width=True, key="pl_net_less_cap")
            st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Full monthly P&L table"):
            tbl_pl = pl.copy()
            for col in ["Gross","Net_Rev","Deductions","LOE","Workover","OpEx","Leasehold","Capital",
                        "Total_Exp","Field_EBITDA","Net_Less_Cap","Net_Income","Cum_Net_Income"]:
                tbl_pl[col] = tbl_pl[col].apply(lambda v: f"${v:,.0f}")
            for col in ["EBITDA_Margin","Net_Margin","Ded_Rate"]:
                tbl_pl[col] = tbl_pl[col].apply(lambda v: f"{v:.1f}%")
            tbl_pl["MoM_Net"] = pl["MoM_Net"].apply(lambda v: f"{v:+.1f}%" if pd.notna(v) else "—")
            tbl_pl = tbl_pl.rename(columns={
                "Gross":"Gross Rev","Net_Rev":"Net Rev","Deductions":"Rev Deds",
                "OpEx":"OpEx","Total_Exp":"Total Exp","Field_EBITDA":"Field EBITDA",
                "Net_Less_Cap":"Net Less Cap","Net_Income":"Net Income",
                "Cum_Net_Income":"Cum Net Income","EBITDA_Margin":"EBITDA Margin",
                "Net_Margin":"Net Margin","Ded_Rate":"Ded Rate","MoM_Net":"Net MoM%",
            })
            st.dataframe(tbl_pl, use_container_width=True, hide_index=True)

    # ── P&L Tab 2: FULL-YEAR MULTI-PERIOD WATERFALL ───────────────────────────
    with pltab2:
        st.markdown('<div class="panel"><div class="panel-title">Full-Year P&L Waterfall — All Periods</div><div class="panel-sub">Cumulative gross revenue → deductions → net rev → LOE → workover → leasehold → capital → net income · every month shown</div>', unsafe_allow_html=True)

        # Build cumulative totals across ALL months in view
        cum_gross    = pl["Gross"].sum()
        cum_deds     = pl["Deductions"].sum()
        cum_net_rev  = pl["Net_Rev"].sum()
        cum_loe_all  = pl["LOE"].sum()
        cum_wo_all   = pl["Workover"].sum()
        cum_lh_all   = pl["Leasehold"].sum()
        cum_cap_all  = pl["Capital"].sum()
        cum_ni_all   = pl["Net_Income"].sum()

        # ── Segment 1: Cumulative summary waterfall ───────────────────────────
        st.markdown("##### Cumulative Period Summary")
        wf_labels_cum = ["Gross Revenue","Rev Deductions","Net Revenue",
                         "LOE","Workover","Leasehold","Capital","Net Income"]
        wf_vals_cum   = [cum_gross, -cum_deds, cum_net_rev,
                         -cum_loe_all, -cum_wo_all, -cum_lh_all, -cum_cap_all, cum_ni_all]
        wf_colors_cum = ["#1040a8","#c81e1e","#047857",
                         C["loe"], C["workover"], C["leasehold"], C["capital"],
                         "#047857" if cum_ni_all >= 0 else "#c81e1e"]

        wf_bases_cum, wf_bars_cum = [], []
        running = 0
        for lbl, val in zip(wf_labels_cum, wf_vals_cum):
            if lbl in ("Gross Revenue", "Net Revenue", "Net Income"):
                wf_bases_cum.append(0)
                wf_bars_cum.append(abs(val) if lbl != "Net Income" else val)
                running = val
            else:
                wf_bases_cum.append(running + val)
                wf_bars_cum.append(-val)
                running += val

        fwf_cum = go.Figure()
        fwf_cum.add_bar(x=wf_labels_cum, y=wf_bases_cum, marker_color="rgba(0,0,0,0)", showlegend=False, hoverinfo="skip")
        fwf_cum.add_bar(
            x=wf_labels_cum, y=wf_bars_cum, marker_color=wf_colors_cum, marker_line_width=0,
            text=[fmt(v) for v in wf_vals_cum], textposition="outside",
            textfont=dict(family=MF, size=11, color="#374151"),
            showlegend=False,
            hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
        )
        fwf_cum.update_layout(**bl(barmode="stack", height=420,
                                   yaxis=dict(tickprefix="$", tickformat=",.0f"),
                                   margin=dict(t=20, b=48, l=12, r=12)))
        sax(fwf_cum)
        st.plotly_chart(fwf_cum, use_container_width=True, key="pl_waterfall_cum")

        ni_cls = "green" if cum_ni_all >= 0 else "red"
        st.markdown(f"""
        <div class="sum-row">
          <div class="sum-cell"><div class="sum-lbl">Gross Revenue</div><div class="sum-val">{fmt(cum_gross)}</div><div class="sum-note">{n_periods} periods</div></div>
          <div class="sum-cell amber"><div class="sum-lbl">Rev Deductions</div><div class="sum-val">{fmt(cum_deds)}</div><div class="sum-note">{f"{cum_deds/cum_gross*100:.1f}% of gross" if cum_gross else "—"}</div></div>
          <div class="sum-cell green"><div class="sum-lbl">Net Revenue</div><div class="sum-val">{fmt(cum_net_rev)}</div><div class="sum-note">{f"{cum_net_rev/cum_gross*100:.1f}% retained" if cum_gross else "—"}</div></div>
          <div class="sum-cell"><div class="sum-lbl">Total OpEx</div><div class="sum-val">{fmt(cum_loe_all+cum_wo_all)}</div></div>
          <div class="sum-cell purple"><div class="sum-lbl">Total Capital</div><div class="sum-val">{fmt(cum_cap_all)}</div></div>
          <div class="sum-cell {ni_cls}"><div class="sum-lbl">Net Income</div><div class="sum-val {'neg' if cum_ni_all < 0 else ''}">{fmt(cum_ni_all)}</div><div class="sum-note">{f"{cum_ni_all/cum_gross*100:.1f}% margin" if cum_gross else "—"}</div></div>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")

        # ── Segment 2: Monthly Net Income bars with cumulative line ──────────
        st.markdown("##### Monthly Net Income · Cumulative Build")
        st.markdown('<div class="panel indigo"><div class="panel-title">Net Income by Period + Cumulative</div><div class="panel-sub">Monthly bars (positive/negative) · right axis: cumulative net income build</div>', unsafe_allow_html=True)

        fni = make_subplots(specs=[[{"secondary_y": True}]])
        bar_colors = pl["Net_Income"].apply(lambda v: "#047857" if v >= 0 else "#c81e1e").tolist()
        fni.add_bar(x=pl["Period"], y=pl["Net_Income"], name="Monthly Net Income",
                    marker_color=bar_colors, marker_line_width=0,
                    hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
                    secondary_y=False)
        fni.add_scatter(x=pl["Period"], y=pl["Cum_Net_Income"], name="Cumulative Net Income",
                        line=dict(color="#4338ca", width=2.5, dash="dot"), mode="lines+markers",
                        marker=dict(size=6, color="#4338ca", line=dict(color="#fff", width=2)),
                        hovertemplate="%{x} cumul: $%{y:,.0f}<extra></extra>",
                        secondary_y=True)
        fni.update_layout(**bl(barmode="relative", height=320))
        tf_ni = dict(family=MF, size=9, color="#b0bbd4")
        fni.update_xaxes(showgrid=False, showline=True, linecolor="#d4d9e8", tickfont=tf_ni)
        fni.update_yaxes(title_text="Monthly Net Income", tickprefix="$", tickformat=",.0f",
                         showgrid=True, gridcolor=GRID, tickfont=tf_ni, secondary_y=False)
        fni.update_yaxes(title_text="Cumulative", tickprefix="$", tickformat=",.0f",
                         showgrid=False, tickfont=tf_ni, secondary_y=True)
        st.plotly_chart(fni, use_container_width=True, key="pl_monthly_ni_cum")
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Segment 3: Monthly waterfall — select period ──────────────────────
        st.markdown("---")
        st.markdown("##### Single-Period Detailed Waterfall")
        ctrl_wf, body_wf = st.columns([1, 4], gap="medium")
        with ctrl_wf:
            st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
            wf_period = st.selectbox("Period", months_sorted[::-1] if months_sorted else ["—"], key="wf_p")

        wf_row = pl[pl["Period"] == wf_period].iloc[0] if not pl.empty and wf_period in pl["Period"].values else None

        with body_wf:
            if wf_row is None:
                st.info("No data for selected period.")
            else:
                gross     = wf_row["Gross"]
                rev_deds  = wf_row["Deductions"]
                net_rev   = wf_row["Net_Rev"]
                loe       = wf_row["LOE"]
                workover  = wf_row["Workover"]
                leasehold = wf_row["Leasehold"]
                capital   = wf_row["Capital"]
                net_inc   = wf_row["Net_Income"]
                ebitda_m  = wf_row["EBITDA_Margin"]
                net_m     = wf_row["Net_Margin"]

                wf_labels = ["Gross Revenue","Rev Deductions","Net Revenue",
                             "LOE","Workover","Leasehold","Capital","Net Income"]
                wf_vals   = [gross, -rev_deds, net_rev, -loe, -workover, -leasehold, -capital, net_inc]
                wf_colors = ["#1040a8","#c81e1e","#047857",
                             C["loe"], C["workover"], C["leasehold"], C["capital"],
                             "#047857" if net_inc >= 0 else "#c81e1e"]

                wf_bases, wf_bars = [], []
                running = 0
                for lbl, val in zip(wf_labels, wf_vals):
                    if lbl in ("Gross Revenue", "Net Revenue", "Net Income"):
                        wf_bases.append(0)
                        wf_bars.append(abs(val) if lbl != "Net Income" else val)
                        running = val
                    else:
                        wf_bases.append(running + val)
                        wf_bars.append(-val)
                        running += val

                st.markdown(f'<div class="panel"><div class="panel-title">P&L Waterfall — {wf_period}</div><div class="panel-sub">Gross → deductions → net rev → opex → capital → net income</div>', unsafe_allow_html=True)
                fwf = go.Figure()
                fwf.add_bar(x=wf_labels, y=wf_bases, marker_color="rgba(0,0,0,0)", showlegend=False, hoverinfo="skip")
                fwf.add_bar(
                    x=wf_labels, y=wf_bars, marker_color=wf_colors, marker_line_width=0,
                    text=[fmt(v) for v in wf_vals], textposition="outside",
                    textfont=dict(family=MF, size=10, color="#374151"),
                    showlegend=False,
                    hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
                )
                fwf.update_layout(**bl(barmode="stack", height=420,
                                       yaxis=dict(tickprefix="$", tickformat=",.0f")))
                sax(fwf)
                st.plotly_chart(fwf, use_container_width=True, key="pl_waterfall_single")
                st.markdown("</div>", unsafe_allow_html=True)

                ni_cls2 = "green" if net_inc >= 0 else "red"
                st.markdown(f"""
                <div class="sum-row">
                  <div class="sum-cell"><div class="sum-lbl">Gross Revenue</div><div class="sum-val">{fmt(gross)}</div></div>
                  <div class="sum-cell amber"><div class="sum-lbl">Rev Deductions</div><div class="sum-val">{fmt(rev_deds)}</div><div class="sum-note">{f"{rev_deds/gross*100:.1f}% of gross" if gross else "—"}</div></div>
                  <div class="sum-cell green"><div class="sum-lbl">Net Revenue</div><div class="sum-val">{fmt(net_rev)}</div></div>
                  <div class="sum-cell"><div class="sum-lbl">OpEx (LOE+WO)</div><div class="sum-val">{fmt(loe+workover)}</div></div>
                  <div class="sum-cell purple"><div class="sum-lbl">Capital</div><div class="sum-val">{fmt(capital)}</div></div>
                  <div class="sum-cell teal"><div class="sum-lbl">EBITDA Margin</div><div class="sum-val">{ebitda_m:.1f}%</div></div>
                  <div class="sum-cell {ni_cls2}"><div class="sum-lbl">Net Income</div><div class="sum-val {'neg' if net_inc < 0 else ''}">{fmt(net_inc)}</div><div class="sum-note">{f"{net_m:.1f}% net margin" if gross else "—"}</div></div>
                </div>""", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── P&L Tab 3: Well P&L ───────────────────────────────────────────────────
    with pltab3:
        ctrl_w, body_w = st.columns([1, 4], gap="medium")
        with ctrl_w:
            st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
            pw_period = st.selectbox("Period", ["All periods"] + (months_sorted[::-1] if months_sorted else []), key="pw_p")
            pw_metric = st.radio("View", ["Net Income","Field EBITDA","Net Less Capital"], key="pw_m")
            pw_top    = st.slider("Top N", 5, 60, 20, key="pw_n")

        rev_w = (
            summary.groupby("Well")
            .apply(lambda g: g[g["Period"] == pw_period] if pw_period != "All periods" else g, include_groups=False)
            .reset_index(level=0).reset_index(drop=True)
            .groupby("Well")
            .agg(Net_Rev=("Net_Revenue","sum"))
            .reset_index()
        ) if not summary.empty else pd.DataFrame(columns=["Well","Net_Rev"])

        exp_w_raw = exp_summary.copy()
        if pw_period != "All periods":
            exp_w_raw = exp_w_raw[exp_w_raw["Period"] == pw_period]
        exp_w = (
            exp_w_raw.pivot_table(index="Well", columns="Bucket", values="Amount", aggfunc="sum", fill_value=0)
            .reset_index()
        ) if not exp_w_raw.empty else pd.DataFrame(columns=["Well"])
        for bk in ["LOE","Leasehold","Capital","Workover"]:
            if bk not in exp_w.columns: exp_w[bk] = 0.0

        well_pl = rev_w.merge(exp_w, on="Well", how="outer").fillna(0)
        well_pl["OpEx"]          = well_pl["LOE"] + well_pl["Workover"]
        well_pl["Total_Exp"]     = well_pl["LOE"] + well_pl["Workover"] + well_pl["Capital"] + well_pl["Leasehold"]
        well_pl["Net_Income"]    = well_pl["Net_Rev"] - well_pl["Total_Exp"]
        well_pl["Field_EBITDA"]  = well_pl["Net_Rev"] - well_pl["OpEx"]
        well_pl["Net_Less_Cap"]  = well_pl["Net_Rev"] - well_pl["Capital"]

        metric_col = {"Net Income":"Net_Income","Field EBITDA":"Field_EBITDA","Net Less Capital":"Net_Less_Cap"}[pw_metric]
        top_wells  = well_pl.sort_values(metric_col, ascending=False).head(pw_top)
        bot_wells  = well_pl.sort_values(metric_col, ascending=True).head(pw_top)

        with body_w:
            TL, TR = st.columns(2, gap="medium")
            with TL:
                st.markdown(f'<div class="panel green"><div class="panel-title">Top {pw_top} Wells — {pw_metric}</div><div class="panel-sub">{pw_period}</div>', unsafe_allow_html=True)
                fw_top = go.Figure(go.Bar(
                    x=top_wells[metric_col], y=top_wells["Well"], orientation="h",
                    marker_color=top_wells[metric_col].apply(lambda v: C["gas"] if v >= 0 else C["ded"]),
                    marker_line_width=0,
                    text=top_wells[metric_col].apply(fmt), textposition="outside",
                    textfont=dict(family=MF, size=10),
                    hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
                ))
                fw_top.update_layout(**bl(height=max(340, pw_top*28),
                                         xaxis=dict(tickprefix="$", tickformat=",.0f"),
                                         yaxis=dict(autorange="reversed"),
                                         margin=dict(t=8, b=32, l=220, r=90)))
                sax(fw_top)
                st.plotly_chart(fw_top, use_container_width=True, key="pl_well_top")
                st.markdown("</div>", unsafe_allow_html=True)
            with TR:
                st.markdown(f'<div class="panel red"><div class="panel-title">Bottom {pw_top} Wells — {pw_metric}</div><div class="panel-sub">{pw_period}</div>', unsafe_allow_html=True)
                fw_bot = go.Figure(go.Bar(
                    x=bot_wells[metric_col], y=bot_wells["Well"], orientation="h",
                    marker_color=bot_wells[metric_col].apply(lambda v: C["gas"] if v >= 0 else C["ded"]),
                    marker_line_width=0,
                    text=bot_wells[metric_col].apply(fmt), textposition="outside",
                    textfont=dict(family=MF, size=10),
                    hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
                ))
                fw_bot.update_layout(**bl(height=max(340, pw_top*28),
                                         xaxis=dict(tickprefix="$", tickformat=",.0f"),
                                         yaxis=dict(autorange="reversed"),
                                         margin=dict(t=8, b=32, l=220, r=90)))
                sax(fw_bot)
                st.plotly_chart(fw_bot, use_container_width=True, key="pl_well_bot")
                st.markdown("</div>", unsafe_allow_html=True)
            with st.expander("Full well P&L table"):
                tbl_w = well_pl.sort_values("Net_Income", ascending=False).copy()
                for col in ["Net_Rev","LOE","Workover","OpEx","Leasehold","Capital","Total_Exp",
                            "Net_Income","Field_EBITDA","Net_Less_Cap"]:
                    tbl_w[col] = tbl_w[col].apply(lambda v: f"${v:,.0f}")
                tbl_w = tbl_w.rename(columns={
                    "Net_Rev":"Net Rev","OpEx":"OpEx","Total_Exp":"Total Exp",
                    "Net_Income":"Net Income","Field_EBITDA":"Field EBITDA","Net_Less_Cap":"Net Less Cap",
                })
                st.dataframe(tbl_w, use_container_width=True, hide_index=True)

    # ── P&L Tab 4: Margin & Trend Analysis ────────────────────────────────────
    with pltab4:
        st.markdown('<div class="panel indigo"><div class="panel-title">Margin Trend Analysis</div><div class="panel-sub">EBITDA margin · Net margin · Deduction rate — all periods</div>', unsafe_allow_html=True)

        f_mg = go.Figure()
        f_mg.add_scatter(x=pl["Period"], y=pl["EBITDA_Margin"], name="Field EBITDA Margin %",
                         line=dict(color=C["gas"], width=2.5), mode="lines+markers",
                         marker=dict(size=6, color=C["gas"], line=dict(color="#fff", width=2)),
                         hovertemplate="%{x}: %{y:.1f}%<extra></extra>")
        f_mg.add_scatter(x=pl["Period"], y=pl["Net_Margin"], name="Net Margin %",
                         line=dict(color=C["net"], width=2.5), mode="lines+markers",
                         marker=dict(size=6, color=C["net"], line=dict(color="#fff", width=2)),
                         hovertemplate="%{x}: %{y:.1f}%<extra></extra>")
        f_mg.add_scatter(x=pl["Period"], y=pl["Ded_Rate"], name="Deduction Rate %",
                         line=dict(color=C["ded"], width=1.5, dash="dot"), mode="lines+markers",
                         marker=dict(size=5, color=C["ded"], line=dict(color="#fff", width=1.5)),
                         hovertemplate="%{x}: %{y:.1f}%<extra></extra>")
        f_mg.add_hline(y=0, line_color="#d4d9e8", line_width=1)
        f_mg.update_layout(**bl(height=340, yaxis=dict(ticksuffix="%", tickformat=".1f")))
        sax(f_mg)
        st.plotly_chart(f_mg, use_container_width=True, key="margin_trend")
        st.markdown("</div>", unsafe_allow_html=True)

        # MoM waterfall of net income changes
        st.markdown('<div class="panel"><div class="panel-title">Month-over-Month Net Income Bridge</div><div class="panel-sub">Period-to-period change in net income — variance attribution</div>', unsafe_allow_html=True)

        if len(pl) >= 2:
            mom_labels = []
            mom_vals   = []
            mom_colors = []
            mom_bases  = []
            running_mom = pl["Net_Income"].iloc[0]

            mom_labels.append(pl["Period"].iloc[0])
            mom_vals.append(running_mom)
            mom_colors.append("#1040a8")
            mom_bases.append(0)

            for i in range(1, len(pl)):
                delta = pl["Net_Income"].iloc[i] - pl["Net_Income"].iloc[i-1]
                mom_labels.append(pl["Period"].iloc[i])
                mom_vals.append(abs(delta))
                mom_colors.append("#047857" if delta >= 0 else "#c81e1e")
                mom_bases.append(min(pl["Net_Income"].iloc[i-1], pl["Net_Income"].iloc[i]))

            mom_labels.append(f"Total ({months_sorted[0]}–{months_sorted[-1]})" if len(months_sorted) > 1 else "Total")
            mom_vals.append(abs(cum_ni_all))
            mom_colors.append("#047857" if cum_ni_all >= 0 else "#c81e1e")
            mom_bases.append(0)

            f_mom = go.Figure()
            f_mom.add_bar(x=mom_labels, y=mom_bases, marker_color="rgba(0,0,0,0)", showlegend=False, hoverinfo="skip")
            f_mom.add_bar(x=mom_labels, y=mom_vals, marker_color=mom_colors, marker_line_width=0,
                          text=[fmt(v * (1 if c == "#047857" or c == "#1040a8" else -1))
                                for v, c in zip(mom_vals, mom_colors)],
                          textposition="outside", textfont=dict(family=MF, size=10),
                          showlegend=False,
                          hovertemplate="%{x}: $%{y:,.0f}<extra></extra>")
            f_mom.update_layout(**bl(barmode="stack", height=340,
                                     yaxis=dict(tickprefix="$", tickformat=",.0f")))
            sax(f_mom)
            st.plotly_chart(f_mom, use_container_width=True, key="mom_bridge")
        else:
            st.info("Need at least 2 periods for MoM bridge.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Revenue vs Cost efficiency scatter (per-well)
        st.markdown('<div class="panel"><div class="panel-title">Well Efficiency Scatter — Revenue vs Cost</div><div class="panel-sub">Bubble size = Net Income · X = Net Revenue · Y = Total Cost · Efficient wells: top-left</div>', unsafe_allow_html=True)
        if not well_pl.empty and len(well_pl) > 1:
            scatter_df = well_pl.copy()
            scatter_df = scatter_df[(scatter_df["Net_Rev"] > 0) | (scatter_df["Total_Exp"] > 0)]
            bubble_sz  = scatter_df["Net_Income"].apply(lambda v: max(abs(v)**0.5 / 10, 4))
            bubble_clr = scatter_df["Net_Income"].apply(lambda v: "#047857" if v >= 0 else "#c81e1e")
            f_sc = go.Figure(go.Scatter(
                x=scatter_df["Net_Rev"], y=scatter_df["Total_Exp"],
                mode="markers+text",
                text=scatter_df["Well"].apply(lambda w: w[:12] + "…" if len(w) > 12 else w),
                textposition="top center", textfont=dict(family=MF, size=8, color="#6b7a99"),
                marker=dict(size=bubble_sz, color=bubble_clr,
                            line=dict(color="#fff", width=1.5), opacity=0.85),
                hovertemplate="<b>%{text}</b><br>Net Rev: $%{x:,.0f}<br>Total Cost: $%{y:,.0f}<extra></extra>",
            ))
            # Add break-even line
            max_ax = max(scatter_df["Net_Rev"].max(), scatter_df["Total_Exp"].max()) * 1.1
            f_sc.add_scatter(x=[0, max_ax], y=[0, max_ax], mode="lines",
                             line=dict(color="#d4d9e8", width=1, dash="dot"),
                             showlegend=False, hoverinfo="skip", name="Break-even")
            f_sc.update_layout(**bl(height=380,
                                    xaxis=dict(tickprefix="$", tickformat=",.0f", title="Net Revenue"),
                                    yaxis=dict(tickprefix="$", tickformat=",.0f", title="Total Cost"),
                                    margin=dict(t=16, b=48, l=60, r=16)))
            sax(f_sc)
            st.plotly_chart(f_sc, use_container_width=True, key="well_scatter")
        else:
            st.info("Need per-well data to render scatter.")
        st.markdown("</div>", unsafe_allow_html=True)
