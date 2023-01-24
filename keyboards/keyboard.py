from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.callback_data import CallbackData

order_cb = CallbackData('order', 'id', 'action')
remove_cb = ReplyKeyboardRemove()


def get_orders_ikb() -> InlineKeyboardMarkup:
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Создать новый заказ', callback_data='add_new_order')],
        [InlineKeyboardButton('Просмотр статуса заказа', callback_data='get_all_orders')],
    ])

    return ikb


def get_start_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton('/orders')]
    ], resize_keyboard=True)
    return kb


def get_cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton('/cancel')]
    ], resize_keyboard=True)
    return kb

