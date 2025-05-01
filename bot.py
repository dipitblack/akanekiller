import logging
import requests
from telethon import TelegramClient, events
from telethon.events import CallbackQuery
from telethon import TelegramClient, Button
from telethon.errors import SessionPasswordNeededError
import random
from killer.kill import process_card as process_card_kill
from killer.kd import kum 
from killer.ded import ded as process_card_ded
from checkers.au import process_card_au 
import json

# Bot configuration
API_ID = 19274214
API_HASH = "bf87adfbc2c24c66904f3c36f3c0af3a"
BOT_TOKEN = "7344124631:AAFjcaMQgBjBx4z1W9sLtbFv6efDRgVvIBE"
AUTHORIZED_USERS = [2104057670, 6827670598, 6490359522]

client = TelegramClient('bot_session', API_ID, API_HASH)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def get_anime_girl_image():
    """Fetch a random anime girl image from waifu.pics API."""
    try:
        response = requests.get('https://api.waifu.pics/sfw/waifu', timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('url')  # API returns {'url': 'image_url'}
        return None
    except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
        print(f"Error fetching anime girl image: {e}")
        return None

# Store the initial anime image globally to avoid changing it after pressing "Back"
start_image_url = None

# Start Command Handler
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    global start_image_url
    # Get random anime girl image (only on /start command)
    start_image_url = get_anime_girl_image()
    
    message = (
            "**Welcome To Akane Killer** \n"
            "__Only authorized users can use this bot.__\n"
        )
    # Create inline buttons
    buttons = [
        [Button.inline("Commands", data="killer"),
         Button.inline("Buy Now", data="pricing")]
    ]

    # Send message with or without image
    try:
        if start_image_url:
            await event.respond(
                message,
                buttons=buttons,
                file=start_image_url  # Send the random image from /start
            )
        else:
            # If waifu.pics fails, try a fallback API
            fallback_url = "https://i.imgur.com/7Z7A1dU.jpg"  # Default anime girl image
            await event.respond(
                message,
                buttons=buttons,
                file=fallback_url  # Fallback image
            )
    except Exception as e:
        print(f"Error sending message: {e}")
        await event.respond(
            message,
            buttons=buttons
        )

# Handle inline button clicks
@client.on(events.CallbackQuery)
async def button_click_handler(event):
    data = event.data.decode('utf-8')
    if data == 'killer':
        await event.edit(
            "🔪 **Killer Commands** 🔪\n\n"
            "- `/kill <cc|mm|yy|cvv>`\n"
            "- `/ded <cc|mm|yy|cvv>`\n\n"
            "__Example__: /kill 4111111111111111|12|25|123",
            buttons=Button.inline("Back", data="back")
        )
    elif data == 'gates':
        await event.edit(
            "🚪 **Gates Section** 🚪\n\n"
            "This section will contain all available gates.\n"
            "Currently under development!",
            buttons=Button.inline("Back", data="back")
        )
    elif data == 'tools':
        await event.edit(
            "🛠️ **Tools Section** 🛠️\n\n"
            "This section will contain useful tools.\n"
            "Currently under development!",
            buttons=Button.inline("Back", data="back")
        )
    elif data == 'pricing':
        await event.edit(
            "**Available plans:-**\n\n"
            "1 Week Trial Plan:\nPrice** - 7$\n**Validity:** 7 Days\n**Credits:** Unlimited**\n\n"
            "1 Month Plan:\nPrice - **20$**\nValidity:** 30 Days**\nCredits:** Unlimited**\n\n**Payment Methods:- Binance, UPI**",
            buttons= [
            
            Button.inline("Back", data="back"),
            Button.url("Purchase", url="https://t.me/Nehxl")
            ]
            
        )
    elif data == 'back':
        # Return to main menu with the same random image
        message = (
            "**Welcome To Akane Killer** \n"
            "__Only authorized users can use this bot.__\n"
        )
        buttons = [
            [Button.inline("Commands", data="killer"),
             Button.inline("Buy Now", data="pricing")]
        ]
        
        try:
            if start_image_url:
                await event.edit(
                    message,
                    buttons=buttons,
                    file=start_image_url  # Use the same image as /start
                )
            else:
                await event.edit(
                    message,
                    buttons=buttons
                )
        except:
            await event.edit(
                message,
                buttons=buttons
            )

        
@client.on(events.NewMessage(pattern=r'/kill\s+(.+)'))
async def kill_handler(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.respond("❌ **Error**: Unauthorized user. Access denied.")
        return

    card_info = event.pattern_match.group(1).strip()
    await process_card_kill(client, event, card_info)


@client.on(events.NewMessage(pattern=r'/ded\s+(.+)'))
async def ded(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.respond("❌ **Error**: Unauthorized user. Access denied.")
        return

    card_info = event.pattern_match.group(1).strip()
    await process_card_ded(client, event, card_info)


@client.on(events.NewMessage(pattern=r'/kd\s+(.+)'))
async def kd_handler(event):
    """Handle the /kd command."""
    if event.sender_id not in AUTHORIZED_USERS:
        await event.respond("❌ **Error**: Unauthorized user. Access denied.")
        return

    card_info = event.pattern_match.group(1).strip()
    await kum(client, event, card_info)
    
async def main():
    try:
        await client.start(bot_token=BOT_TOKEN)
        print("Bot is running...")
        await client.run_until_disconnected()
    except SessionPasswordNeededError:
        print("Two-factor authentication enabled. Please provide your password.")
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")

# Attach event listener
@client.on(events.NewMessage(pattern=r'/au\s+(.+)'))
async def au(event):
    if event.sender_id not in AUTHORIZED_USERS:
        await event.respond("❌ **Error**: Unauthorized user. Access denied.")
        return

    card_info = event.pattern_match.group(1).strip()
    await process_card_au(client, event, card_info)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())