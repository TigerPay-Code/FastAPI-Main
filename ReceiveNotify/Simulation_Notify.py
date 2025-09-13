import requests

notify_url = 'https://notify.king-sms.com/global_pay_in_notify'

headers = {'Content-Type': 'application/json'}

notify_data = {
    "state": 1,
    "sysOrderNo": "20210817100000000000000001",
    "mchOrderNo": "20210817100000000000000001",
    "amount": 10000,
    "sign": "12345678900987654321",
}

request_return = requests.post(
    url=notify_url,
    headers=headers,
    json=notify_data,
    timeout=5
)

print(request_return.text)

