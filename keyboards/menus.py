from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏛 Открыть судебное заседание", callback_data="open_court"))
    builder.row(InlineKeyboardButton(text="📁 Реестр дел", callback_data="cases"))
    builder.row(InlineKeyboardButton(text="📖 Процессуальный регламент", callback_data="regulations"))
    return builder.as_markup()

def court_types_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⚖️ Арбитражное (АПК РФ)", callback_data="type_arbitration"))
    builder.row(InlineKeyboardButton(text="🚔 Административное (КоАП РФ)", callback_data="type_admin"))
    builder.row(InlineKeyboardButton(text="🔒 Уголовное (УПК РФ)", callback_data="type_criminal"))
    builder.row(InlineKeyboardButton(text="👨‍👩‍👧 Гражданское (ГПК РФ)", callback_data="type_civil"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"))
    return builder.as_markup()

def roles_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Назначить Истца", callback_data="set_plaintiff"))
    builder.row(InlineKeyboardButton(text="👤 Назначить Ответчика", callback_data="set_defendant"))
    builder.row(InlineKeyboardButton(text="▶️ Начать заседание", callback_data="start_hearing"))
    builder.row(InlineKeyboardButton(text="❌ Отменить", callback_data="back_to_main"))
    return builder.as_markup()

def duration_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏱ 5 минут", callback_data="time_5"))
    builder.row(InlineKeyboardButton(text="⏱ 10 минут", callback_data="time_10"))
    builder.row(InlineKeyboardButton(text="⏱ 15 минут", callback_data="time_15"))
    builder.row(InlineKeyboardButton(text="✍️ Свое время", callback_data="time_custom"))
    return builder.as_markup()

def hearing_control_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Завершить заседание", callback_data="back_to_main"))
    return builder.as_markup()

def defendant_kb() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="⚖️ ПРОТЕСТ"), KeyboardButton(text="🛑 ДОСРОЧНО")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def plaintiff_kb() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="🛑 ДОСРОЧНО")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def judge_kb() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="🚪 Удалиться в совещательную комнату")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
