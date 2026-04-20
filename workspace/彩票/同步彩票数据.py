#!/usr/bin/env python3
"""彩票历史数据同步脚本
从55128.cn抓取双色球和大乐透历史开奖数据
"""
import re
import csv
import time
import subprocess

BASE = '/root/.openclaw/workspace/彩票'
SSQ_CSV = f'{BASE}/双色球.csv'
DLT_CSV = f'{BASE}/大乐透.csv'

def fetch_url(url):
    """获取网页内容"""
    try:
        r = subprocess.run(['python3', '-c', 
            f'import urllib.request; r=urllib.request.urlopen("{url}", timeout=15); print(r.read().decode("utf-8")[:20000])'],
            capture_output=True, text=True, timeout=20)
        if r.returncode == 0:
            return r.stdout
    except Exception as e:
        print(f"  fetch error: {e}")
    return ""

def parse_ssq_page(html):
    """解析双色球页面数据"""
    records = []
    # 匹配格式: 2026-04-19 2026043 06 09 14 16 25 32 16
    pattern = r'(\d{4}-\d{2}-\d{2})\s+(202\d{3})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})'
    for m in re.finditer(pattern, html):
        date = m.group(1)
        period = m.group(2)
        reds = [m.group(i) for i in [3,4,5,6,7,8]]
        blue = m.group(9)
        records.append((period, date, reds, blue))
    return records

def parse_dlt_page(html):
    """解析大乐透页面数据"""
    records = []
    # 匹配格式: 2026-04-18 26041 04 09 17 30 33 05 09
    # 大乐透期号格式: 5位数字如26041
    pattern = r'(\d{4}-\d{2}-\d{2})\s+(\d{5})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})'
    for m in re.finditer(pattern, html):
        date = m.group(1)
        period = m.group(2)
        fronts = [m.group(i) for i in [3,4,5,6,7]]
        backs = [m.group(i) for i in [8,9]]
        records.append((period, date, fronts, backs))
    return records

def load_existing(csv_file):
    """加载已有期号集合"""
    existing = set()
    try:
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if row:
                    existing.add(row[0])
    except:
        pass
    return existing

def save_csv(csv_file, records, is_ssq=True):
    """保存到CSV，按期号倒序（最新在前），新数据插入到表头之后"""
    existing = load_existing(csv_file)
    
    # 过滤已存在的
    new_records = [r for r in records if r[0] not in existing]
    
    if not new_records:
        print(f"  {csv_file.split('/')[-1]}: 无新数据")
        return 0
    
    # 按期号排序（倒序，最新的在前）
    new_records.sort(key=lambda x: x[0], reverse=True)
    
    # 读取现有内容（含表头）
    with open(csv_file, 'r') as f:
        content = f.read()
    
    # 构建新记录行
    new_lines = []
    for rec in new_records:
        if is_ssq:
            line = ",".join([rec[0], rec[1]] + rec[2] + [rec[3]])
        else:
            line = ",".join([rec[0], rec[1]] + rec[2] + rec[3])
        new_lines.append(line)
    
    # 插入到表头之后（保持倒序）
    lines = content.split('\n')
    header = lines[0]
    existing_data = "\n".join(lines[1:])
    
    new_content = header + "\n" + "\n".join(new_lines)
    if existing_data.strip():
        new_content += "\n" + existing_data
    
    with open(csv_file, 'w') as f:
        f.write(new_content)
    
    print(f"  {csv_file.split('/')[-1]}: 新增 {len(new_records)} 条 (最新: {new_records[0][0]})")
    return len(new_records)

def main():
    print("=== 彩票历史数据同步 ===\n")
    
    # ===== 双色球 =====
    print("正在获取双色球数据...")
    ssq_urls = [
        'https://www.55128.cn/kjh/fcssq-history-120.htm',
        'https://www.55128.cn/kjh/fcssq-history-200.htm',
    ]
    
    all_ssq = []
    for url in ssq_urls:
        print(f"  获取: {url.split('/')[-1]}")
        html = fetch_url(url)
        records = parse_ssq_page(html)
        all_ssq.extend(records)
        print(f"    解析到 {len(records)} 条")
        time.sleep(0.5)
    
    if all_ssq:
        # 去重
        seen = set()
        unique_ssq = []
        for r in all_ssq:
            if r[0] not in seen:
                seen.add(r[0])
                unique_ssq.append(r)
        save_csv(SSQ_CSV, unique_ssq, is_ssq=True)
    
    print()
    
    # ===== 大乐透 =====
    print("正在获取大乐透数据...")
    dlt_urls = [
        'https://www.55128.cn/kjh/fcdlt-history-120.htm',
        'https://www.55128.cn/kjh/fcdlt-history-200.htm',
    ]
    
    all_dlt = []
    for url in dlt_urls:
        print(f"  获取: {url.split('/')[-1]}")
        html = fetch_url(url)
        records = parse_dlt_page(html)
        all_dlt.extend(records)
        print(f"    解析到 {len(records)} 条")
        time.sleep(0.5)
    
    if all_dlt:
        seen = set()
        unique_dlt = []
        for r in all_dlt:
            if r[0] not in seen:
                seen.add(r[0])
                unique_dlt.append(r)
        save_csv(DLT_CSV, unique_dlt, is_ssq=False)
    
    print("\n=== 同步完成 ===")

if __name__ == '__main__':
    main()
