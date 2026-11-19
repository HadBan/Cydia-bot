from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.menus import main_menu

router = Router()


@router.callback_query(F.data == "open_court")
async def open_court(callback: CallbackQuery):
    await callback.message.answer(
        "🏛 Заседание инициировано. Настройка состава суда будет добавлена на следующем этапе."
    )
    await callback.answer()


@router.callback_query(F.data == "cases")
async def cases(callback: CallbackQuery):
    await callback.message.answer("📁 Реестр дел пуст.")
    await callback.answer()


@router.callback_query(F.data == "regulations")
async def regulations(callback: CallbackQuery):
    await callback.message.answer(
        "📖 Процессуальный регламент:\n"
        "1. Открытие заседания\n"
        "2. Изложение иска\n"
        "3. Возражения ответчика\n"
        "4. Исследование доказательств\n"
        "5. Прения сторон\n"
        "6. Последнее слово\n"
        "7. Вынесение решения\n"
        "8. Апелляция"
    )
    await callback.answer()
