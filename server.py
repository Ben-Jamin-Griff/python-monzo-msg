import os
import requests
import secrets
from urllib.parse import urlencode
from dotenv import load_dotenv
load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

redirect_uri = 'http://localhost:8000/callback'

from flask import Flask, request, redirect

app = Flask(__name__)

@app.route('/')
def index():
    return f'Welcome to the Monzo callback server.', 200

@app.route('/login')
def login():
    # Generate a random state token for CSRF protection
    state_token = secrets.token_urlsafe(32)
    # Step 1: Redirect the user to Monzo for authorization
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
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
        "redirect_uri": redirect_uri,
        "code": code,
    }
    
    response = requests.post("https://api.monzo.com/oauth2/token", data=data)
    response.raise_for_status()
    
    print(response.json())
    
    os.environ['ACCESS_TOKEN'] = response.json()['access_token']
        
    return "Visit your Monzo app to grant this token account permissions", 200

@app.route('/token')
def token():    
    return f'Token: {os.getenv("ACCESS_TOKEN")}', 200

@app.route('/hook')
def hook():
    type = request.args.get('type')
    data = request.args.get('data')
        
    return f"Hook: {type}/nData: {data}", 200
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)