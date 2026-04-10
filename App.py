"""
data_loader.py
GL ingestion, normalization, caching
"""

import hashlib
import json
import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd
import streamlit as st

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
CACHE_FILE = DATA_DIR / "gl_cache.parquet"
META_FILE = DATA_DIR / "uploaded_files.json"

# ── Revenue accounts ──────────────────────────────────────────────────────────
REV_ACCOUNTS = {9601, 9621, 9631}
DED_ACCOUNTS = {9602, 9615, 9622, 9627, 9630, 9632, 9636}
ALL_REV_ACCTS = REV_ACCOUNTS | DED_ACCOUNTS

# ── Expense buckets ───────────────────────────────────────────────────────────
LOE_RANGE = (9000, 9099)
LEASEHOLD_RANGE = (9100, 9199)
CAPITAL_RANGE = (9200, 9399)
WORKOVER_RANGE = (9500, 9598)
IGNORE_ACCTS = {9599}

ALL_EXP_ACCTS = set(
    list(range(LOE_RANGE[0], LOE_RANGE[1] + 1))
    + list(range(LEASEHOLD_RANGE[0], LEASEHOLD_RANGE[1] + 1))
    + list(range(CAPITAL_RANGE[0], CAPITAL_RANGE[1] + 1))
    + list(range(WORKOVER_RANGE[0], WORKOVER_RANGE[1] + 1))
) - IGNORE_ACCTS

ALL_ACCTS = ALL_REV_ACCTS | ALL_EXP_ACCTS

# ── Column aliases ────────────────────────────────────────────────────────────
COL_ALIASES = {
    "EffDate": ["EffDate", "Eff Date", "EffectiveDate", "Effective Date"],
    "Account": ["Account", "Acct", "GL Account"],
    "SubAccount": ["SubAccount", "Sub Account", "SubAcct", "Sub Acct"],
    "SubAcctDesc": [
        "SubAccount Desc",
        "SubAccountDesc",
        "SubAcctDesc",
        "SubAccountDescription",
        "Sub Acct Desc",
        "{SubAccount Desc}",
    ],
    "Amount": ["Amount", "Amount Adj", "AmountAdj"],
    "Quantity": ["Quantity", "Qty", "Units"],
    "AcqCode": ["AcqCode", "Acq Code", "AcquisitionCode", "{AcqCode}"],
    "AccountDesc": ["{Account Desc}", "Account Desc", "AccountDesc", "GL Description"],
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _is_expense(acct: int) -> bool:
    if acct in IGNORE_ACCTS:
        return False
    return (
        LOE_RANGE[0] <= acct <= LOE_RANGE[1]
        or LEASEHOLD_RANGE[0] <= acct <= LEASEHOLD_RANGE[1]
        or CAPITAL_RANGE[0] <= acct <= CAPITAL_RANGE[1]
        or WORKOVER_RANGE[0] <= acct <= WORKOVER_RANGE[1]
    )


def _expense_bucket(acct: int) -> str:
    if LOE_RANGE[0] <= acct <= LOE_RANGE[1]:
        return "LOE"
    if LEASEHOLD_RANGE[0] <= acct <= LEASEHOLD_RANGE[1]:
        return "Leasehold"
    if CAPITAL_RANGE[0] <= acct <= CAPITAL_RANGE[1]:
        return "Capital"
    if WORKOVER_RANGE[0] <= acct <= WORKOVER_RANGE[1]:
        return "Workover"
    return "Other"


def _extract_company(filename: str) -> str:
    filename_upper = str(filename or "").upper()
    if "40ACR" in filename_upper:
        return "40ACR"
    if "FAEII" in filename_upper:
        return "FAEII"
    return "Unknown"


def _clean_col(name: str) -> str:
    return str(name).strip().strip("{}").strip()


def _hash_file(file_bytes: bytes) -> str:
    return hashlib.md5(file_bytes).hexdigest()


def _backfill(df: pd.DataFrame) -> None:
    if "SubAccount" not in df.columns:
        df["SubAccount"] = ""

    if "SubAcctNum" not in df.columns:
        df["SubAcctNum"] = (
            df["SubAccount"]
            .fillna("")
            .astype(str)
            .str.strip()
            .replace("", "Unknown")
        )

    if "Well" not in df.columns and "SubAcctDesc" in df.columns:
        df["Well"] = df["SubAcctDesc"].fillna("Unknown").astype(str).str.strip()

    if "AcqCode" not in df.columns:
        df["AcqCode"] = "Unknown"

    if "Period" not in df.columns and "EffDate" in df.columns:
        eff = pd.to_datetime(df["EffDate"], errors="coerce")
        df["EffDate"] = eff
        df["Period"] = eff.dt.to_period("M").astype(str)

    if "Bucket" not in df.columns and "Account" in df.columns:
        acct_num = pd.to_numeric(df["Account"], errors="coerce")
        df["Bucket"] = acct_num.apply(
            lambda a: _expense_bucket(int(a)) if pd.notna(a) and _is_expense(int(a)) else "Revenue"
        )

    if "AccountDesc" not in df.columns:
        df["AccountDesc"] = ""

    if "Company" not in df.columns:
        df["Company"] = "Unknown"

    if "AmountAdj" not in df.columns and "Amount" in df.columns:
        df["AmountAdj"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)

    if "QtyAdj" not in df.columns:
        if "Quantity" in df.columns:
            df["QtyAdj"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0.0)
        else:
            df["QtyAdj"] = 0.0


def _ss() -> Dict:
    if "gl_app" not in st.session_state:
        st.session_state["gl_app"] = {
            "df": None,
            "file_hashes": set(),
            "load_errors": [],
            "files_metadata": [],
        }

        try:
            if CACHE_FILE.exists():
                cached = pd.read_parquet(CACHE_FILE)
                _backfill(cached)
                st.session_state["gl_app"]["df"] = cached
                logger.info("Loaded cache with %s rows", len(cached))

            if META_FILE.exists():
                meta = json.loads(META_FILE.read_text())
                file_list = meta.get("files", [])
                st.session_state["gl_app"]["file_hashes"] = {
                    f.get("hash") for f in file_list if f.get("hash")
                }
                st.session_state["gl_app"]["files_metadata"] = file_list
                logger.info("Loaded metadata for %s files", len(file_list))
        except Exception as e:
            logger.warning("Failed to load cache: %s", e)

    return st.session_state["gl_app"]


def _normalize(df: pd.DataFrame, filename: str = "") -> pd.DataFrame:
    df = df.copy()

    # Clean incoming column names first
    df.columns = [_clean_col(c) for c in df.columns]

    # Resolve aliases to canonical names
    rename_map = {}
    existing_cols = set(df.columns)

    for canon, aliases in COL_ALIASES.items():
        if canon in existing_cols:
            continue

        for alias in aliases:
            cleaned_alias = _clean_col(alias)
            if cleaned_alias in existing_cols:
                rename_map[cleaned_alias] = canon
                break

    df = df.rename(columns=rename_map)

    # Ensure optional cols exist
    if "SubAccount" not in df.columns:
        df["SubAccount"] = ""
    if "AccountDesc" not in df.columns:
        df["AccountDesc"] = ""
    if "AcqCode" not in df.columns:
        df["AcqCode"] = "Unknown"
    if "Quantity" not in df.columns:
        df["Quantity"] = 0.0

    required_cols = ["EffDate", "Account", "SubAcctDesc", "Amount"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Required columns not found: {', '.join(missing)}")

    df["EffDate"] = pd.to_datetime(df["EffDate"], errors="coerce")
    df["Account"] = pd.to_numeric(df["Account"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0.0)

    # Drop rows with invalid dates/accounts before int conversion
    df = df[df["EffDate"].notna() & df["Account"].notna()].copy()
    if df.empty:
        return df

    df["Account"] = df["Account"].astype(int)

    valid_mask = df["Account"].apply(lambda a: a in ALL_REV_ACCTS or _is_expense(a))
    df = df[valid_mask].copy()

    if df.empty:
        return df

    df["Period"] = df["EffDate"].dt.to_period("M").astype(str)
    df["Well"] = df["SubAcctDesc"].fillna("Unknown").astype(str).str.strip()

    df["SubAcctNum"] = (
        df["SubAccount"]
        .fillna("")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
    )

    df["AcqCode"] = df["AcqCode"].fillna("Unknown").astype(str).str.strip()
    df["AccountDesc"] = df["AccountDesc"].fillna("").astype(str).str.strip()
    df["Company"] = _extract_company(filename)

    # Flip revenue signs, leave deductions/expenses as-is
    df["AmountAdj"] = np.where(df["Account"].isin(REV_ACCOUNTS), -df["Amount"], df["Amount"])
    df["QtyAdj"] = np.where(df["Account"].isin(REV_ACCOUNTS), -df["Quantity"], df["Quantity"])

    df["Bucket"] = df["Account"].apply(
        lambda a: _expense_bucket(a) if _is_expense(a) else "Revenue"
    )

    return df.reset_index(drop=True)


def _save_local(
    df: pd.DataFrame,
    fhash: str,
    filename: str,
    rows: int,
    periods: int,
    wells: int,
) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(CACHE_FILE, index=False)

        meta = {"files": []}
        if META_FILE.exists():
            try:
                meta = json.loads(META_FILE.read_text())
            except Exception as e:
                logger.warning("Failed to load existing metadata: %s", e)
                meta = {"files": []}

        existing_hashes = {f.get("hash") for f in meta.get("files", [])}
        if fhash not in existing_hashes:
            meta["files"].append(
                {
                    "hash": fhash,
                    "filename": filename,
                    "company": _extract_company(filename),
                    "loaded_at": datetime.now().isoformat(),
                    "rows": rows,
                    "periods": periods,
                    "wells": wells,
                }
            )
            META_FILE.write_text(json.dumps(meta, indent=2))
            logger.info("Saved metadata for %s. Total files: %s", filename, len(meta["files"]))

    except Exception as e:
        logger.error("Failed to save local cache: %s", e)


def ingest_file(uploaded_file) -> Dict:
    try:
        file_bytes = uploaded_file.read()
        fhash = _hash_file(file_bytes)
        ss = _ss()

        if fhash in ss["file_hashes"]:
            return {"status": "duplicate"}

        ext = Path(uploaded_file.name).suffix.lower()

        try:
            if ext in (".xlsx", ".xls"):
                raw = pd.read_excel(BytesIO(file_bytes))
            elif ext == ".csv":
                raw = pd.read_csv(BytesIO(file_bytes))
            else:
                return {"status": "error", "message": f"Unsupported file type: {ext}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to read file: {str(e)}"}

        try:
            new_df = _normalize(raw, uploaded_file.name)
        except ValueError as e:
            return {"status": "error", "message": str(e)}

        if new_df.empty:
            return {"status": "error", "message": "No recognized GL accounts found in file."}

        rows = len(new_df)
        periods = new_df["Period"].nunique()
        wells = new_df["Well"].nunique()

        if ss["df"] is None or ss["df"].empty:
            ss["df"] = new_df.reset_index(drop=True)
        else:
            combined = pd.concat([ss["df"], new_df], ignore_index=True)

            # Use a safer duplicate key so different companies/acq/subaccounts do not get collapsed
            dedupe_cols = [
                "Company",
                "Period",
                "Account",
                "SubAcctNum",
                "Well",
                "AcqCode",
                "Amount",
                "Quantity",
            ]
            dedupe_cols = [c for c in dedupe_cols if c in combined.columns]

            ss["df"] = (
                combined
                .drop_duplicates(subset=dedupe_cols, keep="last")
                .reset_index(drop=True)
            )

        ss["file_hashes"].add(fhash)
        _save_local(ss["df"], fhash, uploaded_file.name, rows, periods, wells)

        logger.info(
            "Ingested %s: %s rows, %s periods, %s wells",
            uploaded_file.name,
            rows,
            periods,
            wells,
        )
        return {"status": "ok", "rows": rows, "months": periods, "wells": wells}

    except Exception as e:
        logger.error("Unexpected error in ingest_file: %s", e)
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


def load_all_data() -> Optional[pd.DataFrame]:
    return _ss()["df"]


def get_summary(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    rev = df[df["Bucket"] == "Revenue"].copy()
    if rev.empty:
        return pd.DataFrame()

    rows = []
    for (well, period, acq), grp in rev.groupby(["Well", "Period", "AcqCode"], dropna=False):
        r = {"Well": well, "Period": period, "AcqCode": acq}

        r["Oil_Gross"] = grp.loc[grp["Account"] == 9601, "AmountAdj"].sum()
        r["Gas_Gross"] = grp.loc[grp["Account"] == 9621, "AmountAdj"].sum()
        r["Plant_Gross"] = grp.loc[grp["Account"] == 9631, "AmountAdj"].sum()

        r["Oil_Tax"] = grp.loc[grp["Account"] == 9602, "AmountAdj"].sum()
        r["Gas_Tax"] = grp.loc[grp["Account"] == 9622, "AmountAdj"].sum()
        r["Gas_Comp"] = grp.loc[grp["Account"] == 9627, "AmountAdj"].sum()
        r["Gas_LowVol"] = grp.loc[grp["Account"] == 9630, "AmountAdj"].sum()
        r["Plant_Tax"] = grp.loc[grp["Account"] == 9632, "AmountAdj"].sum()
        r["Plant_Deduct"] = grp.loc[grp["Account"] == 9636, "AmountAdj"].sum()
        r["Rejected_Fee"] = grp.loc[grp["Account"] == 9615, "AmountAdj"].sum()

        r["Oil_BBL"] = grp.loc[grp["Account"] == 9601, "QtyAdj"].sum()
        r["Gas_MCF"] = grp.loc[grp["Account"] == 9621, "QtyAdj"].sum()
        r["Plant_GAL"] = grp.loc[grp["Account"] == 9631, "QtyAdj"].sum()

        r["Gross_Revenue"] = r["Oil_Gross"] + r["Gas_Gross"] + r["Plant_Gross"]
        r["Total_Deductions"] = (
            r["Oil_Tax"]
            + r["Gas_Tax"]
            + r["Gas_Comp"]
            + r["Gas_LowVol"]
            + r["Plant_Tax"]
            + r["Plant_Deduct"]
            + r["Rejected_Fee"]
        )
        r["Net_Revenue"] = r["Gross_Revenue"] - r["Total_Deductions"]

        rows.append(r)

    return pd.DataFrame(rows)


def get_expense_summary(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    exp = df[df["Bucket"] != "Revenue"].copy()
    if exp.empty:
        return pd.DataFrame()

    rows = []
    for (well, period, bucket), grp in exp.groupby(["Well", "Period", "Bucket"], dropna=False):
        rows.append(
            {
                "Well": well,
                "Period": period,
                "Bucket": bucket,
                "Amount": grp["AmountAdj"].sum(),
            }
        )

    return pd.DataFrame(rows)
