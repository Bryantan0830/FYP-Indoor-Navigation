from flask import Flask, request, jsonify
import joblib
import pandas as pd

# Initialize Flask server
app = Flask(__name__)

print("========================================")
print("Starting PWise Indoor Navigation AI Engine...")
print("========================================")

# 1. Automatically load the trained 90% accuracy model and selected features at startup
try:
    # Make sure these two files are in the same folder as server.py
    wknn_model = joblib.load('pwise_wknn_model3.pkl')
    top_aps = joblib.load('pwise_top150_features3.pkl')
    print("AI Model (Hybrid RF-WKNN) loaded successfully!")
    print(f"Number of selected access points: {len(top_aps)}")
except Exception as e:
    print(f"Startup failed, model file not found: {e}")
    print("Please check whether the .pkl files are in the current folder!")

# 2. API endpoint accessible by Unity
# When Unity accesses http://your-ip-address:5000/predict,
# this function will be triggered
@app.route('/predict', methods=['POST'])
def predict_location():
    try:
        # Receive JSON data sent from Unity
        data = request.json

        # Expected Unity format:
        # {"scanned_aps": {"MAC1": -60, "MAC2": -80}}
        scanned_aps = data.get('scanned_aps', {})

        # ----------------------------------------
        # Core hybrid logic: RF feature filtering
        # ----------------------------------------
        # Initialize the 15 selected APs with default value -100
        # (assuming they are not detected)
        input_features = {ap: -100 for ap in top_aps}

        # If detected APs match the selected APs,
        # replace with actual RSSI values
        for bssid, rssi in scanned_aps.items():
            if bssid in input_features:
                input_features[bssid] = float(rssi)

        # Convert dictionary into a Pandas DataFrame
        # (single-row input for prediction)
        df_input = pd.DataFrame([input_features])

        # ----------------------------------------
        # Core hybrid logic: WKNN location prediction
        # ----------------------------------------
        prediction = wknn_model.predict(df_input)
        predicted_room = prediction[0]  # Extract predicted room name

        # Send prediction result back to Unity in JSON format
        return jsonify({
            "status": "success",
            "predicted_location": predicted_room,
            "message": "Location prediction successful."
        })

    except Exception as e:
        # Return error message to Unity if something goes wrong
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

if __name__ == '__main__':
    # Start the server
    # host='0.0.0.0' allows devices within the same local network
    # (e.g., mobile phone connected to the same Wi-Fi) to access it
    print("========================================")
    print("Server started. Waiting for Unity requests...")
    print("========================================")
    app.run(host='0.0.0.0', port=5000, debug=False)
