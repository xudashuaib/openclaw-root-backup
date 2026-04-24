#!/usr/bin/env python3
"""重新计算双色球第26044期中奖金额"""

draw = "02 14 17 18 22 30 + 01"
bets = [
    "01 02 20 22 28 32 + 09",
    "07 15 20 21 27 28 + 01",
    "02 04 06 21 30 33 + 11",
    "09 15 16 18 28 29 + 14",
    "09 11 15 17 19 29 + 03",
    "04 14 15 17 28 32 + 15",
]

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

def parse(s):
    parts = s.replace("+", " ").split()
    reds = sorted([int(x) for x in parts[:6]])
    blue = int(parts[6])
    return reds, blue

draw_red, draw_blue = parse(draw)
total_win = 0
results = []

for i, bet in enumerate(bets, 1):
    bet_red, bet_blue = parse(bet)
    red_hit = len(set(bet_red) & set(draw_red))
    blue_hit = 1 if bet_blue == draw_blue else 0
    key = (red_hit, blue_hit)
    name, amount = PRIZES.get(key, ("未中奖", 0))
    results.append((i, bet, red_hit, blue_hit, name, amount))
    if amount != "浮动":
        total_win += amount

print("=" * 60)
print(f"开奖号码: {draw}")
print("=" * 60)
for i, bet, rh, bh, name, amount in results:
    print(f"注{i}: {bet}  → 红球命中{rh}个, 蓝球{'命中' if bh else '未中'} → {name} {'+' + str(amount) + '元' if amount != '浮动' else '(浮动)'}")
print("=" * 60)
print(f"合计中奖: {total_win}元")
print(f"投入: {len(bets) * 2}元")
print(f"净收益: {total_win - len(bets) * 2}元")
