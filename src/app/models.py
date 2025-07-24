from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
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