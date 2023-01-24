from aiogram.dispatcher.filters.state import StatesGroup, State


class OrderStatesGroup(StatesGroup):
    name = State()
    country = State()
    phone = State()
