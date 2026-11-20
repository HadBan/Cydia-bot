from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from services.ai import ask_judge
from handlers.states import CourtFlow

router = Router()
active_courts: dict[int, bool] = {}
court_settings: dict[int, dict] = {}
case_history: dict[int, list[str]] = {}

@router.message(F.text)
async def handle_message(message: Message, state: FSMContext):
    if message.text.startswith("/"):
        return

    current_state = await state.get_state()
    if current_state == CourtFlow.in_deliberation:
        return

    chat_id = message.chat.id
    is_active = active_courts.get(chat_id, False)
    
    bot_username = getattr(message.bot, "my_username", "")
    mentioned = message.text and f"@{bot_username}" in message.text
    is_reply_to_bot = (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == message.bot.id
    )

    # Игнорируем системные кнопки
    if message.text in ["⚖️ ПРОТЕСТ", "🛑 ДОСРОЧНО", "🚪 Удалиться в совещательную комнату"]:
        return

    if not (is_active or mentioned or is_reply_to_bot):
        return

    speaker = message.from_user.full_name
    text = message.text
    
    if chat_id not in case_history:
        case_history[chat_id] = []
    case_history[chat_id].append(f"{speaker}: {text}")

    await message.chat.do("typing")
    
    context_history = "\n".join(case_history[chat_id][-15:])
    response = await ask_judge(context_history, chat_title=message.chat.title or "")
    
    try:
        await message.reply(response, parse_mode=None)
    except Exception as e:
        await message.reply(f"Ошибка отправки: {e}")
