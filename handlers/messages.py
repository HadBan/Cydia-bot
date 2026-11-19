from aiogram import Router, F
from aiogram.types import Message

from services.ai import ask_judge

router = Router()

# Глобальные словари для хранения состояния (в памяти)
active_courts: dict[int, bool] = {}
court_settings: dict[int, dict] = {}


@router.message(F.text)
async def handle_message(message: Message):
    # Если это команда — игнорируем (её ловят другие роутеры)
    if message.text.startswith("/"):
        return

    chat_id = message.chat.id
    is_active = active_courts.get(chat_id, False)
    mentioned = message.text and f"@{message.bot.username}" in message.text
    is_reply_to_bot = (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == message.bot.id
    )

    # Если заседание не активно и нет упоминания — игнорируем
    if not (is_active or mentioned or is_reply_to_bot):
        return

    speaker = message.from_user.full_name
    
    # Если заседание активно, все сообщения идут ИИ-судье
    await message.chat.do("typing")
    response = await ask_judge(speaker, message.text, chat_title=message.chat.title or "")
    await message.reply(response)
