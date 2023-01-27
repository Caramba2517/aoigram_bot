@dp.message_handler(text='Техническая поддержка')  # 1 start
async def start_support(message: types.Message):
    user_name = message.from_user.first_name
    if message.from_user.id == admin_id:
        await message.answer(text=f'Админ {user_name}, вы зашли в чат с техподдержкой', reply_markup=remove_cb)
    else:
        await message.answer(f'{user_name}, Вы зашли в чат с технической поддержкой. Какой у вас вопрос?',
                             reply_markup=remove_cb)
    await SupportStateGroup.text.set()


@dp.message_handler(
     content_types=['text', 'audio', 'photo', 'document', 'voice', 'sticker', 'video', 'location', 'animation']
 )
 async def zero_alarm(message: types.Message):
     message_text = message.text
     button_text = ['/start', 'О группе', 'Купить подписку', 'Состояние подписки', 'Техническая поддержка']

     if message_text not in button_text:
         await message.answer('Бот работает только с кнопками')
         print(False)
     else:
         print(message_text)
         print(True)


@dp.message_handler(content_types=['text', 'photo', 'document'], state=SupportStateGroup.text)  # 2 text
async def support(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    first_name = message.from_user.first_name
    button = [
        types.InlineKeyboardButton(text=f'Ответить', callback_data='answer')
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*button)
    if message.from_user.id == admin_id:
        await message.answer('Ваш ответ отправлен')
    else:
        await bot.send_message(chat_id=admin_id, text=f'Сообщение от `{user_id}`: {full_name}',
                               parse_mode=types.ParseMode.MARKDOWN_V2)
        await bot.copy_message(chat_id=admin_id, from_chat_id=message.from_user.id,
                               message_id=message.message_id, reply_markup=keyboard)
        await message.answer('Ваш вопрос отправлен, ожидайте ответа')


@dp.callback_query_handler(text='answer')# 3
async def answer_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await bot.send_message(chat_id=admin_id, text='Введите ID пользователя (только цифры, без двоеточия):')

    await AnswerStateGroup.user_id.set()


@dp.message_handler(state=SupportStateGroup.user_id) #3
async def answer_callback_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_id']=message.text
    await message.answer('Введите текст ответа:')

    await AnswerStageGroup.next()


@dp.message_handler(content_types=['text', 'photo', 'document'], state=AnswerStageGroup.text)
async def answer_callback_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text

    await message.answer('Ответ отправлен')
    await bot.copy_message(chat_id=data.get('user_id'), from_chat_id=message.from_user.id,
                           message_id=message.message_id)
    await state.finish()