from aiogram.dispatcher.filters.state import StatesGroup, State


class ApproveStatesGroup(StatesGroup):
    text = State()
    photo = State()


class SupportStateGroup(StatesGroup):
    user_id = State()
    text = State()