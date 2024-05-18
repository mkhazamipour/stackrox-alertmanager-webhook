from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route('/', methods=['POST', 'PUT'])
def webhook():
    json_data = request.get_json()
    if json_data["alert"]["id"] == "testalert":
        return "Test webhook received", 200
    elif json_data:
        # Forward JSON data to Alertmanager
        send_to_alertmanager(json_data)
        return jsonify({'message': 'JSON data forwarded to Alertmanager'}), 200
    else:
        return jsonify({'error': 'No JSON data received'}), 400

def send_to_alertmanager(json_data):
    alertmanager_url = os.environ.get("ALERTMANAGER_URL")+"/api/v2/alerts"
    headers = {"Content-Type": "application/json"}

    # Extract data from JSON
    alert = json_data["alert"]
    labels = {
        "ID": alert["id"],
        "PolicyName": alert["policy"]["name"],
        "PolicyDescription": alert["policy"]["description"],
        "ClusterName": alert["clusterName"],
        "Namespace": alert["namespace"],
        "Name": alert["deployment"]["name"],
        "Type": alert["deployment"]["type"],
        "ImageName": alert["deployment"]["containers"][0]["image"]["name"]["fullName"],
        "ContainerName": alert["deployment"]["containers"][0]["name"],
        "Time": alert["time"],
        "firstOccurred": alert["firstOccurred"],
        "Username": next(
            (attr["value"] for attr in alert.get("violations", [{}])[0].get("keyValueAttrs", {}).get("attrs", []) if attr["key"] == "Username"),
            "No-Username"
        )
    }

    # Prepare payload for Alertmanager
    payload = [{"labels": labels}]

    # Send payload to Alertmanager
    response = requests.post(alertmanager_url, headers=headers, json=payload)
    print(payload)

    # Check if request was successful
    if response.status_code == 200:
        print("Alert sent to Alertmanager successfully.")
    else:
        print("Error sending alert to Alertmanager:", response.text)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
