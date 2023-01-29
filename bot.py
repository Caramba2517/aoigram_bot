import asyncio
from datetime import datetime, timedelta

from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from keys import TOKEN, BUTTON
from database import sqlite as db
from keyboards.keyboard import order_cb, get_start_kb, remove_cb, get_start_approve_kb
from database import sqlite_approve as db_a
from database.models import ApproveStatesGroup, SupportStateGroup, AnswerStatesGroup, AdminApprove, CurrentApprove

bot = Bot(TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
admin_id = 1966767
chat_id = -1001844904366
channel_link = 'https://kor.ill.in.ua/m/610x385/2722809.jpg'
welcome_photo_url = 'https://kor.ill.in.ua/m/610x385/2722809.jpg'
admin_approve_photo_url = 'https://koshka.top/uploads/posts/2021-12/1640248531_1-koshka-top-p-kot-ulibaetsya-1.jpg'
group_information_photo_url = 'https://kor.ill.in.ua/m/610x385/2722809.jpg'
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
                                 
                                 f'\nУ тебя есть действуюшая подписка. Подробнее по кнопке: "Состояние подписки"',
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
        await message.answer(text=f'Доступ в премиум-группу стоит 149$/год\n'
                                  f'\nПодписка действует до конца года и на сегодняшний день составляет {n} USDT.\n'
                                  f'\nПожалуйста, не забудь сделать скриншот оплаты. Он потребуется при подтверждении '
                                  f'платежа!',
                             reply_markup=keyboard)


@dp.callback_query_handler(text='payment_check')
async def payment_check(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup()
    user = db.status_callback(callback)
    if not user and callback.message.chat.type == 'private':
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
    await callback.message.answer('Отправь информацию об оплате(ссылка на подтверждение или скриншот) :',
                                  reply_markup=remove_cb)
    await ApproveStatesGroup.info.set()


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
    await message.answer('Cпасибо за оформление подписки, ожидайте подтверждение от администатора!',
                         reply_markup=get_start_approve_kb())

    await state.finish()


# ТУТ ЛОГИКА АПРУВА АДМИНОМ!!!!


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


@dp.callback_query_handler(text='approve')
async def check_approve_id(callback: types.CallbackQuery):
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
    if user:
        await bot.send_photo(
            photo=welcome_photo,
            chat_id=data.get('user_id'),
            caption=f'Администратор одобрил ваш запрос!\n Ваша подписка продлена!',
            reply_markup=get_start_approve_kb())

        await db.change_current_status_approve(message, user_id)
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
        types.InlineKeyboardButton(text='Начать проверку', callback_data='current_payment_selled')
    ]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*buttons)
    await callback.message.answer(text='Чтобы подтвердить платёж следуй инструкциям бота', reply_markup=keyboard)


@dp.callback_query_handler(text='current_payment_selled')
async def cur_add_approve_status(callback: types.CallbackQuery) -> None:
    await callback.message.edit_reply_markup()
    await callback.message.answer('Отправь информацию об оплате (ccылку или скриншот):', reply_markup=remove_cb)
    await ApproveStatesGroup.info.set()


@dp.message_handler(content_types=['text', 'photo'], state=CurrentApprove.info)
async def cur_handle_photo(message: types.Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    button = [
        types.InlineKeyboardButton(text='Подтвердить данные', callback_data='approve')
    ]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*button)
    await db.change_сurrent_status_to_wa(message)
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id
    await db_a.create_new_approve(message, state)
    await bot.send_message(
        chat_id=admin_id,
        text=f'Пользователь `{user_id}` ({user_name}) прислал данные для подтверждения ПРОДЛЕНИЯ ПОДПИСКИ:',
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )
    await bot.send_photo(chat_id=admin_id, caption=data.get('text'), photo=data.get('photo'), reply_markup=keyboard)
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
        full_name = message.from_user.full_name
        button = [
            types.InlineKeyboardButton(text=f'Ответить', callback_data='answer')
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
        await message.answer(text='Спасибо за обращение', reply_markup=get_start_approve_kb())


@dp.callback_query_handler(text='answer')  # 3
async def answer_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await bot.send_message(chat_id=admin_id, text='Введите ID пользователя (только цифры, без двоеточия):')

    await AnswerStatesGroup.user_id.set()


@dp.message_handler(state=AnswerStatesGroup.user_id)  # 3
async def answer_callback_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_id'] = message.text
    await message.answer('Введите текст ответа:')

    await AnswerStatesGroup.next()


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
    admin_name = message.from_user.first_name
    await message.answer('Ответ отправлен')
    # await bot.send_message(chat_id=data.get('user_id'), text=f'Админ {admin_name} вам ответил:')
    await bot.copy_message(chat_id=data.get('user_id'), from_chat_id=message.from_user.id,
                           message_id=message.message_id, reply_markup=keyboard)
    await state.finish()


@dp.message_handler(text='Закончить чат с технической поддержкой')
async def cmd_cancel(message: types.Message) -> None:
    if message.chat.type == 'private':
        await message.answer(text='Спасибо за обращение', reply_markup=get_start_approve_kb())


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           skip_updates=True,
                           on_startup=on_startup)
