import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from config import AppConfig
from processors.document_processor import DocumentProcessor
from processors.gigachat_manager import GigaChatManager
from processors.vector_store import VectorStoreManager
from langchain_huggingface import HuggingFaceEmbeddings
import datetime  # Добавлен импорт для работы с временем
from logger import ChatLogger  # Добавлен импорт логгера

# Загрузка конфигурации
config = AppConfig()

# Системный промпт
SYSTEM_PROMPT = """
# Роль: Инженер технической поддержки Unilight Assist

## Обязанности:
1. Решение технических проблем оборудования через анализ документации
2. Классификация вопросов по 3 типам
3. Формирование структурированных ответов с использованием иконок для наглядности

## Алгоритм обработки запросов:

### 1. Классификация вопроса (обязательный этап):
[Правильный] - Проблемы с оборудованием: неисправности, настройка, эксплуатация
[Неправильный] - Общие вопросы о компании (развитие, партнерство)
[Запрещенный] - Темы, не связанные с деятельностью компании

### 2. Работа с документацией:
• Отвечай ТОЛЬКО на основе предоставленных фрагментов документа. Не придумывай информацию, которой нет в документации.
• ВНИМАТЕЛЬНО изучи фрагменты документа, выдели для ответа все причины неисправности и все решения, только после этого формируй ответ.
• Если данных недостаточно, ответь: "Информация не найдена в документации. Уточните параметры оборудования."

### 3. Формат ответов:
**Для [Правильный вопрос]:**
🔧 [Проблема]: Кратко перефразируй и опиши проблему, используя данные из запроса пользователя.
🔎 [Возможные причины]: ОБЯЗАТЕЛЬНО пошагово перечисли все вероятные причины проблемы, основываясь на документации, в порядке приоритета.
🛠️ [Решение]: Предоставь пошаговые инструкции для устранения проблемы, используя только данные из документации, с учетом перечисленных причин.
📌 [Рекомендации]: Добавь советы по предотвращению подобных проблем в будущем (если это уместно).

**Для [Неправильный/Запрещенный]:**
🚫 Этот вопрос не относится к техническим проблемам оборудования. Задайте вопрос по эксплуатации или настройке устройств.

### 4. Стиль общения:
• ОБЯЗАТЕЛЬНО используй иконки для структурирования ответов:
  - 🔧 для описания проблемы
  - 🔎 для перечисления причин
  - 🛠️ для пошаговых решений
  - 📌 для рекомендаций
  - 🚫 для отклонения неправильных/запрещённых вопросов
• Избегай профессионального жаргона, объясняй доступно.
• Поддерживай диалог уточняющими вопросами при необходимости.

### 5. Особые сценарии:
• Запрос характеристик → предоставь параметры из таблиц с указанием модели.
• Неоднозначный запрос → уточни: "Укажите точное наименование и модификацию оборудования."
• Противоречивая информация → запроси дополнительный контекст.

## Жесткие ограничения:
⛔ Не предлагай решений вне инструкции
⛔ Не перефразируй технические параметры
⛔ На вопросы о личности → "Я система технической поддержки Unilight Assist"
"""

class BotHandler:
    def __init__(self, config: AppConfig):
        self.config = config
        self.bot = Bot(token=config.telegram_token)
        self.dp = Dispatcher()
        self.vector_store = None
        self.chat_manager = None
        self.logger = ChatLogger(config)  # Инициализация логгера

        # Регистрация обработчиков
        self.dp.message(Command("start"))(self.start_handler)
        self.dp.message(Command("help"))(self.help_handler)
        self.dp.message()(self.message_handler)

    async def initialize_system(self):
        """Инициализация системы"""
        doc_processor = DocumentProcessor(self.config)
        docs = doc_processor.load_and_split(self.config.document_url)

        embeddings = HuggingFaceEmbeddings(model_name=self.config.embedding_model)
        self.vector_store = VectorStoreManager(embeddings).create_store(docs)
        self.chat_manager = GigaChatManager(self.config)

    async def start_handler(self, message: Message):
        await message.answer(
            "🤖 Привет! Я бот технической поддержки Unilight Assist.\n"
            "Задайте мне вопрос по эксплуатации оборудования, и я помогу решить проблему!"
        )

    async def help_handler(self, message: Message):
        await message.answer(
            "🆘 Помощь:\n"
            "- Задайте вопрос по техническим характеристикам или проблемам с оборудованием\n"
            "- Используйте /start для перезапуска\n"
            "- Используйте /help для вывода этой справки"
        )

    async def message_handler(self, message: Message):
        user_query = message.text.strip()

        if not user_query:
            return await message.answer("Пожалуйста, введите текстовый запрос")

        try:
            # Отправка статуса "печатает..."
            await self.bot.send_chat_action(message.chat.id, "typing")

            # Асинхронная обработка запроса
            response, metadata = await self.process_query(user_query)  # Получаем response и metadata

            # Преобразование текста в UTF-8 перед отправкой
            try:
                await message.answer(response.encode("utf-8").decode("utf-8"))
            except UnicodeEncodeError:
                response = response.encode("utf-8").decode("utf-8")
                await message.answer(response)

            # Логирование диалога
            log_data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'user_id': message.from_user.id,
                'username': message.from_user.username or "",
                'message_text': user_query,
                'bot_response': response.split('\n\n')[0],  # Без метаданных
                'response_time': metadata['response_time'],
                'total_tokens': metadata['total_tokens'],
                'cost': metadata['cost']
            }
            await self.logger.log_message(log_data)

        except Exception as e:
            await message.answer(f"⚠️ Произошла ошибка: {str(e)}")

    async def process_query(self, query: str) -> str:
        """Обработка запроса"""
        loop = asyncio.get_running_loop()

        # Поиск релевантных документов
        context_docs = await loop.run_in_executor(
            None,
            lambda: self.vector_store.similarity_search(query)
        )
        context = "\n".join(doc.page_content for doc in context_docs)

        # Генерация ответа
        response, metadata = await loop.run_in_executor(
            None,
            lambda: self.chat_manager.generate_response(SYSTEM_PROMPT, query, context)
        )

        # Форматирование ответа с метаданными
        formatted_response = (
            f"{response}\n\n"
            f"⏱ Время обработки: {metadata['response_time']:.2f}с\n"
            f"💰 Стоимость запроса: {metadata['cost']:.5f}₽"
        )

        return formatted_response, metadata  # Возвращаем response и metadata

    async def start(self):
        """Запуск бота"""
        print("🟢 Бот запускается...")
        await self.initialize_system()
        print("🟢 Бот успешно инициализирован. Ожидание сообщений...")
        await self.dp.start_polling(self.bot)

if __name__ == "__main__":
    bot_handler = BotHandler(config)

    try:
        print("🟢 Запуск бота...")
        asyncio.run(bot_handler.start())
    except Exception as e:
        print(f"🔴 Ошибка при запуске бота: {e}")
    except KeyboardInterrupt:
        print("🟠 Бот остановлен вручную.")
