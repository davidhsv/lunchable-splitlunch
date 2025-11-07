"""
SplitLunch Data Models
"""

import datetime
from typing import List, Optional

from lunchable.models import LunchableModel


class SplitLunchExpenseUserShare(LunchableModel):
    """SplitLunch representation of the shares for an expense participant."""

    user_id: int
    paid_share: float
    owed_share: float
    net_balance: float


class SplitLunchExpense(LunchableModel):
    """
    SplitLunch Object for Splitwise Expenses
    """

    splitwise_id: int
    original_amount: float
    self_paid: bool
    financial_impact: float
    description: str
    category: str
    details: Optional[str] = None
    payment: bool
    date: datetime.datetime
    users: List[SplitLunchExpenseUserShare]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    deleted_at: Optional[datetime.datetime] = None
    deleted: bool
