from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Date, UniqueConstraint
from sqlalchemy.sql import func
import enum
from src.app.database import Base

class PositionStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    buy_price = Column(Float, nullable=False)
    buy_date = Column(DateTime(timezone=True), server_default=func.now())
    shares = Column(Integer, nullable=False)
    status = Column(Enum(PositionStatus), default=PositionStatus.OPEN, nullable=False)

    def __repr__(self):
        return f"<Position(id={self.id}, ticker='{self.ticker}', status='{self.status}')>" 

class StockDailyData(Base):
    """
    股票日线行情数据模型
    映射到数据库中的 'stock_daily_data' 表。
    """
    __tablename__ = 'stock_daily_data'

    # 定义表结构
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 核心字段，来自BaoStock
    date = Column(Date, nullable=False, index=True)
    code = Column(String(10), nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    preclose = Column(Float)
    volume = Column(Integer)  # 成交量 (股)
    amount = Column(Float)    # 成交额 (元)
    adjustflag = Column(String(10))
    turn = Column(Float)      # 换手率
    tradestatus = Column(String(10))
    pctChg = Column(Float)    # 涨跌幅
    peTTM = Column(Float)     # 市盈率 (滚动市盈率)
    pbMRQ = Column(Float)     # 市净率 (最新财报)
    psTTM = Column(Float)     # 市销率 (滚动市销率)
    pcfNcfTTM = Column(Float) # 市现率 (滚动市现率)
    isST = Column(String(10))

    # 添加联合唯一约束
    # 确保同一支股票在同一天只有一条记录
    __table_args__ = (UniqueConstraint('date', 'code', name='_date_code_uc'),)

    def __repr__(self):
        return f"<StockDailyData(date='{self.date}', code='{self.code}', close='{self.close}')>" 