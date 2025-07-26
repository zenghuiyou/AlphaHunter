from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# --- 数据库配置 ---

# 获取项目根目录
# __file__ 指的是当前文件 (database.py) 的路径
# os.path.dirname() 用于获取文件所在的目录路径
# 我们需要获取三层上级目录 (src/app -> src -> project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 定义数据库文件的路径
# 我们将数据库文件 'alphahunter.db' 存放在项目根目录下
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'alphahunter.db')}"

# --- SQLAlchemy 引擎和会话设置 ---

# 创建数据库引擎
# connect_args={"check_same_thread": False} 是SQLite特有的配置，允许多线程共享连接
# 这对于FastAPI的后台任务是必要的
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建一个SessionLocal类，这个类的实例将是实际的数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建一个Base类，我们之后创建的所有数据模型（表）都将继承这个类
Base = declarative_base()

# --- 数据库会话管理 ---

def get_db():
    """
    一个依赖项函数，用于在API路由中获取数据库会话。
    它确保每个请求都使用一个独立的会话，并在请求结束后关闭它。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    初始化数据库。
    这个函数会根据我们在models.py中定义的模型来创建所有的表。
    通常在应用启动时调用一次。
    """
    print("正在初始化数据库，创建数据表...")
    # 在实际创建表之前，需要确保定义了模型的模块已经被导入
    # 所以通常会在调用此函数前，先 import models
    Base.metadata.create_all(bind=engine)
    print("数据表创建完成。") 