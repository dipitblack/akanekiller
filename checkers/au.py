import requests
import random
import uuid
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Proxy configuration
proxy_credentials = [
    'tnapkbnn-rotate:8vsviipgym5g',
    # Add more Webshare proxy usernames if available
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
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
]

# Create a fresh session with random proxy and user agent
def create_session():
    session = requests.Session()
    
    # Random proxy selection
    if proxies_list:
        proxy = random.choice(proxies_list)
        session.proxies.update(proxy)
        logger.debug(f"Using proxy: {proxy}")
    
    # Random user agent
    user_agent = random.choice(user_agents)
    session.headers.update({
        'User-Agent': user_agent,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Origin': 'https://bubblegumballoons.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    })
    logger.debug(f"Using user agent: {user_agent}")
    
    return session

# Process order function
async def process_order(cc_number, cc_month, cc_year, cc_cvv):
    logger.debug("Starting process_order")
    try:
        # Generate random IDs
        session_id = str(uuid.uuid4())
        transaction_id = str(uuid.uuid4())
        df_reference_id = f"0_{str(uuid.uuid4())}"
        logger.debug(f"Generated IDs: session_id={session_id}, transaction_id={transaction_id}, df_reference_id={df_reference_id}")
        
        s = create_session()
        
        # Step 1: Add item to basket
        headers = {
            'content-type': 'application/json',
            'referer': 'https://bubblegumballoons.com/products/9840/number-2-cat-balloon-package',
            'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        json_data = {
            'product_id': 9840,
            'product_variations_compound': '9840-1494',
            'product_text_variation': '',
            'product_variation_text_line_2': '',
            'customer_image_url': None,
            'canvas_preview': None,
            'quantity': 1,
            'font_id': None,
        }

        logger.debug("Step 1: Adding item to basket")
        r1 = s.post('https://bubblegumballoons.com/api/basket/items', headers=headers, json=json_data)
        r1.raise_for_status()  # Raise exception for bad status codes
        response_data = r1.json()
        order_id = response_data.get('id')
        order_hash = response_data.get('hash')
        if not order_id or not order_hash:
            logger.error("Step 1 failed: Invalid response data")
            return {'error': 'Invalid response data from basket API'}
        logger.debug(f"Step 1 success: order_id={order_id}, order_hash={order_hash}")

        # Step 2: Update order details
        j1 = {
            'first_name': 'Mohammed',
            'last_name': 'Nehal',
            'email': 'mohammedgggggmushtaq9011@gmail.com',
            'phone': '07975102052',
            'gift_message': '',
            'address_first_name': 'Mohammed',
            'address_last_name': 'Nehal',
            'address_line_1': 'New York Studios',
            'address_line_2': 'New York Road',
            'address_line_3': '',
            'address_company': None,
            'address_city': 'Leeds',
            'address_county': 'West Yorkshire',
            'address_country_iso2': 'GB',
            'address_postcode': 'LS9 7DW',
            'billing_address_first_name': None,
            'billing_address_last_name': None,
            'billing_address_line_1': None,
            'billing_address_line_2': None,
            'billing_address_line_3': None,
            'billing_address_company': None,
            'billing_address_city': None,
            'billing_address_country_iso2': None,
            'billing_address_postcode': None,
            'shipping_rate_id': None,
            'ordered_for': '2025-06-06',
            'prefers_boxes': False,
            'delivery_type': 'collection',
        }

        logger.debug("Step 2: Updating order details")
        r2 = s.patch(f'https://bubblegumballoons.com/api/orders/{order_id}', headers=headers, json=j1)
        r2.raise_for_status()
        logger.debug("Step 2 success")

        # Step 3: Update order with billing details
        j2 = {
            'first_name': 'Mohammed',
            'last_name': 'Nehal',
            'email': 'mohammedgggggmushtaq9011@gmail.com',
            'phone': '07975102052',
            'gift_message': '',
            'address_first_name': 'Mohammed',
            'address_last_name': 'Nehal',
            'address_line_1': 'New York Studios',
            'address_line_2': 'New York Road',
            'address_line_3': '',
            'address_company': None,
            'address_city': 'Leeds',
            'address_county': 'West Yorkshire',
            'address_country_iso2': 'GB',
            'address_postcode': 'LS9 7DW',
            'billing_address_first_name': 'Mohammed',
            'billing_address_last_name': 'Nehal',
            'billing_address_line_1': 'New York Studios',
            'billing_address_line_2': 'New York Road',
            'billing_address_line_3': '',
            'billing_address_company': None,
            'billing_address_city': 'Leeds',
            'billing_address_county': 'West Yorkshire',
            'billing_address_country_iso2': 'GB',
            'billing_address_postcode': 'LS9 7DW',
            'shipping_rate_id': 7,
            'ordered_for': '2025-06-08',
            'prefers_boxes': False,
            'delivery_type': 'collection',
        }

        logger.debug("Step 3: Updating order with billing details")
        r3 = s.patch(f'https://bubblegumballoons.com/api/orders/{order_id}', headers=headers, json=j2)
        r3.raise_for_status()
        order_hash = r3.json().get('hash')
        if not order_hash:
            logger.error("Step 3 failed: Invalid order hash")
            return {'error': 'Invalid order hash from order update'}
        logger.debug("Step 3 success")

        # Step 4: Tokenize credit card with Braintree
        h1 = {
            'authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6IjIwMTgwNDI2MTYtcHJvZHVjdGlvbiIsImlzcyI6Imh0dHBzOi8vYXBpLmJyYWludHJlZWdhdGV3YXkuY29tIn0.eyJleHAiOjE3NDY0Mjg5ODQsImp0aSI6ImEzYmNjMzU1LTI5YWQtNDE3NC1hODMxLTI0OTI5MmU3MmE2NiIsInN1YiI6Ijlwemo0dHcyc2g5anl3cHAiLCJpc3MiOiJodHRwczovL2FwaS5icmFpbnRyZWVnYXRld2F5LmNvbSIsIm1lcmNoYW50Ijp7InB1YmxpY19pZCI6Ijlwemo0dHcyc2g5anl3cHAiLCJ2ZXJpZnlfY2FyZF9ieV9kZWZhdWx0IjpmYWxzZX0sInJpZ2h0cyI6WyJtYW5hZ2VfdmF1bHQiXSwic2NvcGUiOlsiQnJhaW50cmVlOlZhdWx0Il0sIm9wdGlvbnMiOnt9fQ.Buf8jKvR0Yqvn240fHtnVqOsmrpRonT-jRSvetwFzBQTyuqepsOrY31yJ-aWChKndR4etAs1CT9ETsiqCqbi0g',
            'braintree-version': '2018-05-10',
            'content-type': 'application/json',
        }

        j3 = {
            'clientSdkMetadata': {
                'source': 'client',
                'integration': 'dropin2',
                'sessionId': session_id,
            },
            'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   tokenizeCreditCard(input: $input) {     token     creditCard {       bin       brandCode       last4       cardholderName       expirationMonth      expirationYear      binData {         prepaid         healthcare         debit         durbinRegulated         commercial         payroll         issuingBank         countryOfIssuance         productId       }     }   } }',
            'variables': {
                'input': {
                    'creditCard': {
                        'number': cc_number,
                        'expirationMonth': cc_month,
                        'expirationYear': f'20{cc_year}',
                        'cvv': cc_cvv,
                        'billingAddress': {
                            'postalCode': '10040',
                        },
                    },
                    'options': {
                        'validate': False,
                    },
                },
            },
            'operationName': 'TokenizeCreditCard',
        }

        logger.debug("Step 4: Tokenizing credit card")
        r4 = s.post('https://payments.braintree-api.com/graphql', headers=h1, json=j3)
        r4.raise_for_status()
        r4_data = r4.json()
        payment_token = r4_data.get('data', {}).get('tokenizeCreditCard', {}).get('token')
        if not payment_token:
            logger.error("Step 4 failed: No payment token received")
            return {'error': 'No payment token received from Braintree'}
        logger.debug(f"Step 4 success: payment_token={payment_token}")

        # Step 5: 3D Secure lookup
        j4 = {
            'amount': '24.95',
            'additionalInfo': {
                'acsWindowSize': '03',
                'billingLine1': 'New York Studios',
                'billingLine2': 'New York Road',
                'billingCity': 'Leeds',
                'billingPostalCode': 'LS9 7DW',
                'billingCountryCode': 'GB',
                'billingPhoneNumber': '07975102052',
                'billingGivenName': 'Mohammed',
                'email': 'mohammedgggggmushtaq9011@gmail.com',
            },
            'bin': cc_number[:6],
            'dfReferenceId': df_reference_id,
            'clientMetadata': {
                'requestedThreeDSecureVersion': '2',
                'sdkVersion': 'web/3.94.0',
                'cardinalDeviceDataCollectionTimeElapsed': random.randint(200, 300),
                'issuerDeviceDataCollectionTimeElapsed': random.randint(10000, 12000),
                'issuerDeviceDataCollectionResult': True,
            },
            'authorizationFingerprint': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6IjIwMTgwNDI2MTYtcHJvZHVjdGlvbiIsImlzcyI6Imh0dHBzOi8vYXBpLmJyYWludHJlZWdhdGV3YXkuY29tIn0.eyJleHAiOjE3NDY0Mjg5ODQsImp0aSI6ImEzYmNjMzU1LTI5YWQtNDE3NC1hODMxLTI0OTI5MmU3MmE2NiIsInN1YiI6Ijlwemo0dHcyc2g5anl3cHAiLCJpc3MiOiJodHRwczovL2FwaS5icmFpbnRyZWVnYXRld2F5LmNvbSIsIm1lcmNoYW50Ijp7InB1YmxpY19pZCI6Ijlwemo0dHcyc2g5anl3cHAiLCJ2ZXJpZnlfY2FyZF9ieV9kZWZhdWx0IjpmYWxzZX0sInJpZ2h0cyI6WyJtYW5hZ2VfdmF1bHQiXSwic2NvcGUiOlsiQnJhaW50cmVlOlZhdWx0Il0sIm9wdGlvbnMiOnt9fQ.Buf8jKvR0Yqvn240fHtnVqOsmrpRonT-jRSvetwFzBQTyuqepsOrY31yJ-aWChKndR4etAs1CT9ETsiqCqbi0g',
            'braintreeLibraryVersion': 'braintree/web/3.94.0',
            '_meta': {
                'merchantAppId': 'bubblegumballoons.com',
                'platform': 'web',
                'sdkVersion': '3.94.0',
                'source': 'client',
                'integration': 'custom',
                'integrationType': 'custom',
                'sessionId': session_id,
            },
        }

        logger.debug("Step 5: Performing 3D Secure lookup")
        r5 = s.post(f'https://api.braintreegateway.com/merchants/9pzj4tw2sh9jywpp/client_api/v1/payment_methods/{payment_token}/three_d_secure/lookup', headers=h1, json=j4)
        r5.raise_for_status()
        r5_data = r5.json()
        if not r5_data.get('paymentMethod'):
            logger.error("Step 5 failed: No payment method data in 3D Secure response")
            return {'error': 'No payment method data in 3D Secure response'}
        logger.debug("Step 5 success")

        # Step 6: Process payment
        json_data = {
            'order_id': order_id,
            'order_hash': order_hash,
            'ordered_for': '2025-06-08',
            'shipping_rate_id': 7,
            'delivery_type': 'collection',
            'gateway': 'braintree',
            'transaction_id': transaction_id,
            'nonce': {
                'nonce': r5_data['paymentMethod']['nonce'],
                'type': r5_data['paymentMethod']['type'],
                'description': r5_data['paymentMethod']['description'],
                'consumed': r5_data['paymentMethod'].get('consumed', False),
                'details': r5_data['paymentMethod']['details'],
                'threeDSecureInfo': r5_data['paymentMethod']['threeDSecureInfo'],
                'binData': r5_data['paymentMethod']['binData'],
            }
        }

        logger.debug("Step 6: Processing payment")
        r6 = s.post('https://bubblegumballoons.com/api/payment/process', headers=headers, json=json_data)
        r6.raise_for_status()
        response_data = r6.json()
        logger.debug(f"Step 6 success: status_code={r6.status_code}, response={response_data}")
        
        return {
            'status_code': r6.status_code,
            'response': response_data,
            'transaction_id': transaction_id
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
