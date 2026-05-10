from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import uvicorn
import os
import csv
from datetime import datetime

# 1. 初始化 FastAPI 引擎
app = FastAPI(title="PWise AI Engine", description="室内导航定位 API")

print("========================================")
print("Starting PWise Indoor Navigation AI Engine...")
print("========================================")

# 2. 🛡️ 终极防弹模型加载 (自动寻找当前文件夹)
# 获取当前 python 文件所在的文件夹路径，防止找不到模型
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, 'pwise_wknn_model3.pkl')
features_path = os.path.join(current_dir, 'pwise_top150_features3.pkl')

try:
    wknn_model = joblib.load(model_path)
    top_aps = joblib.load(features_path)
    print("✅ AI Model (Hybrid RF-WKNN) loaded successfully!")
    print(f"📡 Number of selected access points: {len(top_aps)}")
except Exception as e:
    print(f"❌ Startup failed, model file not found: {e}")
    print(f"⚠️ 请确保以下两个文件存在于: {current_dir}")
    print(f"   1. {model_path}")
    print(f"   2. {features_path}")
    # 注意：如果这里报错了，接下来的程序虽然能跑，但一收到请求就会崩溃！

# 3. 定义数据格式
class WifiPayload(BaseModel):
    scanned_aps: dict

class FeedbackPayload(BaseModel):
    scanned_aps: dict
    corrected_location: str  # 用户纠正的房间名

# 4. 🎯 主力接口：接收定位请求
@app.post('/predict')
async def predict_location(payload: WifiPayload):
    try:
        scanned_aps = payload.scanned_aps
        print(f"📡 Unity 传来了 {len(scanned_aps)} 个 Wi-Fi 信号！")

        if len(scanned_aps) == 0:
            return {"status": "error", "message": "0 Wi-Fi detected! Please check phone GPS/Permissions."}

        # 特征过滤
        input_features = {ap: -100 for ap in top_aps}
        for bssid, rssi in scanned_aps.items():
            if bssid in input_features:
                input_features[bssid] = float(rssi)

        df_input = pd.DataFrame([input_features])

        # WKNN 预测
        prediction = wknn_model.predict(df_input)

        # 强制转换成纯文字，防止格式错误
        predicted_room = str(prediction[0])

        return {
            "status": "success",
            "predicted_location": predicted_room,
            "message": "Location prediction successful."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 5. 📥 新功能：众包反馈隔离区 (Feedback Receiver)
@app.post('/feedback')
async def receive_feedback(payload: FeedbackPayload):
    try:
        feedback_file = os.path.join(current_dir, 'user_feedback_data.csv')

        # 检查文件是否存在，不存在就先写个表头 (Header)
        file_exists = os.path.isfile(feedback_file)

        with open(feedback_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Timestamp', 'Corrected_Location', 'Raw_WiFi_Data'])

            # 写入：时间戳，纠正的房间，当时扫到的所有 WiFi 数据
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), payload.corrected_location, str(payload.scanned_aps)])

        print(f"📝 收到一条反馈！用户实际位置: {payload.corrected_location}")
        return {"status": "success", "message·": "Feedback safely stored in quarantine zone."}
    except Exception as e:
        return {"status": "error", "message": f"Feedback save failed: {str(e)}"}

# 6. 启动服务器
if __name__ == '__main__':
    print("========================================")
    print("🚀 FastAPI Server started. Waiting for Unity requests...")
    print("========================================")
    uvicorn.run(app, host="0.0.0.0", port=5000)

