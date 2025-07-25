from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    """
    所有扫描策略的基类，定义了策略所需遵循的接口。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略的名称，例如：'箱体突破'"""
        pass

    @abstractmethod
    def scan(self, historical_data: dict) -> list:
        """
        执行扫描的核心逻辑。
        
        :param historical_data: 一个字典，键为股票代码，值为包含其历史数据的DataFrame。
                               DataFrame应包含 'date', 'open', 'high', 'low', 'close', 'volume' 等列。
        :return: 一个机会列表，每个机会是一个字典，包含策略发现的所有相关信息。
        """
        pass 