import time

import requests

# notify_url = 'https://notify.king-sms.com/global_pay_in_notify'
notify_url = 'https://notify.king-sms.com/user'

headers = {'Content-Type': 'application/json'}

notify_data = {
    "state": 1,
    "sysOrderNo": "20210817100000000000000001",
    "mchOrderNo": "20210817100000000000000001",
    "amount": 10000,
    "sign": "12345678900987654321",
}

user_id = 125353
url = f"{notify_url}/{user_id}"

start = time.perf_counter_ns()
try:
    # 发送 GET 请求
    response = requests.get(url, headers=headers)

    # 打印响应状态码
    print(f"状态码: {response.status_code}")

    # 尝试解析 JSON 响应（如果 API 返回 JSON）
    try:
        json_response = response.json()
        print("响应内容 (JSON):")
        print(json_response)
    except ValueError:
        # 如果解析 JSON 失败，打印原始文本
        print("响应内容 (原始文本):")
        print(response.text)

except requests.exceptions.RequestException as e:
    # 处理网络请求异常
    print(f"请求失败: {e}")

end = time.perf_counter_ns()
elapsed_ms = (end - start) / 1_000_000
print(f"耗时: {elapsed_ms:.6f} 毫秒")

