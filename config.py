import os
from dotenv import load_dotenv
from twilio.rest import Client
import mysql.connector

# Load environment variables
load_dotenv()

# Twilio credentials
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
default_receivers = os.getenv("SOS_RECEIVER_NUMBER")

client = Client(account_sid, auth_token)

def send_sos_sms(message, to_number=None):
    """
    Sends SOS SMS to one or multiple numbers.
    - If to_number is given → send only to that number.
    - Otherwise → send to all numbers in SOS_RECEIVER_NUMBER (.env, comma-separated).
    """
    try:
        if to_number:
            receiver_numbers = [to_number]
        else:
            receiver_numbers = default_receivers.split(",")

        results = []
        success = True
        error_msg = None

        for number in receiver_numbers:
            try:
                sms = client.messages.create(
                    body=message,
                    from_=twilio_number,
                    to=number.strip()
                )
                results.append(sms.sid)
            except Exception as e:
                success = False
                error_msg = str(e)

        return success, results if success else error_msg

    except Exception as e:
        return False, str(e)


# ✅ Optional: MySQL DB connection function
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "user"),
            database=os.getenv("DB_NAME", "women_safety")
        )
    except Exception as e:
        print(f"❌ DB connection failed: {e}")
        return None
