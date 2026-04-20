#!/usr/bin/env python3
"""双色球开奖结果核对脚本
每周期（周二/四/日 21:20）执行
1. 搜索最新双色球开奖号码（多渠道确认）
2. 更新双色球.csv
3. 读取predict.md，区分[预测]和[已购]记录
4. 计算中奖：[已购]算入统计，[预测]仅展示
5. 更新stats.json，标记为[已核对]
"""
import csv
import json
import re
import subprocess
from datetime import date, datetime
from collections import Counter

BASE = '/root/.openclaw/workspace/彩票'
SSQ_CSV = f'{BASE}/双色球.csv'
PREDICT_FILE = f'{BASE}/predict.md'
STATS_FILE = f'{BASE}/stats.json'

def search_latest_draw():
    """通过搜索获取最新双色球开奖结果（多渠道）"""
    results = {}
    
    # 渠道1: 搜索
    try:
        r = subprocess.run(['python3', '-c', 
            'from openclaw.tools import web_search; r=web_search.web_search("双色球开奖结果 2026"); print(str(r)[:3000])'],
            capture_output=True, text=True, timeout=15)
        if r.returncode == 0 and r.stdout:
            results['web'] = r.stdout[:2000]
    except:
        pass
    
    # 渠道2: 从/tmp读取（支持多种文件名）
    for fname in ['/tmp/ssq_17500.txt', '/tmp/ssq_latest.txt']:
        try:
            with open(fname, 'r') as f:
                lines = f.readlines()
            if lines:
                parts = lines[0].strip().split()
                if len(parts) >= 9 and parts[0].startswith('20'):
                    results['tmp'] = {
                        'period': parts[0],    # 2026042
                        'date': parts[1],       # 2026-04-16
                        'reds': [int(parts[i]) for i in [2,3,4,5,6,7]],  # 6个红球
                        'blue': int(parts[8])   # 蓝球
                    }
                    break
        except:
            pass
    
    return results

def parse_draw_from_text(text):
    """从文本中解析双色球开奖结果"""
    # 匹配期号格式: 2026043, 2026044 等
    period_match = re.search(r'(\d{7})期', text)
    # 匹配号码格式: 06 09 14 16 25 32 + 16
    numbers_match = re.search(r'(\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2})\s*\+\s*(\d{2})', text)
    # 匹配日期
    date_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{2})', text)
    
    if period_match and numbers_match:
        period = period_match.group(1)
        reds = [int(x) for x in numbers_match.group(1).split()]
        blue = int(numbers_match.group(2))
        
        date_str = None
        if date_match:
            d = date_match.group(1).replace('/', '-')
            if len(d) == 8:  # 26-04-20 格式
                date_str = '20' + d
            elif len(d) == 10:  # 2026-04-20 格式
                date_str = d
        
        return {
            'period': period,
            'date': date_str,
            'reds': reds,
            'blue': blue
        }
    return None

def load_csv_latest():
    """读取CSV最新一期"""
    with open(SSQ_CSV, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row:
                return row
    return None

def append_to_csv(period, draw_date, reds, blue):
    """追加新期号到CSV"""
    existing = set()
    with open(SSQ_CSV, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row:
                existing.add(row[0])
    
    if period in existing:
        return False
    
    with open(SSQ_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([period, draw_date] + reds + [blue])
    return True

def load_stats():
    if __import__('os').path.exists(STATS_FILE):
        with open(STATS_FILE) as f:
            return json.load(f)
    return {'dlt': {'cost': 0, 'win': 0, 'draws': 0}, 'ssq': {'cost': 0, 'win': 0, 'draws': 0}}

def save_stats(stats):
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def parse_predictions(content):
    """解析predict.md中的双色球记录"""
    records = []
    pattern = r'## (\d{7})期\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*双色球\s*\|\s*\[([^\]]+)\](.*?)(?=## |$)'
    for match in re.finditer(pattern, content, re.DOTALL):
        period = match.group(1)
        draw_date = match.group(2)
        status = match.group(3).strip()
        
        bets = []
        numbers_section = match.group(4)
        if '下注记录' in numbers_section or '预测号码' in numbers_section:
            for line in numbers_section.split('\n'):
                line = line.strip()
                m = re.match(r'-\s+(\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2})\s*\+\s*(\d{2})', line)
                if m:
                    reds = [int(x) for x in m.group(1).split()]
                    blue = int(m.group(2))
                    bets.append({'reds': reds, 'blue': blue})
        
        if bets:
            records.append({
                'period': period,
                'date': draw_date,
                'status': status,
                'bets': bets
            })
    
    return records

def calculate_prize(pred_reds, pred_blue, draw_reds, draw_blue):
    """计算单注中奖金额"""
    red_hit = len(set(pred_reds) & set(draw_reds))
    blue_hit = 1 if pred_blue == draw_blue else 0
    
    if red_hit == 6 and blue_hit == 1:
        return ('一等奖（浮动奖）', 0, 'float')
    elif red_hit == 6 and blue_hit == 0:
        return ('二等奖（浮动奖）', 0, 'float')
    elif red_hit == 5 and blue_hit == 1:
        return ('三等奖', 3000, 'fixed')
    elif red_hit == 5 or (red_hit == 4 and blue_hit == 1):
        return ('四等奖', 200, 'fixed')
    elif red_hit == 4 or (red_hit == 3 and blue_hit == 1):
        return ('五等奖', 10, 'fixed')
    elif blue_hit == 1:
        return ('六等奖', 5, 'fixed')
    else:
        return ('未中奖', 0, 'none')

def main():
    today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    print(f"=== 双色球开奖结果核对 {today_str} ===")
    
    # Step 1: 搜索最新开奖数据（多渠道）
    print("\n--- Step 1: 搜索开奖数据 ---")
    sources = search_latest_draw()
    print(f"获取到 {len(sources)} 个数据源")
    
    draw = None
    for src_name, src_data in sources.items():
        print(f"\n[{src_name}]")
        if isinstance(src_data, dict):
            print(f"  期号: {src_data.get('period')} 日期: {src_data.get('date')}")
            red_str = " ".join("%02d" % n for n in sorted(src_data.get('reds', [])))
            blue_str = "%02d" % src_data.get('blue')
            print(f"  号码: {red_str} + {blue_str}")
            draw = src_data
        else:
            parsed = parse_draw_from_text(str(src_data))
            if parsed:
                print(f"  期号: {parsed['period']} 日期: {parsed['date']}")
                red_str = " ".join("%02d" % n for n in sorted(parsed['reds']))
                blue_str = "%02d" % parsed['blue']
                print(f"  号码: {red_str} + {blue_str}")
                draw = parsed
    
    if not draw:
        print("[错误] 无法获取开奖数据")
        return
    
    print(f"\n使用开奖结果: {draw['period']}期 {draw['date']}")
    
    # Step 2: 更新CSV
    print("\n--- Step 2: 更新双色球.csv ---")
    red_sorted = sorted(draw['reds'])
    if append_to_csv(draw['period'], draw['date'], red_sorted, draw['blue']):
        print(f"[新增] {draw['period']} 已写入CSV")
    else:
        print(f"[无需更新] {draw['period']} 已存在")
    
    # Step 3: 读取predict.md
    print("\n--- Step 3: 读取预测/下注记录 ---")
    with open(PREDICT_FILE, 'r') as f:
        content = f.read()
    
    records = parse_predictions(content)
    print(f"解析到 {len(records)} 条双色球记录")
    
    # 找当期记录
    # 找当期记录：优先今日，若无则找最近一次
    current_records = [r for r in records if r['date'] == today_str]
    if not current_records:
        # 取开奖日期<=今日的最新记录
        past_records = [r for r in records if r['date'] <= today_str]
        if past_records:
            latest = max(past_records, key=lambda r: r['date'])
            current_records = [latest]
            print(f"[注意] 今日({today_str})无记录，使用最近一次: {latest['period']}期 {latest['date']}")
        else:
            print(f"[无当期记录] 今日({today_str})无双色球下注/预测记录")
            return
    
    for rec in current_records:
        print(f"  {rec['period']}期 [{rec['status']}] {len(rec['bets'])}注")
    
    # Step 4: 计算中奖
    print("\n--- Step 4: 计算中奖结果 ---")
    stats = load_stats()
    total_win = 0
    total_cost = 0
    
    for rec in current_records:
        is_purchased = rec['status'] == '已购'
        period = rec['period']
        
        print(f"\n{period}期 [{rec['status']}]")
        
        for i, bet in enumerate(rec['bets'], 1):
            prize_name, prize_amount, prize_type = calculate_prize(
                bet['reds'], bet['blue'],
                red_sorted, draw['blue']
            )
            print(f"  {i}: {' '.join('%02d'%n for n in bet['reds'])} + {bet['blue']:02d} → {prize_name}")
            
            if is_purchased and prize_type != 'float' and prize_type != 'none':
                total_win += prize_amount
        
        if is_purchased:
            record_block = re.search(rf'## {period}期.*?\|\s*已购\s*\*+\*+(.*?)(?=## |$)', content, re.DOTALL)
            if record_block:
                amount_match = re.search(r'下注金额.*?(\d+)', record_block.group(1))
                if amount_match:
                    total_cost += int(amount_match.group(1))
    
    # Step 5: 更新统计
    print("\n--- Step 5: 更新统计 ---")
    stats['ssq']['win'] = stats['ssq'].get('win', 0) + total_win
    stats['ssq']['cost'] = stats['ssq'].get('cost', 0) + total_cost
    stats['ssq']['draws'] = stats['ssq'].get('draws', 0) + 1
    save_stats(stats)
    
    print(f"本期中奖: {total_win}元")
    print(f"本期投入: {total_cost}元")
    print(f"累计投入: {stats['ssq']['cost']}元")
    print(f"累计中奖: {stats['ssq']['win']}元")
    print(f"累计期数: {stats['ssq']['draws']}期")
    if stats['ssq']['cost'] > 0:
        roi = (stats['ssq']['win'] / stats['ssq']['cost'] - 1) * 100
        print(f"累计收益率: {roi:.1f}%")
    
    # Step 6: 更新predict.md标记
    print("\n--- Step 6: 更新记录状态 ---")
    for rec in current_records:
        old_pattern = rf'({rec["period"]}期\s*\|\s*{rec["date"]}\s*\|\s*双色球\s*\|\s*)\[已购\]'
        new_pattern = rf'\1[已核对]'
        content = re.sub(old_pattern, new_pattern, content)
    
    with open(PREDICT_FILE, 'w') as f:
        f.write(content)
    print("已将本期已购记录标记为[已核对]")
    
    print("\n=== 执行完成 ===")

if __name__ == '__main__':
    main()
