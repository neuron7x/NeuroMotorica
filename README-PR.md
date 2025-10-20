# PR Quality Pack
Розпакуйте в корінь репозиторію NeuroMotorica.
- Код модуля: `modules/neuromotorica_universal`
- Тести: `modules/neuromotorica_universal/tests`
- CI: `.github/workflows/pr.yml`, `security.yml`
Локальні команди:
  cd modules/neuromotorica_universal && pip install -e ".[dev]" && pytest
