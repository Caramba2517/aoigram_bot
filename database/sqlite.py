import math
from datetime import datetime
import sqlite3

db = sqlite3.connect('bot.db', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
cur = db.cursor()


async def db_connect() -> None:
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER NOT NULL UNIQUE,
     status TEXT NOT NULL, 
     time_create TEXT NOT NULL,
     subscribe_from TEXT NULL)
     """)
    db.commit()


async def add_new_sub(message):
    user = cur.execute("SELECT * FROM users WHERE user_id=?", (message.chat.id,)).fetchall()
    if user:
        pass
    else:
        cur.execute("INSERT INTO users (user_id, status, time_create) VALUES (?, ?, ?)",
                    (message.chat.id, 'zero_state', datetime.now(),))
        db.commit()


async def change_status_to_pc(callback):
    cur.execute("UPDATE users SET status='payment_confirmation' WHERE user_id=?", (callback.message.chat.id,))
    db.commit()


async def change_status_to_wa(callback):
    cur.execute("UPDATE users SET status='wait_approve' WHERE user_id=?", (callback.message.chat.id,))
    db.commit()


async def change_status_approve(message, user_id):
    cur.execute("UPDATE users SET status='Current_group_member' WHERE user_id=?", (user_id,))
    db.commit()
    cur.execute("UPDATE users SET subscribe_from=? WHERE user_id=?", (datetime.now(), user_id,))
    db.commit()


def status_message(message):
    stat = cur.execute("SELECT * FROM users WHERE user_id=? AND status=?",
                       (message.chat.id, 'Current_group_member')).fetchone()
    stat1 = cur.execute("SELECT * FROM users WHERE user_id=? AND status=?",
                        (message.chat.id, 'Current_group_payment_confirmation')).fetchone()
    stat2 = cur.execute("SELECT * FROM users WHERE user_id=? AND status=?",
                        (message.chat.id, 'Current_group_wait_approve')).fetchone()
    stat3 = cur.execute("SELECT * FROM users WHERE user_id=? AND status=?",
                        (message.chat.id, 'Current_group_next_year')).fetchone()
    if stat:
        return stat
    elif stat1:
        return stat1
    elif stat2:
        return stat2
    elif stat3:
        return stat3


def status_check_approve(user_id):
    stat = cur.execute("SELECT * FROM users WHERE user_id=? AND status=?",
                       (user_id, 'Current_group_payment_confirmation')).fetchone()
    return stat


def current_status_message(message):
    stat = cur.execute("SELECT * FROM users WHERE user_id=? AND status='Current_group_next_year'",
                       (message.chat.id,)).fetchone()
    return stat


def status_callback(callback):
    stat = cur.execute("SELECT * FROM users WHERE user_id=? AND status=?",
                       (callback.message.chat.id, 'Current_group_member')).fetchone()
    return stat


def current_status_callback(callback):
    stat = cur.execute("SELECT * FROM users WHERE user_id=? AND status='Current_group_next_year'",
                       (callback.message.chat.id,)).fetchone()
    return stat


def count(message):
    currents = cur.execute("SELECT time_create FROM users WHERE user_id=? ", (message.chat.id,)).fetchall()
    for current in currents:
        current_datetime = datetime.strptime(current[0], '%Y-%m-%d %H:%M:%S.%f')
        end = datetime(current_datetime.year, 12, 31)
        days_left = (end - current_datetime).days
        cost = math.ceil(0.4 * days_left)
        return cost


def subscribe_from(message):
    currents = cur.execute("SELECT subscribe_from FROM users WHERE user_id=? ", (message.chat.id,)).fetchall()
    for current in currents:
        current_datetime = datetime.strptime(current[0], '%Y-%m-%d %H:%M:%S.%f')
        end = datetime(current_datetime.year, 12, 31)
        days_left = (end - current_datetime).days
        return days_left


async def change_current_status_to_pc(callback):
    cur.execute("UPDATE users SET status='Current_group_payment_confirmation' WHERE user_id=?",
                (callback.message.chat.id,))
    db.commit()


async def change_сurrent_status_to_wa(callback):
    cur.execute("UPDATE users SET status='Current_group_wait_approve' WHERE user_id=?", (callback.message.chat.id,))
    db.commit()


async def change_current_status_approve(user_id):
    cur.execute("UPDATE users SET status='Current_group_next_year' WHERE user_id=?", (user_id,))
    db.commit()


def current_subscribe_from(message):
    currents = cur.execute("SELECT subscribe_from FROM users WHERE user_id=? ", (message.chat.id,)).fetchall()
    for current in currents:
        current_datetime = datetime.strptime(current[0], '%Y-%m-%d %H:%M:%S.%f')
        end = datetime(current_datetime.year, 12, 31)
        days_left = (end - current_datetime).days + 365
        return days_left
