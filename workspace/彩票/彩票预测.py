#!/usr/bin/env python3
"""彩票预测脚本
每周生成双色球和大乐透预测号码，写入predict.md（新格式）

规则：
  双色球（周二/四/日开奖）：6组，红球真随机，蓝球取历史最久未开出TOP6
  大乐透（周一/三/六开奖）：6组，前区真随机，后区取历史最近N期最久未出现组合TOP6
"""
import random
import csv
import re
from datetime import date

BASE = '/root/.openclaw/workspace/彩票'
SSQ_CSV = f'{BASE}/双色球.csv'
DLT_CSV = f'{BASE}/大乐透.csv'
PREDICT_FILE = f'{BASE}/predict.md'


def get_ssq_blue_overdue(top=6):
    """双色球蓝球：获取历史最久未开出的TOP6蓝球"""
    with open(SSQ_CSV, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        rows = list(reader)

    first_appear = {}
    for i, row in enumerate(rows):
        if len(row) >= 9:
            blue = int(row[8])
            if blue not in first_appear:
                first_appear[blue] = i

    overdue = sorted(first_appear.keys(), key=lambda b: first_appear[b], reverse=True)
    return overdue[:top]


def get_dlt_back_overdue(top=6, recent_n=10):
    """大乐透后区：获取最近N期最久未出现的后区组合TOP6"""
    with open(DLT_CSV, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        rows = list(reader)

    first_appear = {}
    last_pos = {}
    for i, row in enumerate(rows):
        if len(row) >= 9:
            key = (int(row[7]), int(row[8]))
            if key not in first_appear:
                first_appear[key] = i
            if key not in last_pos or i < last_pos[key]:
                last_pos[key] = i

    recent_keys = {k for k, pos in last_pos.items() if pos < recent_n}
    overdue = sorted(
        [k for k in first_appear if k not in recent_keys],
        key=lambda k: first_appear[k],
        reverse=True
    )
    return overdue[:top]


def calc_ssq_period():
    """计算双色球当期期号（格式26XXX）"""
    today = date.today()
    base = date(2026, 1, 11)  # 26001期=2026-01-11是周日
    base_period = 26001
    days = (today - base).days
    weeks = days // 7
    weekday = today.weekday()  # 0=周一, 1=周二, 3=周四, 6=周日
    ssq_offset = {6: 0, 1: 1, 3: 2}  # 周日=0, 周二=1, 周四=2
    return base_period + weeks * 3 + ssq_offset.get(weekday, 0)


def calc_dlt_period():
    """计算大乐透当期期号（格式26XXX）"""
    today = date.today()
    base = date(2026, 1, 19)  # 26001期=2026-01-19是周一
    base_period = 26001
    days = (today - base).days
    weeks = days // 7
    weekday = today.weekday()  # 0=周一, 2=周三, 5=周六
    dlt_offset = {0: 0, 2: 1, 5: 2}  # 周一=0, 周三=1, 周六=2
    return base_period + weeks * 3 + dlt_offset.get(weekday, 0)


def fmt(nums):
    return " ".join("%02d" % n for n in nums)


def generate_ssq(blue_overdue):
    sets = []
    for blue in blue_overdue:
        reds = sorted(random.sample(range(1, 34), 6))
        sets.append((fmt(reds), fmt([blue])))
    return sets


def generate_dlt(back_overdue):
    sets = []
    for back in back_overdue:
        fronts = sorted(random.sample(range(1, 36), 5))
        sets.append((fmt(fronts), fmt(list(back))))
    return sets


def main():
    today = date.today().isoformat()
    ssq_period = calc_ssq_period()
    dlt_period = calc_dlt_period()

    blue_overdue = get_ssq_blue_overdue(6)
    back_overdue = get_dlt_back_overdue(6)

    ssq_sets = generate_ssq(blue_overdue[:6])
    dlt_sets = generate_dlt(back_overdue[:6])

    # 生成predict.md追加内容（新格式）
    ssq_block = f"## 双色球 {ssq_period}期 | {today} | [预测]\n\n**预测号码（蓝球为历史最久未开出TOP6，红球随机）：**\n"
    for red, blue in ssq_sets:
        ssq_block += f"- {red} + {blue}\n"

    dlt_block = f"## 大乐透 {dlt_period}期 | {today} | [预测]\n\n**预测号码（后区为最近N期最久未出现TOP6，前区随机）：**\n"
    for front, back in dlt_sets:
        dlt_block += f"- {front} + {back}\n"

    # 保留predict.md中的已购/已开奖记录
    with open(PREDICT_FILE, 'r') as f:
        content = f.read()

    markers = [m.start() for m in re.finditer(r'\[已购\]|\[已开奖\]', content)]
    if markers:
        keep_content = content[max(markers):]
    else:
        keep_content = content

    header = """# 彩票预测

> 彩票是概率游戏，每一次开奖都是独立随机事件。历史数据≠未来趋势。理性购彩，量力而行。

---

## 记录格式说明

每条记录格式：
- `[状态]` 标注在标题后，支持：预测 → 已购 → 已开奖
- **下注记录**：每注单独一行，格式为 `红球（6个）+ 蓝球（1个）`
- **下注金额**：当期实际购买总金额（元）
- **开奖号码**：当期官方开奖结果
- **中奖结果**：每注逐一核对，注明红球命中数、蓝球是否命中，中奖奖级和奖金
- **本次收益**：中奖金额 - 下注金额（负数为亏损）

---

"""
    with open(PREDICT_FILE, 'w') as f:
        f.write(header)
        f.write(dlt_block)
        f.write("\n---\n\n")
        f.write(ssq_block)
        f.write("\n---\n\n")
        f.write(keep_content)

    # 仅输出预测号码，不输出期号和日期
    print("大乐透：")
    for front, back in dlt_sets:
        print(f"- {front} + {back}")
    print("\n双色球：")
    for red, blue in ssq_sets:
        print(f"- {red} + {blue}")


if __name__ == '__main__':
    main()
