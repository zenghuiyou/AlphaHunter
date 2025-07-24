import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.database import Base
from src.app.models import Position, PositionStatus
import src.portfolio_manager as portfolio

# --- 测试环境设置 ---
# 使用内存中的SQLite数据库进行测试
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    为每个测试函数创建一个新的、干净的数据库会话。
    测试结束后，回滚所有更改并关闭会话。
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    # 猴子补丁：用测试会话替换模块中的真实会话
    portfolio.SessionLocal = lambda: session
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

# --- 测试用例 ---
def test_add_position(db_session):
    """测试添加新持仓的功能。"""
    ticker = "sh.600036"
    buy_price = 35.50
    shares = 100
    
    new_pos = portfolio.add_position(ticker, buy_price, shares)
    
    assert new_pos.id is not None
    assert new_pos.ticker == ticker
    assert new_pos.status == PositionStatus.OPEN
    
    # 验证数据是否真的写入了数据库
    retrieved_pos = db_session.query(Position).filter(Position.id == new_pos.id).first()
    assert retrieved_pos is not None
    assert retrieved_pos.shares == shares

def test_get_open_positions(db_session):
    """测试获取所有未平仓头寸的功能。"""
    # 准备数据
    portfolio.add_position("sh.000001", 12.80, 200)
    closed_pos = portfolio.add_position("sz.300750", 250.00, 50)
    portfolio.update_position_status(closed_pos.id, PositionStatus.CLOSED)
    portfolio.add_position("sh.601318", 80.00, 100)
    
    open_positions = portfolio.get_open_positions()
    
    assert len(open_positions) == 2
    tickers = {p.ticker for p in open_positions}
    assert "sh.000001" in tickers
    assert "sh.601318" in tickers
    assert "sz.300750" not in tickers

def test_update_position_status(db_session):
    """测试更新持仓状态的功能。"""
    pos_to_update = portfolio.add_position("sh.688981", 55.00, 300)
    
    # 确认初始状态
    assert pos_to_update.status == PositionStatus.OPEN
    
    updated_pos = portfolio.update_position_status(pos_to_update.id, PositionStatus.CLOSED)
    
    assert updated_pos is not None
    assert updated_pos.status == PositionStatus.CLOSED
    
    # 确认数据库中的状态也已改变
    retrieved_pos = db_session.query(Position).filter(Position.id == pos_to_update.id).first()
    assert retrieved_pos.status == PositionStatus.CLOSED 