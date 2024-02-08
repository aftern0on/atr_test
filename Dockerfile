# Образ с Python 3
FROM python:3.11

# Установка рабочей директории в контейнере
WORKDIR /usr/src/app

# Копирование файла зависимостей и установка зависимостей pipenv
COPY ./Pipfile ./Pipfile.lock ./
RUN pip3 install pipenv && pipenv install --system

# Копирование остальных файлов проекта
COPY . .

# Запуск сервер Django на порту 8000 используя pipenv
CMD ["pipenv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]

