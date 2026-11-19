from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.menus import main_menu, court_types_menu, roles_menu
from state import active_courts, court_settings

router = Router()


class RoleSetup(StatesGroup):
    waiting_plaintiff = State()
    waiting_defendant = State()


@router.callback_query(F.data == "open_court")
async def open_court(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏛 Выберите тип судопроизводства:",
        reply_markup=court_types_menu()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("type_"))
async def select_type(callback: CallbackQuery):
    court_type = callback.data.split("_")[1]
    chat_id = callback.message.chat.id
    court_settings[chat_id] = {"type": court_type, "plaintiff": None, "defendant": None}
    
    await callback.message.edit_text(
        f"🏛 Тип заседания: {court_type.upper()}\n\nНазначьте участников процесса или начните заседание:",
        reply_markup=roles_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "set_plaintiff")
async def set_plaintiff(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RoleSetup.waiting_plaintiff)
    await callback.message.edit_text("👤 Введите @username или имя истца (отправьте сообщение в чат):")
    await callback.answer()


@router.callback_query(F.data == "set_defendant")
async def set_defendant(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RoleSetup.waiting_defendant)
    await callback.message.edit_text("👤 Введите @username или имя ответчика (отправьте сообщение в чат):")
    await callback.answer()


@router.message(RoleSetup.waiting_plaintiff)
async def process_plaintiff(message: Message, state: FSMContext):
    chat_id = message.chat.id
    if chat_id in court_settings:
        court_settings[chat_id]["plaintiff"] = message.text
    
    await state.clear()
    await message.answer(f"✅ Истец назначен: {message.text}", reply_markup=roles_menu())


@router.message(RoleSetup.waiting_defendant)
async def process_defendant(message: Message, state: FSMContext):
    chat_id = message.chat.id
    if chat_id in court_settings:
        court_settings[chat_id]["defendant"] = message.text
        
    await state.clear()
    await message.answer(f"✅ Ответчик назначен: {message.text}", reply_markup=roles_menu())


@router.callback_query(F.data == "start_hearing")
async def start_hearing(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    active_courts[chat_id] = True
    settings = court_settings.get(chat_id, {})
    
    await callback.message.edit_text(
        f"🏛 **Судебное заседание объявляется открытым.**\n"
        f"Тип: {settings.get('type', 'не указан').upper()}\n"
        f"Истец: {settings.get('plaintiff') or 'не назначен'}\n"
        f"Ответчик: {settings.get('defendant') or 'не назначен'}\n\n"
        "Судья (ИИ) приветствует стороны. Слово предоставляется истцу. Теперь пишите сообщения в чат."
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "cases")
async def cases(callback: CallbackQuery):
    await callback.message.answer("📁 Реестр дел пуст.")
    await callback.answer()


@router.callback_query(F.data == "regulations")
async def regulations(callback: CallbackQuery):
    await callback.message.answer(
        "📖 Процессуальный регламент:\n"
        "1. Открытие заседания\n2. Изложение иска\n3. Возражения ответчика\n"
        "4. Исследование доказательств\n5. Прения сторон\n6. Последнее слово\n"
        "7. Вынесение решения\n8. Апелляция"
    )
    await callback.answer()
