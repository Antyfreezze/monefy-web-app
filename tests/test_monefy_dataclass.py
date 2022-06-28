"""Monefy Application unittests for MonefyBalance class"""

from src.domain.data_aggregator import MonefyBalance


def test_monefy_balance_class(monefy_data):
    """Test MonefyBalance class current balance calculation method"""
    monefy_balance = MonefyBalance(monefy_data)
    assert monefy_balance.income == 7404
    assert monefy_balance.expense == -5093
    assert monefy_balance.balance == 2311
