#!/usr/bin/env python3
"""大乐透开奖结果核对脚本
每周期（周一/三/六 21:30）执行
1. 从dlt_desc.txt读取最新开奖号码（多渠道确认）
2. 更新大乐透.csv
3. 读取predict.md，区分[预测]和[已购]记录
4. 计算中奖：[已购]算入统计，[预测]仅展示
5. 更新stats.json，标记为[已核对]
"""
import csv
import json
import re
import subprocess
from datetime import date

BASE = '/root/.openclaw/workspace/彩票'
DLT_CSV = f'{BASE}/大乐透.csv'
PREDICT_FILE = f'{BASE}/predict.md'
STATS_FILE = f'{BASE}/stats.json'

def read_from_tmp():
    """从/tmp数据文件读取最新大乐透开奖结果"""
    try:
        with open('/tmp/dlt_desc.txt', 'r') as f:
            lines = f.readlines()
        if not lines:
            return None
        # 第一行是最新数据
        parts = lines[0].strip().split()
        if len(parts) >= 9:
            return {
                'period': parts[0],      # 26041
                'date': parts[1],         # 2026-04-18
                'front': [int(parts[i]) for i in [2,3,4,5,6]],   # 24 25 27 29 34
                'back': [int(parts[7]), int(parts[8])]           # 02 06
            }
    except Exception as e:
        print(f"  [tmp] 读取失败: {e}")
    return None

def search_latest_draw():
    """通过搜索获取最新大乐透开奖结果（多渠道）"""
    results = {}
    
    # 渠道1: 从/tmp读取
    tmp_data = read_from_tmp()
    if tmp_data:
        results['tmp'] = tmp_data
    
    # 渠道2: 搜索（由cron agent在独立session中执行搜索）
    # 这里只做备用渠果web搜索有结果会通过/tmp传入
    try:
        r = subprocess.run(['python3', '-c', 
            'from openclaw.tools import web_search; r=web_search.web_search("大乐透开奖结果 2026"); print(str(r)[:3000])'],
            capture_output=True, text=True, timeout=15)
        if r.returncode == 0 and r.stdout and '大乐透' in r.stdout:
            results['web'] = r.stdout[:2000]
    except:
        pass
    
    return results

def parse_draw_from_text(text):
    """从搜索文本中解析大乐透开奖结果"""
    period_match = re.search(r'(\d{5})期', text)
    numbers_match = re.search(r'(\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2})\s*\+\s*(\d{2}\s+\d{2})', text)
    date_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', text)
    
    if period_match and numbers_match:
        period = period_match.group(1)
        front = [int(x) for x in numbers_match.group(1).split()]
        back = [int(x) for x in numbers_match.group(2).split()]
        
        date_str = None
        if date_match:
            d = date_match.group(1).replace('/', '-')
            if len(d) == 10:
                date_str = d
        
        return {
            'period': period,
            'date': date_str,
            'front': front,
            'back': back
        }
    return None

def append_to_csv(period, draw_date, front, back):
    """追加新期号到CSV"""
    existing = set()
    with open(DLT_CSV, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row:
                existing.add(row[0])
    
    if period in existing:
        return False
    
    with open(DLT_CSV, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([period, draw_date] + front + back)
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
    """解析predict.md中的大乐透记录"""
    records = []
    pattern = r'## (\d+)期\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*大乐透\s*\|\s*\[([^\]]+)\](.*?)(?=## |$)'
    for match in re.finditer(pattern, content, re.DOTALL):
        period = match.group(1)
        draw_date = match.group(2)
        status = match.group(3).strip()
        
        bets = []
        numbers_section = match.group(4)
        if '下注记录' in numbers_section or '预测号码' in numbers_section:
            for line in numbers_section.split('\n'):
                line = line.strip()
                if re.match(r'-\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s*\+\s*\d{2}\s+\d{2}', line):
                    parts = line.replace('-', '').replace('+', ' ').split()
                    if len(parts) >= 7:
                        fronts = sorted([int(parts[i]) for i in range(5)])
                        backs = sorted([int(parts[5]), int(parts[6])])
                        bets.append({'fronts': fronts, 'backs': backs})
        
        if bets:
            records.append({
                'period': period,
                'date': draw_date,
                'status': status,
                'bets': bets
            })
    
    return records

def calculate_prize(pred_fronts, pred_backs, draw_fronts, draw_backs):
    """计算单注中奖金额"""
    front_hit = len(set(pred_fronts) & set(draw_fronts))
    back_hit = len(set(pred_backs) & set(draw_backs))
    
    if front_hit == 5 and back_hit == 2:
        return ('一等奖（浮动奖）', 0, 'float')
    elif front_hit == 5 and back_hit == 1:
        return ('二等奖（浮动奖）', 0, 'float')
    elif front_hit == 5 and back_hit == 0:
        return ('三等奖（浮动奖）', 0, 'float')
    elif front_hit == 4 and back_hit == 2:
        return ('四等奖', 3000, 'fixed')
    elif front_hit == 4 and back_hit == 1:
        return ('五等奖', 300, 'fixed')
    elif front_hit == 3 and back_hit == 2:
        return ('六等奖', 200, 'fixed')
    elif front_hit == 3 and back_hit == 1:
        return ('七等奖', 100, 'fixed')
    elif (front_hit == 1 and back_hit == 2) or (front_hit == 0 and back_hit == 2):
        return ('八等奖', 15, 'fixed')
    elif back_hit >= 1:
        return ('九等奖', 5, 'fixed')
    else:
        return ('未中奖', 0, 'none')

def main():
    today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    print(f"=== 大乐透开奖结果核对 {today_str} ===")
    
    # Step 1: 获取开奖数据（多渠道）
    print("\n--- Step 1: 获取开奖数据 ---")
    sources = search_latest_draw()
    print(f"获取到 {len(sources)} 个数据源")
    
    draw = None
    for src_name, src_data in sources.items():
        print(f"\n[{src_name}]")
        if isinstance(src_data, dict):
            print(f"  期号: {src_data.get('period')} 日期: {src_data.get('date')}")
            front_str = " ".join("%02d" % n for n in sorted(src_data.get('front', [])))
            back_str = " ".join("%02d" % n for n in sorted(src_data.get('back', [])))
            print(f"  号码: {front_str} + {back_str}")
            draw = src_data
        else:
            parsed = parse_draw_from_text(str(src_data))
            if parsed:
                print(f"  期号: {parsed['period']} 日期: {parsed['date']}")
                front_str = " ".join("%02d" % n for n in sorted(parsed['front']))
                back_str = " ".join("%02d" % n for n in sorted(parsed['back']))
                print(f"  号码: {front_str} + {back_str}")
                draw = parsed
    
    if not draw:
        print("[错误] 无法获取开奖数据")
        return
    
    # 验证日期
    if draw.get('date') != today_str:
        print(f"[注意] 开奖日期 {draw.get('date')} 与今日 {today_str} 不符，将使用搜索结果更新")
    
    print(f"\n使用开奖结果: {draw['period']}期 {draw['date']}")
    
    # Step 2: 更新CSV
    print("\n--- Step 2: 更新大乐透.csv ---")
    front_sorted = sorted(draw['front'])
    back_sorted = sorted(draw['back'])
    if append_to_csv(draw['period'], draw['date'], front_sorted, back_sorted):
        print(f"[新增] {draw['period']} 已写入CSV")
    else:
        print(f"[无需更新] {draw['period']} 已存在")
    
    # Step 3: 读取predict.md
    print("\n--- Step 3: 读取预测/下注记录 ---")
    with open(PREDICT_FILE, 'r') as f:
        content = f.read()
    
    records = parse_predictions(content)
    print(f"解析到 {len(records)} 条大乐透记录")
    
    # 找当期记录
    # 找当期记录：优先今日，若无则找最近一次
    current_records = [r for r in records if r['date'] == today_str]
    if not current_records:
        past_records = [r for r in records if r['date'] <= today_str]
        if past_records:
            latest = max(past_records, key=lambda r: r['date'])
            current_records = [latest]
            print(f"[注意] 今日({today_str})无记录，使用最近一次: {latest['period']}期 {latest['date']}")
        else:
            print(f"[无当期记录] 今日({today_str})无大乐透下注/预测记录")
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
                bet['fronts'], bet['backs'],
                front_sorted, back_sorted
            )
            print(f"  {i}: {' '.join('%02d'%n for n in bet['fronts'])} + {' '.join('%02d'%n for n in bet['backs'])} -> {prize_name}")
            
            if is_purchased and prize_type == 'fixed':
                total_win += prize_amount
        
        if is_purchased:
            record_block = re.search(rf'## {period}期.*?\|\s*已购\s*\*+\*+(.*?)(?=## |$)', content, re.DOTALL)
            if record_block:
                amount_match = re.search(r'下注金额.*?(\d+)', record_block.group(1))
                if amount_match:
                    total_cost += int(amount_match.group(1))
    
    # Step 5: 更新统计
    print("\n--- Step 5: 更新统计 ---")
    stats['dlt']['win'] = stats['dlt'].get('win', 0) + total_win
    stats['dlt']['cost'] = stats['dlt'].get('cost', 0) + total_cost
    stats['dlt']['draws'] = stats['dlt'].get('draws', 0) + 1
    save_stats(stats)
    
    print(f"本期中奖: {total_win}元")
    print(f"本期投入: {total_cost}元")
    print(f"累计投入: {stats['dlt']['cost']}元")
    print(f"累计中奖: {stats['dlt']['win']}元")
    print(f"累计期数: {stats['dlt']['draws']}期")
    if stats['dlt']['cost'] > 0:
        roi = (stats['dlt']['win'] / stats['dlt']['cost'] - 1) * 100
        print(f"累计收益率: {roi:.1f}%")
    
    # Step 6: 更新predict.md标记
    print("\n--- Step 6: 更新记录状态 ---")
    for rec in current_records:
        old_pattern = rf'({rec["period"]}期\s*\|\s*{rec["date"]}\s*\|\s*大乐透\s*\|\s*)\[已购\]'
        new_pattern = rf'\1[已核对]'
        content = re.sub(old_pattern, new_pattern, content)
    
    with open(PREDICT_FILE, 'w') as f:
        f.write(content)
    print("已将本期已购记录标记为[已核对]")
    
    print("\n=== 执行完成 ===")

if __name__ == '__main__':
    main()
