#!/usr/bin/env python3
"""识别彩票下注图片并录入predict.md
用户发送图片后自动调用
支持双色球和大乐透票面识别
"""
import re
import json
from datetime import date

BASE = '/root/.openclaw/workspace/彩票'
PREDICT_FILE = f'{BASE}/predict.md'
STATS_FILE = f'{BASE}/stats.json'

def load_stats():
    if __import__('os').path.exists(STATS_FILE):
        with open(STATS_FILE) as f:
            return json.load(f)
    return {'dlt': {'cost': 0, 'win': 0, 'draws': 0}, 'ssq': {'cost': 0, 'win': 0, 'draws': 0}}

def save_stats(stats):
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def parse_ssq_ticket(text):
    """解析双色球票面文本"""
    result = {
        'type': 'ssq',
        'period': None,
        'date': None,
        'bets': [],
        'amount': 0
    }
    
    # 期号
    period_match = re.search(r'(\d{7})', text)
    if period_match:
        result['period'] = period_match.group(1)
    
    # 日期
    date_match = re.search(r'(\d{2}-\d{2}-\d{2})', text)
    if date_match:
        result['date'] = '20' + date_match.group(1)
    
    # 金额
    amount_match = re.search(r'合计\s*(\d+)', text)
    if amount_match:
        result['amount'] = int(amount_match.group(1))
    
    # 号码（双色球格式：6个红球+1个蓝球）
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        # 匹配形如 "01 02 10 14 22 26-01" 的格式
        match = re.search(r'(\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2})-(\d{2})', line)
        if match:
            reds = [int(match.group(i)) for i in range(1, 7)]
            blue = int(match.group(7))
            result['bets'].append({
                'reds': reds,
                'blue': blue,
                'multiplier': 1
            })
            # 检查是否有倍数
            mult_match = re.search(r'\((\d+)\)', line)
            if mult_match:
                result['bets'][-1]['multiplier'] = int(mult_match.group(1))
    
    return result

def parse_dlt_ticket(text):
    """解析大乐透票面文本"""
    result = {
        'type': 'dlt',
        'period': None,
        'date': None,
        'bets': [],
        'amount': 0
    }
    
    # 期号
    period_match = re.search(r'(\d{5})', text)
    if period_match:
        result['period'] = period_match.group(1)
    
    # 日期
    date_match = re.search(r'(\d{2}-\d{2}-\d{2})', text)
    if date_match:
        result['date'] = '20' + date_match.group(1)
    
    # 金额
    amount_match = re.search(r'合计\s*(\d+)', text)
    if amount_match:
        result['amount'] = int(amount_match.group(1))
    
    # 号码（大乐透格式：5个前区+2个后区）
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        match = re.search(r'(\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2})\+(\d{2}\s+\d{2})', line)
        if match:
            fronts = [int(x) for x in match.group(1).split()]
            backs = [int(x) for x in match.group(2).split()]
            result['bets'].append({
                'fronts': fronts,
                'backs': backs,
                'multiplier': 1
            })
            mult_match = re.search(r'\((\d+)\)', line)
            if mult_match:
                result['bets'][-1]['multiplier'] = int(mult_match.group(1))
    
    return result

def format_bet(ticket):
    """格式化下注记录"""
    if ticket['type'] == 'ssq':
        lines = []
        for bet in ticket['bets']:
            red_str = ' '.join('%02d' % r for r in bet['reds'])
            blue_str = '%02d' % bet['blue']
            mult = bet['multiplier']
            lines.append(f"- {red_str} + {blue_str}" + (f"（{mult}注）" if mult > 1 else ""))
        return '\n'.join(lines)
    else:
        lines = []
        for bet in ticket['bets']:
            front_str = ' '.join('%02d' % f for f in bet['fronts'])
            back_str = ' '.join('%02d' % b for b in bet['backs'])
            mult = bet['multiplier']
            lines.append(f"- {front_str} + {back_str}" + (f"（{mult}注）" if mult > 1 else ""))
        return '\n'.join(lines)

def update_predict_file(ticket):
    """更新predict.md"""
    with open(PREDICT_FILE, 'r') as f:
        content = f.read()
    
    type_name = '双色球' if ticket['type'] == 'ssq' else '大乐透'
    period_str = ticket['period']
    date_str = ticket['date']
    
    # 构建新记录
    new_record = f"## {period_str}期 | {date_str} | {type_name} | [已购]\n\n"
    new_record += f"**下注记录：**\n"
    new_record += format_bet(ticket) + "\n"
    new_record += f"\n**下注金额：** {ticket['amount']}元\n"
    new_record += f"\n---\n\n"
    
    # 查找是否已有该期记录
    existing_pattern = rf'## {period_str}期.*?\|.*?\|.*?\|\s*\[.*?\]\s*\n\n'
    if re.search(existing_pattern, content):
        # 替换已有记录
        content = re.sub(existing_pattern, new_record, content)
    else:
        # 在"---"之后插入新记录
        if '---' in content:
            parts = content.split('---', 1)
            content = parts[0] + '---\n\n' + new_record + '---'.join(parts[1:])
        else:
            content = new_record + content
    
    with open(PREDICT_FILE, 'w') as f:
        f.write(content)

def update_stats(ticket):
    """更新统计"""
    stats = load_stats()
    key = 'ssq' if ticket['type'] == 'ssq' else 'dlt'
    
    stats[key]['cost'] += ticket['amount']
    # 注意：这里的win是累计中奖金额，需要开奖后更新
    # 此处只更新投入
    stats[key]['draws'] = stats[key].get('draws', 0) + 1
    
    save_stats(stats)

def process_ticket(image_text, lottery_type=None):
    """处理票面识别结果
    image_text: 从图片识别出的文本
    lottery_type: 'ssq' 或 'dlt'，如果为None则自动判断
    """
    # 自动判断彩种
    if lottery_type is None:
        if '双色球' in image_text or '红球' in image_text or re.search(r'\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}-\d{2}', image_text):
            lottery_type = 'ssq'
        elif '大乐透' in image_text or '前区' in image_text or re.search(r'\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\+\d{2}\s+\d{2}', image_text):
            lottery_type = 'dlt'
    
    if lottery_type == 'ssq':
        ticket = parse_ssq_ticket(image_text)
    elif lottery_type == 'dlt':
        ticket = parse_dlt_ticket(image_text)
    else:
        return {'error': '无法识别彩种'}
    
    if not ticket['bets']:
        return {'error': '未能解析到下注号码', 'ticket': ticket}
    
    update_predict_file(ticket)
    update_stats(ticket)
    
    return {
        'success': True,
        'ticket': ticket,
        'message': f"已录入：{ticket['period']}期 {('双色球' if ticket['type']=='ssq' else '大乐透')} {ticket['amount']}元 {len(ticket['bets'])}注"
    }

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("用法: python3 识别下注图片.py <图片识别文本> [ssq|dlt]")
        sys.exit(1)
    
    image_text = sys.argv[1]
    lottery_type = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = process_ticket(image_text, lottery_type)
    print(json.dumps(result, ensure_ascii=False, indent=2))
