# Oil & Gas Revenue Dashboard

Interactive Streamlit dashboard for analyzing oil & gas GL revenue data.
Upload monthly GL exports (Excel/CSV) and explore revenue trends, commodity
mix, deduction bridges, well rankings, and production volumes.

## Features

- **Multi-file upload** — drop in a new GL export each month; data merges automatically
- **Duplicate detection** — re-uploading the same file is safely ignored
- **Multiple property sets** — supports different well sets across GL dumps
- **Well filter** — search + multiselect across all wells in the loaded data
- **AcqCode / property group filter** — filter by acquisition code to isolate portfolios
- **5 analysis views**: Revenue Trend, Commodity Mix, Deduction Bridge, Well Rankings, Volumes

## Setup

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd gl_revenue_app

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens at http://localhost:8501

## Usage

1. Open the app in your browser
2. Use the **Upload GL Dump** panel in the sidebar to upload your first file
3. Each subsequent month, drop in the new GL export — it merges automatically
4. Use the **Filters** panel to narrow by property group, individual wells, or date range

## Supported GL Format

The app expects a GL export with these key columns (column names may include
curly braces `{ColName}` — both styles are handled automatically):

| Column | Description |
|---|---|
| `EffDate` | Effective date of journal entry |
| `Account` | GL account number |
| `{Account Desc}` | Account description |
| `{SubAccount Desc}` | Well / sub-account name |
| `Amount` | Dollar amount (negative = revenue credit) |
| `Quantity` | Volume quantity |
| `{AcqCode}` | Acquisition code / property group |

### Revenue accounts recognized

| Account | Description |
|---|---|
| 9601 | Oil Sales |
| 9602 | Oil Production Tax |
| 9615 | Rejected Load Fee |
| 9621 | Gas Sales |
| 9622 | Gas Production Tax |
| 9627 | Compression & Treating |
| 9630 | Gas Low Volume Fee |
| 9631 | Plant Sales |
| 9632 | Plant Production Tax |
| 9636 | Plant Other Deduction |

> **Different account numbers?** Edit the `REV_ACCOUNTS` and `DED_ACCOUNTS`
> dictionaries in `data_loader.py`.

## Data Storage

Uploaded data is cached locally in the `data/` directory as a Parquet file.
This directory is excluded from git (see `.gitignore`).

To reset all data: delete `data/gl_cache.parquet` and `data/uploaded_files.json`.

## Extending

- **Add expense categories (LOE, Workover, CAPEX)**: add their account numbers to
  `data_loader.py` and create a new page in `pages/` using `app.py` as a template.
- **Deploy to Streamlit Cloud**: push to GitHub, connect the repo at share.streamlit.io,
  and set `data/` as a persistent volume (or use a database backend like SQLite).
