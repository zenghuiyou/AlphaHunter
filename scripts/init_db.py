
# scripts/init_db.py
import sys
import os

# 将项目根目录添加到Python的模块搜索路径中
# 这对于让脚本能够找到 `src` 目录下的模块至关重要
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.database import init_db
from src.app import models  # 导入models以确保Base能够正确识别所有表

def main():
    """
    数据库初始化主函数
    """
    print("开始执行数据库初始化流程...")
    
    # 调用核心的初始化函数
    init_db()
    
    print("数据库初始化流程执行完毕。")

if __name__ == "__main__":
    main() 