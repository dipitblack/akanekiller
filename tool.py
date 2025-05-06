import requests
import random
from telethon import events
import uuid

AUTHORIZED_USERS = [2104057670, 6827670598, 6490359522]

def luhn_checksum(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_sum = sum(digits[-1::-2])
    even_sum = sum(sum(digits_of(d * 2)) for d in digits[-2::-2])
    return (odd_sum + even_sum) % 10

def is_luhn_valid(card_number):
    return luhn_checksum(card_number) == 0

def complete_luhn(partial_card):
    for i in range(10):
        trial = partial_card + str(i)
        if is_luhn_valid(trial):
            return trial
    return None

def generate_card_from_bin(bin_pattern):
    bin_clean = bin_pattern.lower().replace('x', 'X')
    cards = []

    while len(cards) < 10:
        cc = ''
        for ch in bin_clean:
            cc += str(random.randint(0, 9)) if ch == 'X' else ch

        if len(cc) < 15:
            cc += ''.join(str(random.randint(0, 9)) for _ in range(15 - len(cc)))

        cc = cc[:15]
        cc_final = complete_luhn(cc)
        if cc_final and cc_final not in cards:
            mm = str(random.randint(1, 12)).zfill(2)
            yy = str(random.randint(25, 29))
            cvv = str(random.randint(100, 999))
            cards.append(f"{cc_final}|{mm}|{yy}|{cvv}")
    return cards

def get_random_address(country_code):
    try:
        url = f"https://randomuser.me/api/?nat={country_code}"
        r = requests.get(url)
        data = r.json()['results'][0]
        name = f"{data['name']['first']} {data['name']['last']}"
        street = f"{data['location']['street']['number']} {data['location']['street']['name']}"
        city = data['location']['city']
        state = data['location']['state']
        postcode = data['location']['postcode']
        country = data['location']['country']
        phone = data['phone']
        return (
            f"🏠 **Random Address**\n\n"
            f"👤 Name: `{name}`\n"
            f"📍 Address: `{street}`\n"
            f"🏙️ City/State: `{city}, {state}`\n"
            f"🗺️ Country: `{country}`\n"
            f"📮 ZIP: `{postcode}`\n"
            f"📞 Phone: `{phone}`"
        )
    except Exception as e:
        return f"❌ Error fetching address: {e}"

def check_ip(ip):
    try:
        r = requests.get(f"https://ipinfo.io/{ip}/json")
        data = r.json()
        ip_info = (
            f"🌐 **IP Information**\n\n"
            f"IP: `{data.get('ip', 'N/A')}`\n"
            f"City: `{data.get('city', 'N/A')}`\n"
            f"Region: `{data.get('region', 'N/A')}`\n"
            f"Country: `{data.get('country', 'N/A')}`\n"
            f"Location: `{data.get('loc', 'N/A')}`\n"
            f"ISP: `{data.get('org', 'N/A')}`\n"
            f"Postal: `{data.get('postal', 'N/A')}`\n"
            f"Timezone: `{data.get('timezone', 'N/A')}`"
        )
        return ip_info
    except Exception as e:
        return f"❌ Error checking IP: {e}"

def get_temp_mail():
    try:
        # Using Temp-Mail API (https://temp-mail.io)
        response = requests.get("https://api.temp-mail.io/request/mail/id/" + str(uuid.uuid4()))
        if response.status_code == 200:
            data = response.json()
            email = data['email']
            return email
        else:
            return None
    except Exception as e:
        return f"❌ Error generating temp mail: {e}"

def fetch_temp_mail(email):
    try:
        # Fetch emails using Temp-Mail API
        response = requests.get(f"https://api.temp-mail.io/request/mail/id/{email}")
        if response.status_code == 200:
            emails = response.json().get('mail_list', [])
            if not emails:
                return "📭 No emails received yet."
            messages = []
            for mail in emails:
                messages.append(
                    f"📧 **From:** `{mail.get('mail_from', 'N/A')}`\n"
                    f"📜 **Subject:** `{mail.get('mail_subject', 'N/A')}`\n"
                    f"📩 **Body:** `{mail.get('mail_text', 'N/A')}`\n"
                )
            return "\n\n".join(messages)
        else:
            return "❌ Failed to fetch emails."
    except Exception as e:
        return f"❌ Error fetching emails: {e}"

def setup_tool_handlers(client):

    @client.on(events.NewMessage(pattern=r'/tempmail'))
    async def handle_temp_mail(event):
        if event.sender_id not in AUTHORIZED_USERS:
            return await event.reply("🚫 Not authorized.")
        try:
            email = get_temp_mail()
            if email:
                await event.reply(f"📧 **Temporary Email:** `{email}`\n\nUse this email to receive messages.")
            else:
                await event.reply("❌ Failed to generate temporary email.")
        except Exception as e:
            await event.reply(f"⚠️ Error: {str(e)}")

    @client.on(events.NewMessage(pattern=r'/checkmail\s+(.+)'))
    async def handle_check_mail(event):
        if event.sender_id not in AUTHORIZED_USERS:
            return await event.reply("🚫 Not authorized.")
        email = event.pattern_match.group(1)
        try:
            messages = fetch_temp_mail(email)
            await event.reply(messages)
        except Exception as e:
            await event.reply(f"⚠️ Error: {str(e)}")

    @client.on(events.NewMessage(pattern=r'/bin\s+(\d{6,8})'))
    async def handle_bin_command(event):
        if event.sender_id not in AUTHORIZED_USERS:
            return await event.reply("🚫 Not authorized.")
        bin_code = event.pattern_match.group(1)
        try:
            response = requests.get(f"https://lookup.binlist.net/{bin_code}", headers={"Accept-Version": "3"})
            if response.status_code == 200:
                data = response.json()
                msg = (
                    f"💳 **BIN Info**\n\n"
                    f"• BIN: `{bin_code}`\n"
                    f"• Scheme: `{data.get('scheme', 'N/A')}`\n"
                    f"• Brand: `{data.get('brand', 'N/A')}`\n"
                    f"• Type: `{data.get('type', 'N/A')}`\n"
                    f"• Bank: `{data.get('bank', {}).get('name', 'N/A')}`\n"
                    f"• Country: `{data.get('country', {}).get('name', 'N/A')}`\n"
                    f"• Currency: `{data.get('country', {}).get('currency', 'N/A')}`"
                )
            else:
                msg = "❌ Invalid BIN or lookup failed."
            await event.reply(msg)
        except Exception as e:
            await event.reply(f"⚠️ Error: {str(e)}")

    @client.on(events.NewMessage(pattern=r'/gen\s+([0-9xX]{6,16})'))
    async def generate_cards(event):
        if event.sender_id not in AUTHORIZED_USERS:
            return await event.reply("🚫 Not authorized.")
        bin_pattern = event.pattern_match.group(1)
        try:
            cards = generate_card_from_bin(bin_pattern)
            await event.reply("💳 **Generated Cards**:\n\n" + "\n".join(f"`{c}`" for c in cards))
        except Exception as e:
            await event.reply(f"⚠️ Error: {str(e)}")

    @client.on(events.NewMessage(pattern=r'/addr\s+([a-z]{2})'))
    async def handle_address(event):
        if event.sender_id not in AUTHORIZED_USERS:
            return await event.reply("🚫 Not authorized.")
        country_code = event.pattern_match.group(1).lower()
        msg = get_random_address(country_code)
        await event.reply(msg)

    @client.on(events.NewMessage(pattern=r'/ip\s+([\d.]+)'))
    async def handle_ip_check(event):
        if event.sender_id not in AUTHORIZED_USERS:
            return await event.reply("🚫 Not authorized.")
        ip = event.pattern_match.group(1)
        msg = check_ip(ip)
        await event.reply(msg)
