from aiogram import Router, F
from aiogram.types import Message

from services.ai import ask_judge
from state import active_courts, court_settings

router = Router()


@router.message(F.text)
async def handle_message(message: Message):
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

    if not (is_active or mentioned or is_reply_to_bot):
        return
        
    # Проверяем, кто судья. Если человек - бот не ведет заседание сам, а просто молчит или отвечает по упоминанию.
    settings = court_settings.get(chat_id, {})
    judge_type = settings.get("judge")
    
    if judge_type != "AI" and not (mentioned or is_reply_to_bot):
        return

    speaker = message.from_user.full_name
    
    await message.chat.do("typing")
    response = await ask_judge(speaker, message.text, chat_title=message.chat.title or "")
    await message.reply(response)
