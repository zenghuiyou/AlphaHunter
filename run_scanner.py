import time
import schedule
from tenacity import retry, stop_after_attempt, wait_fixed
from src.data_provider import run_data_pipeline
from src.app.logger_config import log

@retry(stop=stop_after_attempt(3), wait=wait_fixed(10))
def run_pipeline_with_retry():
    """
    使用tenacity包装器来运行数据流水线，确保健壮性。
    如果失败，会每隔10秒重试一次，最多重试3次。
    """
    try:
        run_data_pipeline()
    except Exception as e:
        log.critical(f"数据流水线发生严重错误: {e}", exc_info=True)
        # 抛出异常以触发tenacity的重试机制
        raise

def job():
    log.info("--- [扫描器任务] 开始执行新一轮的数据处理... ---")
    run_pipeline_with_retry()
    log.info("--- [扫描器任务] 本轮任务执行完毕，等待下一个周期... ---")

if __name__ == "__main__":
    log.info("启动独立数据扫描器进程...")
    
    # 使用schedule库来安排任务，每60秒运行一次
    schedule.every(60).seconds.do(job)
    
    # 立即执行一次，不等第一个60秒
    log.info("立即执行第一次任务...")
    schedule.run_all()
    
    while True:
        schedule.run_pending()
        time.sleep(1) 