import logging

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor

from googletrans import Translator
import openai

import requests
from datetime import datetime, timedelta


logging.basicConfig(level=logging.INFO)


def print_answer(text):
    if isinstance(text, list):
        formatted_string = "\n".join([", ".join(d.values()) for d in text])
        return formatted_string
    else:
        formatted_string = text
        return formatted_string
        
        

def translate_to_ukrainian(text):
    translator = Translator()
    translated = translator.translate(text, src='en', dest='uk')
    return translated.text


def parse_news(news_about):
    current_date = datetime.today()

    last_week_date = current_date - timedelta(days=7)

    last_week_date_formatted = last_week_date.strftime('%Y-%m-%d')
    url = f'https://newsapi.org/v2/everything?q={news_about}&from={last_week_date_formatted}&sortBy=popularity&apiKey={news_api}'

    response = requests.get(url).json()
    articles = response['articles']
    top_10_news = []
    
    for article in articles[:9]:
        article_dict = {
        "title": article["title"],
        "url": article["url"]
        }
        top_10_news.append(article_dict)

    return top_10_news


API_TOKEN = '6559560990:AAFrmQPSXR6oU0azHcwvaiRvc2W8jrUmLjo'
openai.api_key = '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'
news_api = 'c901596942e74ee9b1260a55880125ad'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    action = State()
    question = State()
    answer = State()

@dp.message_handler(commands='help')
async def send_welcome(message: types.Message):
    message_text = "Hi, I'm a help bot, here you will find a few useful tricks for you.\nWith this bot, you can explain some pieces of code, create some functions, and more. Give it a try!"
    await message.reply(message_text)

@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Explain Code")
    button2 = types.KeyboardButton("Pros and Cons")
    button3 = types.KeyboardButton("Translator")
    button4 = types.KeyboardButton("Top 10 news")
    markup.add(button1, button2)
    markup.add(button3)
    markup.add(button4)

    await Form.action.set()
    await message.answer("Hi, I'm a help bot, please select an option to work with.", reply_markup=markup)

@dp.message_handler(lambda message: message.text in ["Explain Code", "Pros and Cons"], state=Form.action)
async def process_action(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['action'] = message.text

    await Form.next()

    markup = types.ReplyKeyboardRemove()

    if message.text == "Explain Code":
        await message.answer("Give me your code.", reply_markup=markup)
    else:
        await message.answer("Give me your question about pros and cons.", reply_markup=markup)
        
        
@dp.message_handler(lambda message: message.text in ["Translator"], state=Form.action)
async def process_action(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['action'] = message.text

    await Form.next()

    markup = types.ReplyKeyboardRemove()

    await message.answer("Give me your text for tlanslate.", reply_markup=markup)
    

@dp.message_handler(lambda message: message.text in ["Top 10 news"], state=Form.action)
async def process_action(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['action'] = message.text

    await Form.next()

    markup = types.ReplyKeyboardRemove()

    await message.answer("About what you want to see news?", reply_markup=markup)
        

@dp.message_handler(state=Form.question)
async def process_question_or_code(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        
        data['question'] = message.text
        
        await Form.next()
        await message.answer("Processing...")
        
        if data['action'] == "Translator":
            user_text = data['question']  # Get the user's text for translation
            translated_text = translate_to_ukrainian(user_text)  # Use the translation function
            # Send the translated text to the user
            data['answer'] = translated_text
            
        elif data['action'] in ["Explain Code", "Pros and Cons"]:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{'role': 'user', 'content': message.text}],
                temperature=0,
                max_tokens=1024
            )

            data['answer'] = response['choices'][0]["message"]["content"]
            
        elif data['action'] == "Top 10 news":
            user_text = data['question']
            news = parse_news(user_text)
            
            data['answer'] = news
            print(data['answer'])

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Explain Code")
        button2 = types.KeyboardButton("Pros and Cons")
        button3 = types.KeyboardButton("Translator")
        button4 = types.KeyboardButton("Top 10 news")
        markup.add(button1, button2)
        markup.add(button3)
        markup.add(button4)        
        
        answer = print_answer(data['answer'])
        
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Action:', md.bold(data['action'])),
                md.text('Question:', md.code(data['question'])),
                md.text('Answer:\n', answer),
                sep='\n',
            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )

        await Form.action.set()  # Перехід до вибору опцій після обробки запитання

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
