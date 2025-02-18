import os
from flask import Flask, request, render_template_string
from dotenv import load_dotenv
from square.client import Client

load_dotenv()

# environment defaults to "sandbox" if not set
SQ_ENVIRONMENT = os.getenv('SQ_ENVIRONMENT', 'sandbox').lower()
SQ_APPLICATION_ID = os.getenv('SQ_APPLICATION_ID')
SQ_APPLICATION_SECRET = os.getenv('SQ_APPLICATION_SECRET')

# Determine base URL depending on environment
if SQ_ENVIRONMENT == 'production':
    base_url = "https://connect.squareup.com"
else:
    base_url = "https://connect.squareupsandbox.com"

# The domain from ngrok or your real domain
# e.g. "https://xxxx-18-217-229-6.ngrok-free.app"
# Make sure to NOT have a trailing slash
NGROK_URL = os.getenv('NGROK_URL', 'https://xxxx-18-217-229-6.ngrok-free.app')

app = Flask(__name__)

# Inline HTML templates (for demo). In production, use proper templates.
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><title>Square OAuth Sample</title></head>
<body style="font-family: sans-serif;">
    <h1>Square OAuth Sample</h1>
    <p>This page serves a link that merchants click to authorize your application.</p>
    <a href="{{ authorize_url }}"><button>Authorize with Square</button></a>
</body>
</html>
"""

CALLBACK_HTML = """
<!DOCTYPE html>
<html>
<head><title>Square OAuth Callback</title></head>
<body style="font-family: sans-serif;">
    <h1>{{ title }}</h1>
    <div>{{ message|safe }}</div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    # The explicit redirect_uri is your callback route on the same domain
    redirect_uri = f"{NGROK_URL}/callback"
    # Include scope, e.g., MERCHANT_PROFILE_READ + PAYMENTS_WRITE
    scope = "MERCHANT_PROFILE_READ+PAYMENTS_WRITE"

    # Build the full authorize URL
    authorize_url = (
        f"{base_url}/oauth2/authorize"
        f"?client_id={SQ_APPLICATION_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&state=some_random_state_value"
    )

    print("DEBUG authorize_url:", authorize_url)

    return render_template_string(INDEX_HTML, authorize_url=authorize_url)

@app.route("/callback", methods=["GET"])
def callback():
    authorization_code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return render_template_string(
            CALLBACK_HTML,
            title="Authorization Failed",
            message=f"Square returned an error: {error}"
        )

    if not authorization_code:
        return render_template_string(
            CALLBACK_HTML,
            title="Authorization Failed",
            message="No authorization code provided in callback."
        )

    # Exchange the authorization code for an access token
    body = {
        "client_id": SQ_APPLICATION_ID,
        "client_secret": SQ_APPLICATION_SECRET,
        "code": authorization_code,
        "grant_type": "authorization_code"
    }

    # Initialize the Square client for token exchange
    client = Client(environment=SQ_ENVIRONMENT)
    response = client.o_auth.obtain_token(body)

    if response.is_success():
        tokens = response.body
        message = f"""
        <p>Authorization Succeeded!</p>
        <p><strong>Access Token:</strong> {tokens['access_token']}</p>
        <p><strong>Refresh Token:</strong> {tokens['refresh_token']}</p>
        <p><strong>Expires At:</strong> {tokens['expires_at']}</p>
        <p><strong>Merchant ID:</strong> {tokens['merchant_id']}</p>
        <p>Use the access token to call Square APIs on behalf of this merchant.</p>
        <p>In a real app, you would encrypt and store these tokens securely in a database.</p>
        """
        return render_template_string(CALLBACK_HTML, title="Authorization Succeeded", message=message)
    else:
        errors = response.errors
        return render_template_string(
            CALLBACK_HTML,
            title="Token Exchange Failed",
            message=f"Errors: {errors}"
        )

if __name__ == "__main__":
    # Make sure your server port matches what you open in security group or ngrok
    app.run(host="0.0.0.0", port=8080, debug=True)
