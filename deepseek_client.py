# deepseek_client.py
#
# import requests
#
# class DeepSeekClient:
#     def __init__(self, model="deepseek-r1:8b", base_url="http://localhost:11434"):
#         self.model = model
#         self.base_url = base_url
#
#     def ask(self, prompt):
#         url = f"{self.base_url}/api/generate"
#         data = {
#             "model": self.model,
#             "prompt": prompt,
#             "stream": False
#         }
#         response = requests.post(url, json=data)
#         if response.status_code == 200:
#             return response.json()["response"]
#         else:
#             return f"Error: {response.status_code} {response.text}"



import os
import requests
from dotenv import load_dotenv

load_dotenv()

class DeepSeekClient:
    def __init__(self, model="deepseek-r1:8b", base_url="http://localhost:11434"):
        self.local_model = model
        self.local_base_url = base_url
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_base_url = "https://openrouter.ai/api/v1"

    def ask(self, prompt, model_type="local", model_name=None):
        if model_type == "openrouter":
            return self._ask_openrouter(prompt, model_name)
        else:
            return self._ask_local(prompt)

    def _ask_local(self, prompt):
        url = f"{self.local_base_url}/api/generate"
        data = {
            "model": self.local_model,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"本地模型调用失败: {response.status_code} {response.text}"

    def _ask_openrouter(self, prompt, model_name):
        if not self.openrouter_api_key:
            return "错误: 未配置OpenRouter API密钥"
        url = f"{self.openrouter_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model_name or "deepseek/deepseek-chat:free",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            return f"OpenRouter API调用失败: {str(e)}"
