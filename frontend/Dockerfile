# 使用 Node.js 16 长期支持版作为基础
FROM node:16-alpine

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json (如果存在)
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制所有源代码
COPY . .

# 暴露 Vite 开发服务器的默认端口
EXPOSE 5173

# 运行 Vite 开发服务器，并允许来自任何地址的访问
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
