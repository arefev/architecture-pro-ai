# bot_tg.py
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import os

# импортируем rag-бот
from rag_chain import rag_answer

load_dotenv()

# включаем логирование
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message()
async def handle_message(message: types.Message):
    user_query = message.text.strip()

    await message.answer("🔍 Ищу ответ в базе знаний...")

    try:
        result = rag_answer(user_query)  # запрос в RAG

        answer_text = result["answer"]

        # красивый формат
        response = (
            f"🤖 <b>Ответ RAG-бота:</b>\n\n"
            f"{answer_text}\n\n"
            f"<b>Источники:</b>\n"
        )

        for src in result["sources"]:
            response += f"• {src}\n"

        await message.answer(response, parse_mode=ParseMode.HTML)

    except Exception as e:
        logging.exception("Error during RAG processing")
        await message.answer(
            "⚠️ Произошла ошибка при обработке запроса.\nПопробуйте позже."
        )


async def main():
    print("Telegram bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())