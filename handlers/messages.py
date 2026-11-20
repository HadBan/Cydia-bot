from aiogram import Router, F
from aiogram.types import Message
from services.ai import ask_judge

router = Router()
active_courts: dict[int, bool] = {}
court_settings: dict[int, dict] = {}

@router.message(F.text)
async def handle_message(message: Message):
    if message.text.startswith("/"):
        return

    chat_id = message.chat.id
    is_active = active_courts.get(chat_id, False)
    
    # Берем сохраненный username
    bot_username = getattr(message.bot, "my_username", "")
    mentioned = message.text and f"@{bot_username}" in message.text
    
    is_reply_to_bot = (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == message.bot.id
    )

    if not (is_active or mentioned or is_reply_to_bot):
        return

    speaker = message.from_user.full_name
    await message.chat.do("typing")
    
    response = await ask_judge(speaker, message.text, chat_title=message.chat.title or "")
    
    try:
        await message.reply(response, parse_mode=None)
    except Exception as e:
        await message.reply(f"Ошибка отправки: {e}")
