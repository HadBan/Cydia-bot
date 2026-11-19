from aiogram.types import Message, ChatMemberAdministrator, ChatMemberOwner
from aiogram.enums import ChatType


async def is_admin(message: Message) -> bool:
    if message.chat.type == ChatType.PRIVATE:
        return True
    try:
        member = await message.chat.get_member(message.from_user.id)
        return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))
    except Exception:
        return False
