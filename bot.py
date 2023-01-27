import asyncio

from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from keys import TOKEN
from database import sqlite as db
from keyboards.keyboard import order_cb, get_start_kb, remove_cb, get_start_approve_kb
from database import sqlite_approve as db_a
from database.models import ApproveStatesGroup

bot = Bot(TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def on_startup(_):
    await db.db_connect()
    await db_a.db_connect()
    print('Подключение к БД выполнено успешно.')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    name = message.chat.first_name
    user = db.status_message(message)

    if not user:
        await message.answer(f'Привет, {name}!',
                             reply_markup=get_start_kb())
        await db.add_new_sub(message)

    else:
        await message.answer(f'Привет, {name}!\n'
                             f'\nУ тебя есть действуюшая подписка. Подробнее по кнопке: "Состояние подписки"',
                             reply_markup=get_start_approve_kb())


@dp.message_handler(Text(equals='О группе'))
async def group_info(message: types.Message):
    await message.answer(text='Текст-описание о группе!')


@dp.message_handler(Text(equals='Купить подписку'))
async def buy_subscription(message: types.Message):
    buttons = [
        types.InlineKeyboardButton(text='Я оплатил', callback_data='payment_check'),
    ]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*buttons)
    n = db.count(message)
    await message.answer(text=f'Доступ в премиум-группу стоит 149$/год\n'
                              f'\nПодписка действует до конца года и на сегодняшний день составляет {n} USDT.\n'
                              f'\nПожалуйста, не забудь сделать скриншот оплаты. Он потребуется при подтверждении '
                              f'платежа!',
                         reply_markup=keyboard)


@dp.callback_query_handler(text='payment_check')
async def payment_check(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    user = db.status_callback(callback)
    if not user:
        await db.change_status_to_pc(callback)
        print('СТАТУС В БД ИЗМЕНЕН НА PC')
        buttons = [
            types.InlineKeyboardButton(text='Начать проверку', callback_data='wait_approve')
        ]
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(*buttons)
        await callback.message.answer(text=f'Чтобы подтвердить платёж следуй инструкциям бота',
                                      reply_markup=keyboard)

    else:
        await callback.message.edit_text('У тебя есть действуюшая подписка. Подробнее по кнопке: "Состояние подписки"')


@dp.callback_query_handler(text='wait_approve')
async def add_approve_status(callback: types.CallbackQuery) -> None:
    await callback.message.edit_reply_markup()
    await callback.message.answer('Отправь информацию об оплате, укажите платежную систему:', reply_markup=remove_cb)

    await ApproveStatesGroup.text.set()


@dp.message_handler(state=ApproveStatesGroup.text)
async def handle_title(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['text'] = message.text
    await message.answer('Отправь скриншот об оплате:')

    await ApproveStatesGroup.next()


@dp.message_handler(lambda message: not message.photo, state=ApproveStatesGroup.photo)
async def check_photo(message: types.Message):
    await message.reply('Это не скриншот!')


@dp.message_handler(content_types=['photo'], state=ApproveStatesGroup.photo)
async def handle_photo(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id
    await db_a.create_new_approve(message, state)
    await message.answer('Cпасибо за оформление подписки, ожидайте подтверждение от администатора!',
                         reply_markup=get_start_approve_kb())
    await state.finish()


@dp.callback_query_handler(text='payment_selled')
async def payment_selled(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    name = callback.message.from_user.first_name
    user = db.status_callback(callback)
    if not user:
        await db.change_status_to_wa(callback)
        print('СТАТУС В БД ИЗМЕНЕН НА WA')
    else:
        await callback.message.edit_text(f'{name}, у тебя уже есть подписка.')


async def approve(message: types.Message):
    await message.answer(text='Платеж успешно подтвержден!', reply_markup=get_start_approve_kb())
    await db.change_status_approve(message)
    print('СТАТУС БД ИЗМЕНЕН НА АПРУВ, ПОДПИСКА НАЧАТА')


@dp.message_handler(Text(equals='Техническая поддержка'))
async def support(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        input_field_placeholder='Введи вопрос здесь')
    await message.answer(text='Вы вызывали менеджера, какой у вас вопрос?', reply_markup=keyboard)


@dp.message_handler(Text(equals='Состояние подписки'))
async def buy_subscription(message: types.Message):
    user = db.status_message(message)
    cur_user = db.current_status_message(message)
    if user:
        buttons = [
            types.InlineKeyboardButton(text='Продлить подписку', callback_data='сurrent_payment_check'),
        ]
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(*buttons)
        n = db.subscribe_from(message)

        await message.answer(text=f'Вашей подписке осталось {n} дней',
                             reply_markup=keyboard)

    elif cur_user:
        n = db.current_subscribe_from(message)
        await message.answer(text=f'Вашей подписке осталось {n} дней')

    else:
        await message.answer(text='У вас нет оформленной подписки.',
                             reply_markup=remove_cb)


@dp.callback_query_handler(text='сurrent_payment_check')
async def cur_payment_check(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    await db.change_current_status_to_pc(callback)
    buttons = [
        types.InlineKeyboardButton(text='Отправить платеж на проверку', callback_data='current_payment_selled')
    ]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*buttons)
    await callback.message.answer(text='Чтобы подтвердить платёж...', reply_markup=keyboard)


@dp.callback_query_handler(text='current_payment_selled')
async def cur_payment_selled(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    await callback.message.answer(text='Ожидайте подтверждение платежа...')
    await db.change_status_to_wa(callback)
    print('СТАТУС В БД ИЗМЕНЕН НА ТС')
    await asyncio.sleep(10)
    await callback.message.answer(text='Платеж успешно подтвержден!', reply_markup=get_start_approve_kb())
    await db.change_current_status_approve(callback)
    print('СТАТУС БД ИЗМЕНЕН НА АПРУВ, ПОДПИСКА НАЧАТА')


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           skip_updates=True,
                           on_startup=on_startup)
