import logging
from aiogram import Bot, Dispatcher, executor, types
import sqlite3

API_TOKEN = "PASTE_YOUR_TOKEN_HERE"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT,
    file_name TEXT,
    category TEXT
)''')
conn.commit()

CATEGORIES = [
    "📘 Планы", "📄 Приказы", "📝 Протоколы", "🗂️ Документы",
    "📚 Конспекты", "📖 Книги", "🎓 Аёниятҳо", "📑 Инструкции",
    "📊 Отчёты", "📅 Расписания", "🧾 Другое"
]

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(0, len(CATEGORIES), 2):
        row = CATEGORIES[i:i+2]
        keyboard.add(*[types.KeyboardButton(text) for text in row])
    keyboard.add("🔍 Поиск")
    await message.answer("📂 Главное меню:
Выберите категорию или воспользуйтесь поиском.", reply_markup=keyboard)

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_docs(message: types.Message):
    file_name = message.document.file_name
    file_id = message.document.file_id
    await message.reply("🔤 Введите категорию (или выберите из меню), к которой относится этот документ:")
    dp.current_state(user=message.from_user.id).set_data({"file_id": file_id, "file_name": file_name})

@dp.message_handler(lambda message: message.text in CATEGORIES)
async def categorize_doc(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    data = await state.get_data()
    if not data:
        return await show_docs_by_category(message.text, message)
    file_id = data["file_id"]
    file_name = data["file_name"]
    category = message.text
    cursor.execute("INSERT INTO documents (file_id, file_name, category) VALUES (?, ?, ?)", (file_id, file_name, category))
    conn.commit()
    await message.answer(f"✅ Документ «{file_name}» сохранён в категории {category}.")
    await state.finish()

@dp.message_handler(lambda message: message.text == "🔍 Поиск")
async def prompt_search(message: types.Message):
    await message.answer("🔎 Введите слово или часть названия файла:")

@dp.message_handler()
async def handle_text(message: types.Message):
    query = message.text.strip()
    cursor.execute("SELECT file_name, file_id FROM documents WHERE file_name LIKE ?", ('%' + query + '%',))
    results = cursor.fetchall()
    if results:
        for name, fid in results:
            await message.answer_document(fid, caption=name)
    else:
        await message.answer("❌ Ничего не найдено. Попробуйте другое слово.")

async def show_docs_by_category(category, message):
    cursor.execute("SELECT file_name, file_id FROM documents WHERE category=?", (category,))
    results = cursor.fetchall()
    if results:
        for name, fid in results:
            await message.answer_document(fid, caption=name)
    else:
        await message.answer("⚠️ В этой категории пока нет документов.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)