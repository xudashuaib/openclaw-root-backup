#!/bin/bash
# 兆易创新K线数据获取脚本
# 用法: bash get_kline.sh [天数默认60]

DAYS=${1:-60}
CODE="sh603986"

echo "=== 兆易创新(603986) K线数据 ==="
echo "获取近${DAYS}个交易日日K线..."
echo ""

# 获取K线数据
raw=$(curl -sL --max-time 10 "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=${CODE},day,,,${DAYS},qfq" 2>/dev/null)

# 解析JSON（简单方式，用python3如果可用）
if command -v python3 &>/dev/null; then
    echo "$raw" | python3 -c "
import sys, json, math

data = json.load(sys.stdin)
klines = data.get('data', {}).get('sh603986', {}).get('qfqday', [])
print(f'获取到 {len(klines)} 条K线数据')
print()
print('格式: 日期 | 开盘 | 收盘 | 最高 | 最低 | 成交量(手)')
print('-' * 80)

for k in klines[-20:]:  # 显示最近20条
    date, open_p, close_p, high_p, low_p, vol = k
    change = float(close_p) - float(open_p)
    change_pct = (change / float(open_p)) * 100 if float(open_p) != 0 else 0
    arrow = '▲' if change >= 0 else '▼'
    print(f'{date} | {open_p:>8} | {close_p:>8} | {high_p:>8} | {low_p:>8} | {vol:>10}  {arrow}{abs(change_pct):.2f}%')

print()
print('-' * 80)
print('最新收盘:', klines[-1][1] if klines else 'N/A')
print('最新成交量:', klines[-1][5] if klines else 'N/A', '手')
" 2>/dev/null
else
    echo "$raw" | grep -oP '\["\d{4}-\d{2}-\d{2}","[^"]+","[^"]+","[^"]+","[^"]+","[^"]+"\]' | tail -10
fi
