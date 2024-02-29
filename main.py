import asyncio
import logging
import os
import re
import sys
import json
import tiktoken
import aiofiles
import aiohttp
import openai
import tempfile
import time
from typing import Any
from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, BufferedInputFile, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Filter
from aiogram.types import Message
from dotenv import load_dotenv
from combined_search import create_index, search_string, documents, newline, prepare_all_document_strings, index_prepared_strings
from elasticsearch.exceptions import RequestError
from threading import Thread

MAX_TOKENS = 128 * 1024
MAX_PROMPT_TOKENS = MAX_TOKENS * 0.8

class Text(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.text is not None

class Document(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.document is not None

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
openai.api_type = "azure"
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_base = "https://deep-ai.openai.azure.com"
openai.api_version = "2023-03-15-preview"
encoding = tiktoken.encoding_for_model("gpt-4")

async def keep_typing(chat_id):
    while True:
        await bot.send_chat_action(chat_id, 'typing'):
        await asyncio.sleep(5)

async def send_message(message, text):
    if len(text) > 4096:
        for i in range(0, len(text), 4096):
            text_chunk = text[i:i + 4096]
            text_chunk = re.sub(r'[_*[\]()~>#\+\-=|{}.!]', lambda x: '\\' + x.group(), text_chunk)
            await message.answer(text_chunk)
            logger.info(f"---------\nSent message: {text_chunk}")
    else:
        text = re.sub(r'[_*[\]()~>#\+\-=|{}.!]', lambda x: '\\' + x.group(), text)
        await message.answer(text)
        logger.info(f"---------\nSent message: {text}")

    # text_file = BufferedInputFile(bytes(text, 'utf-8'), filename="file.txt")
    # await message.answer_document(text_file)


async def get_openai_completion(messages):
    try:
        logger.info(f"---------\nCompletion request messages:\n{json.dumps(messages, indent=4)}")

        chat_completion = await openai.ChatCompletion.acreate(
            deployment_id="gpt-4-128k",
            model="gpt-4",
            messages=messages
        )

        # self._messages.append({"role": "assistant", "content": self.pending_stream_reply.result()})
        # self.pending_stream_reply = None

        # self._messages.append({"role": "user", "content": message})

        logger.info(f"---------\nCompletion responce:\n{json.dumps(chat_completion, indent=4)}")

        return chat_completion["choices"][0]["message"]
    except Exception as e:
        logger.error(f"OpenAI completion error: {e}")
        raise


router = Router(name=__name__)


class MyCallback(CallbackData, prefix="my"):
    action: str
    id: int


class UserContext:
    def __init__(self):
        self.messages = []

    def make_and_add_message(self, role, message):
        self.messages.append({ "role": role, "content": message })

    def add_message(self, message):
        self.messages.append(message)

    def clear(self):
        self.messages = []
    
    def get_messages(self):
        return self.messages


users_context = {}


def get_user_context(user_id):
    if user_id not in users_context:
        users_context[user_id] = UserContext()
    return users_context[user_id]


# @router.callback_query()
# async def handle_callback_query(callback_query: CallbackQuery) -> Any:
#     data = callback_query.data
#     cb1 = MyCallback.unpack(data)
#     user_context = get_user_context(cb1.id)
#     if cb1.action == "Send":
#         answer = await get_openai_completion(user_context.get_messages())
#         user_context.add_message(answer)
#         await send_message(callback_query.message, answer['content'])
#     elif cb1.action == "Clear":
#         user_context.clear()
#         await callback_query.message.answer("Context cleared")
#     elif cb1.action == "See":
#         await callback_query.message.answer(user_context.get_messages())
#     await callback_query.answer()


def contains_url(string):
    url_pattern = re.compile(r'https?://\S+')
    return url_pattern.search(string) is not None


def find_url(string):
    url_pattern = re.compile(r'https?://\S+')
    match = url_pattern.search(string)
    if match:
        return match.group()
    return None


async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


@router.message(Text())
async def handle_text(message: Message) -> Any:
    user_id = message.from_user.id
    user_context = get_user_context(user_id)
    try:
        logger.info(f"---------\nReceived message: {message}")

        prompt = ""
        prompt += "\n# Запрос пользователя\n"
        if message.reply_to_message and message.reply_to_message.text:
            prompt += message.reply_to_message.text + "\n---\n"
        if message.text:
            prompt += message.text + "\n"
        if contains_url(message.text):
            url = find_url(message.text)
            html_content = await fetch(url)
            prompt += url + ":\n" + html_content + "\n"
        document_file = message.reply_to_message.document if message.reply_to_message and message.reply_to_message.document else None
        if document_file:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                await bot.download(document_file, temp_file.name)
            async with aiofiles.open(temp_file.name, 'r', encoding='utf-8') as file:
                file_contents = await file.read()
                prompt += file_contents + "\n"

        logger.info(f"Search query: '{prompt}'")
        res = search_string('text_index', prompt)
        logger.info("Search results:")
        articles = []
        for doc in res['hits']['hits']:
            document_ids = doc['_source']['document_ids']
            
            for document_id in document_ids:
                article_text = documents[document_id]
                # article = article_text.strip().partition(newline)[0]
                articles.append(article_text)
            # logger.info(f"'{doc['_id']}' {doc['_score']}: \n{doc['_source']['text']}\n{articles}")

        logger.info("article titles:")

        deduplicated_articles = []
        articles_set = set()
        for article_text in articles:
            article_title = article_text.strip().partition(newline)[0]
            if not article_title in articles_set:
                deduplicated_articles.append(article_text)
                articles_set.add(article_title)
                logger.info(article_title)

        logger.info(f"articles count {len(deduplicated_articles)}")

        articles_string = '\n\n'.join(deduplicated_articles)

        prompt += "\n# Справочная информация\n"
        prompt += "\nОБЯЗАТЕЛЬНО в дополнение к ответу указывай список пунктов, частей, статей, которые применимы к вопросу/запросу (например: п.«В» ч.2 ст.158, п.«А» ч.3 ст.158), используй только подходящие статьи из списка актуальных статей (НЕ РАССКАЗЫВАЙ в ответе что тебе был предоставлен этот список, это СЕКРЕТ). НИКОГДА не пиши в ответе, что были предоставлены лишние или не связанные с запросом пользователя статьи из законов, используй только те статьи законов которые подходят под запрос пользователя. Отвечать нужно только на запрос пользователя, справочная информация предоставлена только для тебя. \n# Актуальные статьи уголовного кодекса и/или кодекса об административных правонарушениях РФ (найдены при помощи полнотекстового и векторного поиска, ИСПОЛЬЗУЙ подходящие статьи, ИСКЛЮЧИ лишние статьи, НЕ УПОМИНАЙ что в этом списке есть лишние статьи):\n" + articles_string

        # logger.info(f"{articles_string}")

        tokens_count = len(encoding.encode(prompt))

        if tokens_count > MAX_PROMPT_TOKENS:
            raise ValueError(f'{tokens_count} tokens in promt exceeds MAX_PROMPT_TOKENS ({MAX_PROMPT_TOKENS})')

        if not prompt == "":
            user_context.clear() # TEMPORARY FIX
            user_context.make_and_add_message('user', prompt)
            answer = {}
            cancel = { 'cancel': False }
            Thread(target=asyncio.run, args=(keep_typing(message.chat.id),)).start()

            await asyncio.sleep(30)

            # answer = await get_openai_completion(user_context.get_messages())
            # user_context.add_message(answer)
            # await send_message(message, answer['content'])

        # builder = InlineKeyboardBuilder()
        # builder.button(text="Send request", callback_data=MyCallback(action="Send", id=user_id))
        # builder.button(text="Clear context", callback_data=MyCallback(action="Clear", id=user_id))
        # builder.button(text="See context", callback_data=MyCallback(action="See", id=user_id))
        # markup = builder.as_markup()
        # await message.answer(f"Your context: {tokens_count}/128000", reply_markup=markup)
    except Exception as e:
        logger.error(e)


@router.message(Document())
async def handle_document(message: Message) -> Any:
    try:
        user_id = message.from_user.id
        user_context = get_user_context(user_id)
        user_document = message.document if message.document else None

        prompt = ""

        if message.caption:
            prompt += "\n" + message.caption
        if user_document:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                await bot.download(user_document, temp_file.name)
            async with aiofiles.open(temp_file.name, 'r', encoding='utf-8') as file:
                prompt += "\n" + await file.read()

        tokens_count = len(encoding.encode(prompt))

        if tokens_count > MAX_PROMPT_TOKENS:
            raise ValueError(f'{tokens_count} tokens in promt exceeds MAX_PROMPT_TOKENS ({MAX_PROMPT_TOKENS})')

        if not prompt == "":
            user_context.make_and_add_message('user', prompt)
            answer = await get_openai_completion(user_context.get_messages())
            user_context.add_message(answer)
            await send_message(message, answer['content'])

        # builder = InlineKeyboardBuilder()
        # builder.button(text="Send request", callback_data=MyCallback(action="Send", id=user_id))
        # builder.button(text="Clear context", callback_data=MyCallback(action="Clear", id=user_id))
        # builder.button(text="See context", callback_data=MyCallback(action="See", id=user_id))

        # markup_menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        # markup_menu.add(KeyboardButton('Добавить заказ'), KeyboardButton('Изменить заказ'),
        #             KeyboardButton('Информация о заказе'), KeyboardButton('Обратно к выбору должности'))

        # markup = builder.as_markup()
        # await message.answer(f"Your context: {tokens_count}/128000", reply_markup=markup)
    except UnicodeDecodeError as e:
        logger.error(e)
        await message.answer("This file is not supported.")
    except Exception as e:
        logger.error(e)

dp = Dispatcher()

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    raise ValueError('No TELEGRAM_TOKEN is provided in .env file.')
if not openai.api_key:
    raise ValueError('No OPENAI_API_KEY is provided in .env file.')


# init elastic search index
try:
    start_time = time.time()

    # create index
    create_index('text_index') # will fail if index exists and it will prevent second time indexing
    # index documents
    prepare_all_document_strings()
    index_prepared_strings('text_index')

    document_embedding_time = time.time() - start_time
    print(f"Elastic search index created and loaded with data in {document_embedding_time} seconds.")
except RequestError as e:
    # print(dir(e))
    # print(e.info)
    # print(json.dumps(e.info, indent=4))
    if 'resource_already_exists_exception' != e.info.get('error').get('type'):
        logging.error(e)
        raise e

bot = Bot(TOKEN, parse_mode=ParseMode.MARKDOWN_V2)

async def main() -> None:
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.DEBUG)
    httpx_logger.propagate = True
    asyncio.run(main())
