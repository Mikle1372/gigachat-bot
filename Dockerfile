FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Установка зависимостей
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Копируем исходный код
COPY . .


# Команда для запуска бота
CMD ["python", "bot.py"]
