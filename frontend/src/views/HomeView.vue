<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
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

// V5.0 最终修复版：与后端数据结构完全对齐
interface StrategicOpportunity {
  ticker: string;
  strategy_name: string;
  breakout_date: string;
  breakout_price: number;
  description: string;
  ai_analysis: string;
  // 以下为数据增强字段，可能不存在，设为可选
  company_profile?: {
    industry?: string;
    total_market_cap?: string;
    circulating_market_cap?: string;
  };
  financial_indicators?: {
    pe_ratio?: number | string;
    pb_ratio?: number | string;
    roe?: number | string;
  };
  recent_news?: string[];
  fund_flow?: any;
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
    try {
      const message = JSON.parse(event.data);
      console.log("WebSocket message received:", message); // 保留用于调试

      // V4.5: 根据消息类型分发数据
      if (message.type === 'REALTIME_UPDATE') {
        opportunities.value = message.data.new_opportunities || []
        sellAlerts.value = message.data.sell_alerts || []
      } else if (message.type === 'STRATEGIC_UPDATE') {
        // V5.0 最终修复版：直接使用 message.data
        strategicOpportunities.value = message.data || [];
        console.log("Updated strategic opportunities:", strategicOpportunities.value);
      }
    } catch (error) {
      console.error("Error parsing or processing WebSocket message:", error);
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

// 新增：计算属性，用于安全地渲染AI分析报告
const renderedMarkdown = (htmlContent: string) => {
  return marked(htmlContent || '');
};

// 新增：用于控制战略机会的展开/收起
const toggleAccordion = (ticker: string) => {
  if (selectedTicker.value === ticker) {
    selectedTicker.value = null;
  } else {
    selectedTicker.value = ticker;
  }
};
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
        <div v-if="strategicOpportunities.length > 0">
          <div v-for="opp in strategicOpportunities" :key="opp.ticker" class="opportunity-card strategic-card">
            <!-- Card header -->
            <div class="card-header">
              <h3 class="ticker">{{ opp.ticker }}</h3>
              <span class="strategy-badge">{{ opp.strategy_name }}</span>
            </div>
            <!-- Card body -->
            <div class="card-body">
              <p class="description">{{ opp.description }}</p>
              <div class="details">
                <span><strong>信号日期:</strong> {{ opp.breakout_date }}</span>
                <span v-if="opp.breakout_price"><strong>信号价格:</strong> {{ opp.breakout_price.toFixed(2) }}</span>
              </div>
            </div>
            <!-- Accordion for AI analysis -->
            <div class="ai-section">
              <button @click="toggleAccordion(opp.ticker)" class="accordion-button">
                深度AI战略分析
                <span class="arrow" :class="{ 'is-rotated': selectedTicker === opp.ticker }">▼</span>
              </button>
              <div 
                class="accordion-content" 
                :class="{ 'is-open': selectedTicker === opp.ticker }"
              >
                <div v-if="selectedTicker === opp.ticker" v-html="renderedMarkdown(opp.ai_analysis)"></div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="no-opportunities">
          <p class="title">暂无战略机会</p>
          <p class="subtitle">离线分析器尚未运行，或未发现符合条件的战略机会。</p>
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
  color: #333; /* 增强可读性 */
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

/* New styles for strategic opportunities */
.strategic-opportunities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 20px;
}

.strategic-card {
  background-color: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease-in-out;
}

.strategic-card:hover {
  transform: translateY(-5px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #ccc;
}

.ticker {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
}

.strategy-badge {
  background-color: #007bff;
  color: white;
  padding: 0.4rem 0.8rem;
  border-radius: 5px;
  font-size: 0.9rem;
  font-weight: bold;
  white-space: nowrap;
}

.card-body {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #eee;
}

.description {
  font-size: 1rem;
  color: #555;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.details {
  font-size: 0.9rem;
  color: #666;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.ai-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #eee;
}

.accordion-button {
  background-color: #f0f0f0;
  border: 1px solid #ccc;
  border-radius: 5px;
  padding: 0.8rem 1.2rem;
  width: 100%;
  text-align: left;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  color: #333;
  transition: background-color 0.3s ease;
}

.accordion-button:hover {
  background-color: #e0e0e0;
}

.accordion-button .arrow {
  transition: transform 0.3s ease;
}

.accordion-button .arrow.is-rotated {
  transform: rotate(180deg);
}

.accordion-content {
  max-height: 0;
  overflow: hidden;
  padding-top: 0;
  padding-bottom: 0;
  margin-top: 0;
  transition: all 0.4s ease-in-out;
  background-color: #fcfcfc;
  border-radius: 5px;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05);
  color: #333; /* 增强可读性 */
}

.accordion-content.is-open {
  max-height: 1500px; /* A value larger than any expected content */
  margin-top: 0.5rem;
  padding: 1rem;
  border: 1px solid #eee;
}

.no-opportunities {
  text-align: center;
  padding: 2rem;
  color: #888;
}

.no-opportunities .title {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.no-opportunities .subtitle {
  font-size: 1rem;
}
</style>
