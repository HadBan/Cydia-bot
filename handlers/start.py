from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from keyboards.menus import main_menu
from utils.permissions import is_admin

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Судебная система подключена к чату.\nДля открытия заседания используйте /суд (только администраторы).",
        reply_markup=main_menu()
    )

@router.message(Command("суд"))
async def court_command(message: Message):
    if not await is_admin(message):
        await message.reply("⛔ Открывать заседание может только администратор чата.")
        return
    await message.answer(
        f"🏛 Судебное заседание объявляется открытым в чате «{message.chat.title}».\nВыберите тип судопроизводства:",
        reply_markup=main_menu() 
    )
