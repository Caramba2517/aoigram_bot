import sqlite3

db = sqlite3.connect('bot.db')
cur = db.cursor()


async def db_connect() -> None:
    cur.execute("CREATE TABLE IF NOT EXISTS orders (user_id INTEGER NOT NULL, name TEXT, country TEXT, phone TEXT)")
    db.commit()


async def get_all_orders(callback):
    order = cur.execute("SELECT * FROM orders WHERE user_id=?", (callback.message.chat.id,)).fetchall()
    return order


async def create_new_order(message, state):
    async with state.proxy() as data:
        order = cur.execute("INSERT INTO orders VALUES (?, ?, ?, ?)", (message.chat.id, data['name'], data['country'], data['phone']))
        db.commit()
    return order
