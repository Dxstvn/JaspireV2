import os
from flask import Flask, request, render_template_string
from dotenv import load_dotenv
from square.client import Client

load_dotenv()

# Determine environment from .env, default to sandbox if not set
SQ_ENVIRONMENT = os.getenv('SQ_ENVIRONMENT', 'sandbox').lower()
SQ_APPLICATION_ID = os.getenv('SQ_APPLICATION_ID')
SQ_APPLICATION_SECRET = os.getenv('SQ_APPLICATION_SECRET')

# If you’re using the sandbox environment, you must use the sandbox base URL
if SQ_ENVIRONMENT == 'production':
    base_url = "https://connect.squareup.com"
else:
    base_url = "https://connect.squareupsandbox.com"

# Your real domain (no trailing slash). 
# e.g. "https://jaspire.co"
JASPIRE_DOMAIN = os.getenv('JASPIRE_DOMAIN', 'https://jaspire.co')

app = Flask(__name__)

# Inline HTML for demo purposes
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
    # Explicitly define your callback route
    redirect_uri = f"{JASPIRE_DOMAIN}/callback"
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
    redirect_uri = "https://jaspire.co/callback"
    
    # Exchange the authorization code for an access token
    body = {
        "client_id": SQ_APPLICATION_ID,
        "client_secret": SQ_APPLICATION_SECRET,
        "code": authorization_code,
        "grant_type": "authorization_code"
    }

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
    # Flask runs on port 8080; Nginx proxies from 80/443 -> 8080
    app.run(host="0.0.0.0", port=8080, debug=True)
