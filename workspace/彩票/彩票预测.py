#!/usr/bin/env python3
"""彩票预测脚本
每周期（周一/三/六 12:30）生成双色球和大乐透预测号码

规则：
  双色球：6组红球随机，蓝球分别使用最久未开出TOP6
  大乐透：6组前区随机，后区分别使用最久未出现TOP6组合
"""
import random
import csv
from datetime import date

BASE = '/root/.openclaw/workspace/彩票'
SSQ_CSV = f'{BASE}/双色球.csv'
DLT_CSV = f'{BASE}/大乐透.csv'
PREDICT_FILE = f'{BASE}/predict.md'

def get_ssq_blue_overdue():
    """双色球蓝球：获取最久未开出的TOP6蓝球
    从新到旧遍历，第一次看到某蓝球=该蓝球最近一次出现。
    很久没出现的蓝球，第一次看到的位置索引会很大。
    按第一次出现位置升序排列，越大=越久未开。
    """
    with open(SSQ_CSV, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        rows = list(reader)
    
    first_appear = {}  # blue -> 第一次出现的位置（从新到旧遍历时）
    for i, row in enumerate(rows):  # 从新到旧
        if len(row) >= 9:
            blue = int(row[8])
            if blue not in first_appear:
                first_appear[blue] = i
    
    # 按第一次出现位置降序：越大=越久未开（最久未开排前面）
    overdue = sorted(first_appear.keys(), key=lambda b: first_appear[b], reverse=True)
    return overdue

def get_dlt_back_overdue(recent_n=10):
    """大乐透后区：获取最久未出现的TOP6后区组合
    recent_n: 排除最近多少期内出现过的组合
    """
    with open(DLT_CSV, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        rows = list(reader)
    
    # 记录每个组合第一次出现的位置（从新到旧，位置越大=越久未开）
    first_appear = {}  # key -> 第一次出现的位置（从新到旧遍历时，越大=越久未开）
    # 同时记录每个组合最近一次出现时的最小位置（越小=最近开过）
    last_pos = {}   # key -> 最近一次出现的位置（取最小=最接近现在）
    
    for i, row in enumerate(rows):  # 从新到旧
        if len(row) >= 9:
            key = tuple(sorted([int(row[7]), int(row[8])]))
            if key not in first_appear:
                first_appear[key] = i
            if key not in last_pos or i < last_pos[key]:
                last_pos[key] = i
    
    # 排除最近N期内出现过的组合（last_pos越小=越近）
    recent_keys = {k for k, pos in last_pos.items() if pos < recent_n}
    
    # 对剩余组合按first_appear降序排列（越大=越久未开，排前面）
    overdue = sorted(
        [k for k in first_appear if k not in recent_keys],
        key=lambda k: first_appear[k],
        reverse=True
    )
    return overdue

def fmt(nums):
    return " ".join("%02d" % n for n in nums)

def generate_ssq_sets(blue_overdue):
    """生成6组双色球（蓝球分别为TOP6，红球随机）"""
    sets = []
    for blue in blue_overdue:
        reds = sorted(random.sample(range(1, 34), 6))  # 真随机
        sets.append((fmt(reds), fmt([blue])))
    return sets

def generate_dlt_sets(back_overdue):
    """生成6组大乐透（后区分别为TOP6，前区随机）"""
    sets = []
    for back in back_overdue:
        fronts = sorted(random.sample(range(1, 36), 5))  # 真随机
        sets.append((fmt(fronts), fmt(list(back))))
    return sets

def main():
    total_ssq = sum(1 for _ in open(SSQ_CSV)) - 1
    total_dlt = sum(1 for _ in open(DLT_CSV)) - 1
    
    print(f"加载: 双色球 {total_ssq}期, 大乐透 {total_dlt}期")
    
    blue_overdue = get_ssq_blue_overdue()
    back_overdue = get_dlt_back_overdue()
    
    print(f"双色球蓝球TOP6（最久未开出）: {blue_overdue}")
    print(f"大乐透后区TOP6（最久未出现）: {back_overdue}")
    
    ssq_sets = generate_ssq_sets(blue_overdue[:6])
    dlt_sets = generate_dlt_sets(back_overdue[:6])
    
    # 生成predict.md新内容
    new_record = f"""## 大乐透 | [预测]

**预测号码（后区为最久未出现TOP6，前区随机）：**
"""
    for front, back in dlt_sets:
        new_record += f"- {front} + {back}\n"
    new_record += f"\n---\n\n"
    new_record += f"## 双色球 | [预测]\n\n**预测号码（蓝球为最久未开出TOP6，红球随机）：**\n\n"
    for red, blue in ssq_sets:
        new_record += f"- {red} + {blue}\n"
    new_record += f"\n---\n\n"

    # 保留已购买记录
    with open(PREDICT_FILE, 'r') as f:
        content = f.read()
    
    import re
    purchased_match = re.search(r'\|\s*\[已购\]\s*\*+\*+', content)
    keep_content = content[purchased_match.start():] if purchased_match else content
    
    with open(PREDICT_FILE, 'w') as f:
        f.write("# 彩票预测\n\n")
        f.write("> 彩票是概率游戏，每一次开奖都是独立随机事件。历史数据≠未来趋势。理性购彩，量力而行。\n\n")
        f.write("> 注：本文件以倒序记录，最新一期排在最前面。\n\n---\n\n")
        f.write(new_record)
        if keep_content.startswith("---"):
            keep_content = keep_content[len("---\n\n"):]
        f.write(keep_content)

    print("\n大乐透：")
    for front, back in dlt_sets:
        print(f"{front} + {back}")
    print("\n双色球：")
    for red, blue in ssq_sets:
        print(f"{red} + {blue}")

if __name__ == '__main__':
    main()
