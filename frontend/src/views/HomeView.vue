<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { marked } from 'marked'

// V4.0 新增：公司概况
interface CompanyProfile {
  industry: string;
  total_market_cap: string;
  circulating_market_cap: string;
}

// V4.0 新增：财务指标
interface FinancialIndicators {
  pe_ratio: number | string;
  pb_ratio: number | string;
  roe: number | string;
}

// V4.0 新增：资金流向
interface FundFlow {
  main_net_inflow: string;
  super_large_net_inflow: string;
}

// V4.0 核心数据结构升级
interface Opportunity {
  // 技术面基础数据
  ticker: string;
  price: number;
  change_pct: number;
  
  // AkShare 增强数据
  company_profile?: CompanyProfile;
  financial_indicators?: FinancialIndicators;
  fund_flow?: FundFlow;
  recent_news?: string[];
  
  // AI 分析报告 (暂时保持字符串，下一步UI重构时再结构化)
  ai_analysis: string;
}

// V4.0 新增：卖出提醒的数据结构
interface SellAlert {
  type: 'SELL_ALERT';
  ticker: string;
  reason: string;
  buy_price: number;
  sell_price: number;
  profit_pct: number;
}

const opportunities = ref<Opportunity[]>([])
const sellAlerts = ref<SellAlert[]>([]) // 新增：用于存放卖出提醒
const connectionStatus = ref('正在连接...')
const selectedTicker = ref<string | null>(null)

// --- Methods ---
const toggleRow = (ticker: string) => {
  if (selectedTicker.value === ticker) {
    selectedTicker.value = null; // 如果再次点击已展开的行，则收起
  } else {
    selectedTicker.value = ticker; // 展开新行
  }
}

const getParsedAnalysis = (analysis: string) => {
  // 使用 'as any' 来绕过 marked 库可能存在的类型定义问题
  return (marked as any)(analysis);
}

onMounted(() => {
  // 从环境变量中读取WebSocket URL
  // Vite会自动根据当前环境 (development/production) 加载对应的.env文件
  const wsUrl = import.meta.env.VITE_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws/dashboard';

  // 使用获取到的URL建立连接
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    connectionStatus.value = '连接成功！'
    console.log('WebSocket connection established.')
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      // V4.0: 处理新的复合数据结构
      if (data.new_opportunities) {
        opportunities.value = data.new_opportunities
      }
      if (data.sell_alerts && data.sell_alerts.length > 0) {
        // 将新的卖出提醒添加到列表开头，使其最先显示
        sellAlerts.value = [...data.sell_alerts, ...sellAlerts.value];
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
    <h1>AlphaHunter V4.0 决策辅助系统</h1>
    <p>连接状态: <span :class="connectionStatus === '连接成功！' ? 'status-ok' : 'status-error'">{{ connectionStatus }}</span></p>

    <!-- 卖出提醒区域 -->
    <div v-if="sellAlerts.length > 0" class="alerts-container">
      <h2>平仓提醒</h2>
      <div v-for="(alert, index) in sellAlerts" :key="index" class="alert-card" :class="alert.profit_pct >= 0 ? 'profit' : 'loss'">
        <p><strong>股票代码:</strong> {{ alert.ticker }}</p>
        <p><strong>平仓原因:</strong> {{ alert.reason }}</p>
        <p><strong>买入价:</strong> {{ alert.buy_price.toFixed(2) }}</p>
        <p><strong>卖出价:</strong> {{ alert.sell_price.toFixed(2) }}</p>
        <p><strong>盈亏:</strong> <span class="profit-pct">{{ (alert.profit_pct * 100).toFixed(2) }}%</span></p>
      </div>
    </div>

    <!-- 新机会列表 -->
    <h2>新机会扫描</h2>
    <div v-if="opportunities.length > 0">
      <table class="opportunity-table">
        <thead>
          <tr>
            <th>股票代码</th>
            <th>当前价格</th>
            <th>涨跌幅</th>
            <th>行业</th>
            <th>市盈率(PE)</th>
            <th>AI分析摘要</th>
          </tr>
        </thead>
        <template v-for="opp in opportunities" :key="opp.ticker">
          <tr @click="toggleRow(opp.ticker)" class="data-row">
            <td>{{ opp.ticker }}</td>
            <td>{{ opp.price.toFixed(2) }}</td>
            <td>{{ opp.change_pct.toFixed(2) }}%</td>
            <td>{{ opp.company_profile?.industry || 'N/A' }}</td>
            <td>{{ opp.financial_indicators?.pe_ratio || 'N/A' }}</td>
            <td class="analysis-summary">{{ opp.ai_analysis.substring(0, 50) }}...</td>
          </tr>
          <tr v-if="selectedTicker === opp.ticker" class="details-row">
            <td colspan="6">
              <div class="analysis-details" v-html="getParsedAnalysis(opp.ai_analysis)"></div>
            </td>
          </tr>
        </template>
      </table>
    </div>
    <div v-else>
      <p>正在等待新的机会...</p>
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
  vertical-align: top; /* 垂直居上对齐 */
}
th {
  background-color: #f4f4f4;
  font-weight: bold;
}
tr:nth-child(even) {
  background-color: #f9f9f9;
}
.analysis-summary {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.opportunity-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}
.data-row {
  cursor: pointer;
  transition: background-color 0.2s;
}
.data-row:hover {
  background-color: #eef8ff;
}
.details-row td {
  padding: 20px;
  background-color: #fcfcfc;
  border-top: 2px solid #007bff;
}
.analysis-details {
  max-width: 100%;
  overflow-x: auto;
}
.status-ok { color: #28a745; }
.status-error { color: #dc3545; }

.alerts-container {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background-color: #fffbe6;
  border: 1px solid #ffeeba;
  border-radius: 8px;
}
.alerts-container h2 {
  margin-top: 0;
  color: #856404;
}
.alert-card {
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 4px;
  border-left-width: 5px;
  border-left-style: solid;
}
.alert-card.profit {
  background-color: #d4edda;
  border-color: #28a745;
}
.alert-card.loss {
  background-color: #f8d7da;
  border-color: #dc3545;
}
.alert-card p {
  margin: 0.5rem 0;
}
.profit-pct {
  font-weight: bold;
}
</style>
