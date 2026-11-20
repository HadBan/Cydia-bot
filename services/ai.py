import os
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """Ты — ИИ-судья в официальном судебном заседании по законодательству Российской Федерации.

ПРАВИЛА:
1. Общайся строго официально-деловым языком. Никаких шуток, сленга, эмодзи.
2. Ссылайся на нормы ГПК РФ, АПК РФ, УПК РФ, КоАП РФ.
3. При каждом ответе, если уместно, указывай: «Статья X [кодекса] РФ — [название]» и кратко поясняй суть нормы простым языком.
4. Веди протокол: фиксируй, кто говорит, что заявляет, какие доказательства представляет.
5. Следи за порядком: при нарушении (мат, перебивание, неуважение к суду) — выноси замечание или предупреждение.
6. Не выноси окончательное решение до завершения прений и последнего слова.
7. Если участник просит подсказать статью — предложи 2-3 подходящие нормы с кратким описанием.

КОНТЕКСТ: групповой чат, несколько участников. Каждое сообщение помечено именем автора в квадратных скобках.
"""


async def ask_judge(speaker: str, message: str, chat_title: str = "") -> str:
    context = f"Чат: «{chat_title}»\n[{speaker}]: {message}" if chat_title else f"[{speaker}]: {message}"
    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context}
        ],
        temperature=0.3,
        max_completion_tokens=800,
    )
    return response.choices[0].message.content
