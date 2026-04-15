#!/usr/bin/env python3
"""
兆易创新实时行情获取脚本
数据来源: 腾讯财经 HTTP API (qt.gtimg.cn)
使用: python3 fetch_realtime.py [股票代码]

股票代码示例:
  sh603986   兆易创新 (A股东京)
  sh600519  贵州茅台
  usNVDA    英伟达
  usAAPL    苹果
  sh000001  上证指数
  sz399006  创业板指
"""

import sys
import urllib.request
import json

# 配置
BASE_URL = "http://qt.gtimg.cn/q="
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def fetch_quote(codes):
    """获取实时行情，支持多股票批量查询"""
    if isinstance(codes, str):
        codes = [codes]
    
    url = BASE_URL + ",".join(codes)
    req = urllib.request.Request(url, headers=HEADERS)
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        # 腾讯接口返回GBK编码
        raw = resp.read()
        try:
            text = raw.decode('gbk')
        except UnicodeDecodeError:
            text = raw.decode('utf-8', errors='replace')
    
    # 解析结果
    results = {}
    for line in text.strip().split('\n'):
        if '=' not in line:
            continue
        key, val = line.split('=', 1)
        if val.strip() == '"1~";' or not val.strip():
            continue
        
        parts = val.strip().lstrip('"').rstrip('";').split('~')
        if len(parts) < 35:
            continue
        
        code = key.replace('v_', '')
        
        # 解析字段
        try:
            results[code] = {
                'name':     parts[1],
                'code':     parts[2],
                'price':    float(parts[3]) if parts[3] else None,
                'open':     float(parts[4]) if parts[4] else None,
                'high':     float(parts[33]) if parts[33] else None,
                'low':      float(parts[34]) if parts[34] else None,
                'change':   float(parts[31]) if parts[31] else None,
                'change_pct': float(parts[32]) if parts[32] else None,
                'volume':   int(parts[6]) if parts[6] else None,       # 手
                'datetime': parts[30] if len(parts) > 30 else None,
                'high_52w': float(parts[47]) if len(parts) > 47 and parts[47] else None,
                'low_52w':  float(parts[48]) if len(parts) > 48 and parts[48] else None,
            }
            # 成交量(手) -> 万手
            if results[code]['volume']:
                results[code]['volume_wan'] = results[code]['volume'] / 10000
        except (ValueError, IndexError):
            continue
    
    return results


def format_quote(data, code):
    """格式化输出行情"""
    if code not in data:
        return f"未找到股票: {code}"
    
    d = data[code]
    change = d.get('change', 0)
    change_pct = d.get('change_pct', 0)
    arrow = '↑' if change >= 0 else '↓'
    color = '+' if change >= 0 else ''
    
    lines = [
        f"📊 {d['name']}({d['code']})",
        f"{'─'*30}",
        f"  当前价:  {d['price']} {arrow} {color}{change:.2f} ({color}{change_pct:+.2f}%)",
        f"  开盘:    {d['open']}",
        f"  最高:    {d['high']}",
        f"  最低:    {d['low']}",
        f"  成交量:  {d.get('volume_wan', 0):.2f}万手",
        f"  52周区间: {d.get('low_52w', 0):.2f} ~ {d.get('high_52w', 0):.2f}",
        f"  更新时间: {d.get('datetime', 'N/A')}",
    ]
    return '\n'.join(lines)


def main():
    # 默认查询兆易创新
    codes = ['sh603986']
    
    if len(sys.argv) > 1:
        codes = sys.argv[1:]
    
    print(f"正在查询: {codes}\n")
    
    try:
        data = fetch_quote(codes)
        for code in codes:
            print(format_quote(data, code))
            print()
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
