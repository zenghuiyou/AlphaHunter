from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.app.logger_config import log

# 数据库文件将存放在项目根目录
DATABASE_URL = "sqlite:///./alphahunter.db"

# 创建数据库引擎
# connect_args 是专门为SQLite配置的，确保在多线程环境中（如FastAPI）安全运行
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建一个SessionLocal类，每个实例都是一个数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建一个Base类，我们的ORM模型将继承这个类
Base = declarative_base()

def init_db():
    """
    初始化数据库，创建所有定义的表。
    """
    log.info("正在初始化数据库，创建所有表格...")
    try:
        # 这里的导入是必需的，以确保模型在创建表之前被SQLAlchemy注册
        from src.app import models
        Base.metadata.create_all(bind=engine)
        log.success("数据库表格创建成功！")
    except Exception as e:
        log.critical(f"数据库表格创建失败: {e}")
        raise 