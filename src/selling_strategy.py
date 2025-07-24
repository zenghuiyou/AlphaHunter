from typing import Dict, Any
from src.app.models import Position
from src.app.logger_config import log

def check_stop_loss(position: Position, current_price: float, stop_loss_pct: float = -0.05) -> Dict[str, Any]:
    """
    检查是否触发止损。

    Args:
        position: 持仓对象。
        current_price: 当前市场价格。
        stop_loss_pct: 止损百分比 (默认为-5%)。

    Returns:
        一个字典，包含是否触发和原因。
    """
    profit_pct = (current_price - position.buy_price) / position.buy_price
    if profit_pct <= stop_loss_pct:
        reason = f"止损触发: 当前盈亏 {profit_pct:.2%} <= 设定阈值 {stop_loss_pct:.2%}"
        log.warning(f"持仓 {position.ticker} {reason}")
        return {"triggered": True, "reason": "止损"}
    return {"triggered": False}

def check_take_profit(position: Position, current_price: float, take_profit_pct: float = 0.10) -> Dict[str, Any]:
    """
    检查是否触发止盈。

    Args:
        position: 持仓对象。
        current_price: 当前市场价格。
        take_profit_pct: 止盈百分比 (默认为+10%)。

    Returns:
        一个字典，包含是否触发和原因。
    """
    profit_pct = (current_price - position.buy_price) / position.buy_price
    if profit_pct >= take_profit_pct:
        reason = f"止盈触发: 当前盈亏 {profit_pct:.2%} >= 设定阈值 {take_profit_pct:.2%}"
        log.info(f"持仓 {position.ticker} {reason}")
        return {"triggered": True, "reason": "止盈"}
    return {"triggered": False}

def check_all_strategies(position: Position, current_price: float) -> Dict[str, Any]:
    """
    运行所有卖出策略检查。

    Args:
        position: 持仓对象。
        current_price: 当前市场价格。

    Returns:
        如果任何一个策略被触发，则返回第一个被触发的策略的结果。
    """
    strategies = [
        check_stop_loss,
        check_take_profit,
        # 未来可以在此添加更多策略，如 check_ma_break
    ]

    for strategy_func in strategies:
        # 注意：这里我们使用默认参数调用策略
        result = strategy_func(position, current_price)
        if result["triggered"]:
            return result
            
    return {"triggered": False}


# --- 本地测试代码 ---
if __name__ == '__main__':
    from datetime import datetime
    
    # 模拟一个持仓对象 (通常从数据库获取)
    mock_position = Position(
        id=1,
        ticker="sh.600519",
        buy_price=1500.00,
        buy_date=datetime.now(),
        shares=100,
        status="OPEN"
    )

    log.info(f"--- 测试卖出策略模块，模拟持仓: {mock_position} ---")

    log.info("\n[1] 测试价格上涨，未触发止盈 (当前价: 1600)")
    result1 = check_all_strategies(mock_position, 1600.00)
    print(f"  - 结果: {result1}")
    
    log.info("\n[2] 测试价格上涨，触发止盈 (当前价: 1651)")
    result2 = check_all_strategies(mock_position, 1651.00)
    print(f"  - 结果: {result2}")

    log.info("\n[3] 测试价格下跌，未触发止损 (当前价: 1450)")
    result3 = check_all_strategies(mock_position, 1450.00)
    print(f"  - 结果: {result3}")

    log.info("\n[4] 测试价格下跌，触发止损 (当前价: 1424)")
    result4 = check_all_strategies(mock_position, 1424.00)
    print(f"  - 结果: {result4}")

    log.info("\n--- 测试完成 ---") 