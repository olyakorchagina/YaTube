# Социальная сеть YaTube

### Описание проекта
Проект создан в рамках учебного курса Яндекс.Практикум.

Социальная сеть для публикации личных записей. Пользователи могут создавать собственную учетную запись, публиковать посты с изображниями, а также подписываться на других авторов и оставлять комментари к их постам. 

Проект реализован на MVT-архитектуре, реализована система регистрации новых пользователей, восстановление паролей пользователей через почту, подключена пагинация постов и кэширование страниц. Для тестирования работы проекта использован unittest

### Системные требования
* Python 3.7+
* Works on Linux, Windows, macOS

### Стек технологий
* Python 3.7
* Django 2.2 
* Unittest
* Pytest
* SQLite3
* CSS
* JS
* HTML

### Установка проекта из репозитория

1. Клонировать репозиторий и перейти в него в командной строке:
```bash
git clone git@github.com:olyakorchagina/YaTube.git
cd YaTube
```
2. Cоздать и активировать виртуальное окружение:
```bash
python3 -m venv env
source env/bin/activate
```
3. Установить зависимости из файла ```requirements.txt```:
```bash
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```
4. Выполнить миграции:
```bash
cd yatube
python3 manage.py migrate
```
5. Запустить проект (в режиме сервера Django):
```bash
python3 manage.py runserver
```
