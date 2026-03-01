import json
import base64
import hmac
import hashlib
import random
import requests

class MobicardDetokenization:
    def __init__(self, merchant_id, api_key, secret_key):
        self.mobicard_version = "2.0"
        self.mobicard_mode = "LIVE"
        self.mobicard_merchant_id = merchant_id
        self.mobicard_api_key = api_key
        self.mobicard_secret_key = secret_key
        self.mobicard_service_id = "20000"
        self.mobicard_service_type = "DETOKENIZATION"
        
        self.mobicard_token_id = str(random.randint(1000000, 1000000000))
        self.mobicard_txn_reference = str(random.randint(1000000, 1000000000))
    
    def detokenize(self, card_token):
        """Detokenize a card token to retrieve original card details"""
        
        # Create JWT Header
        jwt_header = {"typ": "JWT", "alg": "HS256"}
        encoded_header = base64.urlsafe_b64encode(
            json.dumps(jwt_header).encode()
        ).decode().rstrip('=')
        
        # Create JWT Payload
        jwt_payload = {
            "mobicard_version": self.mobicard_version,
            "mobicard_mode": self.mobicard_mode,
            "mobicard_merchant_id": self.mobicard_merchant_id,
            "mobicard_api_key": self.mobicard_api_key,
            "mobicard_service_id": self.mobicard_service_id,
            "mobicard_service_type": self.mobicard_service_type,
            "mobicard_token_id": self.mobicard_token_id,
            "mobicard_txn_reference": self.mobicard_txn_reference,
            "mobicard_card_token": card_token
        }
        
        encoded_payload = base64.urlsafe_b64encode(
            json.dumps(jwt_payload).encode()
        ).decode().rstrip('=')
        
        # Generate Signature
        header_payload = f"{encoded_header}.{encoded_payload}"
        signature = hmac.new(
            self.mobicard_secret_key.encode(),
            header_payload.encode(),
            hashlib.sha256
        ).digest()
        encoded_signature = base64.urlsafe_b64encode(signature).decode().rstrip('=')
        
        jwt_token = f"{encoded_header}.{encoded_payload}.{encoded_signature}"
        
        # Make API Call
        url = "https://mobicardsystems.com/api/v1/card_tokenization"
        payload = {"mobicard_auth_jwt": jwt_token}
        
        try:
            response = requests.post(url, json=payload, verify=False, timeout=30)
            response_data = response.json()
            
            if response_data.get('status') == 'SUCCESS':
                result = {
                    'status': 'SUCCESS',
                    'card_number': response_data['card_information']['card_number'],
                    'card_number_masked': response_data['card_information']['card_number_masked'],
                    'card_expiry_date': response_data['card_information']['card_expiry_date'],
                    'card_token': response_data['card_information']['card_token'],
                    'single_use_token_flag': response_data.get('mobicard_single_use_token_flag', '0'),
                    'raw_response': response_data
                }
                
                # Check if new token was generated (single-use token)
                if result['single_use_token_flag'] == '1':
                    result['new_token_generated'] = True
                    result['message'] = "New token generated. Update your database."
                
                return result
            else:
                return {
                    'status': 'ERROR',
                    'status_code': response_data.get('status_code'),
                    'status_message': response_data.get('status_message')
                }
                
        except Exception as e:
            return {'status': 'ERROR', 'error_message': str(e)}

# Usage
detokenizer = MobicardDetokenization(
    merchant_id="4",
    api_key="YmJkOGY0OTZhMTU2ZjVjYTIyYzFhZGQyOWRiMmZjMmE2ZWU3NGIxZWM3ZTBiZSJ9",
    secret_key="NjIwYzEyMDRjNjNjMTdkZTZkMjZhOWNiYjIxNzI2NDQwYzVmNWNiMzRhMzBjYSJ9"
)

# Token from your database
card_token = "bbaefff665082af8f3a41fa51853062b1628345cec085498bba97e3ae3b1e77e4f7ac5ee0ac9bbf10ff8c151d006d80212a3dac731c48188a9e00f9084b163bf"

result = detokenizer.detokenize(card_token)

if result['status'] == 'SUCCESS':
    print(f"Card Number: {result['card_number_masked']}")
    print(f"Expiry Date: {result['card_expiry_date']}")
    
    if result.get('new_token_generated'):
        print(f"New Token: {result['card_token']}")
        print("Update your database with the new token.")
    
    # Use result['card_number'] for payment processing
else:
    print(f"Error: {result.get('status_message')}")
