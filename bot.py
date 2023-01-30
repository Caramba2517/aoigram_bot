from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from config.id import admin_id, chat_id
from config.keys import TOKEN, BUTTON
from config.links import channel_link, wallet_address, welcome_photo_url, group_information_photo_url, admin_approve_photo_url

from database import sqlite as db
from database import sqlite_approve as db_a
from database.states import ApproveStatesGroup, SupportStateGroup, AnswerStatesGroup, AdminApprove, CurrentApprove

from keyboards.keyboard import get_start_kb, remove_cb, get_start_approve_kb


bot = Bot(TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
a = []


async def on_startup(_):
    await db.db_connect()
    await db_a.db_connect()
    print('Подключение к БД выполнено успешно.')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    welcome_photo = types.input_file.InputFile.from_url(
        url=welcome_photo_url,
        filename='cat.jpg',
        chunk_size=100000
    )
    name = message.chat.first_name
    user = db.status_message(message)
    if message.chat.type == 'private':
        if message.from_user.id == admin_id:
            await message.answer_photo(photo=welcome_photo, caption=f'Для администрирования жмите /admin')
        elif not user:
            await message.answer_photo(photo=welcome_photo, caption=f'Привет, {name}!',
                                 reply_markup=get_start_kb())
            await db.add_new_sub(message)
        else:
            await message.answer_photo(photo=welcome_photo, caption=f'Привет, {name}!\n'
                                 
                                 f'\nУ тебя есть действующая подписка. Подробнее по кнопке: "Состояние подписки"',
                                 reply_markup=get_start_approve_kb())


@dp.message_handler(commands='admin')
async def admin_start(message: types.Message):
    name = message.from_user.first_name
    if message.chat.type == 'private':
        if message.from_user.id == admin_id:
            await message.answer(f'Привет, админ {name}!')
        else:
            await message.answer(f'{name}, для работы с ботом жми /start')


@dp.message_handler(text='О группе')
async def group_info(message: types.Message):
    if message.chat.type == 'private':
        group_information_photo = types.input_file.InputFile.from_url(
            url=group_information_photo_url,
            filename='cat.jpg',
            chunk_size=100000
        )
        await message.answer_photo(
            photo=group_information_photo,
            caption='Текст-описание о группе!'
            )


@dp.message_handler(text='Купить подписку')
async def buy_subscription(message: types.Message):
    buttons = [
        types.InlineKeyboardButton(text='Я оплатил', callback_data='payment_check'),
    ]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*buttons)
    n = db.count(message)
    if message.chat.type == 'private':
        user = db.status_message(message)
        if not user:
            await message.answer(text=f'Доступ в премиум-группу стоит 149$/год\n'
                                    f'\nПодписка действует до конца года и на сегодняшний день составляет {n} USDT.\n'
                                    f'\nОплата производится в USDT, по адресу:'
                                    f'\n<a href="{wallet_address}">Адрес кошелька</a> - сеть BEP20, TRC20',
                                reply_markup=keyboard, parse_mode=types.ParseMode.HTML)
        else:
            await message.answer(text='У тебя уже есть оформленная подписка. Подробнее: "Состояние подписки"',
                                 reply_markup=get_start_approve_kb())


@dp.callback_query_handler(text='payment_check')
async def payment_check(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    user = db.status_callback(callback)
    if not user and callback.message.chat.type == 'private':
        await db.change_status_to_pc(callback)
        print('СТАТУС В БД ИЗМЕНЕН НА PC')
        await callback.message.answer('Пожалуйста, пришлите TxID транзакции, ссылку на транзакцию или скриншот оплаты:')

    else:
        await callback.message.edit_text('У тебя есть действующая подписка. Подробнее по кнопке: "Состояние подписки"')
    await ApproveStatesGroup.info.set()


# @dp.callback_query_handler(text='wait_approve')
# async def add_approve_status(callback: types.CallbackQuery) -> None:
#     await callback.message.edit_reply_markup()


@dp.message_handler(content_types=['text', 'photo'], state=ApproveStatesGroup.info)
async def handle_photo(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    button = [
        types.InlineKeyboardButton(text='Подтвердить данные', callback_data='approve')
    ]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*button)
    await bot.send_message(
        chat_id=admin_id,
        text=f'Пользователь `{user_id}` {user_name} прислал данные для подтверждения:',
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )
    if message.photo:
        async with state.proxy() as data:
            data['info'] = message.photo[0].file_id
            await bot.send_photo(chat_id=admin_id, photo=data.get('info'), reply_markup=keyboard)
    if message.text:
        async with state.proxy() as data:
            data['info'] = message.text
            await bot.send_message(chat_id=admin_id, text=data.get('info'), reply_markup=keyboard)

    await db_a.create_new_approve(message, state)
    await message.answer('Cпасибо за оформление подписки, ожидайте подтверждение от администратора!',
                         reply_markup=get_start_approve_kb())

    await state.finish()


# ТУТ ЛОГИКА АПРУВА АДМИНОМ!!!!


@dp.callback_query_handler(text='payment_sold')
async def payment_sold(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    name = callback.message.from_user.first_name
    user = db.status_callback(callback)
    if not user:
        await db.change_status_to_wa(callback)
        print('СТАТУС В БД ИЗМЕНЕН НА WA')
    else:
        await callback.message.edit_text(f'{name}, у тебя уже есть подписка.')


@dp.callback_query_handler(text='approve')
async def check_approve_id(callback: types.CallbackQuery, state:FSMContext):
    await bot.send_message(chat_id=admin_id, text='Введите ID пользователя (только цифры, без двоеточия):')
    await AdminApprove.user_id.set()


@dp.message_handler(state=AdminApprove.user_id)
async def approve(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_id'] = message.text
    welcome_photo = types.input_file.InputFile.from_url(
        url=admin_approve_photo_url,
        filename='cat.jpg',
        chunk_size=100000
    )
    link = await bot.create_chat_invite_link(chat_id=chat_id, member_limit=1)
    invite_link = link.invite_link
    user_id = message.text
    user = db.status_check_approve(user_id)
    print(user)
    if user:
        await bot.send_photo(
            photo=welcome_photo,
            chat_id=data.get('user_id'),
            caption=f'Администратор одобрил ваш запрос!\n Ваша подписка продлена!',
            reply_markup=get_start_approve_kb())

        await db.change_current_status_approve(user_id)
        await state.finish()

    else:
        await bot.send_photo(
            chat_id=data.get('user_id'),
            photo=welcome_photo,
            caption=f'Администратор одобрил ваш запрос!\nВаша ссылка на закрытую группу <a href="{invite_link}">здесь</a>'
                 f'\nA <a href="{channel_link}">здесь</a> ссылка на наш канал',
            reply_markup=get_start_approve_kb(),
            parse_mode=types.ParseMode.HTML)
        await db.change_status_approve(message, user_id)
        print('СТАТУС БД ИЗМЕНЕН НА АПРУВ, ПОДПИСКА НАЧАТА')
        await state.finish()


@dp.message_handler(text='Состояние подписки')
async def buy_subscription(message: types.Message):
    user = db.status_message(message)
    cur_user = db.current_status_message(message)
    if message.chat.type == 'private':
        if cur_user:
            n = db.current_subscribe_from(message)
            await message.answer(text=f'Вашей подписке осталось {n} дней')
        elif user:
            buttons = [
                types.InlineKeyboardButton(text='Продлить подписку', callback_data='current_payment_check'),
            ]
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(*buttons)
            n = db.subscribe_from(message)

            await message.answer(text=f'Вашей подписке осталось {n} дней',
                                 reply_markup=keyboard)

        else:
            await message.answer(text='У вас нет оформленной подписки.',
                                 reply_markup=remove_cb)


@dp.callback_query_handler(text='current_payment_check')
async def cur_payment_check(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    buttons = [
        types.InlineKeyboardButton(text='Я оплатил', callback_data='current_payment_wa'),
    ]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*buttons)
    await db.change_current_status_to_pc(callback)
    await callback.message.answer(text=f'Продление подписки стоит 149$/год\n'
                              f'\nОплата производится в USDT, по адресу:'
                              f'\n<a href="{wallet_address}">Адрес кошелька</a> - сеть BEP20, TRC20',
                         reply_markup=keyboard, parse_mode=types.ParseMode.HTML)


@dp.callback_query_handler(text='current_payment_wa')
async def cur_add_approve_status(callback: types.CallbackQuery) -> None:
    await callback.message.edit_reply_markup()
    await callback.message.answer('Пожалуйста, пришлите TxID транзакции, ссылку на транзакцию или скриншот оплаты:')
    await db.change_сurrent_status_to_wa(callback)
    await CurrentApprove.info.set()


@dp.message_handler(content_types=['text', 'photo'], state=CurrentApprove.info)
async def handle_photo(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    button = [
        types.InlineKeyboardButton(text='Подтвердить данные', callback_data='approve')
    ]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*button)
    await bot.send_message(
        chat_id=admin_id,
        text=f'Пользователь `{user_id}` {user_name} прислал данные для подтверждения ПРОДЛЕНИЯ ПОДПИСКИ:',
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )
    if message.photo:
        async with state.proxy() as data:
            data['info'] = message.photo[0].file_id
            await bot.send_photo(chat_id=admin_id, photo=data.get('info'), reply_markup=keyboard)
    if message.text:
        async with state.proxy() as data:
            data['info'] = message.text
            await bot.send_message(chat_id=admin_id, text=data.get('info'), reply_markup=keyboard)

    await db_a.create_new_approve(message, state)
    await message.answer('Cпасибо за продление подписки, ожидайте подтверждение от администратора!',
                         reply_markup=get_start_approve_kb())

    await state.finish()


@dp.message_handler(text='Техническая поддержка')  # 1 start
async def start_support(message: types.Message):
    user_name = message.from_user.first_name
    if message.chat.type == 'private':
        await message.answer(f'{user_name}, Вы зашли в чат с технической поддержкой. Какой у вас вопрос?',
                             reply_markup=remove_cb)
        await SupportStateGroup.text.set()


@dp.message_handler(
    content_types=['text', 'audio', 'photo', 'document', 'voice', 'sticker', 'video', 'location', 'animation'])
async def zero_alarm(message: types.Message):
    if message.chat.type == 'private':
        if message.text == 'Закончить чат с технической поддержкой':
            await message.answer(text='Спасибо за обращение', reply_markup=get_start_approve_kb())
        message_text = message.text
        if message_text not in BUTTON:
            await message.answer('Бот работает только с кнопками')


@dp.message_handler(content_types=['text', 'photo', 'document'], state=SupportStateGroup.text)  # 2 text
async def support(message: types.Message, state: FSMContext):
    if message.text not in BUTTON and message.chat.type == 'private':
        async with state.proxy() as data:
            data['text'] = message.text
        user_id = message.from_user.id
        a.append(user_id)
        full_name = message.from_user.full_name
        button = [
            types.InlineKeyboardButton(text=f'Ответить', callback_data='answer'),
            types.InlineKeyboardButton(text=f'Завершить чат с пользователем', callback_data='end_chat')
        ]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*button)
        if message.from_user.id == admin_id and message.chat.type == 'private':
            await message.answer('Ваш ответ отправлен')
        else:
            await bot.send_message(chat_id=admin_id, text=f'Сообщение от `{user_id}`: {full_name}',
                                   parse_mode=types.ParseMode.MARKDOWN_V2)
            await bot.copy_message(chat_id=admin_id, from_chat_id=message.from_user.id,
                                   message_id=message.message_id, reply_markup=keyboard)
            # await message.answer('Ваш вопрос отправлен, ожидайте ответа')
    else:
        await state.finish()
        await message.answer(text='Спасибо за обращение.', reply_markup=get_start_approve_kb())


@dp.callback_query_handler(text='answer')  # 3
async def answer_callback(callback: types.CallbackQuery, state:FSMContext) -> None:
    await callback.message.edit_reply_markup()
    await bot.send_message(chat_id=admin_id, text='Введите ответ:')
    await AnswerStatesGroup.text.set()


@dp.callback_query_handler(text='end_chat')
async def end_chat(callback: types.CallbackQuery, state:FSMContext):
    for b in a:
        await callback.message.edit_reply_markup()
        await bot.send_message(chat_id=b, text='Админ завершил чат. Для продолжения работы с ботом жмите /start')
    await bot.send_message(chat_id=admin_id, text='Вы завершили чат с пользователем')
    a.pop()


@dp.message_handler(content_types=['text', 'photo', 'document'], state=AnswerStatesGroup.text)
async def answer_callback_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text
    button = [
        types.KeyboardButton(text='Закончить чат с технической поддержкой')
    ]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                         input_field_placeholder='Ожидайте ответа администратора')
    keyboard.add(*button)
    await message.answer('Ответ отправлен')
    for b in a:
        await bot.copy_message(chat_id=b, from_chat_id=message.from_user.id,
                           message_id=message.message_id, reply_markup=keyboard)
    a.pop()
    await state.finish()


@dp.message_handler(text='Закончить чат с технической поддержкой')
async def cmd_cancel(message: types.Message) -> None:
    if message.chat.type == 'private':
        await message.answer(text='Спасибо за обращение', reply_markup=get_start_approve_kb())


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           skip_updates=True,
                           on_startup=on_startup)
