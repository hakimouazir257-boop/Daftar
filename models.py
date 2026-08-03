# models.py
# Plain data classes representing the app's core entities. These are kept
# framework-agnostic (no Kivy imports) so they can be reused by services,
# reports, and tests without pulling in the UI stack.

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List

from theme import (
    RATING_EXCELLENT,
    RATING_GOOD,
    RATING_AVERAGE,
    RATING_BAD,
)


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------
@dataclass
class Customer:
    id: Optional[int]
    name: str
    phone: str
    product_name: str
    product_price: float
    first_payment: float
    remaining_amount: float
    monthly_installment: float
    months_count: int
    receive_date: str          # ISO date string YYYY-MM-DD
    end_date: str               # computed
    rating: str = RATING_GOOD
    last_payment_date: Optional[str] = None
    created_at: Optional[str] = None

    @staticmethod
    def compute_remaining(product_price: float, first_payment: float) -> float:
        return max(0.0, round(product_price - first_payment, 2))

    @staticmethod
    def compute_end_date(receive_date: str, months_count: int) -> str:
        """Add `months_count` months to receive_date (ISO string)."""
        y, m, d = [int(p) for p in receive_date.split("-")]
        total = m - 1 + months_count
        y += total // 12
        m = total % 12 + 1
        # clamp day to a safe value (avoid Feb 30 issues)
        try:
            end = date(y, m, min(d, 28))
        except ValueError:
            end = date(y, m, 1)
        return end.isoformat()


# ---------------------------------------------------------------------------
# Installment
# ---------------------------------------------------------------------------
STATUS_PAID = "paid"
STATUS_UNPAID = "unpaid"
STATUS_LATE = "late"


@dataclass
class Installment:
    id: Optional[int]
    owner_id: int                # customer_id OR friend_transaction_id
    owner_type: str              # "customer" or "friend_transaction"
    installment_number: int
    due_date: str
    amount: float
    status: str = STATUS_UNPAID
    payment_date: Optional[str] = None

    def refresh_status(self, today: Optional[date] = None) -> None:
        """Recompute status (except 'paid', which is only set explicitly)."""
        if self.status == STATUS_PAID:
            return
        today = today or date.today()
        due = date.fromisoformat(self.due_date)
        self.status = STATUS_LATE if due < today else STATUS_UNPAID


# ---------------------------------------------------------------------------
# Friend / Friend Transaction
# ---------------------------------------------------------------------------
@dataclass
class Friend:
    id: Optional[int]
    name: str
    phone: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class FriendTransaction:
    id: Optional[int]
    friend_id: int
    customer_name: str
    customer_phone: str
    product_name: str
    product_price: float
    first_payment: float
    monthly_installment: float
    months_count: int
    created_at: str
    notes: Optional[str] = None
    remaining_amount: float = 0.0
    end_date: str = ""
    rating: str = RATING_GOOD
    last_payment_date: Optional[str] = None

    @staticmethod
    def compute_remaining(product_price: float, first_payment: float) -> float:
        return Customer.compute_remaining(product_price, first_payment)

    @staticmethod
    def compute_end_date(created_at: str, months_count: int) -> str:
        return Customer.compute_end_date(created_at, months_count)


# ---------------------------------------------------------------------------
# Rating logic - shared by customers and friend-transaction "customers"
# ---------------------------------------------------------------------------
def compute_rating(installments: List[Installment]) -> str:
    """
    Very small heuristic rating engine:
      - excellent: no late installments ever, majority already paid on time
      - good: at most 1 late installment historically, none currently late
      - average: 2-3 late installments, or 1 currently late
      - bad: more than 3 late (ever) or 2+ currently late
    """
    if not installments:
        return RATING_GOOD

    today = date.today()
    currently_late = 0
    ever_late = 0

    for inst in installments:
        due = date.fromisoformat(inst.due_date)
        if inst.status == STATUS_LATE or (inst.status != STATUS_PAID and due < today):
            currently_late += 1
        if inst.status == STATUS_PAID and inst.payment_date:
            paid_on = date.fromisoformat(inst.payment_date)
            if paid_on > due:
                ever_late += 1
        elif inst.status == STATUS_LATE:
            ever_late += 1

    if currently_late >= 2 or ever_late > 3:
        return RATING_BAD
    if currently_late == 1 or (2 <= ever_late <= 3):
        return RATING_AVERAGE
    if ever_late == 1:
        return RATING_GOOD
    return RATING_EXCELLENT
