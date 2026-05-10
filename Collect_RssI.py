import subprocess, csv, time, statistics, os
from datetime import datetime

# 1. 保存在电脑当前运行的文件夹下
SAVE_PATH = r"D:\Final_Year_Project\Code\wifi_data_pc_real.csv"

def scan_wifi_windows():
    aps = []
    try:
        # 调用 Windows 系统底层命令扫描 BSSID
        result = subprocess.check_output(["netsh", "wlan", "show", "networks", "mode=bssid"])

        # 兼容中文版 Windows (GBK) 和 英文版 Windows (UTF-8)
        try:
            output = result.decode("gbk")
        except:
            output = result.decode("utf-8", errors="ignore")

        current_ssid = ""
        current_bssid = ""

        for line in output.split('\n'):
            line = line.strip()

            # 抓取路由器名称
            if line.startswith("SSID"):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    current_ssid = parts[1].strip()

            # 抓取路由器 MAC 地址
            elif "BSSID" in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    current_bssid = parts[1].strip()

            # 抓取信号强度（同时兼容中文"信号"和英文"Signal"）
            elif "Signal" in line or "信号" in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    signal_pct_str = parts[1].strip().replace("%", "")
                    try:
                        signal_pct = int(signal_pct_str)
                        # 🌟 核心换算：将 Windows 的百分比转换为与安卓一致的 dBm！
                        rssi_dbm = int((signal_pct / 2) - 100)

                        aps.append({
                            "ssid": current_ssid,
                            "bssid": current_bssid,
                            "rssi": rssi_dbm
                        })
                    except ValueError:
                        pass
    except Exception as e:
        print("❌ Windows Wi-Fi 扫描失败:", e)

    return aps

def collect_one_sample(location, sample_id, raw_scans=5, delay=1.5):
    ap_records = {}
    for i in range(raw_scans):
        print(f"  -> 正在进行第 {i+1}/{raw_scans} 次网卡扫描 ...")

        # 替换为调用 Windows 的扫描函数
        aps = scan_wifi_windows()

        for ap in aps:
            b = ap.get("bssid", "")
            s = ap.get("ssid", "")
            r = ap.get("rssi")
            if not b:
                continue
            if b not in ap_records:
                ap_records[b] = {"ssid": s, "rssis": []}
            if r is not None:
                ap_records[b]["rssis"].append(r)

        time.sleep(delay)

    rows = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for bssid, info in ap_records.items():
        if info["rssis"]:
            avg = round(statistics.mean(info["rssis"]), 2)
            rows.append((timestamp, location, sample_id, info["ssid"], bssid, avg))
    return rows

def save_to_csv(rows):
    first_write = not os.path.exists(SAVE_PATH)

    # 修复路径报错：先获取文件夹路径
    dir_name = os.path.dirname(SAVE_PATH)
    # 只有当 dir_name 不是空字符串时，才去尝试创建文件夹
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    # 加上 encoding='utf-8-sig' 防止 Excel 打开时中文字符乱码
    with open(SAVE_PATH, "a", newline="", encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        if first_write:
            writer.writerow(["timestamp", "location", "sample_id", "ssid", "bssid", "avg_rssi"])
        for r in rows:
            writer.writerow(r)

def main():
    print("=== PWise Wi-Fi Fingerprint Collector (Windows 真实网卡版) ===")
    location = input("Enter Location (e.g., MSMR_3001 或 My_Room): ").strip()

    try:
        total_samples = int(input("How many ML samples to collect? (建议 5-10): "))
    except ValueError:
        total_samples = 5

    try:
        raw_scans = int(input("How many raw scans per sample to average? (建议 3-5): "))
    except ValueError:
        raw_scans = 3

    print(f"\n🚀 开始采集 {location} 的真实 Wi-Fi 数据...")

    for s in range(1, total_samples + 1):
        sample_id = f"{location}_S{s:03d}"
        print(f"--- Collecting Sample {s}/{total_samples} [{sample_id}] ---")

        rows = collect_one_sample(location, sample_id, raw_scans=raw_scans, delay=1.5)

        if rows:
            save_to_csv(rows)
            print(f"✅ Sample {s} 保存成功! (找到 {len(rows)} 个 AP)\n")
        else:
            print(f"⚠️ Sample {s} 失败或未找到任何 Wi-Fi 信号。\n")

        if s < total_samples:
            time.sleep(1)

    print(f"🎉 采集完成！数据已保存至当前目录下的 {SAVE_PATH}")

if __name__ == "__main__":
    main()
