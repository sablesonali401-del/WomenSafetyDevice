from flask import Flask, render_template, request, jsonify
from config import get_db_connection, send_sos_sms
from datetime import datetime

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/send_sos", methods=["POST"])
def send_sos():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No JSON payload"}), 400

    lat = data.get("latitude")
    lon = data.get("longitude")
    address = data.get("address", "Unknown location")  # 👈 new field
    receiver = data.get("receiver")  # optional override

    if lat is None or lon is None:
        return jsonify({"status": "error", "message": "latitude and longitude are required"}), 400

    # Compose message with Google Maps link + address
    message = (
        f"🚨 SOS Alert!\n"
        f"📍 Location: https://maps.google.com/?q={lat},{lon}\n"
        f"🏠 Address: {address}"
    )

    # Send SMS
    success, info = send_sos_sms(message, to_number=receiver)

    # store into DB (best-effort)
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            status = "sent" if success else "failed"
            insert_query = """
                INSERT INTO sos_alerts (latitude, longitude, address, receiver, message, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (lat, lon, address, receiver or '', message, status))
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"❌ DB insert error: {e}")
        finally:
            conn.close()

    if success:
        return jsonify({"status": "success", "message": "SOS alert sent!"})
    else:
        return jsonify({"status": "error", "message": f"Failed to send SMS: {info}"}), 500


@app.route("/history", methods=["GET"])
def history():
    """
    Optional endpoint to view recent alerts. Returns JSON list of alerts.
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "DB connection failed"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, latitude, longitude, address, receiver, message, status, sent_at FROM sos_alerts ORDER BY sent_at DESC LIMIT 50"
        )
        rows = cursor.fetchall()
        cursor.close()
        return jsonify({"status": "success", "data": rows})
    except Exception as e:
        print(f"❌ DB read error: {e}")
        return jsonify({"status": "error", "message": "Failed to fetch history"}), 500
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
