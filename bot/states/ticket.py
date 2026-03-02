from aiogram.fsm.state import State, StatesGroup


class TicketForm(StatesGroup):
    waiting_for_subject = State()
    waiting_for_body = State()
    confirming = State()
