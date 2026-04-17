import requests
import json

# 假设服务器就在你的电脑上
url = "http://127.0.0.1:5000/predict"

# 假装你的手机在走廊里扫到了下面这些 Wi-Fi 信号 (包括垃圾信号和黄金信号)
fake_unity_data = {
    "scanned_aps": {
        "00:11:22:33:44:55": -65,  # 某个不知名热点
        "aa:bb:cc:dd:ee:ff": -50,  # 假设这是一个极强的黄金信号
        # 这里你可以随便编几个 MAC 地址和信号强度
    }
}

print("📱 [模拟手机] 正在向 Python 服务器发送 Wi-Fi 信号...")
response = requests.post(url, json=fake_unity_data)

print("📩 [服务器返回结果]:")
print(json.dumps(response.json(), indent=4, ensure_ascii=False))
