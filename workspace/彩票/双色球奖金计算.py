#!/usr/bin/env python3
"""双色球中奖金额计算

规则（固定奖）:
  三等奖: 5红+1蓝 → 3000元
  四等奖: 5红+0蓝 或 4红+1蓝 → 200元
  五等奖: 4红+0蓝 或 3红+1蓝 → 10元
  六等奖: 2红+1蓝 或 1红+1蓝 或 0红+1蓝 → 5元

浮动奖（一二等奖）需要当期销售额和奖池数据，本脚本仅返回"浮动"而非具体金额。

用法:
  python3 双色球奖金计算.py "01 02 03 04 05 06 + 07" "01 02 07 08 09 10 + 07"
  python3 双色球奖金计算.py 01 02 03 04 05 06 07  # 7个参数=6红+1蓝
"""

import sys

# 固定奖金表
PRIZES = {
    (6, 1): ("一等奖", "浮动"),
    (6, 0): ("二等奖", "浮动"),
    (5, 1): ("三等奖", 3000),
    (5, 0): ("四等奖", 200),
    (4, 1): ("四等奖", 200),
    (4, 0): ("五等奖", 10),
    (3, 1): ("五等奖", 10),
    (2, 1): ("六等奖", 5),
    (1, 1): ("六等奖", 5),
    (0, 1): ("六等奖", 5),
}

def parse_bet(bet_str):
    """解析投注号码，返回(红球列表, 蓝球)"""
    bet_str = bet_str.strip()
    if '+' in bet_str:
        parts = bet_str.replace('+', ' ').split()
        reds = sorted([int(x) for x in parts[:6]])
        blue = int(parts[6])
    else:
        nums = bet_str.split()
        reds = sorted([int(x) for x in nums[:6]])
        blue = int(nums[6])
    return reds, blue

def calc(bet_str, draw_str):
    """计算一个投注的中奖等级和奖金"""
    bet_red, bet_blue = parse_bet(bet_str)
    draw_red, draw_blue = parse_bet(draw_str)

    red_hit = len(set(bet_red) & set(draw_red))
    blue_hit = 1 if bet_blue == draw_blue else 0

    key = (red_hit, blue_hit)
    if key in PRIZES:
        return PRIZES[key]
    return ("未中奖", 0)

def main():
    if len(sys.argv) < 3:
        print("用法: python3 双色球奖金计算.py <投注号码> <开奖号码>")
        print("例: python3 双色球奖金计算.py \"01 02 03 04 05 06 + 07\" \"02 07 12 19 24 31 + 10\"")
        sys.exit(1)

    bet_str = sys.argv[1]
    draw_str = sys.argv[2]

    prize_name, amount = calc(bet_str, draw_str)

    if amount == "浮动":
        print(f"{prize_name}（浮动奖，当期销售额和奖池决定）")
    else:
        print(f"{prize_name} +{amount}元")

if __name__ == '__main__':
    main()
