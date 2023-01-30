from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
from aiogram.utils.callback_data import CallbackData
from database import sqlite as db

order_cb = CallbackData('order', 'id', 'action')
remove_cb = ReplyKeyboardRemove()


def get_start_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(keyboard=[
        [
        KeyboardButton('О группе'),
        KeyboardButton('Техническая поддержка'),
        KeyboardButton('Купить подписку'),
        ]
    ],
        resize_keyboard=True,
        input_field_placeholder='Бот распознаёт только нажатие кнопок')
    return kb


def get_start_approve_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton('О группе'),
            KeyboardButton('Техническая поддержка'),
            KeyboardButton('Состояние подписки'),
        ]
    ],
        resize_keyboard=True,
        input_field_placeholder='Бот распознаёт только нажатие кнопок')
    return kb


def support_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(
        resize_keyboard=True,
        input_field_placeholder='Ожидайте ответа администратора')
    return kb
