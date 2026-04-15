#!/bin/bash
# 中国A股交易日历检查脚本
# 返回 0: 是交易日, 1: 非交易日

today=$(date +%Y-%m-%d)
weekday=$(date +%w)  # 0=周日, 6=周六

# 周末判断
if [ "$weekday" = "0" ] || [ "$weekday" = "6" ]; then
    echo "[TRADING_CAL] today=$today (weekend), NOT a trading day"
    exit 1
fi

# 2026年A股节假日列表 (农历节日可能有1-2天偏差, 以交易所公告为准)
# 格式: YYYY-MM-DD
holidays_2026=(
    "2026-01-01"  # 元旦
    "2026-01-26"  # 春节前最后交易日(除夕)
    "2026-01-27"  # 春节
    "2026-01-28"
    "2026-01-29"
    "2026-01-30"
    "2026-01-31"
    "2026-02-01"  # 春节后首个交易日(初五)
    "2026-02-02"
    "2026-04-03"  # 清明节
    "2026-04-04"
    "2026-04-05"
    "2026-04-06"  # 清明节后首个交易日
    "2026-05-01"  # 劳动节
    "2026-05-02"
    "2026-05-03"
    "2026-05-04"  # 劳动节后首个交易日
    "2026-05-30"  # 端午节
    "2026-05-31"
    "2026-06-01"
    "2026-06-02"  # 端午节后首个交易日
    "2026-09-24"  # 中秋节
    "2026-09-25"
    "2026-09-26"
    "2026-09-27"  # 中秋节后首个交易日
    "2026-10-01"  # 国庆节
    "2026-10-02"
    "2026-10-03"
    "2026-10-04"
    "2026-10-05"
    "2026-10-06"
    "2026-10-07"
    "2026-10-08"  # 国庆节后首个交易日
    "2026-10-09"
)

# 检查今日是否在节假日列表中
for holiday in "${holidays_2026[@]}"; do
    if [ "$today" = "$holiday" ]; then
        echo "[TRADING_CAL] today=$today (holiday=$holiday), NOT a trading day"
        exit 1
    fi
done

# 通过腾讯财经API双重验证（上证指数有数据=交易日）
# 格式: date YYYYMMDD
today_qt=$(date +%Y%m%d)
qt_result=$(curl -s --max-time 5 "http://qt.gtimg.cn/q=sh000001" 2>/dev/null)
if echo "$qt_result" | grep -q "$today_qt"; then
    echo "[TRADING_CAL] today=$today (verified by Tencent Finance API), IS a trading day"
    exit 0
else
    echo "[TRADING_CAL] today=$today (no market data from API), NOT a trading day"
    exit 1
fi
