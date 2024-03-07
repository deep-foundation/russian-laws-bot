import os, ast, json, openai, asyncio

openai.api_key = os.getenv('OPENAI_API_KEY')

if not openai.api_key:
    raise ValueError('No OPENAI_API_KEY is provided in .env file.')

openai.api_type = "azure"
openai.api_base = "https://deep-ai.openai.azure.com"
openai.api_version = "2023-03-15-preview"
encoding = tiktoken.encoding_for_model("gpt-4")

async def get_openai_completion(messages):
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