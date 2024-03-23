from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import xml.etree.ElementTree as ET
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import validators

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Copyscape credentials
api_key = "0kdbtuaqkzf7vhas"  # Replace with your Copyscape API key
username = "asidd99"  # Replace with your Copyscape username

# Executor for running synchronous code asynchronously
executor = ThreadPoolExecutor(max_workers=2)

# Copyscape API call
async def check_copyscape(url, api_key, username):
    api_endpoint = "https://www.copyscape.com/api/"
    params = {
        'u': username,
        'k': api_key,
        'o': 'csearch',
        'q': url,
        'f': 'xml',
    }

    # Run the synchronous requests.get in an executor to avoid blocking
    # the async loop
    response = await asyncio.get_event_loop().run_in_executor(executor, requests.get, api_endpoint, params)
    
    logger.info(f"Response from Copyscape API: {response.text}")  # Log the response from Copyscape API

    if response.status_code == 200:
        try:
            root = ET.fromstring(response.content)
            results = []
            for result in root.findall('result'):
                url = result.find('url').text
                title = result.find('title').text
                matched_words = result.find('minwordsmatched').text
                results.append({
                    'URL': url,
                    'Title': title,
                    'Matched Words': matched_words
                })
            
            logger.info("Copyscape API call successful.")
            return results
        except ET.ParseError as e:
            logger.error(f"Error parsing XML: {str(e)}")
            return "Error parsing XML 🛑."
    else:
        logger.error(f"Error contacting Copyscape API. Status code: {response.status_code}")
        return "Error contacting Copyscape API 🛑."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Hi there! 👋 Please use /check <url> to check a URL with Copyscape.')

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Please provide a URL to check. 🔍')
        return
    
    input_url = ' '.join(args)
    
    if not validators.url(input_url):
        await context.bot.send_message(chat_id=update.effective_chat.id, text='The provided text is not a valid URL format. Please provide a valid URL to check. ❌')
        logger.warning(f"Invalid URL format provided: {input_url}")
        return

    logger.info(f"Checking URL: {input_url}")  # Log the URL being checked
    
    try:
        response = await check_copyscape(input_url, api_key, username)
        if response:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Here are the results: ✅\n{response}')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='No results found. Your content is unique! 🎉')
    except Exception as e:
        logger.error(f"An error occurred while checking the URL: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text='An error occurred while checking the URL. 🚨')

def main() -> None:
    application = Application.builder().token("7011319545:AAGZaDo7rWAijdEY3t1I2w9zY0Q9RVGRW3I").build()  # Replace with your Telegram bot token

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check))

    logger.info("Bot started successfully 🤖.")
    application.run_polling()

if __name__ == '__main__':
    main()