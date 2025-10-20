# NeuroMotorica

> Нейром'язова платформа симуляції нервово-м'язових з'єднань (NMJ) з ко-трансмісією ацетилхоліну (ACh) та гістаміну (Hist), побудована за принципом *Perceive → Infer → Coach → Adapt*.

## Огляд
- **Фізіологічно обґрунтовані моделі**: `NMJ`, `EnhancedNMJ`, `OptimizedEnhancedNMJ`, `Muscle`.
- **Повний цикл дослідження**: від симуляцій до валідації та клінічних протоколів.
- **Автоматизована якість**: CI-матриця (Ubuntu/macOS/Windows, Python 3.9–3.12), статичний аналіз, тести, безпекові сканування.
- **Документація рівня клінічних досліджень**: етика, ризики, менеджмент даних, пререгістрація.

### Архітектура (фрактальна петля)
1. **Perceive** — генерація та очищення сигналу моторних одиниць (MU).
2. **Infer** — моделі NMJ (ACh/Hist) з адаптивними ядрами згортки.
3. **Coach** — персоналізація протоколів, API для рекомендацій.
4. **Adapt** — моніторинг, валідація, оновлення параметрів.

## Можливості
- **Симуляції**: сценарії одиночних імпульсів, пуассонівські та пачкові режими з профілями `data/profiles/*.json`.
- **Патології**: моделювання міастенії, ALS, каналопатій.
- **Візуалізація**: CLI-команди `plot`, `run-demo`, генерація графіків у `outputs/`.
- **Валідація**: автоматична перевірка проти діапазонів у `data/benchmarks/physio_ranges.json`.
- **API**: REST-сервіс для запису та рекомендацій підказок (`run-api`).
- **Розширення**: стохастична надійність, механочутливість, трипартидна модуляція.

## Швидкий старт
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
python -m pip install -U pip
pip install -e ".[dev]"
```

Після встановлення доступний CLI `neuromotorica`.

### Типові сценарії
```bash
# Симуляція моторних одиниць з валідацією та вибором профілю
neuromotorica simulate --seconds 1.0 --units 64 --rate 10 --profile baseline

# Порівняння моделі з ко-трансмісією проти базової
neuromotorica validate-model --seconds 2.0 --rate 25

# Візуалізація активності та сили у каталозі outputs/ для профілю реабілітації
neuromotorica plot --seconds 1.0 --units 64 --rate 10 --outdir outputs --profile rehab

# Демо-петля (сенсорика → рекомендації)
neuromotorica run-demo --data sample_data/mock_reps.json

# API персоналізації (Swagger доступний на /docs)
neuromotorica run-api --host 0.0.0.0 --port 8000
```

## Структура проєкту
```
├── docs/                 # MkDocs-документація (моделі, алгоритми, клінічні протоколи)
├── src/neuromotorica/    # Ядро симуляції, CLI, API
├── data/                 # Еталонні діапазони та приклади даних
├── tests/                # Pytest-набори (модульні та інтеграційні)
├── sample_data/          # Вхідні дані для демо та інтеграційних тестів
└── mkdocs.yml            # Конфігурація документації
```

## Розробка та якість
- **Тестування**: `pytest` (покриття, property-based, golden-файли).
- **Статика**: `ruff`, `mypy`, `bandit`, `pip-audit`.
- **Git hooks**: `pre-commit` (форматування, лінт, безпека).
- **CI/CD**: GitHub Actions (матриця ОС × версії Python), `CodeQL`, `actionlint`.

Для локального циклу розробки:
```bash
pre-commit install
pytest
ruff check src tests
mypy src
```

## Документація
- Повний портал: `mkdocs serve`
- Основні розділи: модель, алгоритми, валідація, оптимізації, API, протоколи R&D.

## Дані та валідація
- Еталонні діапазони: `data/benchmarks/physio_ranges.json`.
- Метрики: twitch amplitude, tetanus ratio, SNR, failure rate.
- Автозвіт CLI `simulate` із JSON-виходом для аналізу (конфіг включає обраний профіль).

## Контрибуція
Будь ласка, ознайомтеся з `CONTRIBUTING.md`, використовуйте семантичні заголовки PR та підтримуйте 100% прохідність CI.

## Ліцензія
MIT (research only). Для публікацій додавайте посилання на цей репозиторій.

## Цитування
```bibtex
@software{neuromotorica,
  title        = {NeuroMotorica: NMJ co-transmission simulation platform},
  year         = {2025},
  url          = {https://github.com/NeuroMotorica/NeuroMotorica}
}
```
