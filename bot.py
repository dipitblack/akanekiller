import logging
import requests
from telethon import TelegramClient, events
from telethon.events import CallbackQuery
from telethon import TelegramClient, Button
from telethon.errors import SessionPasswordNeededError
import random
from killer.kill import process_card as process_card_kill
from killer.ded import ded as process_card_ded
from killer.kd import kum
from checkers.au import process_order
import json
import time
import re
from tool import setup_tool_handlers 

# Bot configuration
API_ID = 5689646
API_HASH = "895de5ae804308803c19814afabb0de7"
BOT_TOKEN = "7344124631:AAFjcaMQgBjBx4z1W9sLtbFv6efDRgVvIBE"
AUTHORIZED_USERS = [2104057670, 6827670598, 6490359522, 985410451, 7002368713, 1650751589]

client = TelegramClient('bot_session', API_ID, API_HASH)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

setup_tool_handlers(client)

def get_anime_girl_image():
    """Fetch random anime girl image from waifu.pics API."""
    try:
        response = requests.get('https://api.waifu.pics/sfw/waifu', timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('url')
        return None
    except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
        print(f"Error fetching image: {e}")
        return None

start_image_url = None

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    global start_image_url
    start_image_url = get_anime_girl_image()
    
    message = (
        "**Akane Killer Bot**\n\n"
        "**Premium tools for authorized users.**\n"
        "__Restricted access.__\n"
        "Select an option:"
    )
    buttons = [
        [Button.inline("Killer", data="killer"), Button.inline("Gates", data="gates")],
        [Button.inline("Tools", data="tools"), Button.inline("Buy Now", data="pricing")]
    ]

    try:
        if start_image_url:
            await event.respond(message, buttons=buttons, file=start_image_url)
        else:
            fallback_url = "https://i.imgur.com/7Z7A1dU.jpg"
            await event.respond(message, buttons=buttons, file=fallback_url)
    except Exception as e:
        print(f"Error sending message: {e}")
        await event.respond(message, buttons=buttons)

@client.on(events.CallbackQuery)
async def button_click_handler(event):
    data = event.data.decode('utf-8')
    if data == 'killer':
        await event.edit(
            "**Killer Commands | 3 Gates**\n━━━━━━━━━━━━\n"
            "1. **Killer v1**\n"
            "→ **Command**: `$kill`\n"
            "→ **Format**: `cc|mm|yy|cvv`\n"
            "→ **Condition**: **ON ✅**\n\n"
            "2. **Killer v2**\n"
            "→ **Command**: `$ded`\n"
            "→ **Format**: `cc|mm|yy|cvv`\n"
            "→ **Condition**: **ON ✅**\n\n"
            "3. **Killer v3**\n"
            "→ **Command**: `$kd`\n"
            "→ **Format**: `cc|mm|yy|cvv`\n"
            "→ **Condition**: **ON ✅**",
            buttons=Button.inline("Back", data="back")
        )
    elif data == 'gates':
        await event.edit(
            "**Checker Commands**\n━━━━━━━━━━━━\n"
            "1. **Braintree**\n"
            "→ **Command**: `$chk`\n"
            "→ **Format**: `cc|mm|yy|cvv`\n"
            "→ **Condition**: **ON ✅**",
            buttons=Button.inline("Back", data="back")
        )
    elif data == 'tools':
        await event.edit(
            "**Tools Commands**\n━━━━━━━━━━━━\n"
            "1. **Bin Lookup**\n"
            "→ **Command**: `$bin`\n"
            "→ **Format**: `/bin <bin>`\n━━━━━━━━━━━━\n"
            "2. **Card Generator**\n"
            "→ **Command**: `$gen`\n"
            "→ **Format**: `/gen <bin>`\n━━━━━━━━━━━━\n"
            "3. **Address Generator**\n"
            "→ **Command**: `$addr`\n"
            "→ **Format**: `/addr <code>`\n━━━━━━━━━━━━\n"
            "4. **IP Lookup**\n"
            "→ **Command**: `$ip`\n"
            "→ **Format**: `/ip <ip>`\n━━━━━━━━━━━━\n",
            buttons=Button.inline("Back", data="back")
        )
    elif data == 'pricing':
        await event.edit(
    "**💢 NANI?! Not For Sale?! 💢**\n\n"
    "This waifu bot is too powerful for mere mortals!\n"
    "Even the Akatsuki can't afford this...\n"
    "__Try again in your next isekai life!__ ",
    buttons=[
        Button.inline("Back", data="back"),
        Button.url("Summon the Master", url="https://t.me/Nehxl")
    ]
)

    elif data == 'back':
        message = (
            "**Akane Killer Bot**\n\n"
            "**Killer for authorized users.**\n"
            "__Restricted access.__\n"
        )
        buttons = [
            [Button.inline("Killer", data="killer"), Button.inline("Gates", data="gates")],
            [Button.inline("Tools", data="tools"), Button.inline("Buy Now", data="pricing")]
        ]
        
        try:
            if start_image_url:
                await event.edit(message, buttons=buttons, file=start_image_url)
            else:
                await event.edit(message, buttons=buttons)
        except:
            await event.edit(message, buttons=buttons)

        
@client.on(events.NewMessage(pattern=r'/kill\s+(.+)'))
async def kill_handler(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.respond("❌ **Error**: Unauthorized user. Access denied.")
        return

    card_info = event.pattern_match.group(1).strip()
    await process_card_kill(client, event, card_info)

@client.on(events.NewMessage(pattern=r'/kd\s+(.+)'))
async def kill_handler_kd(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.respond("❌ **Error**: Unauthorized user. Access denied.")
        return

    card_info = event.pattern_match.group(1).strip()
    await kum(client, event, card_info)

@client.on(events.NewMessage(pattern=r'/ded\s+(.+)'))
async def ded(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.respond("❌ **Error**: Unauthorized user. Access denied.")
        return

    card_info = event.pattern_match.group(1).strip()
    await process_card_ded(client, event, card_info)


async def main():
    try:
        await client.start(bot_token=BOT_TOKEN)
        print("Bot is running...")
        await client.run_until_disconnected()
    except SessionPasswordNeededError:
        print("Two-factor authentication enabled. Please provide your password.")
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")

def get_bin_info(bin_number):
    try:
        url = f"https://bins.antipublic.cc/bins/{bin_number}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Assuming the new API returns fields in a similar structure
        scheme = data.get('scheme', 'UNKNOWN').upper()
        card_type = data.get('type', 'UNKNOWN').upper()
        brand = data.get('brand', 'UNKNOWN').upper()
        bank = data.get('bank', 'UNKNOWN').upper()
        country = data.get('country_name', 'UNKNOWN').upper()
        country_emoji = data.get('country_emoji', '')  # Some APIs might not have emoji

        bin_info = f"{scheme} - {card_type} - {brand}"
        return {
            'bin_info': bin_info,
            'bank': bank,
            'country': f"{country} {country_emoji}"
        }
    except Exception as e:
        logger.error(f"BIN lookup failed: {str(e)}")
        return {
            'bin_info': 'Unknown',
            'bank': 'Unknown',
            'country': 'Unknown'
        }

# Telegram bot event handler
@client.on(events.NewMessage(pattern=r'^/chk\s+(.+)'))
async def check_card(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.respond("❌ **Error**: Unauthorized user. Access denied.")
        return
    logger.debug("Received /chk command")
    start_time = time.time()
    
    # Extract input using regex
    input_text = event.pattern_match.group(1)
    pattern = r'^(\d{16})\|(\d{2})\|(\d{2})\|(\d{3})$'
    match = re.match(pattern, input_text)
    
    if not match:
        logger.warning(f"Invalid input format: {input_text}")
        await event.reply("Invalid input format. Use: /chk cc|mm|yy|cvv\nExample: /chk 4207670303764172|02|29|082")
        return
    
    cc_number, cc_month, cc_year, cc_cvv = match.groups()
    logger.debug(f"Parsed input: cc_number={cc_number}, cc_month={cc_month}, cc_year={cc_year}, cc_cvv={cc_cvv}")
    
    # Get BIN info
    bin_info = get_bin_info(cc_number[:6])
    
    # Process the order
    result = await process_order(cc_number, cc_month, cc_year, cc_cvv)
    processing_time = time.time() - start_time
    
    # Format response
    if result is None or 'error' in result:
        error_msg = result.get('error', 'Unknown error occurred') if result else 'Process order returned None'
        logger.error(f"Order processing failed: {error_msg}")
        await event.reply(f"Order processing failed: {error_msg}")
        return
    
    response_data = result['response']
    status = response_data.get('status', False)
    message = response_data.get('message', 'Unknown')

    bold = lambda s: f"**{s}**"
    arrow = "➟"
    
    if status:
        response_text = f"✅ {bold('Approved')}\n\n"
    else:
        response_text = f"❌ {bold('Declined')}\n\n"
        
        response_text += f"{bold('Card')} {arrow} {cc_number}|{cc_month}|20{cc_year}|{cc_cvv}\n"
        response_text += f"{bold('Gateway')} {arrow} Braintree Auth 1\n"
        response_text += f"{bold('Response')} {arrow} {message}\n\n"
        response_text += f"{bold('BIN')} {arrow} {bin_info['bin_info']}\n"
        response_text += f"{bold('Bank')} {arrow} {bin_info['bank']}\n"
        response_text += f"{bold('Country')} {arrow} {bin_info['country']}\n"
        response_text += f"{bold('Time')} {arrow} {processing_time:.2f}s"

        await event.reply(response_text)



if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
