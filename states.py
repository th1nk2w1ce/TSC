from aiogram.fsm.state import StatesGroup, State


class BuyTSStates(StatesGroup):
    AmountInput = State()
    Approve = State()


class SellTSStates(StatesGroup):
    AmountInput = State()
    Approve = State()


class StakeSTSStates(StatesGroup):
    AmountInput = State()
    Approve = State()


class UnstakeSTSStates(StatesGroup):
    AmountInput = State()
    Approve = State()
