# Проект codeGen

## Установка и настройка MinIO

1. Скачайте и установите MinIO с [официального сайта](https://min.io/download).
2. Запустите MinIO.
3. Откройте браузер и перейдите по адресу `http://127.0.0.1:9000`.
4. Введите `minioadmin` в качестве имени пользователя и пароля для входа.
5. Создайте новый бакет с именем `codegen`.

## Созданиe виртуального окружения Python

``` bash
uv venv --python 3.13 --prompt code_gen --seed 
source .venv/bin/activate
pip install -r requirements.txt
```

## Подгрузка шаблонизатора

Выполните следующие команды в корне проекта:

```bash
git submodule init
git submodule update
```

## Запуск проекта

1. Примените миграции:

   ```bash
   python manage.py migrate
   ```

2. Создайте пользователей:

   ```bash
   python codeGen/create_users.py
   ```

3. Добавьте в `/etc/hosts` следующее:

  ```bash
  127.0.0.1 postgres
  127.0.0.1 mailpit
  127.0.0.1 s3.minio.localhost
  ```

4. Поднимите проект:

   ```bash
   docker compose up
   ```

## Конечные точки (Endpoints)

### Авторизация пользователя

**POST** `/login/`

- **Описание:** Авторизация пользователя.
- **Тело запроса:**

  ```json
  {
    "email": "user@example.com",
    "password": "yourpassword"
  }
  ```

- **Пример cURL:**

  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"email": "user@example.com", "password": "yourpassword"}' http://localhost:8000/login/
  ```

### Регистрация пользователя

**POST** `/create_user/`

- **Описание:** Регистрация нового пользователя.
- **Тело запроса:**

  ```json
  {
    "email": "user@example.com",
    "firstname": "John",
    "lastname": "Doe",
    "password": "yourpassword"
  }
  ```

- **Пример cURL:**

  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"email": "user@example.com", "firstname": "John", "lastname": "Doe", "password": "yourpassword"}' http://localhost:8000/create_user/
  ```

### Загрузка файла

**POST** `/upload/`

- **Описание:** Загрузка файла и создание проекта.
- **Тело запроса:** Файл с ключом `file`, а также поля:

  ```json
  {
    "project_name": "Project Name",
    "description": "Project Description",
    "project_type": "Type",
    "status": "Status"
  }
  ```

- **Пример cURL:**

  ```bash
  curl -X POST -F "file=@path/to/your/file" -F "project_name=Project Name" -F "description=Project Description" -F "project_type=Type" -F "status=Status" http://localhost:8000/upload/
  ```

### Скачивание файла

**GET** `/download/<file_id>/<file_name>/`

- **Описание:** Скачивание файла по идентификатору и имени файла.
- **Пример cURL:**

  ```bash
  curl -X GET http://localhost:8000/download/<file_id>/<file_name>/ --output <local_file_name>
  ```

### Просмотр проектов пользователя

**GET** `/user_projects/<email>/`

- **Описание:** Получение списка проектов пользователя по его email.
- **Пример cURL:**

  ```bash
  curl -X GET http://localhost:8000/user_projects/user@example.com/
  ```

### Доступ только для администратора

**GET** `/admin-only/`

- **Описание:** Информация доступна только администраторам.
- **Пример cURL:**

  ```bash
  curl -X GET http://localhost:8000/admin-only/
  ```

### Документация API

- **JSON-схема API:**
  **GET** `/api/schema/`
- **Swagger UI:**
  **GET** `/api/docs/`
