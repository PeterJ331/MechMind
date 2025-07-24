# utils/cloud_model_api.py
import os
import requests

# ⚠️ 从环境变量读取 API KEY，安全性更高
API_KEY = os.getenv("OPENROUTER_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

def ask_cloud_model(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat-v3-32k",  # 或 "deepseek-chat"、"deepseek-coder"
        "messages": [
            {"role": "system", "content": "你是一个专业问答助手，请准确简洁地回答用户问题"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']
