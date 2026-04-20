#!/usr/bin/env python3
"""图片理解 - 使用 MiniMax API 直接调用图像理解能力"""
import base64
import json
import urllib.request
import urllib.error
import os
import sys

API_KEY_FILE = os.path.expanduser('~/.openclaw/agents/main/agent/auth-profiles.json')
API_HOST = 'https://api.minimaxi.com'
API_ENDPOINT = '/v1/coding_plan/vlm'

def get_api_key():
    """从 auth-profiles.json 读取 MiniMax API Key"""
    try:
        with open(API_KEY_FILE) as f:
            data = json.load(f)
        return data['profiles']['minimax:cn']['key']
    except (FileNotFoundError, KeyError) as e:
        print(f"无法读取API Key: {e}", file=sys.stderr)
        return None

def image_to_base64(filepath):
    """将图片转为 base64 编码"""
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def understand_image(image_path, prompt="描述这张图片的内容，提取所有文字和数字"):
    """
    调用 MiniMax 图像理解 API
    
    Args:
        image_path: 图片路径（本地文件）
        prompt: 提示词
    
    Returns:
        API 响应内容
    """
    api_key = get_api_key()
    if not api_key:
        return None
    
    # 图片转 base64
    if not os.path.exists(image_path):
        print(f"图片文件不存在: {image_path}", file=sys.stderr)
        return None
    
    img_b64 = image_to_base64(image_path)
    data_uri = f"data:image/jpeg;base64,{img_b64}"
    
    payload = json.dumps({
        "prompt": prompt,
        "image_url": data_uri
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{API_HOST}{API_ENDPOINT}",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            if result.get("base_resp", {}).get("status_code") == 0:
                return result.get("content", "")
            else:
                print(f"API错误: {result}", file=sys.stderr)
                return None
    except urllib.error.HTTPError as e:
        print(f"HTTP错误: {e.code} - {e.reason}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"URL错误: {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        return None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 image_understand.py <图片路径> [提示词]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "提取图片中所有文字和数字内容"
    
    result = understand_image(image_path, prompt)
    if result:
        print(result)
    else:
        print("图片理解失败", file=sys.stderr)
        sys.exit(1)