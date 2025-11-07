"""Run Tests on the Splitwise Plugin."""

import datetime
import json
import logging
from os import path

import pytest
import splitwise

from lunchable_splitlunch.lunchmoney_splitwise import (
    SplitLunch,
    _calculate_self_paid_splits,
    _get_splitwise_impact,
)
from lunchable_splitlunch.models import SplitLunchExpense, SplitLunchExpenseUserShare
from tests.conftest import lunchable_cassette

logger = logging.getLogger(__name__)


@pytest.mark.filterwarnings("ignore:datetime.datetime.utcfromtimestamp")
@lunchable_cassette
def test_update_balance() -> None:
    """
    Update the Balance
    """
    lunch = SplitLunch()
    lunch.update_splitwise_balance()


@pytest.mark.filterwarnings("ignore:datetime.datetime.utcfromtimestamp")
def test_financial_impact() -> None:
    """
    Test the financial impact algorithm
    """
    for [file, expected_self_paid, expected_impact] in [
        # For both expenses and transfers, when someone else pays,
        # financial impact should be positive
        ["splitwise_non_user_paid_expense.json", False, 9.99],
        ["splitwise_non_user_paid_transfer.json", False, 523.84],
        # When you pay, financial impact should be negative
        ["splitwise_user_paid_expense.json", True, -61.65],
        ["splitwise_user_paid_transfer.json", True, -431.92],
        # And any transaction that doesn't involve you should have no impact
        ["splitwise_non_involved_expense.json", False, 0],
        ["splitwise_non_involved_transfer.json", False, 0],
    ]:
        with open(path.join(path.dirname(__file__), f"data/{file}")) as json_file:
            expense = splitwise.Expense(json.load(json_file))
        financial_impact, self_paid = _get_splitwise_impact(
            expense=expense, current_user_id=1234059
        )
        assert (
            self_paid is expected_self_paid
        ), f"Expected {expected_self_paid} for {file}"
        assert (
            financial_impact == expected_impact
        ), f"Expected {expected_impact} for {file}"


def test_calculate_self_paid_splits() -> None:
    """Ensure self-paid expenses are split into personal and reimbursable portions."""

    now = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    expense = SplitLunchExpense(
        splitwise_id=1,
        original_amount=100.0,
        self_paid=True,
        financial_impact=-90.0,
        description="Example expense",
        category="General",
        details=None,
        payment=False,
        date=now,
        users=[
            SplitLunchExpenseUserShare(
                user_id=111,
                paid_share=100.0,
                owed_share=10.0,
                net_balance=90.0,
            ),
            SplitLunchExpenseUserShare(
                user_id=222,
                paid_share=0.0,
                owed_share=90.0,
                net_balance=-90.0,
            ),
        ],
        created_at=now,
        updated_at=now,
        deleted_at=None,
        deleted=False,
    )
    personal, reimbursable = _calculate_self_paid_splits(expense, current_user_id=111)
    assert personal == 10.0
    assert reimbursable == 90.0
