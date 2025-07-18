FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt requirements.txt

# 使用清华大学的镜像源来加速pip安装，并增加超时时间
RUN pip install --no-cache-dir --default-timeout=100 -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制应用源代码
COPY ./src ./src

# 暴露端口
EXPOSE 8000

# 启动应用的命令
CMD ["uvicorn", "src.api_server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
