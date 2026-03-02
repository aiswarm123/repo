from aiogram.fsm.state import State, StatesGroup


class AdminReply(StatesGroup):
    waiting_reply = State()


class AdminBroadcast(StatesGroup):
    waiting_text = State()
