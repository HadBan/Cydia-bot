import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from keyboards.menus import (
    main_menu, court_types_menu, roles_menu, duration_menu, 
    hearing_control_menu, defendant_kb, plaintiff_kb, judge_kb
)
from handlers.messages import active_courts, court_settings, case_history
from handlers.states import CourtFlow
from services.ai import ask_judge_for_verdict, ask_judge_for_protest

router = Router()

# Словари для таймеров и досрочных завершений
court_tasks: dict[int, asyncio.Task] = {}
early_termination_votes: dict[int, set] = {}

@router.callback_query(F.data == "open_court")
async def open_court(callback: CallbackQuery):
    await callback.message.edit_text("🏛 Выберите тип судопроизводства:", reply_markup=court_types_menu())
    await callback.answer()

@router.callback_query(F.data.startswith("type_"))
async def select_type(callback: CallbackQuery):
    court_type = callback.data.split("_")[1]
    chat_id = callback.message.chat.id
    court_settings[chat_id] = {"type": court_type, "plaintiff": None, "defendant": None, "duration": 10}
    case_history[chat_id] = []
    early_termination_votes[chat_id] = set()
    
    await callback.message.edit_text(
        f"🏛 Тип: {court_type.upper()}\nНазначьте участников процесса:",
        reply_markup=roles_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "set_plaintiff")
async def set_plaintiff(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CourtFlow.waiting_plaintiff)
    await callback.message.edit_text("👤 Введите @username или имя истца:")
    await callback.answer()

@router.callback_query(F.data == "set_defendant")
async def set_defendant(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CourtFlow.waiting_defendant)
    await callback.message.edit_text("👤 Введите @username или имя ответчика:")
    await callback.answer()

@router.message(CourtFlow.waiting_plaintiff)
async def process_plaintiff(message: Message, state: FSMContext):
    chat_id = message.chat.id
    if chat_id in court_settings:
        court_settings[chat_id]["plaintiff"] = message.text
    await state.clear()
    await message.answer(f"✅ Истец назначен: {message.text}", reply_markup=roles_menu())

@router.message(CourtFlow.waiting_defendant)
async def process_defendant(message: Message, state: FSMContext):
    chat_id = message.chat.id
    if chat_id in court_settings:
        court_settings[chat_id]["defendant"] = message.text
    await state.clear()
    await message.answer(f"✅ Ответчик назначен: {message.text}", reply_markup=roles_menu())

# --- ВЫБОР ВРЕМЕНИ ---
@router.callback_query(F.data.startswith("time_"))
async def select_time(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    data = callback.data
    
    if data == "time_custom":
        await state.set_state(CourtFlow.waiting_custom_time)
        await callback.message.edit_text("✍️ Напишите время заседания в минутах (например, 3):")
    else:
        minutes = int(data.split("_")[1])
        court_settings[chat_id]["duration"] = minutes
        await start_actual_hearing(callback.message, chat_id)
    
    await callback.answer()

@router.message(CourtFlow.waiting_custom_time)
async def process_custom_time(message: Message, state: FSMContext):
    try:
        minutes = int(message.text.strip())
        if minutes <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите корректное число минут.")
        return
        
    chat_id = message.chat.id
    court_settings[chat_id]["duration"] = minutes
    await state.clear()
    await start_actual_hearing(message, chat_id, is_message=True)

@router.callback_query(F.data == "start_hearing")
async def choose_duration(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    if not court_settings.get(chat_id, {}).get("plaintiff") or not court_settings.get(chat_id, {}).get("defendant"):
        await callback.answer("⚠️ Сначала назначьте истца и ответчика!", show_alert=True)
        return
        
    await callback.message.edit_text("⏱ Выберите время длительности заседания:", reply_markup=duration_menu())
    await callback.answer()

# --- НЕПОСРЕДСТВЕННО ЗАПУСК ---
async def start_actual_hearing(msg_or_cb, chat_id: int, is_message: bool = False):
    active_courts[chat_id] = True
    settings = court_settings.get(chat_id, {})
    minutes = settings.get("duration", 10)
    
    text = (
        f"🏛 **Судебное заседание объявляется открытым.**\n"
        f"Тип: {settings.get('type', 'не указан').upper()}\n"
        f"Истец: {settings.get('plaintiff')}\n"
        f"Ответчик: {settings.get('defendant')}\n"
        f"Регламент времени: {minutes} мин.\n\n"
        f"Слово предоставляется истцу. Участники получили кнопки управления."
    )
    
    if is_message:
        await msg_or_cb.answer(text, reply_markup=hearing_control_menu())
    else:
        await msg_or_cb.edit_text(text, reply_markup=hearing_control_menu())
        
    # Выдаем клавиатуры
    await msg_or_cb.answer("Панель Истца:", reply_markup=plaintiff_kb())
    await msg_or_cb.answer("Панель Ответчика:", reply_markup=defendant_kb())
    await msg_or_cb.answer("Панель Судьи:", reply_markup=judge_kb())

    # Запуск таймера
    if chat_id in court_tasks and not court_tasks[chat_id].done():
        court_tasks[chat_id].cancel()
        
    court_tasks[chat_id] = asyncio.create_task(court_timer(chat_id, minutes))

async def court_timer(chat_id: int, minutes: int):
    try:
        await asyncio.sleep(minutes * 60)
        if active_courts.get(chat_id):
            await finish_hearing(chat_id, reason="Истекло время заседания.")
    except asyncio.CancelledError:
        pass

# --- ЗАВЕРШЕНИЕ ---
async def finish_hearing(chat_id: int, reason: str):
    active_courts[chat_id] = False
    early_termination_votes[chat_id] = set()
    settings = court_settings.get(chat_id, {})
    history_text = "\n".join(case_history.get(chat_id, []))
    
    # Отправляем сообщение в чат (используем бота через dispatcher, но проще передать его из хендлера)
    # Для простоты мы будем использовать callback/message объект в хендлерах, 
    # а тут просто сгенерируем текст и сохраним его
    # В реальном коде лучше использовать bot.send_message, но у нас нет прямого доступа к bot.
    return reason # Заглушка, логика перенесена в хендлеры

# --- ПРОТЕСТ ---
@router.message(F.text == "⚖️ ПРОТЕСТ")
async def handle_protest(message: Message):
    chat_id = message.chat.id
    if chat_id not in case_history:
        case_history[chat_id] = []
        
    await message.answer("⚖️ Ответчик заявляет протест. ИИ составляет возражение...")
    history_text = "\n".join(case_history[chat_id])
    protest_text = await ask_judge_for_protest(history_text)
    
    case_history[chat_id].append(f"ПРОТЕСТ ОТВЕТЧИКА: {protest_text}")
    await message.answer(protest_text, parse_mode=None)

# --- ДОСРОЧНОЕ ЗАВЕРШЕНИЕ (ДОСРОЧНО) ---
@router.message(F.text == "🛑 ДОСРОЧНО")
async def handle_early_termination(message: Message, state: FSMContext):
    chat_id = message.chat.id
    user_id = message.from_user.id
    settings = court_settings.get(chat_id, {})
    
    if chat_id not in early_termination_votes:
        early_termination_votes[chat_id] = set()
        
    early_termination_votes[chat_id].add(user_id)
    
    # В реальной жизни нужно проверить, что нажал именно истец или ответчик. 
    # Здесь просто считаем два уникальных нажатия.
    if len(early_termination_votes[chat_id]) >= 2:
        if chat_id in court_tasks and not court_tasks[chat_id].done():
            court_tasks[chat_id].cancel()
            
        await message.answer("🛑 Обе стороны согласились на досрочное завершение. Суд удаляется.")
        
        await state.set_state(CourtFlow.in_deliberation)
        await asyncio.sleep(3) # Небольшая пауза
        
        history_text = "\n".join(case_history.get(chat_id, []))
        verdict = await ask_judge_for_verdict(
            plaintiff=settings.get('plaintiff', 'Истец'),
            defendant=settings.get('defendant', 'Ответчик'),
            court_type=settings.get('type', 'civil'),
            history=history_text,
            reason="Досрочное завершение по согласию сторон."
        )
        
        active_courts[chat_id] = False
        early_termination_votes[chat_id] = set()
        await state.clear()
        
        await message.answer("🔨 **Суд вернулся.**", reply_markup=ReplyKeyboardRemove())
        await message.answer(verdict, parse_mode=None)
    else:
        await message.answer(f"🛑 Ваш голос за досрочное завершение принят. Ожидаем вторую сторону. (1/2)")

# --- УДАЛЕНИЕ СУДЬИ ---
@router.message(F.text == "🚪 Удалиться в совещательную комнату")
async def handle_deliberation(message: Message, state: FSMContext):
    chat_id = message.chat.id
    await state.set_state(CourtFlow.in_deliberation)
    
    # Отменяем таймер, если он был
    if chat_id in court_tasks and not court_tasks[chat_id].done():
        court_tasks[chat_id].cancel()
        
    await message.answer(
        "🚪 **Суд удаляется в совещательную комнату.**\nОжидайте приговора.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    await asyncio.sleep(10) # Для теста сделаем 10 секунд (можешь поменять на 60)
    
    settings = court_settings.get(chat_id, {})
    history_text = "\n".join(case_history.get(chat_id, []))
    
    await message.answer("🔨 **Суд вернулся из совещательной комнаты.**")
    
    verdict = await ask_judge_for_verdict(
        plaintiff=settings.get('plaintiff', 'Истец'),
        defendant=settings.get('defendant', 'Ответчик'),
        court_type=settings.get('type', 'civil'),
        history=history_text,
        reason="Суд удалился для вынесения приговора."
    )
    
    active_courts[chat_id] = False
    await state.clear()
    await message.answer(verdict, parse_mode=None)

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    if chat_id in court_tasks and not court_tasks[chat_id].done():
        court_tasks[chat_id].cancel()
    active_courts[chat_id] = False
    await state.clear()
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu())
    await callback.answer()

@router.callback_query(F.data == "cases")
async def cases(callback: CallbackQuery):
    await callback.message.answer("📁 Реестр дел пуст.")
    await callback.answer()

@router.callback_query(F.data == "regulations")
async def regulations(callback: CallbackQuery):
    await callback.message.answer("📖 Регламент: Открытие -> Иск -> Возражения -> Прения -> Приговор.")
    await callback.answer()
