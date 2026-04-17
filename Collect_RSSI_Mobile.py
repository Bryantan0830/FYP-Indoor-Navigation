#!/data/data/com.termux/files/usr/bin/python3
import subprocess, json, csv, time, statistics, os
from datetime import datetime

# 建议换一个新的文件名，以免和旧数据混淆
SAVE_PATH = "/sdcard/Download/wifi_data_v2.csv"

def scan_wifi():
    try:
        out = subprocess.check_output(["termux-wifi-scaninfo"]).decode("utf-8")
        aps = json.loads(out)
    except Exception as e:
        print("❌ Error:", e)
        aps = []
    return aps

def collect_one_sample(location, sample_id, raw_scans=5, delay=1.5):
    ap_records = {}
    for i in range(raw_scans):
        print(f"  -> Raw Scan {i+1}/{raw_scans} ...")
        aps = scan_wifi()
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
    # 增加时间戳，便于后续按时间排查异常数据
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for bssid, info in ap_records.items():
        if info["rssis"]:
            avg = round(statistics.mean(info["rssis"]), 2)
            # 输出增加 timestamp 和 sample_id
            rows.append((timestamp, location, sample_id, info["ssid"], bssid, avg))
    return rows

def save_to_csv(rows):
    first_write = not os.path.exists(SAVE_PATH)
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    with open(SAVE_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if first_write:
            # 更新表头
            writer.writerow(["timestamp", "location", "sample_id", "ssid", "bssid", "avg_rssi"])
        for r in rows:
            writer.writerow(r)

def main():
    print("=== PWise Wi-Fi Fingerprint Auto-Collector ===")
    location = input("Enter Location (e.g., MSMR_3001 or L2_Corner_A): ").strip()

    try:
        total_samples = int(input("How many ML samples to collect? (e.g., 20 or 30): "))
    except ValueError:
        print("Invalid number. Defaulting to 10.")
        total_samples = 10

    try:
        raw_scans = int(input("How many raw scans per sample to average? (e.g., 3 or 5): "))
    except ValueError:
        raw_scans = 5

    print(f"\n🚀 Starting collection for {location}. Total ML Samples: {total_samples}")
    print("💡 Tip: Hold your phone and walk slowly around the area to capture signal variations.\n")

    for s in range(1, total_samples + 1):
        # 自动生成类似 MSMR_3001_S001 的 Sample ID
        sample_id = f"{location}_S{s:03d}"
        print(f"--- Collecting Sample {s}/{total_samples} [{sample_id}] ---")

        # 延迟设为 1.5 秒，加快整体速度
        rows = collect_one_sample(location, sample_id, raw_scans=raw_scans, delay=1.5)

        if rows:
            save_to_csv(rows)
            print(f"✅ Sample {s} saved! ({len(rows)} APs found)\n")
        else:
            print(f"⚠️ Sample {s} failed or no APs found.\n")

        if s < total_samples:
            time.sleep(1) # 批次之间稍微停顿 1 秒

    print(f"🎉 All {total_samples} samples collected for {location}! Saved to {SAVE_PATH}")

if __name__ == "__main__":
    main()
