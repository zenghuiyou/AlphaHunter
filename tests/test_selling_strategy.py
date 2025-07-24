import pytest
from datetime import datetime
from src.app.models import Position
from src.selling_strategy import check_stop_loss, check_take_profit

@pytest.fixture
def mock_position():
    """创建一个可供所有测试用例使用的模拟持仓对象。"""
    return Position(
        id=1,
        ticker="sh.600519",
        buy_price=100.00,
        buy_date=datetime.now(),
        shares=100,
        status="OPEN"
    )

# --- 测试 check_stop_loss ---
def test_stop_loss_not_triggered(mock_position):
    """测试：价格下跌但未触及止损线。"""
    result = check_stop_loss(mock_position, current_price=98.00, stop_loss_pct=-0.05)
    assert not result["triggered"]

def test_stop_loss_triggered_exactly(mock_position):
    """测试：价格下跌正好触及止損线。"""
    result = check_stop_loss(mock_position, current_price=95.00, stop_loss_pct=-0.05)
    assert result["triggered"]
    assert result["reason"] == "止损"

def test_stop_loss_triggered_below(mock_position):
    """测试：价格下跌超过止损线。"""
    result = check_stop_loss(mock_position, current_price=90.00, stop_loss_pct=-0.05)
    assert result["triggered"]

# --- 测试 check_take_profit ---
def test_take_profit_not_triggered(mock_position):
    """测试：价格上涨但未触及止盈线。"""
    result = check_take_profit(mock_position, current_price=105.00, take_profit_pct=0.10)
    assert not result["triggered"]

def test_take_profit_triggered_exactly(mock_position):
    """测试：价格上涨正好触及止盈线。"""
    result = check_take_profit(mock_position, current_price=110.00, take_profit_pct=0.10)
    assert result["triggered"]
    assert result["reason"] == "止盈"

def test_take_profit_triggered_above(mock_position):
    """测试：价格上涨超过止盈线。"""
    result = check_take_profit(mock_position, current_price=120.00, take_profit_pct=0.10)
    assert result["triggered"] 