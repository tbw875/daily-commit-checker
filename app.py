from flask import Flask, request, jsonify
import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')
YOUR_PHONE_NUMBER = os.getenv('YOUR_PHONE_NUMBER')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Verify secret token
    auth_header = request.headers.get('X-Webhook-Secret')
    if not auth_header or auth_header != WEBHOOK_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.json
        message = data.get('message', "Don't forget to make your daily commit!")
        
        # Send SMS via Twilio
        message = client.messages.create(
            body=message,
            from_=TWILIO_FROM_NUMBER,
            to=YOUR_PHONE_NUMBER
        )
        
        return jsonify({
            'success': True,
            'message_sid': message.sid
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Health check endpoint
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    # Get port from environment variable or default to 8080
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
