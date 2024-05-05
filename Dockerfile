# Вибір базового образу Python
FROM python:3.10-slim

# Встановлення необхідних пакетів для MongoDB
RUN pip install pymongo

# Створення директорії для застосунку
WORKDIR /app

# Копіювання коду в контейнер
COPY . . 

EXPOSE 3000

# Запуск застосунку
CMD ["python", "main.py"]
