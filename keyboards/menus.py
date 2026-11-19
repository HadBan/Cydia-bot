from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏛 Открыть судебное заседание", callback_data="open_court"))
    builder.row(InlineKeyboardButton(text="📁 Реестр дел", callback_data="cases"))
    builder.row(InlineKeyboardButton(text="📖 Процессуальный регламент", callback_data="regulations"))
    return builder.as_markup()
