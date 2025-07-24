<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'

// --- 数据接口定义 ---
interface CompanyProfile { industry?: string }
interface FinancialIndicators { pe_ratio?: number }
interface FundFlow { main_inflow?: string }
interface SellAlert {
  type: 'SELL_ALERT';
  ticker: string;
  reason: string;
  buy_price: number;
  sell_price: number;
  profit_pct: number;
}

interface RealtimeOpportunity {
  ticker: string;
  price: number;
  change_pct: number;
  company_profile?: CompanyProfile;
  financial_indicators?: FinancialIndicators;
  fund_flow?: FundFlow;
  recent_news?: string[];
  ai_analysis: string;
}

interface StrategicOpportunity {
  ticker: string;
  opportunity_details: {
    breakout_date: string;
    breakout_price: number;
    box_high: number;
    box_low: number;
  };
  ai_strategic_report: string;
}

// --- 响应式状态 ---
const connectionStatus = ref('正在连接...')
const opportunities = ref<RealtimeOpportunity[]>([])
const sellAlerts = ref<SellAlert[]>([])
const strategicOpportunities = ref<StrategicOpportunity[]>([]) // 新增：存储战略机会
const selectedTicker = ref<string | null>(null)
const activeTab = ref<'realtime' | 'strategic'>('realtime') // 新增：控制标签页显示

let socket: WebSocket | null = null

// --- WebSocket 连接逻辑 ---
const connectWebSocket = () => {
  // 从环境变量中读取WebSocket URL
  // Vite会自动根据当前环境 (development/production) 加载对应的.env文件
  const wsUrl = import.meta.env.VITE_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws/dashboard';

  // 使用获取到的URL建立连接
  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    connectionStatus.value = '连接成功！'
    console.log('WebSocket connection established.')
  }

  socket.onmessage = (event) => {
    const message = JSON.parse(event.data)
    
    // V4.5: 根据消息类型分发数据
    if (message.type === 'REALTIME_UPDATE') {
      opportunities.value = message.data.new_opportunities || []
      sellAlerts.value = message.data.sell_alerts || []
    } else if (message.type === 'STRATEGIC_UPDATE') {
      strategicOpportunities.value = message.data.strategic_opportunities || []
    }
  }

  socket.onerror = (error) => {
    connectionStatus.value = '连接错误！'
    console.error('WebSocket error:', error)
  }

  socket.onclose = () => {
    connectionStatus.value = '连接已断开'
    console.log('WebSocket connection closed.')
  }
}

// --- 生命周期钩子 ---
onMounted(() => { connectWebSocket() })
onUnmounted(() => {
  if (socket) {
    socket.close();
  }
})

// --- UI辅助函数 ---
const toggleRow = (ticker: string) => {
  if (selectedTicker.value === ticker) {
    selectedTicker.value = null; // 如果再次点击已展开的行，则收起
  } else {
    selectedTicker.value = ticker; // 展开新行
  }
}

const getParsedMarkdown = (markdown: string) => {
  return marked(markdown)
}
</script>

<template>
  <main class="dashboard">
    <header class="dashboard-header">
      <h1>AlphaHunter V4.5 决策辅助系统</h1>
      <p class="connection-status" :class="{ 'connected': connectionStatus === '连接成功！' }">
        连接状态: <strong>{{ connectionStatus }}</strong>
      </p>
    </header>

    <!-- V4.5 新增: 标签页切换 -->
    <div class="tabs">
      <button @click="activeTab = 'realtime'" :class="{ 'active': activeTab === 'realtime' }">
        实时战术机会
      </button>
      <button @click="activeTab = 'strategic'" :class="{ 'active': activeTab === 'strategic' }">
        盘后战略精选
      </button>
    </div>

    <!-- 实时战术机会视图 -->
    <div v-if="activeTab === 'realtime'" class="tab-content">
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
                <div class="analysis-details" v-html="getParsedMarkdown(opp.ai_analysis)"></div>
              </td>
            </tr>
          </template>
        </table>
      </div>
      <div v-else>
        <p>正在等待新的机会...</p>
      </div>
    </div>

    <!-- 盘后战略精选视图 -->
    <div v-if="activeTab === 'strategic'" class="tab-content">
      <div v-if="strategicOpportunities.length === 0" class="no-data">
        <h2>暂无战略机会</h2>
        <p>离线分析器尚未运行，或未发现符合条件的战略机会。</p>
      </div>
      
      <div v-else class="strategic-opportunities-grid">
        <div v-for="opp in strategicOpportunities" :key="opp.ticker" class="strategic-card">
          <div class="card-header">
            <h3>{{ opp.ticker }}</h3>
            <span class="breakout-date">突破日期: {{ opp.opportunity_details.breakout_date }}</span>
          </div>
          <div class="card-body">
            <div class="opportunity-details">
              <h4>突破详情</h4>
              <ul>
                <li><strong>突破价格:</strong> {{ opp.opportunity_details.breakout_price.toFixed(2) }}</li>
                <li><strong>箱体上轨:</strong> {{ opp.opportunity_details.box_high.toFixed(2) }}</li>
                <li><strong>箱体下轨:</strong> {{ opp.opportunity_details.box_low.toFixed(2) }}</li>
              </ul>
            </div>
            <div class="ai-report" v-html="getParsedMarkdown(opp.ai_strategic_report)">
            </div>
          </div>
        </div>
      </div>
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
