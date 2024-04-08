from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from languages import buttons


def connect_wallet_kb(url: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=buttons['open_wallet'], url=url)
    kb.adjust(1)
    return kb.as_markup()


def check_subs_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=buttons['check_subs'], callback_data='check_subs')
    kb.adjust(1)
    return kb.as_markup()


def main_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=buttons['buy_ts'], callback_data='buy_ts')
    kb.button(text=buttons['sell_ts'], callback_data='sell_ts')
    kb.button(text=buttons['stake_sts'], callback_data='stake_sts')
    kb.button(text=buttons['unstake_sts'], callback_data='unstake_sts')
    kb.button(text=buttons['refresh'], callback_data='start')
    kb.adjust(1, 1, 1, 1, 1)
    return kb.as_markup()


def open_wallet_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=buttons['open_wallet'], url='https://app.tonkeeper.com/ton-connect')
    kb.adjust(1)
    return kb.as_markup()


def back_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=buttons['back'], callback_data='start')
    kb.adjust(1)
    return kb.as_markup()


def yes_no_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=buttons['yes'], callback_data='yes')
    kb.button(text=buttons['no'], callback_data='no')
    kb.adjust(2)
    return kb.as_markup()
