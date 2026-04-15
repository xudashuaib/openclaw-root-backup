# 兆易创新（603986）分析任务方案

**版本：v2.0**
**制定日期：2026-04-13**
**标的：兆易创新（603986.SH）**

---

## 一、任务目标

对兆易创新进行长期跟踪分析，每日（A股交易日）定时进行走势预测与复盘，逐步优化分析模型，形成可复盘、可迭代的投研追踪体系。

---

## 二、分析模型（15个维度）

| 编号 | 维度 | 核心内容 |
|------|------|---------|
| D1 | 基本面（财务质量） | 成长性、盈利能力、偿债能力、运营效率、现金流、EPS、股东回报 |
| D2 | 估值 | PE/PB/PS历史分位、PEG、股息率、EV/EBITDA |
| D3 | 行业面 | 周期位置、波特五力、政策环境、竞争格局 |
| D4 | 主营业务 | 产品结构、上下游地位、区域分布、客户集中度 |
| D5 | 竞争壁垒 | 技术壁垒、认证周期、生态规模、切换成本 |
| D6 | 商业模式 | Fabless轻资产、客户结构、经销商网络 |
| D7 | 管理层 | 创始人背景、团队稳定性、激励机制 |
| D8 | 资金面 | 北向资金、机构持仓、融资融券、主力流向 |
| D9 | 技术面 | 均线系统、MACD/RSI/KDJ、量价背离、支撑压力位、筹码分布、K线形态分析（15min/60min/日线） |
| D10 | 事件驱动 | 财报发布、重大并购、IPO、政策影响、新品发布 |
| D11 | 外部风险 | 地缘政治、中美关系、汇率、宏观利率 |
| D12 | 产业链 | 上游晶圆厂、下游客户、替代威胁、互补品 |
| D13 | 市场情绪 | 分析师评级、共识预测、融资金额、情绪指数 |
| D14 | 长期趋势 | 市占率变化、产品迭代、研发投入、产能扩张 |
| D15 | 风险监控 | 黑天鹅指标、尾部风险、止损预警 |

---

## 三、每日任务流程

### 定时任务执行时间（仅限交易日）

| 时间 | 任务 | 说明 |
|------|------|------|
| **09:00** | 早盘预测 | 获取隔夜外围市场概况，预测当日走势方向、波动区间、概率分布，记录至 `tracking/daily_prediction.json` |
| **12:00** | 午盘复盘 + 下午预测 | 复盘上午实际走势（开盘价、11:30收盘价、涨跌幅、成交量），对比早盘预测判断准确度，预测下午走势 |
| **15:00** | 尾盘复盘 | 复盘下午实际走势（15:00收盘价、涨跌幅、全日成交量），对比下午预测，更新 `daily_prediction.json` 准确率统计，更新 `tracking/daily_price.json`；**拉取日K线数据，进行K线形态分析（MACD/RSI/KDJ/均线金叉死叉/支撑压力位）** |

> ⚠️ **交易日说明**：定时任务 Cron 表达式为 `0 9 * * 1-5`（周一至周五），A股节假日（春节、国庆等）不在自动排除范围内。
> 
> **双重保障方案：**
> 1. **Cron任务**（周一至周五自动执行）：09:00 早盘预测 / 12:00 午盘复盘+下午预测 / 15:00 尾盘复盘
> 2. **HEARTBEAT心跳提醒**：每周五自动检查下周是否涉及节假日/调休，提前提醒手动暂停/恢复任务
> 
> **暂停/恢复命令：**
> ```bash
> # 暂停
> openclaw cron update --jobId <id> --disabled
> # 恢复
> openclaw cron update --jobId <id> --enabled
> ```
> 
> 定时任务ID记录于 `~/.openclaw/workspace/HEARTBEAT.md`

---

## 四、文件结构

```
stocks/603986_gigadevice/
├── raw/
│   └── 2026-04/
│       ├── price_*.json           # 行情原始数据
│       ├── financials_*.json       # 财报原始数据
│       └── industry_*.json        # 行业数据
│
├── indicators/
│   ├── revenue_growth.csv         # 营收增速指标
│   └── financial_indicators.csv   # 综合财务指标
│
├── model/
│   └── model_history.json          # 模型版本历史
│
├── tracking/
│   ├── daily_price.json           # 每日行情
│   └── daily_prediction.json      # 每日预测+复盘+准确率
│
├── reports/2026/
│   ├── 行业分析_*.md             # 行业维度报告
│   ├── 基本面分析_*.md           # 财务维度报告
│   ├── 技术分析_*.md             # 技术维度报告
│   └── 综合研判_*.md             # 综合研判报告
│
├── scripts/
│   ├── fundamental_screen.py
│   ├── technical_analysis.py
│   └── valuation_model.py
│
└── PROJECT_PLAN.md               # 本方案文件
```

---

## 五、model_history.json（模型演进记录）

每次模型调整（维度增减/权重变化/新指标加入）均在此文件追加记录。

```json
{
  "model_name": "兆易创新(603986)分析模型",
  "current_version": "v1.0",
  "versions": [
    {
      "version": "v1.0",
      "date": "2026-04-13",
      "dimension_count": 15,
      "dimensions": ["D1基本面","D2估值","D3行业面","D4主营业务","D5竞争壁垒",
                     "D6商业模式","D7管理层","D8资金面","D9技术面","D10事件驱动",
                     "D11外部风险","D12产业链","D13市场情绪","D14长期趋势","D15风险监控"],
      "scoring_method": "百分制加权",
      "changes_from_previous": "初始版本",
      "notes": "参考a-stock-fundamental-screening + china-stock-analysis框架构建"
    }
  ]
}
```

---

## 六、daily_price.json（每日行情）

```json
{
  "code": "603986.SH",
  "entries": [
    {
      "date": "2026-04-11",
      "open": null,
      "high": null,
      "low": null,
      "close": 265.09,
      "change_pct": 5.83,
      "volume_hand": 534800,
      "amount_yi": null,
      "northbound_flow_yi": null,
      "margin_balance_yi": null,
      "main_net_flow_yi": null,
      "ws_change": null,
      "event": "大买盘异动",
      "updated_at": "2026-04-13T..."
    }
  ]
}
```

---

## 七、daily_prediction.json（每日预测+复盘）

```json
{
  "code": "603986.SH",
  "entries": [
    {
      "date": "2026-04-11",
      "am_session": {
        "prediction": {
          "direction": "震荡偏强",
          "expected_range": [255, 275],
          "probability_distribution": {"up": 0.4, "震荡": 0.4, "down": 0.2},
          "logic": "大单买入信号+存储景气延续"
        },
        "review": {
          "actual_open": null,
          "actual_close": null,
          "actual_high": null,
          "actual_low": null,
          "actual_change_pct": null,
          "verdict": null,
          "deviation": null,
          "lesson": null
        }
      },
      "pm_session": {
        "prediction": {
          "direction": "震荡整理",
          "expected_range": [258, 270],
          "probability_distribution": {"up": 0.3, "震荡": 0.5, "down": 0.2},
          "logic": "早盘大涨后下午情绪消化"
        },
        "review": {
          "actual_close": null,
          "actual_change_pct": null,
          "verdict": null,
          "deviation": null,
          "lesson": null
        }
      }
    }
  ],
  "statistics": {
    "total_predictions": 0,
    "accurate": 0,
    "partial": 0,
    "missed": 0,
    "accuracy_rate": null
  }
}
```

---

## 八、报告更新机制

| 触发条件 | 更新内容 |
|---------|---------|
| 每个交易日收盘后 | `daily_price.json` + `daily_prediction.json` |
| 每季度财报发布 | 全面更新 D1-D8 维度，输出综合研判报告 |
| 重大事件（并购/政策/黑天鹅） | 触发专项分析，更新相关维度 |
| 模型调整时 | 追加 `model_history.json` 版本记录 |
| 每月底 | 月度复盘报告（准确率统计 + 模型优化建议） |

---

## 九、准确率评估体系

| 标签 | 定义 |
|------|------|
| **准确** | 方向判断正确 + 实际涨跌幅在预测区间内 |
| **部分准确** | 方向判断正确但幅度超出区间 / 区间正确但方向小偏差 |
| **失误** | 方向判断错误 |

准确率 = 准确次数 / 总预测次数

---

## 十、模型优化触发机制

| 触发条件 | 操作 |
|---------|------|
| 准确率 < 50% | 触发模型优化审查，分析失误原因，调整预测维度或权重 |
| 连续3次同维度预测失误 | 专项复盘该维度，修正模型参数 |
| 新维度发现 | 追加至 D1-D15，更新 `model_history.json` |
| 重大事件导致模型失效 | 全维度审查，更新版本号 |

**追踪红线：**
- 准确率 < 50% → 模型优化审查
- 准确率 < 40%（连续5个交易日）→ 模型紧急复盘

---

*分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。*
