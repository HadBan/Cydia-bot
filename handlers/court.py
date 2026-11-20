import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards.menus import (
    main_menu, court_types_menu, roles_menu, duration_menu, hearing_control_menu
)
from handlers.messages import active_courts, court_settings, case_history
from handlers.states import CourtFlow
from services.ai import ask_judge_for_verdict, ask_judge_for_protest

router = Router()

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
    # Теперь мы храним ID вместо строк, чтобы точно знать, кто есть кто
    court_settings[chat_id] = {
        "type": court_type, 
        "plaintiff_id": None, "plaintiff_name": None,
        "defendant_id": None, "defendant_name": None,
        "judge": "ИИ-Судья", "duration": 10
    }
    case_history[chat_id] = []
    early_termination_votes[chat_id] = set()
    
    await callback.message.edit_text(
        f"🏛 Тип: {court_type.upper()}\nНазначьте участников процесса:",
        reply_markup=roles_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "set_judge")
async def set_judge(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    court_settings[chat_id]["judge"] = "ИИ-Судья"
    await callback.message.edit_text("👨‍⚖️ Судья: ИИ-Судья назначен.", reply_markup=roles_menu())
    await callback.answer()

@router.callback_query(F.data == "set_plaintiff")
async def set_plaintiff(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CourtFlow.waiting_plaintiff)
    await callback.message.edit_text("👤 **Истец, отправьте любое сообщение в чат** (например, «Я истец»), чтобы бот вас запомнил:")
    await callback.answer()

@router.callback_query(F.data == "set_defendant")
async def set_defendant(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CourtFlow.waiting_defendant)
    await callback.message.edit_text("👤 **Ответчик, отправьте любое сообщение в чат** (например, «Я ответчик»), чтобы бот вас запомнил:")
    await callback.answer()

@router.message(CourtFlow.waiting_plaintiff)
async def process_plaintiff(message: Message, state: FSMContext):
    chat_id = message.chat.id
    if chat_id in court_settings:
        court_settings[chat_id]["plaintiff_id"] = message.from_user.id
        court_settings[chat_id]["plaintiff_name"] = message.from_user.full_name
    await state.clear()
    await message.answer(f"✅ Истец назначен: {message.from_user.full_name}", reply_markup=roles_menu())

@router.message(CourtFlow.waiting_defendant)
async def process_defendant(message: Message, state: FSMContext):
    chat_id = message.chat.id
    if chat_id in court_settings:
        court_settings[chat_id]["defendant_id"] = message.from_user.id
        court_settings[chat_id]["defendant_name"] = message.from_user.full_name
    await state.clear()
    await message.answer(f"✅ Ответчик назначен: {message.from_user.full_name}", reply_markup=roles_menu())

@router.callback_query(F.data.startswith("time_"))
async def select_time(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    data = callback.data
    if data == "time_custom":
        await state.set_state(CourtFlow.waiting_custom_time)
        await callback.message.edit_text("✍️ Напишите время заседания в минутах:")
    else:
        court_settings[chat_id]["duration"] = int(data.split("_")[1])
        await start_actual_hearing(callback.message, chat_id)
    await callback.answer()

@router.message(CourtFlow.waiting_custom_time)
async def process_custom_time(message: Message, state: FSMContext):
    try:
        minutes = int(message.text.strip())
        if minutes <= 0: raise ValueError
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
    if not court_settings.get(chat_id, {}).get("plaintiff_id") or not court_settings.get(chat_id, {}).get("defendant_id"):
        await callback.answer("⚠️ Сначала назначьте истца и ответчика!", show_alert=True)
        return
    await callback.message.edit_text("⏱ Выберите время заседания:", reply_markup=duration_menu())
    await callback.answer()

async def start_actual_hearing(msg_or_cb, chat_id: int, is_message: bool = False):
    active_courts[chat_id] = True
    settings = court_settings.get(chat_id, {})
    
    text = (
        f"🏛 **Судебное заседание объявлено открытым.**\n"
        f"Судья: ИИ\n"
        f"Истец: {settings.get('plaintiff_name')}\n"
        f"Ответчик: {settings.get('defendant_name')}\n\n"
        f"Участники могут пользоваться кнопками. Бот реагирует только на действия тех, кому они предназначены."
    )
    
    if is_message:
        await msg_or_cb.answer(text, reply_markup=hearing_control_menu())
    else:
        await msg_or_cb.edit_text(text, reply_markup=hearing_control_menu())

    if chat_id in court_tasks and not court_tasks[chat_id].done():
        court_tasks[chat_id].cancel()
    court_tasks[chat_id] = asyncio.create_task(court_timer(chat_id, settings.get("duration", 10)))

async def court_timer(chat_id: int, minutes: int):
    try:
        await asyncio.sleep(minutes * 60)
        if active_courts.get(chat_id):
            active_courts[chat_id] = False
            history_text = "\n".join(case_history.get(chat_id, []))
            settings = court_settings.get(chat_id, {})
            verdict = await ask_judge_for_verdict(
                plaintiff=settings.get('plaintiff_name', 'Истец'), 
                defendant=settings.get('defendant_name', 'Ответчик'),
                court_type=settings.get('type'), history=history_text, reason="Время истекло."
            )
            from main import bot
            await bot.send_message(chat_id, "⏰ **Время истекло. Суд удалился.**\n\n" + verdict, parse_mode=None)
    except asyncio.CancelledError:
        pass

# --- ПРОВЕРКА ПРАВ ДЛЯ КНОПОК ---

@router.callback_query(F.data == "action_protest")
async def handle_protest(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    settings = court_settings.get(chat_id, {})
    
    # Проверяем, что нажал именно ответчик
    if user_id != settings.get("defendant_id"):
        await callback.answer("⛔ Протест может заявить только назначенный Ответчик!", show_alert=True)
        return

    await callback.answer("Составляем протест...")
    await callback.message.answer(f"⚖️ Ответчик {callback.from_user.full_name} заявляет протест...")
    history_text = "\n".join(case_history.get(chat_id, []))
    protest_text = await ask_judge_for_protest(history_text)
    case_history[chat_id].append(f"ПРОТЕСТ ОТВЕТЧИКА: {protest_text}")
    await callback.message.answer(protest_text, parse_mode=None)

@router.callback_query(F.data == "action_early")
async def handle_early(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    settings = court_settings.get(chat_id, {})
    
    # Проверяем, что нажал истец или ответчик
    if user_id not in [settings.get("plaintiff_id"), settings.get("defendant_id")]:
        await callback.answer("⛔ Только Истец или Ответчик могут завершить заседание досрочно!", show_alert=True)
        return

    if chat_id not in early_termination_votes:
        early_termination_votes[chat_id] = set()
    early_termination_votes[chat_id].add(user_id)
    
    if len(early_termination_votes[chat_id]) >= 2:
        if chat_id in court_tasks and not court_tasks[chat_id].done():
            court_tasks[chat_id].cancel()
        await callback.message.answer("🛑 Обе стороны согласились на досрочное завершение. Суд удаляется.")
        active_courts[chat_id] = False
        history_text = "\n".join(case_history.get(chat_id, []))
        verdict = await ask_judge_for_verdict(
            plaintiff=settings.get('plaintiff_name'), defendant=settings.get('defendant_name'),
            court_type=settings.get('type'), history=history_text, reason="Досрочное завершение."
        )
        await callback.message.answer("🔨 **Суд вернулся.**\n\n" + verdict, parse_mode=None)
    else:
        await callback.answer("Ваш голос принят. Ожидаем вторую сторону (1/2).", show_alert=True)

@router.callback_query(F.data == "action_deliberate")
async def handle_deliberation(callback: CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    # Проверка: удаляться может только Судья (в нашем случае ИИ, но нажимать может админ чата)
    # Для простоты пока разрешим всем, но если нужно - добавим проверку на админа чата.
    
    await callback.answer("Суд удаляется...")
    await state.set_state(CourtFlow.in_deliberation)
    
    if chat_id in court_tasks and not court_tasks[chat_id].done():
        court_tasks[chat_id].cancel()
        
    await callback.message.answer("🚪 **Суд удаляется в совещательную комнату.** Ожидайте приговора.")
    await asyncio.sleep(10)
    
    settings = court_settings.get(chat_id, {})
    history_text = "\n".join(case_history.get(chat_id, []))
    verdict = await ask_judge_for_verdict(
        plaintiff=settings.get('plaintiff_name'), defendant=settings.get('defendant_name'),
        court_type=settings.get('type'), history=history_text, reason="Суд удалился."
    )
    active_courts[chat_id] = False
    await state.clear()
    await callback.message.answer("🔨 **Суд вернулся.**\n\n" + verdict, parse_mode=None)

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
