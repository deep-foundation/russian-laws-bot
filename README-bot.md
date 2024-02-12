# telegram-gpt-bot

Before you begin, make sure you have Docker and Python installed.

## Creating a bot in Telegram
- Open `@BotFather`.
- Type `/newbot` and follow the instructions to create a new bot.
- `@BotFather` will provide a token for the new bot.

## Clone the repository
```bash
git clone https://github.com/deep-foundation/chatpgt-telegram-bot
```

## Login to the code folder
```bash
cd .\chatpgt-telegram-bot\python\
```

## Setting environment variables
After entering the code folder, you will need to set up environment variables. To do this, create a `.env` file. In this file you can change the values as follows:
```env
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_TOKEN=your_telegram_bot_token
```

## Run locally

```bash
pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
python ./main.py
```

## Building a Docker image
```bash
docker build -t deep-chatgpt-telegram-bot .
```

## Running a Docker container
```bash
docker run -p 8080:8080 --name container-deep-chatgpt-telegram-bot deep-chatgpt-telegram-bot
```
