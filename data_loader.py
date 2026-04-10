"""
data_loader.py — GL ingestion, normalization, caching (revenue + expenses)
Production-grade data pipeline with validation, error handling, and performance optimizations
"""

import json
import hashlib
import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, Tuple, Set

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
REV_ACCOUNTS = {9601, 9621, 9631}  # Oil, Gas, Plant gross revenue
DED_ACCOUNTS = {9602, 9615, 9622, 9627, 9630, 9632, 9636}  # Taxes, fees, compression
ALL_REV_ACCTS = REV_ACCOUNTS | DED_ACCOUNTS

# ── Expense buckets ───────────────────────────────────────────────────────────
LOE_RANGE = (9000, 9099)  # Lease operating expenses
LEASEHOLD_RANGE = (9100, 9199)  # Leasehold costs
CAPITAL_RANGE = (9200, 9399)  # Capital expenditures
WORKOVER_RANGE = (9500, 9598)  # Workover / repair costs
IGNORE_ACCTS = {9599}  # JIB billing — excluded from analysis

ALL_EXP_ACCTS = set(
    list(range(LOE_RANGE[0], LOE_RANGE[1] + 1))
    + list(range(LEASEHOLD_RANGE[0], LEASEHOLD_RANGE[1] + 1))
    + list(range(CAPITAL_RANGE[0], CAPITAL_RANGE[1] + 1))
    + list(range(WORKOVER_RANGE[0], WORKOVER_RANGE[1] + 1))
) - IGNORE_ACCTS

ALL_ACCTS = ALL_REV_ACCTS | ALL_EXP_ACCTS

# ── Column mapping with aliases ───────────────────────────────────────────────
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


# ── Helper functions ──────────────────────────────────────────────────────────
def _is_expense(acct: int) -> bool:
    """Check if account number is an expense account."""
    if acct in IGNORE_ACCTS:
        return False
    return (
        LOE_RANGE[0] <= acct <= LOE_RANGE[1]
        or LEASEHOLD_RANGE[0] <= acct <= LEASEHOLD_RANGE[1]
        or CAPITAL_RANGE[0] <= acct <= CAPITAL_RANGE[1]
        or WORKOVER_RANGE[0] <= acct <= WORKOVER_RANGE[1]
    )


def _expense_bucket(acct: int) -> str:
    """Classify expense account into bucket."""
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
    """Extract company code from filename (e.g., '40ACR_FEB_REV.xlsx' -> '40ACR')"""
    filename_upper = str(filename).upper()
    if "40ACR" in filename_upper:
        return "40ACR"
    elif "FAEII" in filename_upper:
        return "FAEII"
    return "Unknown"


def _clean_col(name: str) -> str:
    """Strip curly braces and whitespace from column name."""
    return str(name).strip("{}").strip()


def _hash_file(file_bytes: bytes) -> str:
    """Generate MD5 hash of file contents."""
    return hashlib.md5(file_bytes).hexdigest()


# ── Session state management ──────────────────────────────────────────────────
def _ss() -> Dict:
    """Initialize and return session state."""
    if "gl_app" not in st.session_state:
        st.session_state["gl_app"] = {"df": None, "file_hashes": set(), "load_errors": []}
        try:
            if CACHE_FILE.exists():
                cached = pd.read_parquet(CACHE_FILE)
                _backfill(cached)
                st.session_state["gl_app"]["df"] = cached
                logger.info(f"Loaded cache with {len(cached)} rows")

            if META_FILE.exists():
                meta = json.loads(META_FILE.read_text())
                st.session_state["gl_app"]["file_hashes"] = {f["hash"] for f in meta.get("files", [])}
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")

    return st.session_state["gl_app"]


def _backfill(df: pd.DataFrame) -> None:
    """Ensure all required columns exist with sensible defaults."""
    if "SubAccount" not in df.columns:
        df["SubAccount"] = ""
    if "SubAcctNum" not in df.columns:
        df["SubAcctNum"] = (
            df["SubAccount"].astype(str).str.strip().replace("", "Unknown").fillna("Unknown")
        )
    if "Well" not in df.columns and "SubAcctDesc" in df.columns:
        df["Well"] = df["SubAcctDesc"].fillna("Unknown").astype(str).str.strip()
    if "AcqCode" not in df.columns:
        df["AcqCode"] = "Unknown"
    if "Period" not in df.columns and "EffDate" in df.columns:
        df["EffDate"] = pd.to_datetime(df["EffDate"], errors="coerce")
        df["Period"] = df["EffDate"].dt.to_period("M").astype(str)
    if "Bucket" not in df.columns and "Account" in df.columns:
        df["Bucket"] = df["Account"].apply(
            lambda a: _expense_bucket(int(a)) if pd.notna(a) and _is_expense(int(a)) else "Revenue"
        )
    if "AccountDesc" not in df.columns:
        df["AccountDesc"] = ""
    if "Company" not in df.columns:
        df["Company"] = "Unknown"


def _normalize(df: pd.DataFrame, filename: str = "") -> pd.DataFrame:
    """
    Normalize GL export to standard schema.
    - Resolve column aliases
    - Type conversion
    - Sign adjustment for revenue accounts
    - Bucket classification
    """
    df = df.copy()

    # Strip {} from column names
    df = df.rename(columns={c: _clean_col(c) for c in df.columns})

    # Resolve column aliases to canonical names
    resolved = {}
    for canon, aliases in COL_ALIASES.items():
        cleaned_aliases = [_clean_col(a) for a in aliases]
        for alias in cleaned_aliases:
            if alias in df.columns:
                resolved[alias] = canon
                break

    df = df.rename(columns=resolved)

    # Ensure optional columns exist
    if "SubAccount" not in df.columns:
        df["SubAccount"] = ""
    if "AccountDesc" not in df.columns:
        df["AccountDesc"] = ""
    if "AcqCode" not in df.columns:
        df["AcqCode"] = "Unknown"

    # Validate required columns
    required_cols = ["EffDate", "Account", "SubAcctDesc", "Amount"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Required columns not found: {', '.join(missing)}")

    # Type conversions with error handling
    df["EffDate"] = pd.to_datetime(df["EffDate"], errors="coerce")
    df["Account"] = pd.to_numeric(df["Account"], errors="coerce").astype("Int64")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
    df["Quantity"] = pd.to_numeric(df.get("Quantity", 0), errors="coerce").fillna(0.0)

    # Filter to valid accounts (revenue + expense)
    valid_mask = df["Account"].apply(
        lambda a: pd.notna(a) and (int(a) in ALL_REV_ACCTS or _is_expense(int(a)))
    )
    df = df[valid_mask].copy()

    if df.empty:
        return df

    # Normalize text fields
    df["Period"] = df["EffDate"].dt.to_period("M").astype(str)
    df["Well"] = df["SubAcctDesc"].fillna("Unknown").astype(str).str.strip()
    df["SubAcctNum"] = (
        df["SubAccount"].astype(str).str.strip().replace("", "Unknown").fillna("Unknown")
    )
    df["AcqCode"] = df["AcqCode"].fillna("Unknown").astype(str).str.strip()
    df["AccountDesc"] = df["AccountDesc"].fillna("").astype(str).str.strip()
    df["Company"] = _extract_company(filename)

    # Adjust amounts: GL stores revenue as credits (negative), flip to positive
    df["AmountAdj"] = np.where(df["Account"].isin(REV_ACCOUNTS), -df["Amount"], df["Amount"])
    df["QtyAdj"] = np.where(df["Account"].isin(REV_ACCOUNTS), -df["Quantity"], df["Quantity"])

    # Classify into buckets
    df["Bucket"] = df["Account"].apply(
        lambda a: _expense_bucket(int(a)) if _is_expense(int(a)) else "Revenue"
    )

    return df


# ── File ingestion ────────────────────────────────────────────────────────────
def ingest_file(uploaded_file) -> Dict:
    """
    Ingest GL export file (Excel or CSV).
    Returns metadata about successful load or error details.
    """
    try:
        file_bytes = uploaded_file.read()
        fhash = _hash_file(file_bytes)
        ss = _ss()

        # Check for duplicates
        if fhash in ss["file_hashes"]:
            return {"status": "duplicate"}

        # Read file
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

        # Normalize
        try:
            new_df = _normalize(raw, uploaded_file.name)
        except ValueError as e:
            return {"status": "error", "message": str(e)}

        if new_df.empty:
            return {"status": "error", "message": "No recognized GL accounts found in file."}

        rows = len(new_df)
        periods = new_df["Period"].nunique()
        wells = new_df["Well"].nunique()

        # Merge with existing data
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

        logger.info(
            f"Ingested {uploaded_file.name}: {rows} rows, {periods} periods, {wells} wells"
        )
        return {"status": "ok", "rows": rows, "months": periods, "wells": wells}

    except Exception as e:
        logger.error(f"Unexpected error in ingest_file: {e}")
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


def _save_local(
    df: pd.DataFrame, fhash: str, filename: str, rows: int, periods: int, wells: int
) -> None:
    """Persist dataframe and metadata locally."""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        df.to_parquet(CACHE_FILE, index=False)

        meta = {"files": []}
        if META_FILE.exists():
            meta = json.loads(META_FILE.read_text())

        company = _extract_company(filename)
        meta["files"].append(
            {
                "hash": fhash,
                "filename": filename,
                "company": company,
                "loaded_at": datetime.now().isoformat(),
                "rows": rows,
                "periods": periods,
                "wells": wells,
            }
        )
        META_FILE.write_text(json.dumps(meta, indent=2))
        logger.info(f"Saved cache and metadata to {DATA_DIR}")
    except Exception as e:
        logger.error(f"Failed to save local cache: {e}")


def load_all_data() -> Optional[pd.DataFrame]:
    """Load all cached data."""
    return _ss()["df"]


# ── Summary aggregations ──────────────────────────────────────────────────────
def get_summary(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    Aggregate revenue by well, period, and acquisition.
    Returns commodity breakdown (oil, gas, plant), taxes, volumes, and net revenue.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    rev = df[df["Bucket"] == "Revenue"].copy()
    if rev.empty:
        return pd.DataFrame()

    rows = []
    for (well, period, acq), grp in rev.groupby(["Well", "Period", "AcqCode"]):
        r = {"Well": well, "Period": period, "AcqCode": acq}

        # Commodity breakdown
        r["Oil_Gross"] = grp.loc[grp["Account"] == 9601, "AmountAdj"].sum()
        r["Gas_Gross"] = grp.loc[grp["Account"] == 9621, "AmountAdj"].sum()
        r["Plant_Gross"] = grp.loc[grp["Account"] == 9631, "AmountAdj"].sum()

        # Deductions
        r["Oil_Tax"] = grp.loc[grp["Account"] == 9602, "AmountAdj"].sum()
        r["Gas_Tax"] = grp.loc[grp["Account"] == 9622, "AmountAdj"].sum()
        r["Gas_Comp"] = grp.loc[grp["Account"] == 9627, "AmountAdj"].sum()
        r["Gas_LowVol"] = grp.loc[grp["Account"] == 9630, "AmountAdj"].sum()
        r["Plant_Tax"] = grp.loc[grp["Account"] == 9632, "AmountAdj"].sum()
        r["Plant_Deduct"] = grp.loc[grp["Account"] == 9636, "AmountAdj"].sum()
        r["Rejected_Fee"] = grp.loc[grp["Account"] == 9615, "AmountAdj"].sum()

        # Volumes
        r["Oil_BBL"] = grp.loc[grp["Account"] == 9601, "QtyAdj"].sum()
        r["Gas_MCF"] = grp.loc[grp["Account"] == 9621, "QtyAdj"].sum()
        r["Plant_GAL"] = grp.loc[grp["Account"] == 9631, "QtyAdj"].sum()

        # Aggregates
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
    """
    Aggregate expenses by well, period, and bucket (LOE, Leasehold, Capital, Workover).
    """
    if df is None or df.empty:
        return pd.DataFrame()

    exp = df[df["Bucket"] != "Revenue"].copy()
    if exp.empty:
        return pd.DataFrame()

    rows = []
    for (well, period, bucket), grp in exp.groupby(["Well", "Period", "Bucket"]):
        rows.append(
            {"Well": well, "Period": period, "Bucket": bucket, "Amount": grp["AmountAdj"].sum()}
        )

    return pd.DataFrame(rows)


def get_expense_detail(
    df: Optional[pd.DataFrame], well: Optional[str] = None, period: Optional[str] = None
) -> pd.DataFrame:
    """
    Return line-level expense rows with optional filtering by well and/or period.
    Useful for detailed account-level analysis.
    """
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


def get_data_quality_report(df: Optional[pd.DataFrame]) -> Dict:
    """
    Generate a data quality report with row counts, missing values, and account coverage.
    Useful for validating loaded data.
    """
    if df is None or df.empty:
        return {"status": "empty", "rows": 0, "issues": []}

    issues = []

    # Check for missing critical fields
    critical_cols = ["EffDate", "Account", "Amount", "Well", "Period"]
    for col in critical_cols:
        if col in df.columns:
            missing_pct = (df[col].isna().sum() / len(df)) * 100
            if missing_pct > 5:
                issues.append(f"{col} is {missing_pct:.1f}% missing")

    # Check for zero amounts
    if "AmountAdj" in df.columns:
        zero_pct = (df["AmountAdj"] == 0).sum() / len(df) * 100
        if zero_pct > 30:
            issues.append(f"{zero_pct:.1f}% of amounts are zero")

    # Account coverage
    accounts_found = df["Account"].dropna().nunique()
    accounts_expected = len(ALL_ACCTS)

    return {
        "status": "ok",
        "rows": len(df),
        "periods": df["Period"].nunique(),
        "wells": df["Well"].nunique(),
        "companies": df["Company"].nunique() if "Company" in df.columns else 0,
        "accounts_found": accounts_found,
        "accounts_expected": accounts_expected,
        "date_range": f"{df['EffDate'].min()} to {df['EffDate'].max()}"
        if "EffDate" in df.columns
        else "Unknown",
        "issues": issues,
    }
