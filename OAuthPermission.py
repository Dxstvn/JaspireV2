import os
from flask import Flask, request, redirect, render_template_string
from dotenv import load_dotenv
from square.client import Client

# Load environment variables from .env
load_dotenv()

SQ_ENVIRONMENT = os.getenv('SQ_ENVIRONMENT', 'sandbox').lower()
print("DEBUG: SQ_ENVIRONMENT is:", repr(SQ_ENVIRONMENT))

# Read environment variables
SQ_ENVIRONMENT = os.getenv('SQ_ENVIRONMENT', 'sandbox').lower()
SQ_APPLICATION_ID = os.getenv('SQ_APPLICATION_ID')
SQ_APPLICATION_SECRET = os.getenv('SQ_APPLICATION_SECRET')

# Determine base URL depending on environment
if SQ_ENVIRONMENT == 'production':
    base_url = "https://connect.squareup.com"
else:
    base_url = "https://connect.squareupsandbox.com"

# Initialize the Square Python SDK client
client = Client(
    environment=SQ_ENVIRONMENT,
    user_agent_detail="Jaspire_Card_OAuth_Sample"  # optional
)

obtain_token = client.o_auth.obtain_token

app = Flask(__name__)

# Inline HTML templates (for demo). In production, use proper templates.
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Square OAuth Sample</title>
</head>
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
<head>
    <title>Square OAuth Callback</title>
</head>
<body style="font-family: sans-serif;">
    <h1>{{ title }}</h1>
    <div>{{ message|safe }}</div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    """
    The home route provides a link to Square's OAuth authorization page.
    """
    authorize_url = f"{base_url}/oauth2/authorize?client_id={SQ_APPLICATION_ID}"
    return render_template_string(INDEX_HTML, authorize_url=authorize_url)

@app.route("/callback", methods=["GET"])
def callback():
    """
    This is the Redirect URL where Square sends the user after authorization.
    It extracts the authorization code, exchanges it for an access token, and displays the result.
    """
    authorization_code = request.args.get("code")
    error = request.args.get("error")
    state = request.args.get("state")  # If you implement a 'state' param, verify it here.

    if error:
        # If Square returned an error, handle it here (e.g., user declined).
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

    response = obtain_token(body)

    if response.is_success():
        # If successful, you'll get an access token, refresh token, etc.
        tokens = response.body
        # Store tokens securely. For demonstration, we just display them.
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
        # The token exchange failed. Print the errors for debugging.
        errors = response.errors
        return render_template_string(
            CALLBACK_HTML,
            title="Token Exchange Failed",
            message=f"Errors: {errors}"
        )

if __name__ == "__main__":
    # Now runs on port 5000 instead of 8080
    app.run(host="0.0.0.0", port=8080, debug=True)
