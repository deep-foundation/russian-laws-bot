import os, ast, json, openai, asyncio, tiktoken
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

if not openai.api_key:
    raise ValueError('No OPENAI_API_KEY is provided in .env file.')

openai.api_type = "azure"
openai.api_base = "https://deep-ai.openai.azure.com"
openai.api_version = "2023-03-15-preview"
encoding = tiktoken.encoding_for_model("gpt-4")

async def get_openai_completion(logger, messages):
    try:
        logger.info(f"---------\nCompletion request messages:\n{ast.literal_eval(json.dumps(messages, indent=4))}")

        chat_completion = await openai.ChatCompletion.acreate(
            deployment_id="gpt-4-128k",
            model="gpt-4",
            messages=messages
        )

        response = chat_completion["choices"][0]["message"]

        logger.info(f"---------\nCompletion responce:\n{ast.literal_eval(json.dumps(response, indent=4))}")

        return response
    except Exception as e:
        logger.error(f"OpenAI completion error: {e}")
        raise


async def search_query_to_key_words(logger, search_query):
    response = await get_openai_completion(logger, [{'role': 'user', 'content': '```\n' + search_query + '```\n Составь список ключевых слов и фраз которые помогут векторному и полнотекстовому поиску найти применяемые в этом случае статьи закона в виде массива строк представленных JSON. Составляй список ключевых слов и фраз таким образом, чтобы он содержал только самые важные слова/фразы, которые позволят найти применимые к запросу пользователя статьи законов. Несущественные обстоятельства лучше опустить. Ответ должен содержать исключительно JSON без Markdown. Используй юридический язык, чтобы повысить вероятность, что в тексте законов встретятся такие слова/фразы. Можно добавлять несколько вариантов одного и того же слова/фразы.' }])

    key_words = json.loads(response['content'].strip().removeprefix('```json').removesuffix('```').strip())

    modified_search_query = ',\n'.join(key_words)

    logger.info(f"---------modified_search_query:\n{modified_search_query}", )

    return modified_search_query

async def filter_documents(logger, search_query, documents):
    json_documents = json.dumps(documents, ensure_ascii=False, indent=4).encode('utf8').decode()
    
    logger.info(f"---------Documents to request:\n{json_documents}")
    
    response = await get_openai_completion(logger, [{'role': 'user', 'content': '# Запроc пользователя:\n```\n' + search_query + '```\n# Найденные статьи законов:\n```json\n' + json_documents + '```\n Оставь в JSON-массиве найденных документов только те, которые применимы к запросу пользователя с юридической точки зрения. Ответ должен содержать исключительно JSON без Markdown.' }])
        
    logger.info(f"---------Documents filter response:\n{response['content']}")

    filtered_documents = json.loads(response['content'].strip().removeprefix('```json').removesuffix('```').strip())

    return filtered_documents