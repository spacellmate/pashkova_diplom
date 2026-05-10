# Проект «Свой Повар"

Готовый локальный проект без изменения дизайна сайта.

## Что сделано
- сайт запускается локально как обычный сайт;
- добавлена обязательная галочка согласия на обработку персональных данных;
- добавлен счетчик посещений;
- заявки сохраняются в CSV и XLSX на вашем компьютере.

## Состав проекта
- `povar.html` — страница сайта;
- `app.py` — backend на Flask;
- `requirements.txt` — зависимости;
- `data/` — появится автоматически после запуска, там будут база и таблицы.

## Запуск на Windows
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Сайт будет на `http://localhost:8000`.

## Публичная ссылка без роутера
```powershell
cloudflared tunnel --url http://localhost:8000
```

Пока сервер и `cloudflared` работают, люди смогут заходить по выданной ссылке.

## Где смотреть заявки
- `data/submissions.csv`
- `data/submissions.xlsx`

## Проверка статистики
- `http://localhost:8000/api/stats`
