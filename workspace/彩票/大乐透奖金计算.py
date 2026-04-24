#!/usr/bin/env python3
"""大乐透中奖金额计算

规则（2026年新规则）:
  奖池 < 8亿:
    一等奖: 5+2 → 浮动（追加+80%，最高1800万）
    二等奖: 5+1 → 浮动（追加+80%）
    三等奖: 5+0 / 4+2 → 5000元（追加+80%）
    四等奖: 4+1 → 300元（追加+80%）
    五等奖: 4+0 / 3+2 → 150元（追加+80%）
    六等奖: 3+1 / 2+2 → 15元（追加+80%）
    七等奖: 3+0 / 2+1 / 1+2 / 0+2 → 5元（追加不参与）

  奖池 ≥ 8亿（固定奖升级）:
    三等奖: 5000 → 6666元
    四等奖: 300 → 380元
    五等奖: 150 → 200元
    六等奖: 15 → 18元
    七等奖: 5 → 7元

用法:
  python3 大乐透奖金计算.py "01 02 03 04 05 + 06 07" "24 25 27 29 34 + 02 06"
  python3 大乐透奖金计算.py "24 25 27 29 34 + 02 06" "24 25 27 29 34 + 02 06" 追加
  python3 大乐透奖金计算.py "24 25 27 29 34 + 02 06" "24 25 27 29 34 + 02 06" 追加 8亿
"""

import sys

def parse_bet(bet_str):
    """解析投注号码，返回(前区列表, 后区列表)"""
    bet_str = bet_str.strip()
    if '+' in bet_str:
        # 格式: "01 02 03 04 05 + 06 07"
        part = bet_str.split('+')
        front = sorted([int(x) for x in part[0].split()])
        back = sorted([int(x) for x in part[1].split()])
    else:
        # 格式: "01 02 03 04 05 06 07"（7个数字，空格分隔）
        nums = bet_str.split()
        if len(nums) == 7:
            front = sorted([int(x) for x in nums[:5]])
            back = sorted([int(x) for x in nums[5:7]])
        else:
            raise ValueError(f"无法解析: {bet_str}")
    return front, back

def calc(bet_str, draw_str, 追加=False, 奖池8亿=False):
    """计算中奖等级和奖金
    奖池8亿: False=奖池<8亿, True=奖池≥8亿（固定奖升级）
    返回 (奖等名称, 基本奖金, 追加奖金/0)
    """
    bet_front, bet_back = parse_bet(bet_str)
    draw_front, draw_back = parse_bet(draw_str)

    front_hit = len(set(bet_front) & set(draw_front))
    back_hit = len(set(bet_back) & set(draw_back))

    add_ratio = 0.8 if 追加 else 0

    if front_hit == 5 and back_hit == 2:
        label = "一等奖"
        base = "浮动"
        extra = "浮动" if 追加 else None
    elif front_hit == 5 and back_hit == 1:
        label = "二等奖"
        base = "浮动"
        extra = "浮动" if 追加 else None
    elif front_hit == 5 or (front_hit == 4 and back_hit == 2):
        label = "三等奖"
        base = 6666 if 奖池8亿 else 5000
        extra = int(base * add_ratio) if add_ratio else 0
    elif front_hit == 4 and back_hit == 1:
        label = "四等奖"
        base = 380 if 奖池8亿 else 300
        extra = int(base * add_ratio) if add_ratio else 0
    elif (front_hit == 4 and back_hit == 0) or (front_hit == 3 and back_hit == 2):
        label = "五等奖"
        base = 200 if 奖池8亿 else 150
        extra = int(base * add_ratio) if add_ratio else 0
    elif (front_hit == 3 and back_hit == 1) or (front_hit == 2 and back_hit == 2):
        label = "六等奖"
        base = 18 if 奖池8亿 else 15
        extra = int(base * add_ratio) if add_ratio else 0
    elif (front_hit == 3 and back_hit == 0) or (front_hit == 2 and back_hit == 1) or (front_hit == 1 and back_hit == 2) or (front_hit == 0 and back_hit == 2):
        label = "七等奖"
        base = 7 if 奖池8亿 else 5
        extra = 0  # 七等奖追加不参与
    else:
        return ("未中奖", 0, 0)

    return (label, base, extra)

def main():
    if len(sys.argv) < 3:
        print("用法: python3 大乐透奖金计算.py <投注号码> <开奖号码> [追加] [8亿]")
        print("例: python3 大乐透奖金计算.py \"01 02 03 04 05 + 06 07\" \"24 25 27 29 34 + 02 06\"")
        print("例: python3 大乐透奖金计算.py \"24 25 27 29 34 + 02 06\" \"24 25 27 29 34 + 02 06\" 追加")
        print("例: python3 大乐透奖金计算.py \"02 08 10 13 28 + 01 03\" \"02 07 13 19 24 + 03 08\" 追加 8亿")
        sys.exit(1)

    bet_str = sys.argv[1]
    draw_str = sys.argv[2]
    追加 = "追加" in sys.argv
    奖池8亿 = "8亿" in sys.argv

    label, base, extra = calc(bet_str, draw_str, 追加, 奖池8亿)

    if base == "浮动":
        suffix = "（浮动奖" + ("+80%追加）" if 追加 else "）")
        print(f"{label}{suffix}")
    else:
        total = base + (extra or 0)
        if 追加 and extra > 0:
            print(f"{label} +{total}元（基本{base}+追加{extra}）")
        else:
            print(f"{label} +{total}元")

if __name__ == '__main__':
    main()
