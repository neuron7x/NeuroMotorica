# NeuroMotorica (2025)

Повноцінна **нейрофізіологічна система симуляції NMJ з ко-трансмісією (ACh+Hist)** —
тепер під новою назвою **NeuroMotorica**. Все, що було, збережено й покращено:
фрактальна архітектура (**Perceive → Infer → Coach → Adapt**), візуалізація, валідація,
та **максимально автоматизовані GitHub-тести для кожного PR**.

## Ключове
- Модель: `NMJ`, `EnhancedNMJ`, `OptimizedEnhancedNMJ` (нелінійна інтеграція ACh×Hist,
  zero-phase biquad), `Muscle`.
- Аналіз: сценарії (single/poisson/burst), патології (міастенія, ALS), **валідація проти
  літературних діапазонів** (див. `data/benchmarks/physio_ranges.json`).
- Візуалізація: CLI `neuromotorica plot` генерує графіки активації/сил/спайків і зберігає в `outputs/`.
- CI: **matrix (Ubuntu/macOS/Windows + py3.9–3.12)**, лінт, формат, типи, юніт-тести з покриттям,
  **pre-commit**, **CodeQL**, **pip-audit**, **Bandit**, **actionlint**, артефакти (coverage, звіти, графіки).
- PR-гейт: Semantic PR title check; усі джоби запускаються на `pull_request`.

## Оптимізації ядра (v0.5.0)
- **Стабільне нормалізоване альфа-ядро**: уникнення числової нестабільності при `tau_rise ≈ tau_decay`.
- **Адаптивна згортка**: автоматичний вибір між `np.convolve` та **FFT-згорткою** для довгих послідовностей.
- **Zero-phase biquad** фільтрація — без SciPy, сумісно з CI.

## Встановлення
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e ".[dev]"
```

## Приклади
```bash
# Демо edge-петлі
neuromotorica run-demo --data sample_data/mock_reps.json

# Симуляції + патології (JSON)
neuromotorica simulate --seconds 1.0 --units 64 --rate 10

# Порівняння база vs ко-трансмісія
neuromotorica validate-model --seconds 2.0 --rate 25

# Побудова графіків у outputs/
neuromotorica plot --seconds 1.0 --units 64 --rate 10 --outdir outputs

# API персоналізації (Swagger /docs)
neuromotorica run-api --host 0.0.0.0 --port 8000
```

## Документація
- `docs/` (MkDocs): модель, алгоритми, валідація, оптимізація, API, протокол, етика, ризики, дані.
- `data/benchmarks/physio_ranges.json` — емпіричні діапазони для тестів.

## Ліцензія
MIT (research only).


## Extended Features (v0.6.0)
- Stochastic reliability (channel noise)
- Mechano-sensitivity (topography)
- Tripartite modulation (glia)
