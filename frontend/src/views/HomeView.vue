<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Opportunity {
  ticker: string;
  price: number;
  change_pct: number; // 修正: 与JSON数据保持一致
  ai_analysis: string;
}

const opportunities = ref<Opportunity[]>([])
const connectionStatus = ref('正在连接...')

onMounted(() => {
  // 从本地开发环境 (ws://) 切换到云端生产环境 (wss://)
  const ws = new WebSocket('wss://alphahunter-backend-ojwr.onrender.com/ws/dashboard')

  ws.onopen = () => {
    connectionStatus.value = '连接成功！'
    console.log('WebSocket connection established.')
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      // The backend sends an array of opportunities
      if (Array.isArray(data)) {
        opportunities.value = data
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error)
    }
  }

  ws.onerror = (error) => {
    connectionStatus.value = '连接错误！'
    console.error('WebSocket error:', error)
  }

  ws.onclose = () => {
    connectionStatus.value = '连接已断开'
    console.log('WebSocket connection closed.')
  }
})
</script>

<template>
  <main>
    <h1>AlphaHunter驾驶舱实时机会列表</h1>
    <p>连接状态: {{ connectionStatus }}</p>

    <div v-if="opportunities.length > 0">
      <table>
        <thead>
          <tr>
            <th>股票代码</th>
            <th>当前价格</th>
            <th>涨跌幅</th>
            <th>AI分析</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="opp in opportunities" :key="opp.ticker">
            <td>{{ opp.ticker }}</td>
            <td>{{ opp.price.toFixed(2) }}</td>
            <td>{{ opp.change_pct.toFixed(2) }}%</td> <!-- 修正: 使用 change_pct -->
            <td>{{ opp.ai_analysis }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else>
      <p>正在等待数据...</p>
    </div>
  </main>
</template>

<style scoped>
main {
  padding: 2rem;
  font-family: sans-serif;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}
th, td {
  border: 1px solid #ddd;
  padding: 12px;
  text-align: left;
}
th {
  background-color: #f4f4f4;
  font-weight: bold;
}
tr:nth-child(even) {
  background-color: #f9f9f9;
}
</style>
