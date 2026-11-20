import os
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """Ты — ИИ-судья в официальном судебном заседании по законодательству РФ.
Веди протокол, следи за порядком, ссылайся на кодексы (ГПК, УПК, АПК, КоАП)."""

VERDICT_PROMPT = """Ты — ИИ-судья. Ты вернулся из совещательной комнаты.
Вынеси окончательный, официальный приговор (решение) по делу на основе истории прений.
Структура: Вводная, Описательная, Мотивировочная, Резолютивная части."""

PROTEST_PROMPT = """Ты — ИИ-адвокат. Составь официальный и краткий протест (возражение) на иск истца от лица ответчика.
Основывайся на законодательстве РФ и истории прений."""

async def ask_judge(history: str, chat_title: str = "") -> str:
    try:
        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Чат: «{chat_title}»\nИстория:\n{history}"}
            ],
            temperature=0.3,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Ошибка ИИ: {str(e)}"

async def ask_judge_for_verdict(plaintiff: str, defendant: str, court_type: str, history: str, reason: str = "timeout") -> str:
    prompt = f"Дело типа {court_type.upper()}. Истец: {plaintiff}. Ответчик: {defendant}.\nПричина завершения: {reason}\nИстория:\n{history}\nВынеси окончательный приговор."
    try:
        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": VERDICT_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Ошибка приговора: {str(e)}"

async def ask_judge_for_protest(history: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": PROTEST_PROMPT},
                {"role": "user", "content": f"История прений:\n{history}\nСоставь краткий протест."}
            ],
            temperature=0.4,
            max_tokens=600,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Ошибка протеста: {str(e)}"
