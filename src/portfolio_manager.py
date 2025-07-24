from typing import List
from src.app.database import SessionLocal
from src.app.models import Position, PositionStatus
from src.app.logger_config import log

def get_db():
    """数据库会话生成器，确保会话在使用后关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def add_position(ticker: str, buy_price: float, shares: int) -> Position:
    """
    添加一个新的持仓记录。

    Returns:
        创建的Position对象。
    """
    db_session = next(get_db())
    log.info(f"正在添加新持仓: {ticker}, 价格: {buy_price}, 数量: {shares}")
    
    new_position = Position(
        ticker=ticker,
        buy_price=buy_price,
        shares=shares,
        status=PositionStatus.OPEN
    )
    db_session.add(new_position)
    db_session.commit()
    db_session.refresh(new_position)
    
    log.success(f"成功添加持仓记录, ID: {new_position.id}")
    return new_position

def get_open_positions() -> List[Position]:
    """获取所有状态为'OPEN'的持仓记录。"""
    db_session = next(get_db())
    log.info("正在查询所有未平仓头寸...")
    positions = db_session.query(Position).filter(Position.status == PositionStatus.OPEN).all()
    log.info(f"查询到 {len(positions)} 个未平仓头寸。")
    return positions

def update_position_status(position_id: int, new_status: PositionStatus) -> Position:
    """
    更新指定ID的持仓记录的状态。

    Returns:
        更新后的Position对象, 如果未找到则返回None。
    """
    db_session = next(get_db())
    log.info(f"正在更新持仓ID {position_id} 的状态为 {new_status.value}...")
    
    position = db_session.query(Position).filter(Position.id == position_id).first()
    
    if position:
        position.status = new_status
        db_session.commit()
        db_session.refresh(position)
        log.success(f"持仓ID {position_id} 的状态已更新。")
        return position
    else:
        log.warning(f"未找到ID为 {position_id} 的持仓记录。")
        return None

# --- 本地测试代码 ---
if __name__ == '__main__':
    from src.app.database import init_db
    log.info("--- 初始化数据库用于测试 portfolio_manager ---")
    init_db()

    log.info("\n--- [1] 测试添加新持仓 ---")
    pos1 = add_position(ticker="sh.600036", buy_price=35.50, shares=100)
    pos2 = add_position(ticker="sz.000001", buy_price=12.80, shares=200)

    log.info("\n--- [2] 测试获取所有未平仓头寸 ---")
    open_positions = get_open_positions()
    for p in open_positions:
        print(f"  - 找到持仓: {p}")

    log.info(f"\n--- [3] 测试更新持仓状态 (将ID: {pos1.id} 设置为 CLOSED) ---")
    update_position_status(pos1.id, PositionStatus.CLOSED)

    log.info("\n--- [4] 再次获取所有未平仓头寸 ---")
    open_positions_after_update = get_open_positions()
    for p in open_positions_after_update:
        print(f"  - 找到持仓: {p}")

    log.info("\n--- 测试完成 ---") 