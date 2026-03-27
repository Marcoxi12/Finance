"""
data_loader.py — GL ingestion, normalization, caching (revenue + expenses)
"""

import json
import hashlib
from datetime import datetime
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_DIR = Path("data")
CACHE_FILE = DATA_DIR / "gl_cache.parquet"
META_FILE = DATA_DIR / "uploaded_files.json"

# ── Revenue accounts ──────────────────────────────────────────────────────────
REV_ACCOUNTS  = {9601, 9621, 9631}
DED_ACCOUNTS  = {9602, 9615, 9622, 9627, 9630, 9632, 9636}
ALL_REV_ACCTS = REV_ACCOUNTS | DED_ACCOUNTS

# ── Expense buckets ───────────────────────────────────────────────────────────
LOE_RANGE       = (9000, 9099)   # LOE
LEASEHOLD_RANGE = (9100, 9199)   # Leasehold
CAPITAL_RANGE   = (9200, 9399)   # Capital costs
WORKOVER_RANGE  = (9500, 9598)   # LOE Workover
IGNORE_ACCTS    = {9599}         # JIB billing — excluded

def _is_expense(acct):
    if acct in IGNORE_ACCTS:
        return False
    return (
        LOE_RANGE[0]       <= acct <= LOE_RANGE[1]       or
        LEASEHOLD_RANGE[0] <= acct <= LEASEHOLD_RANGE[1] or
        CAPITAL_RANGE[0]   <= acct <= CAPITAL_RANGE[1]   or
        WORKOVER_RANGE[0]  <= acct <= WORKOVER_RANGE[1]
    )

def _expense_bucket(acct):
    if LOE_RANGE[0]       <= acct <= LOE_RANGE[1]:       return "LOE"
    if LEASEHOLD_RANGE[0] <= acct <= LEASEHOLD_RANGE[1]: return "Leasehold"
    if CAPITAL_RANGE[0]   <= acct <= CAPITAL_RANGE[1]:   return "Capital"
    if WORKOVER_RANGE[0]  <= acct <= WORKOVER_RANGE[1]:  return "Workover"
    return "Other"

ALL_EXP_ACCTS = set(
    list(range(LOE_RANGE[0],       LOE_RANGE[1]       + 1)) +
    list(range(LEASEHOLD_RANGE[0], LEASEHOLD_RANGE[1] + 1)) +
    list(range(CAPITAL_RANGE[0],   CAPITAL_RANGE[1]   + 1)) +
    list(range(WORKOVER_RANGE[0],  WORKOVER_RANGE[1]  + 1))
) - IGNORE_ACCTS

ALL_ACCTS = ALL_REV_ACCTS | ALL_EXP_ACCTS

COL_ALIASES = {
    "EffDate":     ["EffDate", "Eff Date", "EffectiveDate"],
    "Account":     ["Account"],
    "SubAccount":  ["SubAccount", "Sub Account", "SubAcct", "Sub Acct"],
    "SubAcctDesc": ["SubAccount Desc", "SubAccountDesc", "SubAcctDesc",
                    "SubAccountDescription", "{SubAccount Desc}"],
    "Amount":      ["Amount"],
    "Quantity":    ["Quantity"],
    "AcqCode":     ["AcqCode", "Acq Code", "AcquisitionCode", "{AcqCode}"],
    "AccountDesc": ["{Account Desc}", "Account Desc", "AccountDesc"],
}

# ── Session state ─────────────────────────────────────────────────────────────
def _ss():
    if "gl_app" not in st.session_state:
        st.session_state["gl_app"] = {"df": None, "file_hashes": set()}
        try:
            if CACHE_FILE.exists():
                cached = pd.read_parquet(CACHE_FILE)
                _backfill(cached)
                st.session_state["gl_app"]["df"] = cached
            if META_FILE.exists():
                meta = json.loads(META_FILE.read_text())
                st.session_state["gl_app"]["file_hashes"] = {f["hash"] for f in meta.get("files", [])}
        except Exception:
            pass
    return st.session_state["gl_app"]

def _backfill(df):
    if "SubAccount" not in df.columns:
        df["SubAccount"] = ""
    if "SubAcctNum" not in df.columns:
        df["SubAcctNum"] = df["SubAccount"].astype(str).str.strip().replace("", "Unknown").fillna("Unknown")
    if "Well" not in df.columns and "SubAcctDesc" in df.columns:
        df["Well"] = df["SubAcctDesc"].fillna("Unknown").astype(str).str.strip()
    if "AcqCode" not in df.columns:
        df["AcqCode"] = "Unknown"
    if "Period" not in df.columns and "EffDate" in df.columns:
        df["EffDate"] = pd.to_datetime(df["EffDate"], errors="coerce")
        df["Period"] = df["EffDate"].dt.to_period("M").astype(str)
    if "Bucket" not in df.columns and "Account" in df.columns:
        df["Bucket"] = df["Account"].apply(lambda a: _expense_bucket(int(a)) if pd.notna(a) and _is_expense(int(a)) else "Revenue")
    if "AccountDesc" not in df.columns:
        df["AccountDesc"] = ""

def _clean_col(name):
    return str(name).strip("{}").strip()

def _normalize(df):
    # Strip {} from column names
    df = df.rename(columns={c: _clean_col(c) for c in df.columns})

    resolved = {}
    for canon, aliases in COL_ALIASES.items():
        cleaned_aliases = [_clean_col(a) for a in aliases]
        for alias in cleaned_aliases:
            if alias in df.columns:
                resolved[alias] = canon
                break

    df = df.rename(columns=resolved)

    if "SubAccount" not in df.columns:
        df["SubAccount"] = ""
    if "AccountDesc" not in df.columns:
        df["AccountDesc"] = ""

    for req in ["EffDate", "Account", "SubAcctDesc", "Amount"]:
        if req not in df.columns:
            raise ValueError(f"Required column not found: '{req}'")

    df["EffDate"]  = pd.to_datetime(df["EffDate"], errors="coerce")
    df["Account"]  = pd.to_numeric(df["Account"], errors="coerce").astype("Int64")
    df["Amount"]   = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
    df["Quantity"] = pd.to_numeric(df.get("Quantity", 0), errors="coerce").fillna(0.0)

    if "AcqCode" not in df.columns:
        df["AcqCode"] = "Unknown"

    # Keep revenue AND expense accounts
    df = df[df["Account"].apply(lambda a: pd.notna(a) and (
        int(a) in ALL_REV_ACCTS or _is_expense(int(a))
    ))].copy()

    if df.empty:
        return df

    df["Period"]    = df["EffDate"].dt.to_period("M").astype(str)
    df["Well"]      = df["SubAcctDesc"].fillna("Unknown").astype(str).str.strip()
    df["SubAcctNum"] = df["SubAccount"].astype(str).str.strip().replace("", "Unknown").fillna("Unknown")
    df["AcqCode"]   = df["AcqCode"].fillna("Unknown").astype(str).str.strip()
    df["AccountDesc"] = df["AccountDesc"].fillna("").astype(str).str.strip()

    # Revenue sign flip (credits are stored negative in GL)
    df["AmountAdj"] = np.where(df["Account"].isin(REV_ACCOUNTS), -df["Amount"], df["Amount"])
    df["QtyAdj"]    = np.where(df["Account"].isin(REV_ACCOUNTS), -df["Quantity"], df["Quantity"])

    # Bucket tag
    df["Bucket"] = df["Account"].apply(
        lambda a: _expense_bucket(int(a)) if _is_expense(int(a)) else "Revenue"
    )

    return df

# ── Public API ────────────────────────────────────────────────────────────────
def ingest_file(uploaded_file):
    file_bytes = uploaded_file.read()
    fhash = hashlib.md5(file_bytes).hexdigest()
    ss = _ss()

    if fhash in ss["file_hashes"]:
        return {"status": "duplicate"}

    ext = Path(uploaded_file.name).suffix.lower()
    try:
        if ext in (".xlsx", ".xls"):
            raw = pd.read_excel(BytesIO(file_bytes))
        else:
            raw = pd.read_csv(BytesIO(file_bytes))
        new_df = _normalize(raw)
    except Exception as e:
        return {"status": "error", "message": str(e)}

    if new_df.empty:
        return {"status": "error", "message": "No recognized GL accounts found."}

    rows    = len(new_df)
    periods = new_df["Period"].nunique()
    wells   = new_df["Well"].nunique()

    if ss["df"] is None:
        ss["df"] = new_df.reset_index(drop=True)
    else:
        ss["df"] = (
            pd.concat([ss["df"], new_df], ignore_index=True)
            .drop_duplicates(subset=["Period", "Account", "Well", "Amount"], keep="last")
            .reset_index(drop=True)
        )

    ss["file_hashes"].add(fhash)
    _save_local(ss["df"], fhash, uploaded_file.name, rows, periods, wells)
    return {"status": "ok", "rows": rows, "months": periods, "wells": wells}

def load_all_data():
    return _ss()["df"]

def _save_local(df, fhash, filename, rows, periods, wells):
    try:
        DATA_DIR.mkdir(exist_ok=True)
        df.to_parquet(CACHE_FILE, index=False)
        meta = {"files": []}
        if META_FILE.exists():
            meta = json.loads(META_FILE.read_text())
        meta["files"].append({
            "hash": fhash, "filename": filename,
            "loaded_at": datetime.now().isoformat(),
            "rows": rows, "periods": periods, "wells": wells,
        })
        META_FILE.write_text(json.dumps(meta, indent=2))
    except Exception:
        pass

# ── Revenue summary (unchanged) ───────────────────────────────────────────────
def get_summary(df):
    if df is None or df.empty:
        return pd.DataFrame()
    rev = df[df["Bucket"] == "Revenue"].copy()
    if rev.empty:
        return pd.DataFrame()

    rows = []
    for (well, period, acq), grp in rev.groupby(["Well", "Period", "AcqCode"]):
        r = {"Well": well, "Period": period, "AcqCode": acq}
        r["Oil_Gross"]   = grp.loc[grp["Account"] == 9601, "AmountAdj"].sum()
        r["Gas_Gross"]   = grp.loc[grp["Account"] == 9621, "AmountAdj"].sum()
        r["Plant_Gross"] = grp.loc[grp["Account"] == 9631, "AmountAdj"].sum()
        r["Oil_Tax"]     = grp.loc[grp["Account"] == 9602, "AmountAdj"].sum()
        r["Gas_Tax"]     = grp.loc[grp["Account"] == 9622, "AmountAdj"].sum()
        r["Gas_Comp"]    = grp.loc[grp["Account"] == 9627, "AmountAdj"].sum()
        r["Gas_LowVol"]  = grp.loc[grp["Account"] == 9630, "AmountAdj"].sum()
        r["Plant_Tax"]   = grp.loc[grp["Account"] == 9632, "AmountAdj"].sum()
        r["Plant_Deduct"]= grp.loc[grp["Account"] == 9636, "AmountAdj"].sum()
        r["Rejected_Fee"]= grp.loc[grp["Account"] == 9615, "AmountAdj"].sum()
        r["Oil_BBL"]     = grp.loc[grp["Account"] == 9601, "QtyAdj"].sum()
        r["Gas_MCF"]     = grp.loc[grp["Account"] == 9621, "QtyAdj"].sum()
        r["Plant_GAL"]   = grp.loc[grp["Account"] == 9631, "QtyAdj"].sum()
        r["Gross_Revenue"]     = r["Oil_Gross"] + r["Gas_Gross"] + r["Plant_Gross"]
        r["Total_Deductions"]  = (r["Oil_Tax"] + r["Gas_Tax"] + r["Gas_Comp"] +
                                   r["Gas_LowVol"] + r["Plant_Tax"] + r["Plant_Deduct"] + r["Rejected_Fee"])
        r["Net_Revenue"]       = r["Gross_Revenue"] - r["Total_Deductions"]
        rows.append(r)
    return pd.DataFrame(rows)

# ── Expense summary ────────────────────────────────────────────────────────────
def get_expense_summary(df):
    """Return per-well / per-period / per-bucket expense totals."""
    if df is None or df.empty:
        return pd.DataFrame()
    exp = df[df["Bucket"] != "Revenue"].copy()
    if exp.empty:
        return pd.DataFrame()

    rows = []
    for (well, period, bucket), grp in exp.groupby(["Well", "Period", "Bucket"]):
        rows.append({
            "Well":    well,
            "Period":  period,
            "Bucket":  bucket,
            "Amount":  grp["AmountAdj"].sum(),
        })
    return pd.DataFrame(rows)

def get_expense_detail(df, well=None, period=None):
    """Return line-level expense rows, optionally filtered."""
    if df is None or df.empty:
        return pd.DataFrame()
    exp = df[df["Bucket"] != "Revenue"].copy()
    if well:
        exp = exp[exp["Well"] == well]
    if period:
        exp = exp[exp["Period"] == period]
    cols = ["Well", "Period", "Bucket", "Account", "AccountDesc", "AmountAdj"]
    available = [c for c in cols if c in exp.columns]
    return exp[available].copy()
