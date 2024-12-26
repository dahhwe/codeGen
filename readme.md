
# Проект codeGen

## Установка и настройка MinIO

1. Скачайте и установите MinIO с [официального сайта](https://min.io/download).
2. Запустите MinIO
3. Откройте браузер и перейдите по адресу `http://127.0.0.1:9000`.
4. Введите `minioadmin` в качестве имени пользователя и пароля для входа.
5. Создайте новый бакет с именем `codegen`.

## Запуск проекта


1. Примените миграции:
   ```bash
   python manage.py migrate
   ```
2. Создайте пользователей:
   ```bash
   python codeGen/create_users.py
   ```
3. Запустите сервер:
   ```bash
   python manage.py runserver
   ```

## Конечные точки (Endpoints)

### Доступ только для администратора

**GET** `http://localhost:8000/admin-only/`

Эта конечная точка доступна только для администратора. Используйте учетные данные администратора для доступа.

### Загрузка файла

**POST** `http://localhost:8000/upload/`

Тело запроса должно содержать файл с ключом `file`. Пример запроса с использованием `curl`:

```bash
curl -X POST -F "file=@path/to/your/file" http://localhost:8000/upload/
```

### Вход пользователя

**POST** `http://localhost:8000/login/`

Тело запроса должно содержать JSON с полями `email` и `password`. Пример запроса с использованием `curl`:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"email": "user@example.com", "password": "yourpassword"}' http://localhost:8000/login/
```

### Регистрация пользователя

**POST** `http://localhost:8000/create_user/`

Тело запроса должно содержать JSON с полями `email`, `firstname`, `lastname` и `password`. Пример запроса с использованием `curl`:

```bash
curl -X POST -H "Content-Type: application/json" -d '{"email": "user@example.com", "firstname": "John", "lastname": "Doe", "password": "yourpassword"}' http://localhost:8000/create_user/
```