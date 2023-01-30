from aiogram.dispatcher.filters.state import StatesGroup, State


class AdminApprove(StatesGroup):
    user_id = State()


class AnswerStatesGroup(StatesGroup):
    text = State()


class ApproveStatesGroup(StatesGroup):
    info = State()


class CurrentApprove(StatesGroup):
    info = State()


class SupportStateGroup(StatesGroup):
    text = State()
