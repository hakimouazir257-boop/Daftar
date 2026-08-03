# database.py
# SQLite persistence layer for the "Daftar" app.
# All tables are created automatically on first run. This module exposes a
# single `Database` class used by the whole application (screens, services,
# reports) so there is one source of truth for data access.

import os
import sqlite3
from datetime import date, datetime
from typing import List, Optional, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "assets", "database", "daftar.db")


class Database:
    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def create_tables(self) -> None:
        cur = self.conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                product_name TEXT,
                product_price REAL NOT NULL DEFAULT 0,
                first_payment REAL NOT NULL DEFAULT 0,
                remaining_amount REAL NOT NULL DEFAULT 0,
                monthly_installment REAL NOT NULL DEFAULT 0,
                months_count INTEGER NOT NULL DEFAULT 0,
                receive_date TEXT,
                end_date TEXT,
                rating TEXT DEFAULT 'good',
                last_payment_date TEXT,
                created_at TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS installments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                owner_type TEXT NOT NULL DEFAULT 'customer', -- 'customer' | 'friend_transaction'
                installment_number INTEGER NOT NULL,
                due_date TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'unpaid',
                payment_date TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                created_at TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS friend_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                friend_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                product_name TEXT,
                product_price REAL NOT NULL DEFAULT 0,
                first_payment REAL NOT NULL DEFAULT 0,
                remaining_amount REAL NOT NULL DEFAULT 0,
                monthly_installment REAL NOT NULL DEFAULT 0,
                months_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT,
                end_date TEXT,
                rating TEXT DEFAULT 'good',
                last_payment_date TEXT,
                notes TEXT,
                FOREIGN KEY (friend_id) REFERENCES friends(id) ON DELETE CASCADE
            )
            """
        )

        self.conn.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return dict(row) if row is not None else None

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------
    def add_customer(self, data: Dict[str, Any]) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO customers
            (name, phone, product_name, product_price, first_payment,
             remaining_amount, monthly_installment, months_count,
             receive_date, end_date, rating, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"], data.get("phone", ""), data.get("product_name", ""),
                data.get("product_price", 0), data.get("first_payment", 0),
                data.get("remaining_amount", 0), data.get("monthly_installment", 0),
                data.get("months_count", 0), data.get("receive_date", ""),
                data.get("end_date", ""), data.get("rating", "good"),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        self.conn.commit()
        customer_id = cur.lastrowid
        self._generate_installments(customer_id, "customer", data)
        return customer_id

    def _generate_installments(self, owner_id: int, owner_type: str, data: Dict[str, Any]) -> None:
        from models import Customer  # local import to avoid circularity at module load
        months = int(data.get("months_count", 0) or 0)
        monthly = float(data.get("monthly_installment", 0) or 0)
        start = data.get("receive_date") or date.today().isoformat()
        y, m, d = [int(p) for p in start.split("-")]
        cur = self.conn.cursor()
        for i in range(1, months + 1):
            total = (m - 1) + i
            ny = y + total // 12
            nm = total % 12 + 1
            try:
                due = date(ny, nm, min(d, 28)).isoformat()
            except ValueError:
                due = date(ny, nm, 1).isoformat()
            cur.execute(
                """
                INSERT INTO installments (owner_id, owner_type, installment_number,
                                           due_date, amount, status)
                VALUES (?, ?, ?, ?, ?, 'unpaid')
                """,
                (owner_id, owner_type, i, due, monthly),
            )
        self.conn.commit()

    def get_customers(self, search: str = "") -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        if search:
            like = f"%{search}%"
            cur.execute(
                "SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? ORDER BY id DESC",
                (like, like),
            )
        else:
            cur.execute("SELECT * FROM customers ORDER BY id DESC")
        return [self._row_to_dict(r) for r in cur.fetchall()]

    def get_customer(self, customer_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        return self._row_to_dict(cur.fetchone())

    def update_customer(self, customer_id: int, data: Dict[str, Any]) -> None:
        fields = ", ".join(f"{k} = ?" for k in data.keys())
        values = list(data.values()) + [customer_id]
        self.conn.execute(f"UPDATE customers SET {fields} WHERE id = ?", values)
        self.conn.commit()

    def delete_customer(self, customer_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        cur.execute(
            "DELETE FROM installments WHERE owner_id = ? AND owner_type = 'customer'",
            (customer_id,),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Installments (generic - shared by customers & friend transactions)
    # ------------------------------------------------------------------
    def get_installments(self, owner_id: int, owner_type: str = "customer") -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT * FROM installments WHERE owner_id = ? AND owner_type = ?
            ORDER BY installment_number ASC
            """,
            (owner_id, owner_type),
        )
        return [self._row_to_dict(r) for r in cur.fetchall()]

    def mark_installment_paid(self, installment_id: int) -> Dict[str, Any]:
        """Mark an installment as paid 'today', update owner's last_payment_date
        and rating. Returns the updated installment row."""
        cur = self.conn.cursor()
        today_iso = date.today().isoformat()
        cur.execute(
            "UPDATE installments SET status = 'paid', payment_date = ? WHERE id = ?",
            (today_iso, installment_id),
        )
        self.conn.commit()

        cur.execute("SELECT * FROM installments WHERE id = ?", (installment_id,))
        inst = self._row_to_dict(cur.fetchone())

        self._refresh_owner_after_payment(inst["owner_id"], inst["owner_type"], today_iso)
        return inst

    def _refresh_owner_after_payment(self, owner_id: int, owner_type: str, payment_date: str) -> None:
        from models import Installment, compute_rating

        rows = self.get_installments(owner_id, owner_type)
        installments = [
            Installment(
                id=r["id"], owner_id=r["owner_id"], owner_type=r["owner_type"],
                installment_number=r["installment_number"], due_date=r["due_date"],
                amount=r["amount"], status=r["status"], payment_date=r["payment_date"],
            )
            for r in rows
        ]
        rating = compute_rating(installments)

        table = "customers" if owner_type == "customer" else "friend_transactions"
        self.conn.execute(
            f"UPDATE {table} SET last_payment_date = ?, rating = ? WHERE id = ?",
            (payment_date, rating, owner_id),
        )
        self.conn.commit()

    def refresh_late_statuses(self) -> None:
        """Call periodically (e.g. on app start) to flag overdue unpaid
        installments as 'late'."""
        today_iso = date.today().isoformat()
        self.conn.execute(
            """
            UPDATE installments SET status = 'late'
            WHERE status = 'unpaid' AND due_date < ?
            """,
            (today_iso,),
        )
        self.conn.commit()

    def get_due_today(self) -> List[Dict[str, Any]]:
        today_iso = date.today().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM installments WHERE due_date = ? AND status != 'paid'",
            (today_iso,),
        )
        return [self._row_to_dict(r) for r in cur.fetchall()]

    def get_late_installments(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM installments WHERE status = 'late'")
        return [self._row_to_dict(r) for r in cur.fetchall()]

    def get_week_installments(self) -> List[Dict[str, Any]]:
        from datetime import timedelta
        today = date.today()
        end = today + timedelta(days=7)
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM installments WHERE due_date BETWEEN ? AND ? AND status != 'paid'",
            (today.isoformat(), end.isoformat()),
        )
        return [self._row_to_dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # Friends
    # ------------------------------------------------------------------
    def add_friend_if_missing(self, name: str, phone: str = "") -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM friends WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur.execute(
            "INSERT INTO friends (name, phone, created_at) VALUES (?, ?, ?)",
            (name, phone, datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_friends(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM friends ORDER BY id DESC")
        return [self._row_to_dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # Friend transactions
    # ------------------------------------------------------------------
    def add_friend_transaction(self, data: Dict[str, Any]) -> int:
        friend_id = data.get("friend_id")
        if not friend_id:
            friend_id = self.add_friend_if_missing(
                data.get("friend_name", "").strip(), data.get("friend_phone", "")
            )

        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO friend_transactions
            (friend_id, customer_name, customer_phone, product_name, product_price,
             first_payment, remaining_amount, monthly_installment, months_count,
             created_at, end_date, rating, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                friend_id, data["customer_name"], data.get("customer_phone", ""),
                data.get("product_name", ""), data.get("product_price", 0),
                data.get("first_payment", 0), data.get("remaining_amount", 0),
                data.get("monthly_installment", 0), data.get("months_count", 0),
                data.get("created_at", date.today().isoformat()),
                data.get("end_date", ""), data.get("rating", "good"),
                data.get("notes", ""),
            ),
        )
        self.conn.commit()
        transaction_id = cur.lastrowid

        gen_data = dict(data)
        gen_data["receive_date"] = data.get("created_at", date.today().isoformat())
        self._generate_installments(transaction_id, "friend_transaction", gen_data)
        return transaction_id

    def get_friend_transactions(self, search: str = "") -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        query = """
            SELECT ft.*, f.name AS friend_name, f.phone AS friend_phone
            FROM friend_transactions ft
            JOIN friends f ON f.id = ft.friend_id
        """
        params: tuple = ()
        if search:
            like = f"%{search}%"
            query += " WHERE f.name LIKE ? OR ft.customer_name LIKE ? OR ft.customer_phone LIKE ?"
            params = (like, like, like)
        query += " ORDER BY ft.id DESC"
        cur.execute(query, params)
        return [self._row_to_dict(r) for r in cur.fetchall()]

    def get_friend_transaction(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT ft.*, f.name AS friend_name, f.phone AS friend_phone
            FROM friend_transactions ft
            JOIN friends f ON f.id = ft.friend_id
            WHERE ft.id = ?
            """,
            (transaction_id,),
        )
        return self._row_to_dict(cur.fetchone())

    def update_friend_transaction(self, transaction_id: int, data: Dict[str, Any]) -> None:
        fields = ", ".join(f"{k} = ?" for k in data.keys())
        values = list(data.values()) + [transaction_id]
        self.conn.execute(f"UPDATE friend_transactions SET {fields} WHERE id = ?", values)
        self.conn.commit()

    def delete_friend_transaction(self, transaction_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM friend_transactions WHERE id = ?", (transaction_id,))
        cur.execute(
            "DELETE FROM installments WHERE owner_id = ? AND owner_type = 'friend_transaction'",
            (transaction_id,),
        )
        self.conn.commit()

    def get_friends_report(self) -> List[Dict[str, Any]]:
        """Aggregated per-friend statistics for the friends report screen."""
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT f.id AS friend_id, f.name AS friend_name,
                   COUNT(ft.id) AS customers_count,
                   COALESCE(SUM(ft.product_price), 0) AS total_amount,
                   SUM(CASE WHEN ft.rating = 'bad' THEN 1 ELSE 0 END) AS late_customers
            FROM friends f
            LEFT JOIN friend_transactions ft ON ft.friend_id = f.id
            GROUP BY f.id
            ORDER BY customers_count DESC
            """
        )
        return [self._row_to_dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # Global stats (home screen + reports)
    # ------------------------------------------------------------------
    def get_dashboard_stats(self) -> Dict[str, Any]:
        cur = self.conn.cursor()
        stats: Dict[str, Any] = {}

        cur.execute("SELECT COUNT(*) AS c FROM customers")
        stats["customers_count"] = cur.fetchone()["c"]

        today_iso = date.today().isoformat()
        cur.execute(
            "SELECT COUNT(*) AS c FROM installments WHERE due_date = ? AND status != 'paid'",
            (today_iso,),
        )
        stats["due_today"] = cur.fetchone()["c"]

        cur.execute("SELECT COUNT(*) AS c FROM installments WHERE status = 'late'")
        stats["late_count"] = cur.fetchone()["c"]

        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM installments WHERE status = 'paid'"
        )
        stats["collected_total"] = cur.fetchone()["s"]

        return stats

    def get_full_report(self) -> Dict[str, Any]:
        cur = self.conn.cursor()
        report: Dict[str, Any] = {}

        cur.execute("SELECT COUNT(*) AS c FROM customers")
        report["customers_count"] = cur.fetchone()["c"]

        cur.execute("SELECT COALESCE(SUM(product_price), 0) AS s FROM customers")
        report["total_money"] = cur.fetchone()["s"]

        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM installments "
            "WHERE status = 'paid' AND owner_type = 'customer'"
        )
        report["collected_money"] = cur.fetchone()["s"]

        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS s FROM installments "
            "WHERE status != 'paid' AND owner_type = 'customer'"
        )
        report["remaining_money"] = cur.fetchone()["s"]

        cur.execute(
            "SELECT COUNT(*) AS c FROM customers WHERE rating IN ('excellent', 'good')"
        )
        report["committed_customers"] = cur.fetchone()["c"]

        cur.execute(
            "SELECT COUNT(*) AS c FROM customers WHERE rating IN ('average', 'bad')"
        )
        report["late_customers"] = cur.fetchone()["c"]

        return report

    def close(self) -> None:
        self.conn.close()
