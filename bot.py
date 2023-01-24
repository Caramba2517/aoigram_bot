from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from keys import TOKEN
from database import sqlite as db
from keyboards.keyboard import get_orders_ikb, order_cb, get_start_kb, get_cancel_kb, remove_cb
from database.models import OrderStatesGroup

bot = Bot(TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def on_startup(_):
    await db.db_connect()
    print('Подключение к БД выполнено успешно.')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    name = message.chat.first_name
    await bot.send_message(chat_id=message.from_user.id,
                           text=f'Привет, {name}!',
                           reply_markup=get_start_kb())


@dp.message_handler(commands=['cancel'], state='*')
async def cancel(message: types.Message, state: FSMContext):
    name = message.chat.first_name
    if state is None:
        return

    await state.finish()
    await message.answer(f'{name}, действие отменено!',
                         reply_markup=get_start_kb())


@dp.message_handler(commands=['orders'])
async def orders(message: types.Message):
    name = message.chat.first_name
    await message.answer(f'{name}, что бы хотел сделать?',
                         reply_markup=get_orders_ikb())


@dp.callback_query_handler(text='get_all_orders')
async def cb_get_all_products(callback: types.CallbackQuery):
    order = await db.get_all_orders(callback)
    if not order:
        await callback.message.edit_text('Заказов в ожидании нет.')
        return await callback.answer()
    await callback.message.edit_text(order)


@dp.callback_query_handler(text='add_new_order')
async def cb_add_new_product(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text('Напиши че хочешь, это тест:')
    await OrderStatesGroup.name.set()


@dp.message_handler(state=OrderStatesGroup.name)
async def handle_name(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer('В какой стране ты проживаешь?',
                         reply_markup=get_cancel_kb())
    await OrderStatesGroup.next()


@dp.message_handler(state=OrderStatesGroup.country)
async def handle_country(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['country'] = message.text
    await message.answer('Отправь номер телефона',
                         reply_markup=get_cancel_kb())
    await OrderStatesGroup.country.set()
    await OrderStatesGroup.next()


@dp.message_handler(state=OrderStatesGroup.phone)
async def handle_phone(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['phone'] = message.text

    await db.create_new_order(message, state)
    await message.answer('Заказ успешно сохранен.',
                         reply_markup=get_orders_ikb())
    await OrderStatesGroup.phone.set()
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           skip_updates=True,
                           on_startup=on_startup)
