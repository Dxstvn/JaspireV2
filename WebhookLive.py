import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# We'll import the data retrieval functions
from merchant_data import get_merchant_info, get_location_info

load_dotenv()

app = Flask(__name__)

# In production, you might have a real DB to store and retrieve tokens keyed by merchant_id or location_id.
# For demo, let's just pretend we have a dictionary in memory.
# e.g., "location_id" -> "access_token"
fake_db_tokens = {}

# Example: after OAuth, you'd store something like:
# fake_db_tokens["LK98HJ23"] = "EAAA..."

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    This endpoint handles real-time notifications from Square.
    For a real app, configure this URL in your Square Developer Dashboard (Webhooks).
    """
    try:
        event_json = request.get_json()
        if not event_json:
            return jsonify({"message": "No JSON received"}), 400

        # For production, you should also verify the signature to ensure the request is from Square.
        # https://developer.squareup.com/docs/webhooks/overview#verify-webhook-signatures

        # Check the event type
        event_type = event_json["type"]  # e.g., "payment.created" or "payment.updated"
        data_object = event_json["data"]["object"]["payment"]

        payment_id = data_object["id"]
        location_id = data_object["location_id"]
        amount_money = data_object["amount_money"]  # e.g., {"amount": 100, "currency": "USD"}

        print(f"Received webhook: {event_type}, Payment ID: {payment_id}, Location ID: {location_id}")

        # 1) Identify which merchant is associated with this location_id
        # In a real scenario, you'd do a DB lookup:
        #   merchant_access_token = get_token_for_location(location_id)
        # For demo, let's see if we have it in our fake_db_tokens
        merchant_access_token = fake_db_tokens.get(location_id)
        if not merchant_access_token:
            print("No stored access token for this location. Unable to retrieve merchant data.")
            return jsonify({"message": "No access token found for location_id"}), 200

        # 2) Retrieve merchant info or location info in real time
        environment = os.getenv("SQ_ENVIRONMENT", "sandbox").lower()

        merchant_info = get_merchant_info(merchant_access_token, environment=environment)
        location_info = get_location_info(merchant_access_token, environment=environment, location_id=location_id)

        # Log or do something with the data
        if merchant_info:
            print("Merchant Business Name:", merchant_info.get("business_name"))
        if location_info:
            print("Location Nickname:", location_info.get("name"))

        # 3) Return a 200 so Square knows we received it
        return jsonify({"message": "Webhook processed"}), 200

    except Exception as e:
        print("Error handling webhook:", str(e))
        return jsonify({"message": "Internal error"}), 500

if __name__ == "__main__":
    # Run on port 5001 (for example). Ensure your Square Webhook is configured for this URL.
    app.run(host="0.0.0.0", port=8081, debug=True)
