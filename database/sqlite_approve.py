from database.sqlite import db, cur


async def db_connect() -> None:
    cur.execute("""CREATE TABLE IF NOT EXISTS approve(
    user_id INTEGER NOT NULL,
    info TEXT NOT NULL)
    """)

    db.commit()


async def create_new_approve(message, state):
    async with state.proxy() as data:
        approve = cur.execute("INSERT INTO approve VALUES (?, ?)", (message.chat.id, data['info'],))
        db.commit()

    return approve