import sqlite3, time
from pathlib import Path
from typing import List, Dict, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    sku TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity >= 0),
    price REAL NOT NULL CHECK(price >= 0),
    updated_at TEXT NOT NULL
);
"""

class Store:
    def __init__(self, db_path: Path):
        self.db_path = str(db_path)
        self._ensure_schema()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self):
        with self._conn() as conn:
            conn.execute(SCHEMA)

    def add_item(self, sku: str, name: str, quantity: int, price: float):
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        with self._conn() as conn:
            # Check existence
            cur = conn.execute("SELECT sku FROM items WHERE sku=?", (sku,))
            if cur.fetchone():
                raise ValueError(f"SKU '{sku}' already exists. Use update instead.")
            conn.execute("INSERT INTO items (sku, name, quantity, price, updated_at) VALUES (?,?,?,?,?)",
                         (sku, name, quantity, price, now))

    def add_or_update(self, sku: str, name: str, quantity: int, price: float):
        try:
            self.add_item(sku, name, quantity, price)
        except ValueError:
            self.update_item(sku, name=name, quantity=quantity, price=price)

    def subtract_quantity(self, sku: str, qty: int) -> int:
        with self._conn() as conn:
            cur = conn.execute("SELECT quantity FROM items WHERE sku=?", (sku,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"SKU '{sku}' not found.")
            current = row[0]
            if qty > current:
                raise ValueError(f"Cannot subtract {qty}; only {current} in stock.")
            new_q = current - qty
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            conn.execute("UPDATE items SET quantity=?, updated_at=? WHERE sku=?", (new_q, now, sku))
            return new_q

    def update_item(self, sku: str, name: Optional[str]=None, quantity: Optional[int]=None, price: Optional[float]=None):
        if name is None and quantity is None and price is None:
            return
        with self._conn() as conn:
            cur = conn.execute("SELECT sku FROM items WHERE sku=?", (sku,))
            if not cur.fetchone():
                raise ValueError(f"SKU '{sku}' not found.")
            fields = []
            params = []
            if name is not None:
                fields.append("name=?"); params.append(name)
            if quantity is not None:
                if quantity < 0:
                    raise ValueError("Quantity must be >= 0")
                fields.append("quantity=?"); params.append(quantity)
            if price is not None:
                if price < 0:
                    raise ValueError("Price must be >= 0")
                fields.append("price=?"); params.append(price)
            fields.append("updated_at=?"); params.append(time.strftime('%Y-%m-%d %H:%M:%S'))
            params.append(sku)
            sql = f"UPDATE items SET {', '.join(fields)} WHERE sku=?"
            conn.execute(sql, tuple(params))

    def delete_item(self, sku: str):
        with self._conn() as conn:
            cur = conn.execute("SELECT sku FROM items WHERE sku=?", (sku,))
            if not cur.fetchone():
                raise ValueError(f"SKU '{sku}' not found.")
            conn.execute("DELETE FROM items WHERE sku=?", (sku,))

    def list_items(self):
        with self._conn() as conn:
            cur = conn.execute("SELECT sku, name, quantity, price, updated_at FROM items ORDER BY sku")
            rows = [dict(zip([c[0] for c in cur.description], r)) for r in cur.fetchall()]
            return rows

    def get_item(self, sku: str):
        with self._conn() as conn:
            cur = conn.execute("SELECT sku, name, quantity, price, updated_at FROM items WHERE sku=?", (sku,))
            r = cur.fetchone()
            if not r:
                return None
            return dict(zip([c[0] for c in cur.description], r))
