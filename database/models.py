from aiogram.dispatcher.filters.state import StatesGroup, State


class ApproveStatesGroup(StatesGroup):
    info = State()



class SupportStateGroup(StatesGroup):
    text = State()


class AnswerStatesGroup(StatesGroup):
    user_id = State()
    text = State()


class AdminApprove(StatesGroup):
    user_id = State()


class CurrentApprove(StatesGroup):
    info = State()

