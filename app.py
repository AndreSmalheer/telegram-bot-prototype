from flask import Flask, request, jsonify
import requests
import sqlite3
import base64


app = Flask(__name__)

db_file = "data.db"

def get_db_connection(db_file = db_file):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    return cursor, conn

def get_bot_data(bot_name):
    bot_name = bot_name.lower()
    
    # Connect to database
    cursor, conn = get_db_connection()

    cursor.execute("""
    SELECT * 
    FROM bots 
    WHERE name = ?
    """, (bot_name,))

    bot = cursor.fetchone()
    conn.close()

    return bot

@app.route("/add_bot", methods=["POST"])
def add_bot():
    data = request.get_json(force=True)

    bot_name  = data.get("bot_name", None)
    bot_token = data.get("bot_token", None)
    chat_id = data.get("chat_id", None)

    if not chat_id:
        return jsonify({"status": "error", "message": "Missing chat ID"}), 400

    if not bot_name:
        return jsonify({"status": "error", "message": "Bot name missing"}), 400

    if not bot_token:
        return jsonify({"status": "error", "message": "Bot token missing"}), 400

    cursor, conn = get_db_connection()

    try:
        cursor.execute("""
            INSERT INTO bots (name, token, chat_id) 
            VALUES (?, ?, ?)
        """, (bot_name.lower(), bot_token, chat_id))

        conn.commit()
        return {"status": "success", "message": "bot succsefully created", "bot_id": cursor.lastrowid}

    except sqlite3.IntegrityError as e:
        return {"status": "error", "message": str(e)}

    finally:
        conn.close()

@app.route("/delete_bot", methods=["POST"])
def delete_bot():
    data = request.get_json(force=True)

    bot_name  = data.get("bot_name", None)
    bot_token = data.get("bot_token", None)
    bot_id    = data.get("id", None)

    if bot_name is None and bot_token is None and bot_id is None:
        return jsonify({"error": "No bot_name + bot_token or id previded"}), 400

    cursor, conn = get_db_connection()
    
    try:
        messages = []

        if bot_id:
            cursor.execute("DELETE FROM bots WHERE id = ?", (bot_id,))
            messages.append(f"Bot with ID {bot_id} deleted.")

        elif bot_token:
            cursor.execute("DELETE FROM bots WHERE token = ?", (bot_token,))
            messages.append("Bot deleted by token.")
            
        elif bot_name:
            cursor.execute("DELETE FROM bots WHERE name = ?", (bot_name.lower(),))
            messages.append(f"Bot '{bot_name}' deleted by name.")

        conn.commit()
        return jsonify({"success": True, "messages": messages})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@app.route("/edit_bot", methods=["POST"])
def edit_bot():
    data = request.get_json(force=True)

    bot_id    = data.get("id")
    bot_name  = data.get("bot_name")
    bot_token = data.get("bot_token")

    new_name     = data.get("new_name")
    new_token    = data.get("new_token")
    new_chat_id  = data.get("new_chat_id")

    if not (bot_id or bot_name or bot_token):
        return jsonify({"error": "No identifier provided (id, bot_name, or bot_token)"}), 400

    if not (new_name or new_token or new_chat_id):
        return jsonify({"error": "No new values provided to update"}), 400

    cursor, conn = get_db_connection()

    try:
        updates = []
        values = []

        if new_name:
            updates.append("name = ?")
            values.append(new_name.lower())

        if new_token:
            updates.append("token = ?")
            values.append(new_token)

        if new_chat_id:
            updates.append("chat_id = ?")
            values.append(new_chat_id)

        set_clause = ", ".join(updates)

        if bot_id:
            query = f"UPDATE bots SET {set_clause} WHERE id = ?"
            values.append(bot_id)

        elif bot_token:
            query = f"UPDATE bots SET {set_clause} WHERE token = ?"
            values.append(bot_token)

        else: 
            query = f"UPDATE bots SET {set_clause} WHERE name = ?"
            values.append(bot_name.lower())

        cursor.execute(query, tuple(values))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "No bot found to update"}), 404

        return jsonify({"success": True, "message": "Bot updated successfully"})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@app.route("/notify", methods=["POST"])
def notify():
    data = request.get_json(force=True)
    bot = data.get("bot", None)
    text = data.get("text", None)

    if not text:
        return jsonify({"status": "error", "message": "No text provided"}), 400
    
    if not bot:
        return jsonify({"status": "error", "message": "No bot provided"}), 400
    
    data = get_bot_data(bot.lower())

    if data:
        name = data['name']
        token = data['token']
        CHAT_ID = data['chat_id']

        if not name:
            return jsonify({"status": "error", "message": "Bot name not found in db"}), 400

        if not token:
            return jsonify({"status": "error", "message": "Bot token not found in db"}), 400

        if not CHAT_ID:
            return jsonify({"status": "error", "message": "No chat ID found in db"}), 400
 
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text}

        response = requests.post(url, data=payload, timeout=10)  
        response.raise_for_status()  

        return jsonify({"status": "sent", "telegram_response": response.json()}), 200
    else:
        return jsonify({"status": "error", "message": "no data in db"}), 400

@app.route("/list_bots")
def list_bots():
    cursor, conn = get_db_connection()

    cursor.execute("""SELECT * FROM bots """)
    rows = cursor.fetchall()
    conn.close()

    bots = [dict(row) for row in rows]

    print(bots)

    return jsonify({"status": "ok", "bots": bots}), 200

@app.route("/")
def status():
    return "Server Online"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)