import os

class Settings:
    """
    项目配置类
    优先从环境变量读取，如果不存在则使用默认值。
    """
    # --- API Keys ---
    # 强烈建议从环境变量获取，以避免将敏感信息硬编码到代码中
    # 您需要在您的服务器环境中设置这些变量
    ZHIPUAI_API_KEY: str = os.getenv("ZHIPUAI_API_KEY", "YOUR_ZHIPUAI_API_KEY_HERE")

    # --- 服务器配置 ---
    SERVER_HOST: str = "0.0.0.0"  # 监听所有网络接口，用于部署
    SERVER_PORT: int = 8000

    # --- 扫描参数 ---
    SCANNER_CHANGE_PCT_THRESHOLD: float = 2.0

# 创建一个全局可用的配置实例
settings = Settings()

# --- 本地测试代码 ---
if __name__ == '__main__':
    print("--- 项目配置信息 ---")
    print(f"ZhipuAI API Key: {settings.ZHIPUAI_API_KEY}")
    print(f"服务器监听地址: {settings.SERVER_HOST}")
    print(f"服务器监听端口: {settings.SERVER_PORT}")
    print(f"扫描阈值 (涨跌幅): {settings.SCANNER_CHANGE_PCT_THRESHOLD}%") 