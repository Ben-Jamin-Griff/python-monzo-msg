import os
import requests
import secrets
from urllib.parse import urlencode
from dotenv import load_dotenv
import logging
from twilio.rest import Client
from flask import Flask, request, redirect

load_dotenv()

# Set up logging configuration
logging.basicConfig(level=logging.INFO,  # Set the logging level
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # Format for the log messages

logger = logging.getLogger(__name__)

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

twil_id = os.getenv("TWILIO_ACCOUNT_ID")
twil_token = os.getenv("TWILIO_WUTH_TOKEN")
twil_number = os.getenv("TWILIO_NUMBER")
my_number = os.getenv("MY_NUMBER")

client = Client(twil_id, twil_token)

event_ids = []

app = Flask(__name__)

@app.route('/')
def index():
    logger.info("Welcome")
    return f'Welcome to the Monzo callback server.', 200

@app.route('/login')
def login():
    # Generate a random state token for CSRF protection
    state_token = secrets.token_urlsafe(32)
    # Step 1: Redirect the user to Monzo for authorization
    params = {
        "client_id": client_id,
        "redirect_uri": 'http://localhost:8000/callback',
        "response_type": "code",
        "state": state_token
    }
    
    auth_url = f"https://auth.monzo.com/?{urlencode(params)}"
    
    return redirect(auth_url) 

@app.route('/accounts')
def accounts():
    headers = {
        "Authorization": f'Bearer {os.getenv("ACCESS_TOKEN")}'
    }
    
    url = "https://api.monzo.com/accounts"
    
    response = requests.get(url, headers=headers)
    
    return response.json(), 200

@app.route('/callback')
def callback():
    code = request.args.get('code')
    
    # Step 3: Exchange the authorization code for an access token
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": 'http://localhost:8000/callback',
        "code": code,
    }
    
    response = requests.post("https://api.monzo.com/oauth2/token", data=data)
    response.raise_for_status()
    
    os.environ['ACCESS_TOKEN'] = response.json()['access_token']
        
    return "Visit your Monzo app to grant this token account permissions", 200

@app.route('/token')
def token():    
    return f'Token: {os.getenv("ACCESS_TOKEN")}', 200

@app.route('/hook', methods=['POST'])
def hook():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.data
    
    logger.info(f"Headers: {request.headers}")        
    logger.info(f"JSON payload: {data}")
    
    if data['type'] == 'transaction.created':
        if data['data']['id'] not in event_ids:
            event_ids.append(data['data']['id'])
            
            moved_amount = abs(int(data['data']['amount']/100))
            
            logger.info(f"Sending message to: {my_number}")
            message = client.messages.create(
                    body=f"You just moved £{moved_amount} around in Monzo!",
                    from_=twil_number,
                    to=my_number
                 )
            
    return "Webhook received", 200
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)