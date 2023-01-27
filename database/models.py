from aiogram.dispatcher.filters.state import StatesGroup, State


class ApproveStatesGroup(StatesGroup):
    text = State()
    photo = State()


class SupportStateGroup(StatesGroup):
    text = State()


class AnswerStatesGroup(StatesGroup):
    user_id = State()
    text = State()
