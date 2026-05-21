# Heat Analytics System

Система анализа теплопотребления многоквартирных домов (МКД) для магистерского диплома.

## 📋 Описание

Веб-приложение для загрузки, анализа и визуализации данных теплосчётчиков МКД с использованием статистических моделей машинного обучения.

### Основные возможности

- **Загрузка данных**: Импорт Excel-файлов с показаниями теплосчётчиков
- **Регрессионный анализ**: OLS, Huber, Ridge, Lasso, квантильная регрессия
- **Временные ряды**: Декомпозиция, Holt-Winters, Prophet
- **Поиск аномалий**: EWMA, Isolation Forest, LOF, консенсус-детектирование
- **Кластеризация**: K-Means++, DBSCAN, GMM
- **Экспорт отчётов**: PDF и CSV форматы

## 🛠 Технологический стек

| Компонент | Технология |
|-----------|------------|
| Backend | Python 3.10+, FastAPI, SQLAlchemy (async) |
| Analytics | pandas, numpy, scikit-learn, statsmodels, prophet |
| Frontend | React 18, Vite, TypeScript, TailwindCSS, Recharts |
| Database | SQLite (aiosqlite) |
| Контейнеризация | Docker, docker-compose |

## 🚀 Быстрый старт

### Требования

- Docker и Docker Compose
- Или Python 3.10+ и Node.js 18+ для локальной разработки

### Запуск через Docker (рекомендуется)

```bash
cd heat-analytics
docker-compose up --build
```

После запуска:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger документация: http://localhost:8000/docs

### Локальная разработка

#### Backend

```bash
cd heat-analytics
poetry install
poetry run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd heat-analytics/frontend
npm install
npm run dev
```

## 📁 Структура проекта

```
heat-analytics/
├── backend/
│   ├── main.py                 # FastAPI приложение
│   ├── config/                 # Настройки (settings.py, norms.yaml)
│   ├── models/                 # SQLAlchemy модели + Pydantic схемы
│   ├── routers/                # API эндпоинты
│   │   ├── upload.py           # Загрузка файлов
│   │   ├── analysis.py         # Запуск анализа
│   │   ├── results.py          # Получение результатов
│   │   ├── buildings.py        # Управление зданиями
│   │   └── export.py           # Экспорт отчётов
│   ├── services/               # Бизнес-логика
│   │   ├── db.py               # База данных
│   │   ├── parser.py           # Парсинг Excel
│   │   └── analytics_runner.py # Пайплайн анализа
│   └── analytics/              # Аналитические модули
│       ├── features.py         # Генерация признаков
│       ├── regression.py       # Регрессионные модели
│       ├── timeseries.py       # Анализ временных рядов
│       ├── anomaly.py          # Поиск аномалий
│       └── clustering.py       # Кластеризация
├── frontend/
│   ├── src/
│   │   ├── components/         # React компоненты
│   │   ├── pages/              # Страницы приложения
│   │   └── services/           # API клиент
│   └── package.json
├── data/                       # Данные (SQLite, uploads, reports)
├── tests/                      # Тесты
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## 📊 Формат входных данных

Excel-файлы должны содержать:
- Строки 1-4: Метаданные (отчёт, тепловычислитель, потребитель, схема)
- Строка 5: Заголовки колонок
- Строки 6+: Данные измерений

### Ожидаемые колонки

| Колонка | Описание |
|---------|----------|
| Дата | Дата измерения (DD.MM.YYYY или MM/DD/YY) |
| Время | Время измерения |
| T1 | Температура подачи (°C) |
| T2 | Температура обратки (°C) |
| P1, P2 | Давление в подаче/обратке |
| V1, V2 | Объёмный расход |
| M1, M2 | Массовый расход |
| Q | Тепловая энергия (Гкал) |
| НС | Коды нештатных ситуаций |
| Состояние | Статус измерения |

## 🔬 Аналитические методы

### 1. Регрессионный анализ (раздел 1.2.1 диплома)

- **OLS** - Обычный метод наименьших квадратов
- **Huber** - Робастная регрессия
- **Ridge/Lasso** - Регуляризация
- **Quantile** - Квантильная регрессия

### 2. Анализ временных рядов (раздел 1.2.2)

- **Seasonal Decompose** - Сезонная декомпозиция
- **Holt-Winters** - Экспоненциальное сглаживание
- **Prophet** - Прогнозирование от Facebook

### 3. Поиск аномалий (раздел 2.2.iii)

- **EWMA** - Экспоненциально взвешенное скользящее среднее
- **Isolation Forest** - Лес изоляции
- **LOF** - Local Outlier Factor
- **Consensus** - Консенсусное детектирование

### 4. Кластеризация (раздел 1.2.3)

- **K-Means++** - K-средних с улучшенной инициализацией
- **DBSCAN** - Плотностная кластеризация
- **GMM** - Гауссовы смеси

## ⚙️ Конфигурация

Переменные окружения (через `.env` файл):

```bash
DB_PATH=./data/heat_analytics.db
NORM_HDD=4500
ANOMALY_THRESHOLD=3.0
CLUSTER_K=4
LOG_LEVEL=INFO
```

## 🧪 Тестирование

```bash
# Запустить все тесты
poetry run pytest

# С отчётом о покрытии
poetry run pytest --cov=backend --cov-report=html
```

## 📝 API Endpoints

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/api/upload` | Загрузка Excel файла |
| POST | `/api/analyze` | Запуск анализа |
| GET | `/api/results/{run_id}` | Получение результатов |
| GET | `/api/results/{run_id}/summary` | Сводка результатов |
| GET | `/api/results/{run_id}/chart-data` | Данные для графиков |
| GET | `/api/buildings` | Список зданий |
| POST | `/api/export/pdf` | Экспорт PDF отчёта |
| GET | `/api/export/csv/{building_id}` | Экспорт CSV |

## 📄 Лицензия

Учебный проект для магистерского диплома.

## 👨‍💻 Автор

Студент магистратуры
Email: student@example.com
