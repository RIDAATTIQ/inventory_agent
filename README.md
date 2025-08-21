# Inventory Agent (CLI + Optional Gemini Assist)

A simple, production-ready inventory CLI in Python that supports **add, subtract, update, delete, list, import, export**, and an optional **natural-language agent** powered by Google Gemini.

## Features
- SQLite database (`inventory.db`) — no server needed.
- Idempotent schema creation.
- Commands via `typer` CLI.
- CSV import/export.
- Validations: non-negative quantities, existence checks.
- Optional Gemini-powered natural language parser (`agent` command).

## Quick Start (Windows PowerShell friendly)
```powershell
# 1) Create & activate virtual environment (if not already)
python -m venv .venv
.\.venv\Scripts\activate

# 2) Install requirements
pip install -r requirements.txt

# 3) (Optional) Put your Gemini API Key in .env
# Create a .env file with:
# GEMINI_API_KEY=your_key_here

# 4) Initialize DB and try some commands
python -m inventory add --sku A100 --name "Apple" --qty 50 --price 150
python -m inventory add --sku O200 --name "Orange" --qty 30 --price 120
python -m inventory list
python -m inventory subtract --sku A100 --qty 5
python -m inventory update --sku O200 --price 130
python -m inventory delete --sku O200
python -m inventory list

# Natural-language (optional, requires GEMINI_API_KEY):
python -m inventory agent "Add 20 bananas with sku B300 price 90"
python -m inventory agent "subtract 3 from sku A100"
```

## Commands
- `add` — Add a new item.
- `subtract` — Decrease quantity of an item.
- `update` — Update name/price/quantity of an item.
- `delete` — Delete an item by SKU.
- `list` — Show all items (or a single SKU).
- `import-csv` — Bulk import items from CSV.
- `export-csv` — Export items to CSV.
- `agent` — Parse natural language to actions (Gemini if available, else rule-based fallback).

## CSV Format
For import: headers must be `sku,name,quantity,price`.
