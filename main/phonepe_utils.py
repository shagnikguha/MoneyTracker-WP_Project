import json
import uuid
import base64
import hashlib
import requests
from django.conf import settings
from django.urls import reverse

def generate_transaction_id():
    """Generate a unique transaction ID for PhonePe payments"""
    return f"TX{uuid.uuid4().hex[:16].upper()}"

def create_payment_request(request, amount, user):
    """Create PhonePe payment request object"""
    merchant_id = settings.PHONEPAY_MERCHANT_ID
    salt_key = settings.PHONEPAY_SALT_KEY
    salt_index = settings.PHONEPAY_SALT_INDEX
    
    # Generate unique transaction ID
    transaction_id = generate_transaction_id()
    
    # Create callback URL with the domain
    callback_url = request.build_absolute_uri(
        reverse('payment_callback')
    )
    redirect_url = request.build_absolute_uri(
        reverse('payment_status', args=[transaction_id])
    )
    
    # Create payload
    payload = {
        "merchantId": merchant_id,
        "merchantTransactionId": transaction_id,
        "merchantUserId": f"MUID{user.id}",
        "amount": int(float(amount) * 100),  # PhonePe expects amount in paise
        "redirectUrl": redirect_url,
        "redirectMode": "POST",
        "callbackUrl": callback_url,
        "paymentInstrument": {
            "type": "PAY_PAGE"
        }
    }
    
    # Add phone number if available
    if hasattr(user, 'profile') and hasattr(user.profile, 'phone'):
        payload["mobileNumber"] = user.profile.phone
    
    # Convert to base64
    payload_str = json.dumps(payload)
    payload_encoded = base64.b64encode(payload_str.encode()).decode()
    
    # Calculate checksum
    string_to_hash = payload_encoded + "/pg/v1/pay" + salt_key
    sha256_hash = hashlib.sha256(string_to_hash.encode()).hexdigest()
    checksum = sha256_hash + "###" + str(salt_index)
    
    # Create final request body
    request_body = {
        "request": payload_encoded
    }
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "X-VERIFY": checksum
    }
    
    # Make API request to PhonePe
    api_url = "https://api-preprod.phonepe.com/apis/pg-sandbox/pg/v1/pay"
    
    response = requests.post(api_url, json=request_body, headers=headers)
    response_data = response.json()
    
    # Check if successful
    if response_data.get('success'):
        return {
            'success': True,
            'transaction_id': transaction_id,
            'payment_url': response_data.get('data', {}).get('instrumentResponse', {}).get('redirectInfo', {}).get('url'),
            'amount': amount
        }
    else:
        return {
            'success': False,
            'error': response_data.get('error', {}).get('message', 'Payment initialization failed')
        }

def verify_payment_callback(request_data, salt_key, salt_index):
    """Verify the callback from PhonePe"""
    if 'response' not in request_data or 'X-VERIFY' not in request_data:
        return {'success': False, 'error': 'Invalid callback data'}
    
    # Extract base64 response and checksum
    base64_response = request_data.get('response')
    received_checksum = request_data.get('X-VERIFY')
    
    # Calculate checksum
    string_to_hash = base64_response + "/pg/v1/status/" + salt_key
    calculated_hash = hashlib.sha256(string_to_hash.encode()).hexdigest() + "###" + str(salt_index)
    
    # Verify checksum
    if calculated_hash != received_checksum:
        return {'success': False, 'error': 'Checksum verification failed'}
    
    # Decode response
    try:
        decoded_response = json.loads(base64.b64decode(base64_response).decode())
        return {
            'success': True,
            'data': decoded_response
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}