import typer
from .store import Store
from .agent import Agent, AgentParseError
from tabulate import tabulate
from pathlib import Path
import csv
import sys

app = typer.Typer(help="Inventory CLI (SQLite) with optional Gemini agent.")

def _store() -> Store:
    return Store(db_path=Path.cwd() / "inventory.db")

@app.command()
def add(sku: str = typer.Option(..., help="Unique SKU"),
        name: str = typer.Option(..., help="Item name"),
        qty: int = typer.Option(..., min=0, help="Starting quantity"),
        price: float = typer.Option(..., min=0.0, help="Unit price")):
    """Add a new item."""
    s = _store()
    s.add_item(sku, name, qty, price)
    typer.echo(f"✔ Added {sku} ({name}) qty={qty} price={price}")

@app.command()
def subtract(sku: str = typer.Option(..., help="SKU to subtract from"),
             qty: int = typer.Option(..., min=1, help="Quantity to subtract")):
    """Subtract quantity from an item."""
    s = _store()
    new_qty = s.subtract_quantity(sku, qty)
    typer.echo(f"✔ {sku} new quantity: {new_qty}")

@app.command()
def update(sku: str = typer.Option(..., help="SKU to update"),
           name: str = typer.Option(None, help="New name"),
           qty: int = typer.Option(None, help="New quantity (>=0)"),
           price: float = typer.Option(None, help="New unit price (>=0)")):
    """Update an item's fields."""
    s = _store()
    s.update_item(sku, name=name, quantity=qty, price=price)
    typer.echo(f"✔ Updated {sku}")

@app.command()
def delete(sku: str = typer.Option(..., help="SKU to delete")):
    """Delete an item by SKU."""
    s = _store()
    s.delete_item(sku)
    typer.echo(f"✔ Deleted {sku}")

@app.command(name="list")
def list_items(sku: str = typer.Option(None, help="If provided, show only this SKU")):
    """List items (optionally a single SKU)."""
    s = _store()
    rows = [s.get_item(sku)] if sku else s.list_items()
    if not rows:
        typer.echo("No items found.")
        raise typer.Exit(code=0)
    headers = ["sku", "name", "quantity", "price", "updated_at"]
    table = [ [r["sku"], r["name"], r["quantity"], r["price"], r["updated_at"]] for r in rows ]
    typer.echo(tabulate(table, headers=headers, tablefmt="github"))

@app.command()
def import_csv(path: str = typer.Option(..., help="CSV path with sku,name,quantity,price")):
    s = _store()
    count = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            s.add_or_update(row["sku"], row["name"], int(row["quantity"]), float(row["price"]))
            count += 1
    typer.echo(f"✔ Imported {count} rows.")

@app.command()
def export_csv(path: str = typer.Option("inventory_export.csv", help="Output CSV path")):
    s = _store()
    rows = s.list_items()
    if not rows:
        typer.echo("No items to export.")
        raise typer.Exit(code=0)
    headers = ["sku", "name", "quantity", "price"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in headers})
    typer.echo(f"✔ Exported {len(rows)} rows to {path}")

@app.command()
def agent(command: str = typer.Argument(..., help="Natural language command, e.g. 'add 5 apples with sku A1 price 10'")):
    s = _store()
    ag = Agent()
    try:
        action = ag.parse(command)
    except AgentParseError as e:
        typer.echo(f"✖ Could not parse command: {e}")
        raise typer.Exit(code=1)
    # Execute
    typ = action["type"]
    if typ == "add":
        s.add_item(action["sku"], action["name"], action["quantity"], action["price"])
        typer.echo(f"✔ Added {action['sku']} ({action['name']}) qty={action['quantity']} price={action['price']}")
    elif typ == "subtract":
        new_q = s.subtract_quantity(action["sku"], action["quantity"])
        typer.echo(f"✔ {action['sku']} new quantity: {new_q}")
    elif typ == "update":
        s.update_item(action["sku"], name=action.get("name"), quantity=action.get("quantity"), price=action.get("price"))
        typer.echo(f"✔ Updated {action['sku']}")
    elif typ == "delete":
        s.delete_item(action["sku"])
        typer.echo(f"✔ Deleted {action['sku']}")
    else:
        typer.echo(f"✖ Unknown action: {typ}")
        raise typer.Exit(code=1)
