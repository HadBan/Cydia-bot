from aiogram.fsm.state import State, StatesGroup

class CourtFlow(StatesGroup):
    waiting_plaintiff = State()
    waiting_defendant = State()
    waiting_custom_time = State()
    in_deliberation = State()
