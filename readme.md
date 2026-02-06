# Telegram API Server

This is a simple **Telegram API server** that allows you to send messages using Telegram bots.  
All bot data is stored in a **local database**.

## API Endpoints

### `POST /notify`
Sends a message using the Telegram Bot API.

**Parameters:**
- `bot` — The name of the bot stored in the database  
- `text` — The message the bot should send  

---

### `POST /add_bot`
Adds a new bot to the local database.

**Parameters:**
- `bot_name` — The name you want to give the bot  
- `bot_token` — The bot token provided by Telegram  
- `chat_id` — The ID of the chat where the bot will send messages  

---

### `GET /list_bots`

Lists all bots stored in the database.

**Returns:**
```json
{
  "status": "ok",
  "bots": [
    {
      "chat_id": "string",
      "name": "string",
      "token": "string"
    }
  ]
}
```

---

## How to Install

1. Clone this repository:
   ```bash
   git clone https://github.com/AndreSmalheer/telegram-bot-prototype
   ```

2. Install all required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:
   ```bash
   python app.py
   ```