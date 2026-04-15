# 实时行情 API 使用说明

## 已安装技能
**allstock-data** — 腾讯财经接口，A/H股+美股实时行情，无需API Key

---

## 快速查询

### 命令行方式
```bash
python3 /root/.openclaw/workspace/stocks/603986_gigadevice/scripts/fetch_realtime.py <股票代码>
```

### 示例
```bash
# 兆易创新
python3 scripts/fetch_realtime.py sh603986

# 多股票批量查询
python3 scripts/fetch_realtime.py sh603986 sh600519 usNVDA

# A股主要指数
python3 scripts/fetch_realtime.py sh000001 sz399001 sz399006

# 美股个股
python3 scripts/fetch_realtime.py usNVDA usAAPL usTSLA usGOOGL
```

---

## 股票代码对照表

### A股 (腾讯接口)
| 市场 | 前缀 | 示例 |
|------|------|------|
| 沪市主板 | `sh60xxxx` | `sh603986` 兆易创新 |
| 科创板 | `sh688xxx` | `sh688111` |
| 深市主板 | `sz00xxxx` | `sz000001` |
| 创业板 | `sz300xxx` | `sz300033` |
| ETF | `sz15xxxx` | `sz159919` |

### A股指数
| 指数 | 代码 |
|------|------|
| 上证指数 | `sh000001` |
| 深证成指 | `sz399001` |
| 创业板指 | `sz399006` |
| 科创50 | `sz399987` |
| 沪深300 | `sh000300` |

### 美股
| 前缀 | 示例 |
|------|------|
| `us` + ticker | `usNVDA` `usAAPL` `usTSLA` |

### 港股
| 前缀 | 示例 |
|------|------|
| `hk` + 代码 | `hk00700` 腾讯 |

---

## K线历史数据

```bash
# 获取日K线(最近10天)
curl -s "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param=sh603986,day,,,10,qfqa" | iconv -f GBK -t UTF-8

# 获取周K线(最近5周)
curl -s "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_weekqfq&param=sh603986,week,,,5,qfqa" | iconv -f GBK -t UTF-8
```

---

## 注意事项

1. **编码**: 腾讯接口返回GBK编码，需要转换
2. **延迟**: 实时数据可能有15秒内延迟
3. **频率**: 避免高频请求，批量查询用逗号分隔
4. **时间**: A股交易时间 9:30-11:30 / 13:00-15:00
5. **非交易时间**: 返回最近收盘价

---

## 数据精度说明

| 数据项 | 精度 |
|--------|------|
| 当前价/涨跌 | 实时 |
| 52周高低 | 精确 |
| 成交量 | 精确(手) |
| K线OHLC | 精确 |
| 指数数据 | 实时 |
